# Noto Color Emoji CJK

A **color-emoji + symbol font whose every glyph is pre-fit to the CJK character
cell**, so emoji and enclosed symbols stay perfectly column-aligned next to a
monospace CJK font — in grid-based editors, above all **Emacs**.

It is **not a general-purpose emoji font**. It is a *metrics-matched companion*:
you keep your equal-width CJK mono font as the primary, and route emoji/symbol
codepoints to this font, which has been rebuilt so each glyph occupies exactly
the right number of cells (`中`'s advance for wide chars, ASCII width for narrow
ones) at **every font size**.

```
|中|文|对|齐|测|试|字|符|宽|度|
|😀|🎉|🚀|🔥|💯|✨|🌟|🎨|🍕|🚗|   colour emoji — 2 cells each
|🅐|🅔|🀄|🂡|🁢|🅿|🆎|🄋|🄐|🅂|   merged Symbola symbols — same grid
```

Every `|` lines up straight down the columns. That is the whole point.

## Why it exists (the Emacs-specific reasons)

- **Emacs's macOS NS build only paints `sbix` color fonts.** `COLRv1` (Noto's
  native vector color) and `CBDT` render **blank**. So Noto Color Emoji's PNG
  strikes are extracted and repackaged into an `sbix` table.
- **Emoji must land on the 2-cell grid.** Each glyph is re-composited to sit on
  the donor CJK font's cell: ink scaled to ≈`中`'s height, centered in the
  advance, bottom on the baseline. Metrics are baked as ratios, and the font is
  routed **without `:size`**, so it tracks the primary font at px-18, px-22, …
- **Symbols that aren't emoji used to be tofu.** Codepoints like `🅔` (U+1F154)
  live in the emoji blocks but aren't color emoji, so a color-emoji font has no
  glyph for them. This font fills those holes with **Symbola** outlines, scaled
  and centered onto the same cell (see [How it works](#how-it-works)).

## Use in Emacs

Pair a monospace CJK font (the *primary*) with this font (the emoji/symbol
*fallback*):

```elisp
;; 1. Primary: an equal-width CJK mono font (ASCII : CJK = 1 : 2 cells)
(set-face-attribute 'default nil :family "Maple Mono NF CN" :height 140)

;; 2. Route emoji + symbols to the metrics-matched companion. On the macOS NS
;;    build, clear the target first (a built-in Apple Color Emoji entry would
;;    otherwise win the prepend), then set it. No :size -> it tracks the primary
;;    font's size at every step.
(let ((f (font-spec :family "Noto Color Emoji CJK")))
  (set-fontset-font t 'emoji nil)
  (set-fontset-font t 'emoji f)
  (set-fontset-font t '(#x1F000 . #x1FFFF) f))   ; enclosed alphanumerics, cards, …
```

Doom Emacs:

```elisp
(setq doom-font         (font-spec :family "Maple Mono NF CN" :size 14)
      doom-unicode-font (font-spec :family "Maple Mono NF CN" :size 14))

(add-hook! 'after-setting-font-hook
  (let ((f (font-spec :family "Noto Color Emoji CJK")))
    (set-fontset-font t 'emoji nil)
    (set-fontset-font t 'emoji f)
    (set-fontset-font t '(#x1F000 . #x1FFFF) f)))
```

Open [`tests/alignment.md`](tests/alignment.md) in GUI Emacs — every `|` column
must stay straight across ASCII / 中文 / 😀 / 🅔 rows.

> **Composition note:** ZWJ sequences, flags, and VS16 emoji-presentation
> (`base + U+FE0F`) need Emacs `auto-composition` plus the source font's GSUB;
> single-codepoint emoji are covered by this font directly. Enable
> `eaw-fullwidth` so East-Asian *Ambiguous* chars count as 2 columns for
> `string-width` / table alignment.

## Install

### Homebrew (recommended)

```sh
brew tap unship/fonts
brew install --cask font-noto-color-emoji-cjk
```

### Manual

Download `Noto-Color-Emoji-CJK.ttf` from the
[latest release](https://github.com/unship/noto-color-emoji-cjk/releases/latest)
and copy it to `~/Library/Fonts/`. Restart the Emacs daemon (a fresh daemon
avoids stale font-cache entries).

## Build it yourself

Tune the metrics to *your* CJK mono font by passing it as the donor:

```sh
make font DONOR="$HOME/Library/Fonts/MapleMono-NF-CN-Regular.ttf" \
          SYMBOLA="$HOME/Library/Fonts/Symbola_hint.ttf"
make install        # -> ~/Library/Fonts
```

`make` creates a venv (`fonttools` + `pillow`), downloads Noto Color Emoji's
CBDT build, runs the recompositor, then the Symbola merge. Useful targets:

| target | what it does |
|---|---|
| `make font` | build `Noto-Color-Emoji-CJK.ttf` |
| `make poc` | merge **only** `🅔` and install — validates NS rendering before the full build |
| `make install` | copy the font into `~/Library/Fonts` |
| `make clean` | remove `build/` and the output |

Override `DONOR`, `SYMBOLA`, `EMOJI_H_EM`, `SYMBOL_H_EM`, `LO`, `HI` as needed.

## How it works

Two stages, both fitting glyphs to the donor CJK cell:

1. **`scripts/make_emoji_font.py`** — extracts Noto Color Emoji's PNG strikes and
   rebuilds them as an `sbix` font. Because the NS renderer clips bitmaps below
   the baseline, each PNG is re-composited (trim to ink → scale to ≈`中`'s height
   → center in the advance → bottom on the baseline) rather than offset.

2. **`scripts/merge_symbola.py`** — for every codepoint in the emoji blocks that
   Symbola covers but the emoji font does not, it copies Symbola's **vector**
   outline, picks the cell width from
   [`unicodedata.east_asian_width`](https://docs.python.org/3/library/unicodedata.html)
   (`W/F/A → 2 cells`, else `1 cell`), scales the ink to ≈`中`'s height (clamped
   to the cell), centers it, and adds it as a plain `glyf` glyph **with no `sbix`
   strike** — so it renders as crisp monochrome vector at any size while the
   emoji stay color. The result is a hybrid `sbix` (color) + `glyf` (mono) font
   on one cell grid.

## License

The font (`Noto-Color-Emoji-CJK.ttf`) is licensed under the **SIL Open Font
License 1.1** ([`LICENSE`](LICENSE)); see [`NOTICE`](NOTICE) for attribution of
Noto Color Emoji (OFL), Symbola (George Douros' permissive grant), and Maple
Mono (metrics donor — no glyph embedded). The build scripts in
[`scripts/`](scripts/) are MIT-licensed.

"Noto" is used per the Noto project's policy that its fonts carry **no Reserved
Font Name**, so derivatives may keep the name. This is a community derivative and
is not affiliated with or endorsed by Google or the Noto project.
