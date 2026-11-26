# Format: wyr (Would You Rather, with a catch)

Split screen: option A on the top panel, option B on the bottom, "OR" badge in the middle. The narrator reads both, a 3–4 s countdown runs, then **THE CATCH** pops in under one or both options, a twist that makes the "easy" pick worse. Viewers argue in the comments. Renderer: `formats.py` (`"style": "wyr"`). Full example: `guides/examples/wyr.json`.

## Writing
- **3–4 dilemmas, 30–45 s.** No intro card: dilemma 1 is on screen at frame 0, so make it the strongest, most instantly readable pair.
- Each option: **4–10 words**, concrete and visual ("Hear knocking every night at 3 AM"), not abstract ("Be scared forever").
- The two options must feel roughly equal at first. The catch flips it. Put the catch on the option most people would pick. Use both catches on the last dilemma only.
- Catch: **one sentence, 5–12 words**, ending on the twist word ("...coming from inside your closet.").
- Rotate the TONE (check posted.md): creepy (night theme, `"music": "tense"`, `"ambience": "drone"`, `"scary": true`) · funny / everyday (classic or mint theme, upbeat, `"scary": false`) · weird superpowers with a cost. At least 1 in 2 should be creepy, since that's the channel.
- No fake poll results or percentages. No real people, brands, gore. PG-13.
- Never reuse a dilemma already in posted.md or stories/.

## JSON
```
{"style": "wyr", "title": "... #shorts #wouldyourather", "description": "...", "tags": [...],
 "theme": "classic | night | sunset | mint", "label": "WOULD YOU RATHER (optional override)",
 "voice": "narrator | narrator_f | british_m ...", "music": "tense | upbeat", "ambience": "none | drone | ...", "scary": true,
 "questions": [{"a": "...", "b": "...", "seconds": 3, "a_catch": "...", "b_catch": "...",
                "say": "optional custom read of A", "b_say": "optional custom read of B"}],
 "outro": "A or B? Comment your picks."}
```
The voice reads "Would you rather {a}" … "or {b}?" automatically. Write `a`/`b` lowercase-friendly so that sentence sounds natural; capitalise the first word for the screen.

## Title / description
- Title ≤ 70 chars + ` #shorts #wouldyourather`. Patterns: "Would You Rather… (But There's a Catch)", "Every Choice Is a Trap. Pick One.", "Only Brave People Pick B".
- Description: 1 line + "\n\n#wouldyourather #thisorthat #quiz #shorts". `tags`: ["would you rather","would you rather scary","this or that","choose one","shorts"].
