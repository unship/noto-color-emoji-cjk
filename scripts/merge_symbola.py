#!/usr/bin/env python3
"""Merge Symbola's vector glyphs into the recomposited sbix emoji font.

`make_emoji_font.py` produces a colour `sbix` font whose emoji sit on the donor
CJK cell. This script makes the font match kitty by *presentation*: every
codepoint that is NOT Unicode Emoji_Presentation=Yes -- the text-presentation
symbols (enclosed alphanumerics like U+1F154 🅔, mahjong, cards, and dingbats
like ★ ❤ ☀ that kitty draws as 1-cell mono) -- is routed to a cell-fitted
Symbola outline, added as a plain `glyf` glyph (no `sbix` strike) so it renders
as crisp monochrome vector at any size. Emoji-presentation codepoints (😀 ⌚ ⏰
✅) keep their 2-cell colour glyph. This OVERRIDES the colour glyph for
text-presentation chars Noto happens to cover (❤ ☀ ✈ …), matching kitty.

Cell width per codepoint follows wcwidth -- the same rule kitty uses: W/F -> 2
cells, everything else -> 1 cell. East-Asian *Ambiguous* codepoints (the
enclosed alphanumerics like U+1F154 🅔) are therefore **1 cell** by default,
matching kitty / the terminal. Pass AMBIGUOUS=wide for a CJK-context 2-cell
layout instead. The outline is scaled to ~the CJK ink height, clamped to the
cell, centred horizontally, and sat on the baseline.

Usage:
  merge_symbola.py BASE.ttf SYMBOLA.ttf DONOR_CJK.ttf OUT.ttf \
                   [RANGES=1F000-1FFFF,2300-23FF,2600-27BF] [TARGET_H_EM=0.78] [AMBIGUOUS=narrow|wide]

  BASE.ttf    output of make_emoji_font.py (sbix colour emoji on the CJK cell)
  SYMBOLA.ttf Symbola source (monochrome vector symbols)
  DONOR_CJK   the SAME CJK mono font used to build BASE (the metrics donor)
  OUT.ttf     merged font
  RANGES      comma-separated hex codepoint ranges to fill (e.g. "2600-27BF,1F154")

POC tip: pass a single codepoint as RANGES, e.g. `... OUT.ttf 1F154`.
"""
import sys
import os
import unicodedata
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.sbixGlyph import Glyph as SbixGlyph
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

base_p, symb_p, donor_p, out_p = sys.argv[1:5]
RANGES_STR = sys.argv[5] if len(sys.argv) > 5 else "1F000-1FFFF"
TARGET_H_EM = float(sys.argv[6]) if len(sys.argv) > 6 else 0.78
# Width policy for East-Asian *Ambiguous* codepoints (the enclosed alphanumerics
# 🅔, dingbats like ★ …). Default "narrow" = 1 cell, matching kitty / standard
# wcwidth. Set "wide" for a CJK-context 2-cell layout.
AMBIG_WIDE = (sys.argv[7] if len(sys.argv) > 7 else "narrow").lower().startswith("w")
WIDTH_FILL = 0.92   # max fraction of the cell the ink may span before width-clamp

def parse_ranges(s):
    rs = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        a, _, b = part.partition("-")
        lo = int(a, 16)
        rs.append((lo, int(b, 16) if b else lo))
    return rs

def iter_codepoints(ranges):
    for lo, hi in ranges:
        for cp in range(lo, hi + 1):
            yield cp

def load_emoji_presentation():
    """Codepoints with Unicode Emoji_Presentation=Yes (kept as 2-cell colour).
    Snapshot lives next to this script; regenerate from
    unicode.org/Public/UCD/latest/ucd/emoji/emoji-data.txt."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "emoji-presentation.txt")
    pres = set()
    with open(path) as fh:
        for line in fh:
            line = line.split("#")[0].strip()
            if not line:
                continue
            if ".." in line:
                a, b = line.split("..")
                pres.update(range(int(a, 16), int(b, 16) + 1))
            else:
                pres.add(int(line, 16))
    return pres

RANGES = parse_ranges(RANGES_STR)
EMOJI_PRES = load_emoji_presentation()

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

for cp in iter_codepoints(RANGES):
    if cp in EMOJI_PRES:          # default emoji presentation -> keep 2-cell colour
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
