#!/usr/bin/env python3
"""Merge Symbola's vector glyphs into the recomposited sbix emoji font.

`make_emoji_font.py` produces a colour `sbix` font whose emoji sit on the donor
CJK cell, but it only carries actual emoji. Non-emoji codepoints in the SMP
emoji blocks (enclosed alphanumerics like U+1F154 NEGATIVE CIRCLED LATIN CAPITAL
LETTER E, mahjong, dominoes, playing cards, supplemental arrows) have no glyph
and render as tofu. This script fills those holes with Symbola's outlines,
re-fit to the same CJK cell, added as plain `glyf` glyphs (no `sbix` strike) so
they render as crisp monochrome vector at any size.

Cell width per codepoint follows wcwidth -- the same rule kitty uses: W/F -> 2
cells, everything else -> 1 cell. East-Asian *Ambiguous* codepoints (the
enclosed alphanumerics like U+1F154 🅔) are therefore **1 cell** by default,
matching kitty / the terminal. Pass AMBIGUOUS=wide for a CJK-context 2-cell
layout instead. The outline is scaled to ~the CJK ink height, clamped to the
cell, centred horizontally, and sat on the baseline.

Usage:
  merge_symbola.py BASE.ttf SYMBOLA.ttf DONOR_CJK.ttf OUT.ttf \
                   [LO=0x1F000] [HI=0x1FFFF] [TARGET_H_EM=0.78] [AMBIGUOUS=narrow|wide]

  BASE.ttf    output of make_emoji_font.py (sbix colour emoji on the CJK cell)
  SYMBOLA.ttf Symbola source (monochrome vector symbols)
  DONOR_CJK   the SAME CJK mono font used to build BASE (the metrics donor)
  OUT.ttf     merged font

POC tip: pass LO==HI to merge a single codepoint, e.g. `... OUT.ttf 0x1F154 0x1F154`.
"""
import sys
import unicodedata
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.sbixGlyph import Glyph as SbixGlyph
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

base_p, symb_p, donor_p, out_p = sys.argv[1:5]
LO = int(sys.argv[5], 0) if len(sys.argv) > 5 else 0x1F000
HI = int(sys.argv[6], 0) if len(sys.argv) > 6 else 0x1FFFF
TARGET_H_EM = float(sys.argv[7]) if len(sys.argv) > 7 else 0.78
# Width policy for East-Asian *Ambiguous* codepoints (the enclosed alphanumerics,
# 🅔 etc.). Default "narrow" = 1 cell, matching kitty / standard wcwidth. Set
# "wide" for a CJK-context 2-cell layout.
AMBIG_WIDE = (sys.argv[8] if len(sys.argv) > 8 else "narrow").lower().startswith("w")
WIDTH_FILL = 0.92   # max fraction of the cell the ink may span before width-clamp

base = TTFont(base_p)
symb = TTFont(symb_p)
donor = TTFont(donor_p, fontNumber=0)

upm = base["head"].unitsPerEm

# --- donor cell metrics (the 2:1 grid) ---
dupm = donor["head"].unitsPerEm
cjk_adv_ratio = donor["hmtx"][donor.getBestCmap()[0x4E2D]][0] / dupm   # 中 advance / em
CELL2 = round(cjk_adv_ratio * upm)        # 2-cell advance (= 中)
CELL1 = round(CELL2 / 2)                   # 1-cell advance (ASCII, half of 2:1 cell)
TARGET_H = TARGET_H_EM * upm               # target ink height (base units)
print(f"cell2={CELL2} cell1={CELL1} target_h={TARGET_H:.0f} upm={upm}")

base_cmap = base.getBestCmap()
symb_cmap = symb.getBestCmap()
symb_gs = symb.getGlyphSet()

glyf = base["glyf"]
hmtx = base["hmtx"]
order = list(base.getGlyphOrder())
new_names = []

for cp in range(LO, HI + 1):
    if cp in base_cmap:           # base already covers it (emoji) -> keep colour
        continue
    sname = symb_cmap.get(cp)
    if not sname:                 # Symbola lacks it -> nothing to fill
        continue

    bp = BoundsPen(symb_gs)       # ink bounds (components auto-decomposed)
    symb_gs[sname].draw(bp)
    if bp.bounds is None:         # whitespace / empty -> skip
        continue
    xmin, ymin, xmax, ymax = bp.bounds
    ink_w = xmax - xmin
    ink_h = ymax - ymin
    if ink_w <= 0 or ink_h <= 0:
        continue

    eaw = unicodedata.east_asian_width(chr(cp))
    wide = eaw in ("W", "F") or (AMBIG_WIDE and eaw == "A")   # wcwidth / kitty
    adv = CELL2 if wide else CELL1

    k = TARGET_H / ink_h                      # scale to target ink height
    if ink_w * k > adv * WIDTH_FILL:          # too wide -> clamp to the cell
        k = adv * WIDTH_FILL / ink_w
    tx = (adv - k * ink_w) / 2 - k * xmin     # centre horizontally in the cell
    ty = -k * ymin                            # bottom on the baseline

    rec = DecomposingRecordingPen(symb_gs)    # flatten composites
    symb_gs[sname].draw(rec)
    gpen = TTGlyphPen(None)
    rec.replay(TransformPen(gpen, Transform(k, 0, 0, k, tx, ty)))

    gname = "symb%04X" % cp
    glyf[gname] = gpen.glyph()
    hmtx[gname] = (adv, round(tx + k * xmin))  # lsb == glyph xMin
    new_names.append((cp, gname))

# --- register the new glyphs ---
for _cp, gname in new_names:
    order.append(gname)
base.setGlyphOrder(order)
base["maxp"].numGlyphs = len(order)

# sbix is a per-GID array: give the new (colourless) glyphs empty strike entries
if "sbix" in base:
    for strike in base["sbix"].strikes.values():
        for _cp, gname in new_names:
            strike.glyphs[gname] = SbixGlyph(glyphName=gname)

# map the codepoints in every Unicode cmap subtable
for table in base["cmap"].tables:
    if table.isUnicode():
        for cp, gname in new_names:
            table.cmap[cp] = gname

base.save(out_p)
sample = ", ".join("U+%04X" % cp for cp, _ in new_names[:8])
print(f"merged {len(new_names)} Symbola glyphs into {out_p}")
if new_names:
    print(f"  e.g. {sample}{' …' if len(new_names) > 8 else ''}")
