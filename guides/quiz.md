# Format: quiz (riddles / brain teasers)

Bright, upbeat, interactive. Each question slides in, a countdown ring ticks, then the answer pops up green. Viewers pause, guess, rewatch and comment their score. Renderer: `formats.py` (`"style": "quiz"`). Full example: `guides/examples/quiz.json`.

## Writing
- **3–5 questions, 25–45 s total.** Intro hook ≤ 12 words ("Only 1 in 10 people solve all 4. Ready?"). Outro asks for a comment ("How many did you get? Comment your score.").
- Rotate the TOPIC each time (check posted.md): classic riddles · lateral-thinking puzzles · "what am I?" · math tricks (quick, no long calculations) · spooky riddles · logic ("which glass fills first" style, described in words) · word puzzles. Never repeat a riddle already used (search posted.md and stories/).
- Order: easy first, hardest last. The last one should make people go "ohhh".
- Answers are short (1–4 words). Every question and answer must be correct and unambiguous; for anything factual, double-check it.
- `options` (4 choices, one exactly equal to `a`) on about half the questions makes them more visual.
- `seconds`: 3 for easy, 4–5 for hard.

## JSON
```
{"style": "quiz", "title": "... #shorts #riddles", "description": "...", "tags": [...],
 "theme": "purple | teal | orange | night | blue", "label": "RIDDLE | QUESTION | PUZZLE",
 "voice": "narrator_f", "music": "upbeat",
 "intro": "...",
 "questions": [{"q": "What has hands but can't clap?", "a": "A clock", "seconds": 3,
                "options": ["A clock", "A tree", "A glove", "A robot"], "why": "optional short explanation"}],
 "outro": "..."}
```
Vary the theme colour and the label each time.

## Title / description
- Title ≤ 70 chars + ` #shorts #riddles` (or #quiz / #brainteaser). Patterns: "Only 1 in 10 People Solve All 4 Riddles", "Can You Beat a 10-Year-Old?", "3 Riddles That Break Your Brain".
- Description: 1 line + "\n\n#riddles #brainteaser #quiz #shorts". `tags`: ["riddles","brain teasers","quiz","riddles with answers","shorts"].
