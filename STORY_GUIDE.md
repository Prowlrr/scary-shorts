# Daily scary Short: story-writing guide

Write ONE brand-new, original scary story per day as `stories/YYYY-MM-DD.json` (format in `make_short.py`). Read `posted.md` first, and never reuse a premise, twist, setting combo, character name or title that's already listed there.

## What to write
- **Any kind of scary story.** Vary it day to day: first-person ("I"), second-person ("you") or third-person; urban legends, home invasions, cursed objects, road trips, babysitting, camping, lake houses, cabins, cemeteries, things in the mirror, wrong numbers, voices that copy people, missing time, creepy neighbors, etc. Don't fall back on the same "emergency alert" format.
- **A COMPLETE story, 1–2 minutes long: 18–28 beats, 200–300 words** (~80–115 s of narration). Each beat is 1–2 short sentences, in simple words that land when read aloud.
- It needs a full arc. Hook (beat 1, under 15 words, makes the viewer stop scrolling) → setup (who, where, the rule or strange thing) → escalation (3+ creepy events that get worse) → climax (the confrontation) → resolution (what happened after, so the mystery is answered) → final chilling line. Never end on "to be continued", "part 2" or an unexplained cliffhanger.
- Use concrete details (times, sounds, messages, small wrong things). No moral, no "the end", no question to the audience.
- Keep it PG-13: dread and suspense, no gore, no self-harm, no real people, places or brands, no copyrighted characters.

## Visual variety (same art style every time, different look per story)
- Story-level `"season"`: autumn | summer | rain | fog. Rotate it; don't use the same one two days in a row. **Never use winter/snow, and don't set stories in snowy mountain towns.**
- Scenes (one per beat): street, town, road, lake, cabin, forest, cemetery, campsite (outdoor) · livingroom, kitchen, bedroom, hallway, basement, bathroom, door, window, phone (indoor).
  - Pick scenes that fit the story's setting, use at least 8 different scenes per story, and never use the same scene more than 3 times in a row (phone conversations are the exception). Make the mix of settings different from the last few days in posted.md. Use `town` rarely.
- `figure: true/false` shows or hides the lurking silhouette (most scenes show it by default; livingroom, kitchen, cabin and street hide it by default). Hide it before the reveal.
- `mood: "scared"` changes the character's face (livingroom, kitchen, bedroom). `shake: true` for bangs, knocks and the twist.

## Overlays (use 3–6 per story where they fit)
- `text` {from, message}: a phone notification (great on `phone`).
- `alert` {header?, lines[2–3 short lines], red:[indexes]}: a warning card (header can be anything: "Weather Alert", "Missing Person", "Note on the door"…).
- `clock` {time:"3:07 AM"}: time badge. Phone scenes show the last time used (or pass `time`).
- `sign` {name, sub}: a roadside or town sign. `label` {text}: red tag, e.g. "DO NOT ENTER".

## YouTube metadata (put in the story JSON)
- `title`: ≤ 70 chars, curiosity-driven, matching the hook, + ` #shorts #scarystories`
- `description`: 1 creepy teaser line + "\n\nFollow for a new scary story every night.\n\n#scarystory #horrorstories #creepy #shorts"
