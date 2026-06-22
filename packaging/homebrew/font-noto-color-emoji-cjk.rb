# Homebrew Cask for Noto Color Emoji CJK.
#
# This file is the source of truth for the cask. To make it installable, copy it
# into a tap repo named `homebrew-fonts` (so it becomes a tap), e.g.:
#
#   github.com/unship/homebrew-fonts/Casks/font-noto-color-emoji-cjk.rb
#
# Then users install with:
#
#   brew tap unship/fonts
#   brew install --cask font-noto-color-emoji-cjk
#
# `version`/`sha256` are filled per release. Get the sha256 with:
#   shasum -a 256 Noto-Color-Emoji-CJK.ttf
cask "font-noto-color-emoji-cjk" do
  version "1.0.0"
  sha256 "87290d472c99309ca5eabf05d3b2ff44f7635990847078bb7f977c1c824d2b65"

  url "https://github.com/unship/noto-color-emoji-cjk/releases/download/v#{version}/Noto-Color-Emoji-CJK.ttf"
  name "Noto Color Emoji CJK"
  desc "Colour emoji + symbols pre-fit to the CJK cell, for grid-aligned editors"
  homepage "https://github.com/unship/noto-color-emoji-cjk"

  font "Noto-Color-Emoji-CJK.ttf"

  # No uninstall stanza needed: the `font` artifact is removed on `brew uninstall`.
end
