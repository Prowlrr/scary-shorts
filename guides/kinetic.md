# Format: kinetic (bold animated typography)

Big words appear in sync with the voice on a textured background; the punch line lands in the accent colour with a hit. No pictures: the words are the show. Renderer: `formats.py` (`"style": "kinetic"`). Full example: `guides/examples/kinetic.json`.

## Writing
- **30–55 s.** An intro hook line, then 4–6 cards of 1–3 lines each. The last line of each card is the punch line (`"punch"` = index of the punch line; default the last).
- Rotate the SERIES type (check posted.md):
  - two-sentence horror (5 cards, all original; never retell famous ones),
  - "rules" lists ("If you hear knocking at 3 AM, follow these rules": 5 rules, last one twists),
  - one tiny complete story told over 4–5 cards,
  - non-scary: "things that feel illegal but aren't", life-hack style tips, "red flags", fun "would you rather" (`"scary": false`, palette mint/sunset/night).
  Factual claims must be true; if unsure, don't use it.
- Save the best card for last and say so in the intro ("Don't watch the last one alone").
- Keep each line under ~18 words so it fits on screen.

## JSON
```
{"style": "kinetic", "title": "...", "description": "...", "tags": [...],
 "palette": "ink | bone | blood | night | mint | sunset", "voice": "am_echo", "scary": true,
 "ambience": "drone | wind | rain | quiet | none", "music": "tense | upbeat | (leave out)",
 "intro": "Five two-sentence horror stories. Don't watch the last one alone.",
 "cards": [{"label": "#1", "lines": ["setup line", "punch line"], "punch": 1, "hold": 0.9}],
 "outro": "optional"}
```
Vary palette, voice (am_echo, bm_george, af_nicole, am_onyx, bf_emma) and ambience between videos.

## Title / description
- Title ≤ 70 chars + ` #shorts` + one genre hashtag. Patterns: "5 Two-Sentence Horror Stories…", "Rules for Living Alone in an Old House", "Things That Feel Illegal But Aren't".
- Description: 1 teaser line + "\n\nFollow for more every day.\n\n#shorts" + 2–3 genre hashtags. `tags`: 5–7 relevant tags.
