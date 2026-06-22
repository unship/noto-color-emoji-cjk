# Noto Color Emoji CJK — Open-Source + Symbola Merge

- **Date:** 2026-06-22
- **Status:** Implemented; released as **v1.1.0**. This is the design snapshot — see
  the [README](README.md) for as-built behavior.
- **As-built refinement:** the final width model is *presentation-aware* —
  `Emoji_Presentation=Yes` → 2-cell color, text-presentation → 1-cell mono
  (overriding Noto's color glyph for ❤ ☀ ✈ …) — refining the wcwidth-only rule
  sketched in §5.3.
- **Origin:** Doom module `modules/my/font/emoji/` (build script + docs already existed)

---

## 1. Context

`make-emoji-font.py` already builds **Noto Color Emoji CJK**: it extracts Noto
Color Emoji's PNG strikes and repackages them as an `sbix` color font in which
every glyph is re-composited to sit on the donor CJK font's cell (advance = 中's
width, ink scaled to ≈中's height, centered, bottom on baseline). This is needed
because the macOS **NS Emacs build only paints `sbix` color fonts** (`COLRv1`
and `CBDT` render blank), and because emoji must occupy the exact 2-cell grid at
every font size.

A gap surfaced: `config.el` routes the whole `#x1F000–#x1FFFF` range **solely**
to this font, but the font only carries actual emoji. Non-emoji codepoints in
that range (e.g. `🅔` U+1F154 NEGATIVE CIRCLED LATIN CAPITAL LETTER E, the rest
of the enclosed alphanumerics, mahjong, dominoes, playing cards, supplemental
arrows) have **no glyph** → "no font available". A runtime fontset gap-fill
(Symbola, coverage-driven) was added today as a stopgap. This project folds that
coverage **into the font itself** and publishes the result.

## 2. Use case / positioning

This is **not a standalone emoji font**. It is a **metrics-matched companion**
to a monospace CJK font, for **grid-based editors where every character cell
must line up** — primarily **Emacs**.

- **Primary font** = an equal-width CJK mono (ASCII : CJK = 1 : 2 cells), e.g.
  Maple Mono NF CN.
- **This font** = the emoji/symbol fallback, every glyph **pre-fit to that
  font's cell**, so `😀` and (after the merge) `🅔` never break column alignment.

Emacs-specific reasons it exists: (1) the NS build only paints `sbix` color
fonts; (2) it pairs with `eaw-fullwidth` (East-Asian Ambiguous width → 2 cells)
so the cell arithmetic agrees.

**Metrics are donor-specific.** They are baked from the CJK font passed to the
build (default donor = Maple Mono NF CN). Alignment is *exact* with the donor;
with another equal-width CJK mono it is close, and a one-line rebuild against
that font makes it exact. The build script's metrics argument is therefore
documented as **"your CJK mono font = the metrics donor."**

## 3. Goals / Non-goals

**Goals**
- Publish the pipeline as an OFL-1.1 open-source project (repo + README + tests + license).
- Merge Symbola's gap glyphs (codepoints in `#x1F000–#x1FFFF` that Symbola covers and Noto lacks; ~958 today) into the font, **cell-fitted** so they align like emoji.
- A GitHub Pages specimen page.
- `brew install` via a personal Homebrew tap.
- A built, **verified** artifact this session.

**Non-goals**
- ZWJ / flag / VS16 composition — that's Emacs `auto-composition`, font-independent.
- Merging *all* of Symbola — gaps only.
- Submitting to official `homebrew/cask` now — notability-gated for a new repo.
- Changing the Doom module's behavior — it just consumes the installed font. The
  runtime gap-fill stays as a fallback (no-ops once the merged font is installed).

## 4. Deliverables

1. **Public repo** `noto-color-emoji-cjk` — build scripts, README (with Emacs
   setup), `tests/alignment.md`, `LICENSE` (OFL-1.1) + `NOTICE`, and a **GitHub
   Release** carrying the built `.ttf` (~50 MB binary as a release asset, not
   git-tracked).
2. **Symbola gap-merge** integrated into the build (§5.3).
3. **GitHub Pages specimen** served from `/docs`.
4. **Homebrew tap** `homebrew-fonts` with `Casks/font-noto-color-emoji-cjk.rb`.

## 5. Architecture

### 5.1 Repo layout

```
noto-color-emoji-cjk/
├── README.md            # adapted from emoji/README.md; leads with use case + Emacs setup
├── LICENSE              # OFL 1.1  (binds the .ttf)
├── NOTICE               # Noto OFL · Symbola/Douros grant · Maple (metrics only)
├── Makefile             # venv -> fetch Noto CBDT -> build -> merge -> out
├── scripts/
│   ├── make_emoji_font.py   # existing recompositor (logic unchanged)
│   └── merge_symbola.py     # NEW: vector gap-merge
├── tests/alignment.md   # the alignment test sheet
├── docs/index.html      # GitHub Pages specimen (static, no framework)
└── .github/workflows/release.yml   # optional: build -> release -> deploy Pages
```

Standalone clone at `~/src/noto-color-emoji-cjk`. The Doom module is unchanged.

### 5.2 Build pipeline (unchanged)

`make_emoji_font.py NOTO_CBDT.ttf DONOR_CJK.ttf OUT.ttf [TARGET_H_EM] [BOTTOM_EM] [NAME]`
produces the `sbix` color font with emoji on the donor's cell grid.

### 5.3 Symbola vector merge — the core

**Scope:** codepoints in `[#x1F000, #x1FFFF]` that Symbola covers and the
recomposited font does not (computed live from both fonts' glyph coverage — the
same coverage-driven rule the runtime gap-fill uses, so it self-corrects when
either font changes). ~958 codepoints today.

**Approach A — vector `glyf` (recommended).** For each gap codepoint:
1. Resolve Symbola's outline (decompose composites to simple contours).
2. Determine cell width by `wcwidth` (kitty's rule): `W/F → 2 cells` (= 中
   advance), everything else incl. East-Asian *Ambiguous* `A` → `1 cell`
   (= ASCII = ½ the 中 advance). So 🅔 and the enclosed alphanumerics are
   **1 cell**, matching kitty; an `AMBIGUOUS=wide` knob opts into 2-cell. Emacs's
   column count must agree: the Doom config forces `char-width` to 1 for these
   (`+font--kitty-narrow-ranges`), countering `eaw-fullwidth`'s ambiguous=2.
3. Affine-transform the outline: scale ink to ≈中's height, clamp to the cell
   width, center horizontally in the advance, sit the bottom on the baseline —
   the vector analogue of the PNG recompositing.
4. Add to `glyf` + `hmtx` (per-glyph advance) + `cmap` + `glyphOrder`, with **no
   `sbix` strike** → renders as crisp monochrome vector at any size.

Result: a hybrid font — `sbix` color for emoji, `glyf` mono for the merged
symbols — both on the same cell grid.

**Approach B — bitmap `sbix` (fallback).** Render each Symbola gap glyph to a
grayscale PNG, recomposite exactly like emoji, add as an `sbix` strike. Proven
render path, but bitmap (blurs when scaled up) and larger. Used only if A fails
the POC.

### 5.4 POC gate + fallback

The one real unknown: does the NS Emacs build render a **pure-`glyf` glyph with
no `sbix` strike, inside an `sbix` font**? The README documents NS being picky
about color tables, so this is validated before the full merge:

- **POC:** merge only `🅔` U+1F154 as vector, install, confirm
  `internal-char-font` resolves it to the font **and** it renders visibly.
- **If it fails:** switch to Approach B (bitmap). Either way the chosen path is
  documented in the README.

## 6. Licensing (verified)

| Component | License | Effect on output |
|---|---|---|
| Noto Color Emoji | OFL-1.1, **no Reserved Font Name** ([notofonts FAQ](https://github.com/notofonts/noto-fonts/issues/662)) | Output **must be OFL-1.1**; name "Noto Color Emoji CJK" permitted |
| Symbola (G. Douros) | "free for any use … modified … redistributed" ([fontlibrary](https://fontlibrary.org/en/font/symbola)) | Merged glyphs allowed; **attribute** in NOTICE |
| Maple Mono NF CN | OFL-1.1 | **Metrics only, no glyph embedded** — does not bind output; courtesy credit |

- Font `.ttf` → **OFL-1.1** (`LICENSE`). `NOTICE` credits Noto, Symbola, Maple.
- Build **scripts** → **MIT** (own code).
- The Adobe-RFN "Source" exception applies to Noto Sans/Serif **CJK**, *not* Noto
  Color **Emoji** — no name conflict. NOTICE states the base is Noto Color Emoji
  to avoid confusion with Adobe's Noto CJK families.

## 7. Homebrew distribution

**Personal tap (chosen).** Repo `<gh>/homebrew-fonts`, cask
`Casks/font-noto-color-emoji-cjk.rb`:

```ruby
cask "font-noto-color-emoji-cjk" do
  version "1.0.0"
  sha256 "<filled at release>"
  url "https://github.com/<gh>/noto-color-emoji-cjk/releases/download/v#{version}/Noto-Color-Emoji-CJK.ttf"
  name "Noto Color Emoji CJK"
  homepage "https://github.com/<gh>/noto-color-emoji-cjk"
  font "Noto-Color-Emoji-CJK.ttf"
end
```

Install: `brew tap <gh>/fonts && brew install --cask font-noto-color-emoji-cjk`.
Official `homebrew/cask` is noted as a later option (notability gate blocks a
brand-new font repo today).

## 8. Emacs usage (README content)

```elisp
;; 1. Primary: an equal-width CJK mono font (1:2 cell grid)
(set-face-attribute 'default nil :family "Maple Mono NF CN" :height 140)

;; 2. Route emoji + symbols to the metrics-matched companion. On the macOS NS
;;    build, clear the target first (a built-in Apple Color Emoji entry would
;;    otherwise win the prepend), then set it. No :size -> tracks the primary
;;    font's size at every step.
(let ((f (font-spec :family "Noto Color Emoji CJK")))
  (set-fontset-font t 'emoji nil)
  (set-fontset-font t 'emoji f)
  (set-fontset-font t '(#x1F000 . #x1FFFF) f))   ; enclosed alphanumerics, cards, …
```

Doom variant wraps the same `set-fontset-font` block in `after-setting-font-hook`
with `doom-font`/`doom-unicode-font` set to the donor CJK font. Proof of
alignment: open `tests/alignment.md` in GUI Emacs; every `|` column stays
straight across ASCII / 中文 / 😀 / 🅔 rows.

## 9. Build & verify (this session)

1. venv with `fonttools` + `pillow`.
2. Fetch `NotoColorEmoji.ttf` (CBDT build) from the noto-emoji repo.
3. Run `make_emoji_font.py` (emoji recompositor) → base font.
4. **POC**: merge `🅔` only → install → verify NS renders it (§5.4). Branch to A or B.
5. Full gap-merge → `Noto-Color-Emoji-CJK.ttf`.
6. Install to `~/Library/Fonts/`, start a fresh daemon.
7. Verify against `tests/alignment.md`: `🅔` + neighbors render and align;
   emoji/flags unregressed (re-run the per-codepoint `internal-char-font` check
   used for the runtime fix).

## 10. Publishing (gated)

`gh repo create`, push, upload the release `.ttf`, enable Pages, create the tap —
**only on explicit go-ahead**, after the artifact and diffs are shown. Publishing
is outward-facing and irreversible-ish; it is not part of the unattended build.

## 11. Risks & validation

- **R1 — NS pure-`glyf` rendering.** Mitigation: POC gate (§5.4); bitmap fallback.
- **R2 — 1-cell vs 2-cell drift.** Advance set from `east_asian_width`; verify
  visually against the test sheet's ruler rows.
- **R3 — Symbola informal license.** Permissive and widely relied upon
  (matplotlib, distros); attributed in NOTICE, not relicensed.
- **R4 — Name confusion** with Adobe Noto CJK. Cosmetic; NOTICE clarifies the base.
- **R5 — Donor-specific metrics.** Documented; rebuild for a different donor font.

## 12. Success criteria

- `🅔` and the merged gap set render in GUI Emacs; color emoji unregressed; columns
  align in `tests/alignment.md`.
- A clean clone builds the font via `make`.
- `brew install` from the tap installs the font.
- The Pages specimen renders the font.

## 13. Minor defaults

- Repo `noto-color-emoji-cjk`; disk `~/src/`; first release `v1.0.0`.
- GitHub handle resolved via `gh api user` at publish time.
- Pages specimen: minimal static HTML, no framework.
