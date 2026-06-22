# Font / Emoji / CJK Alignment Test Sheet

Open in **GUI Emacs**. In every fenced (monospace) block the `|` separators — and
the right-hand edge against the ruler — must line up vertically across rows.
Any drift means a glyph isn't its expected cell width.

**Cell rule:** ASCII/Latin = 1 cell · CJK = 2 cells · emoji = 2 cells.

Status legend from this font work: ✅ should be correct · ⚠️ known-tricky (needs the
char-width / auto-composition / dingbat-routing fixes).

---

## 0. Ruler — each digit is exactly 1 cell

```
         1111111111222222222233333333334444444444
1234567890123456789012345678901234567890123456789
```

## 1. Cell grid — every `|` must align straight down the columns  ✅

```
|AB|CD|EF|GH|IJ|KL|MN|OP|QR|ST|   ASCII pairs (2 cells)
|中|文|对|齐|测|试|字|符|宽|度|   CJK
|あ|い|う|え|お|か|き|く|け|こ|   Hiragana
|ア|イ|ウ|エ|オ|カ|キ|ク|ケ|コ|   Katakana
|한|국|어|테|스|트|정|렬|확|인|   Hangul
|😀|🎉|🚀|🔥|💯|✨|🌟|🎨|🍕|🚗|   modern emoji (colour, 2 cells)
|❤|⚙|✳|☀|★|☎|✈|☂|✂|✏|   ⚠️ bare dingbats
```

## 2. Right-edge alignment — all rows should end at column 30  ✅

```
123456789012345678901234567890
中中中中中中中中中中中中中中中
😀😀😀😀😀😀😀😀😀😀😀😀😀😀😀
あいうえおかきくけこさしすせそ
한국어테스트정렬너비확인검사함
ABABABABABABABABABABABABABABAB
```

## 3. Mixed widths in one line — the closing `|` should align  ✅

```
|A中B😀C|
|X文Y🎉Z|
|1字2🔥3|
|=符+💯-|
```

## 4. Emoji — single codepoint (each should be 2 cells, in colour)  ✅

Faces: 😀 😃 😄 😁 😆 😅 😂 🙂 🙃 😉 😊 🥰 😍 🤩 😘 😜 🤪 🤔 🫡 🥹
People/body: 👍 👎 👏 🙌 👐 🤝 💪 🦾 🧠 👀 👋 ✊ 🤙 🫶 🙏
Animals/nature: 🐱 🐶 🦊 🐼 🐻 🦁 🐸 🐙 🦋 🌍 🌙 ⭐ 🌈 🔥 💧 🌸 🍀
Food: 🍕 🍔 🍟 🌮 🍣 🍜 🍱 🍎 🍇 🍓 🍰 ☕ 🍺 🥑 🌶
Travel/objects: 🚗 🚕 🚌 🚀 🛸 ⛵ 🚲 🏠 🏢 💻 📱 ⌚ 📷 🎧 🔑 💡 📦
Symbols/marks: ✅ ❌ ⭕ ❗ ❓ 💯 🔔 🎯 🎵 🔆 ♻️ 🆗 🈵 🅰️

## 5. ⚠️ Known-tricky emoji (regression watch)

Bare dingbats — U+2300–27BF, default *text* presentation (may route to a text
font and lose the 2-cell width unless forced to the emoji font):
```
❤ ⚙ ✳ ☀ ★ ☎ ✈ ☂ ✂ ✏ ⚡ ☯ ✝ ☮ ☢ ☣ ⌛ ⏰ ⏳ ⌨ ⏪ ⏩ ⏫ ⏬
```

VS16 emoji-presentation (`base + U+FE0F`) — need **auto-composition** to be one
2-cell glyph; otherwise the selector adds ~1px:
```
❤️ ⚙️ ✳️ ☀️ ✈️ ⏰️ ⭐️ ☂️ ☎️ ✝️ ♻️ ▶️ ⏸️ ⏹️
```

ZWJ sequences — one glyph if composed, else several:
```
👨‍👩‍👧 👨‍👩‍👧‍👦 👩‍💻 👨‍🚀 🧑‍🍳 👨‍👨‍👦 👩‍❤️‍👨 🏳️‍🌈 🏴‍☠️ 🐻‍❄️ 😶‍🌫️
```

Flags — regional-indicator pairs — 2 cells if composed, else 4:
```
🇨🇳 🇺🇸 🇯🇵 🇰🇷 🇬🇧 🇩🇪 🇫🇷 🇪🇺 🇮🇳 🇧🇷 🇨🇦 🇦🇺
```

Skin-tone modifiers:
```
👍🏻 👍🏼 👍🏽 👍🏾 👍🏿  👋🏽 🤙🏾 ✊🏿 🫶🏼 🙏🏽
```

Keycap sequences:
```
0️⃣ 1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟 #️⃣ *️⃣
```

## 6. CJK scripts

- 简体中文：对齐测试，宽度检查，字符渲染，标点符号。
- 繁體中文：對齊測試，寬度檢查，字符渲染，標點符號。
- 日本語：ひらがな、カタカナ、漢字、全角混在テスト。
- 한국어: 한글 정렬 테스트, 너비 확인, 문자 렌더링.
- Full-width punctuation: ，。、！？；：「」『』（）【】《》〈〉

## 7. ⚠️ East-Asian Ambiguous (EAW pitfall — Maple draws these at 1 cell)

```
1234567890123456789012345
áóéñ üöä àèì âêî ãõ çß       accented Latin
‘’“”…—–·•                    quotes / dashes / bullets
αβγδ εζηθ ΩΣΛΦ Ψ            Greek
①②③④⑤ ⑥⑦⑧⑨⑩              circled numbers
■□▲△●○◆◇★☆                geometric
```
If EAW forces these to width-2 but Maple renders 1 cell, the right edge drifts
left of the ruler (this is the calfw-detach problem).

## 8. Markdown table — string-width alignment

| key     | 状态   | emoji | flag | note        |
|---------|--------|-------|------|-------------|
| alpha   | 完成   | ✅    | 🇺🇸   | done        |
| 测试项目 | 进行中 | 🔥    | 🇨🇳   | running 中文 |
| heart   | 心动   | ❤️    | 🇯🇵   | vs16        |
| family  | 家庭   | 👨‍👩‍👧   | 🇰🇷   | zwj         |

## 9. Box drawing — CJK & emoji in 7-cell cells

```
┌───────┬───────┐
│ ASCII │ 中文  │
├───────┼───────┤
│ test  │ 测试  │
│ 1234  │ 😀😀  │
│ abcd  │ 🎉🚀  │
└───────┴───────┘
```

## 10. Nerd Font glyphs (Maple NF — should be 1 or 2 cells, mono)

```
files:                 git:        
arrows:                powerline:     
status:                misc:        
```

## 11. Real-world mixed text

- Commit: `feat(font): 中文 + emoji 对齐 ✅ 完成 🎉`
- 这是一个 test，混合 English、中文、emoji 😀、dingbat ❤、symbol ✳ 和 flag 🇨🇳。
- TODO ⏰: fix `❤️` / `👨‍👩‍👧` alignment → issue #42 🔥🔥🔥
- `printf("%d 个 → %s ✅\n", n, "完成")` 中英 code 混排。
- emoji density 😀😀😀 中文中文 😀😀😀 中文中文 😀😀😀 ← bars below should match

```
😀😀😀中文中文😀😀😀中文中文😀😀😀
123456789012345678901234567890123456
```
