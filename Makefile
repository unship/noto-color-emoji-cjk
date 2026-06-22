# Noto Color Emoji CJK -- build orchestration
#
#   make font      build the merged font (Noto-Color-Emoji-CJK.ttf)
#   make poc       merge ONLY U+1F154 and install, to validate NS rendering
#   make install   copy the built font into ~/Library/Fonts
#   make clean     remove build/ and the output font
#
# Override the metrics donor / Symbola source on the command line, e.g.
#   make font DONOR=/path/to/YourCJKMono-Regular.ttf

PY      ?= python3
VENV    := .venv
PYTHON  := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip

# Inputs (override as needed)
DONOR   ?= $(HOME)/Library/Fonts/MapleMono-NF-CN-Regular.ttf
SYMBOLA ?= $(HOME)/Library/Fonts/Symbola_hint.ttf
NOTO_URL ?= https://github.com/googlefonts/noto-emoji/raw/main/fonts/NotoColorEmoji.ttf

# Tuning
NAME        ?= Noto Color Emoji CJK
EMOJI_H_EM  ?= 0.86
SYMBOL_H_EM ?= 0.78
RANGES      ?= 1F000-1FFFF,2300-23FF,2600-27BF
AMBIGUOUS   ?= narrow   # ambiguous-width symbols: narrow=1 cell (kitty), wide=2 cells

OUT  := Noto-Color-Emoji-CJK.ttf
NOTO := build/NotoColorEmoji.ttf
BASE := build/base.ttf

.PHONY: all font poc install clean
all: font

$(VENV):
	$(PY) -m venv $(VENV)
	$(PIP) install -q --upgrade pip fonttools pillow

$(NOTO): | $(VENV)
	mkdir -p build
	curl -fsSL -o $(NOTO) "$(NOTO_URL)"

$(BASE): scripts/make_emoji_font.py $(NOTO)
	$(PYTHON) scripts/make_emoji_font.py $(NOTO) "$(DONOR)" $(BASE) $(EMOJI_H_EM) 0.0 "$(NAME)"

$(OUT): scripts/merge_symbola.py $(BASE)
	$(PYTHON) scripts/merge_symbola.py $(BASE) "$(SYMBOLA)" "$(DONOR)" $(OUT) "$(RANGES)" $(SYMBOL_H_EM) $(AMBIGUOUS)

font: $(OUT)

# Proof-of-concept: a single vector glyph (🅔 U+1F154) in the sbix font.
poc: $(BASE)
	$(PYTHON) scripts/merge_symbola.py $(BASE) "$(SYMBOLA)" "$(DONOR)" build/poc.ttf 1F154 $(SYMBOL_H_EM) $(AMBIGUOUS)
	cp build/poc.ttf "$(HOME)/Library/Fonts/$(OUT)"
	@echo ">> POC installed. Restart the Emacs daemon, then check 🅔 (U+1F154)."

install: $(OUT)
	cp $(OUT) "$(HOME)/Library/Fonts/"
	@echo ">> installed $(OUT) -> ~/Library/Fonts (restart the Emacs daemon)"

clean:
	rm -rf build $(OUT)
