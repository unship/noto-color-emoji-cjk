#!/usr/bin/env python3
"""Scale-proof sbix color emoji, with each glyph re-composited to sit like CJK.

Renderer clips bitmaps below the baseline, so originOffsetY must be 0. To make
the emoji look centered (match Maple's 中 ink box) we instead reposition the art
INSIDE each PNG: scale ink to ~中's height, center horizontally in the advance,
sit the bottom on the baseline.

Usage: build_centered.py NOTO_CBDT.ttf MAPLE.ttf OUT.ttf [TARGET_H_EM] [BOTTOM_EM] [NAME]
"""
import sys, io
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables.sbixStrike import Strike
from fontTools.ttLib.tables.sbixGlyph import Glyph as SbixGlyph
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image

inp, maple, out = sys.argv[1], sys.argv[2], sys.argv[3]
TARGET_H_EM = float(sys.argv[4]) if len(sys.argv) > 4 else 0.86
BOTTOM_EM   = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
newname = sys.argv[6] if len(sys.argv) > 6 else "Noto Color Emoji CJK Centered"
PPEM = 128

# --- Maple ratios ---
m = TTFont(maple, fontNumber=0)
mupm = m["head"].unitsPerEm
adv_ratio = m["hmtx"][m.getBestCmap()[0x4E2D]][0] / mupm
asc_ratio = m["hhea"].ascent / mupm
desc_ratio = -m["hhea"].descent / mupm
gap_ratio = m["hhea"].lineGap / mupm
print(f"Maple adv={adv_ratio:.4f} asc={asc_ratio:.4f} desc={desc_ratio:.4f}")

f = TTFont(inp)
upm = f["head"].unitsPerEm
order = f.getGlyphOrder()
advance_fu = round(adv_ratio * upm)
asc_fu, desc_fu, gap_fu = round(asc_ratio*upm), round(desc_ratio*upm), round(gap_ratio*upm)

# canvas: width == advance, height == ascent region (origin 0 puts bottom on baseline)
Wc, Hc = round(adv_ratio * PPEM), round(asc_ratio * PPEM)
ink_h = round(TARGET_H_EM * PPEM)
bottom_px = round(BOTTOM_EM * PPEM)
print(f"Noto upm={upm} advance={advance_fu} asc={asc_fu} desc={desc_fu} ppem={PPEM} "
      f"canvas={Wc}x{Hc} ink_h={ink_h}")

def reposition(png_bytes):
    im = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    bbox = im.getchannel("A").getbbox()           # ink bounds
    if bbox:
        im = im.crop(bbox)
    w, h = im.size
    nw = max(1, round(w * ink_h / h))
    im = im.resize((nw, ink_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    x = (Wc - nw) // 2                            # center horizontally
    y = Hc - ink_h - bottom_px                    # bottom on baseline (+ margin)
    canvas.paste(im, (x, y), im)
    o = io.BytesIO(); canvas.save(o, format="PNG"); return o.getvalue()

pngs = {}
for name, g in f["CBDT"].strikeData[0].items():
    if g.imageData[:8] == b"\x89PNG\r\n\x1a\n":
        pngs[name] = reposition(g.imageData)

# glyf dummy outline (box covers the canvas, on baseline)
def empty_glyph(): return TTGlyphPen(None).glyph()
def box_glyph(x0, y0, x1, y1):
    p = TTGlyphPen(None)
    p.moveTo((x0, y0)); p.lineTo((x1, y0)); p.lineTo((x1, y1)); p.lineTo((x0, y1)); p.closePath()
    return p.glyph()
bw, bh = round(Wc*upm/PPEM), round(Hc*upm/PPEM)
glyf = newTable("glyf"); glyf.glyphOrder = order; glyf.glyphs = {}
for nm in order:
    glyf.glyphs[nm] = box_glyph(0, 0, bw, bh) if nm in pngs else empty_glyph()
f["glyf"] = glyf; f["loca"] = newTable("loca"); f["head"].indexToLocFormat = 0
mp = f["maxp"]; mp.tableVersion = 0x00010000
for a in ("maxPoints","maxContours","maxCompositePoints","maxCompositeContours","maxZones",
          "maxTwilightPoints","maxStorage","maxFunctionDefs","maxInstructionDefs",
          "maxStackElements","maxSizeOfInstructions","maxComponentElements","maxComponentDepth"):
    setattr(mp, a, 0)
mp.maxZones = 1

for nm in order:
    f["hmtx"][nm] = (advance_fu, 0)

sbix = newTable("sbix"); sbix.version = 1; sbix.flags = 1; sbix.numStrikes = 1
strike = Strike(ppem=PPEM, resolution=72); strike.glyphs = {}
for nm in order:
    strike.glyphs[nm] = (SbixGlyph(glyphName=nm, graphicType="png ", imageData=pngs[nm],
                                   originOffsetX=0, originOffsetY=0)
                         if nm in pngs else SbixGlyph(glyphName=nm))
sbix.strikes = {PPEM: strike}
f["sbix"] = sbix
for t in ("CBDT", "CBLC"):
    if t in f: del f[t]

hhea, os2 = f["hhea"], f["OS/2"]
hhea.ascent, hhea.descent, hhea.lineGap = asc_fu, -desc_fu, gap_fu
os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = asc_fu, -desc_fu, gap_fu
os2.usWinAscent, os2.usWinDescent = asc_fu, desc_fu
os2.fsSelection |= (1 << 7)

ps = newname.replace(" ", "")
for rec in f["name"].names:
    if rec.nameID in (1, 4, 16): rec.string = newname
    elif rec.nameID == 6: rec.string = ps
    elif rec.nameID == 17: rec.string = "Regular"

f.save(out)
print("saved", out, "family:", newname)
