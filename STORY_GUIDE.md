# Daily scary Short: story-writing guide

Write ONE brand-new, original horror micro-story per day as `stories/YYYY-MM-DD.json` (format in `make_short.py`). Look at `posted.md` first, and never reuse a premise, twist, town name or title that's already listed there.

## Style (match the reference channel)
- **Second-person "what if" hook** as beat 1, under 15 words, so a viewer stops scrolling: "If every phone in your town gets the same alert…", "If you hear your name from the closet at 3 AM…".
- Beat 2 is a short command or warning: "Don't answer." / "Don't open it."
- Set it in a small quiet town at night, with you as the main character, ordinary details (a time, a phone, a door) and one rule that gets broken.
- **8–12 beats, 75–120 words total (~30–45 s).** Each beat is 1–2 short sentences. Simple words that land when read aloud.
- Build tension with concrete times ("It's 3:07 AM."), sounds and messages.
- **The last beat is the twist**, one punchy line that recontextualises everything. No moral, no "the end", no question to the audience inside the story.
- Keep it PG-13: suspense and dread, no gore, no self-harm, no real people, places or brands, no copyrighted characters.

## Scenes (pick one per beat, vary them, never the same scene 3x in a row)
street, town, livingroom, phone, door, window, hallway, bedroom, forest
- `figure: true` shows the lurking silhouette (default true for window/door/hallway/bedroom/forest). Save it for the moments it should appear, and set false before the reveal.
- `mood: "scared"` changes the character's face (livingroom, bedroom).
- `shake: true` for knocks, bangs and twist moments.

## Overlays (use 4–6 per story, they carry the format)
- `alert` {header?, lines[2–3 short ALL-CAPS-able lines], red:[indexes]}: emergency alerts. On the `phone` scene it appears inside the phone.
- `text` {from, message}: a text message notification (great on `phone`).
- `clock` {time:"3:07 AM"}: time badge. Phone scenes show the last time used.
- `sign` {name, sub}: town sign (use with `town`).
- `label` {text}: red tag, e.g. "ROAD CLOSED".

## YouTube metadata
- title: ≤ 70 chars, curiosity-driven, matching the hook, + ` #shorts #scarystories`
- description: 1 creepy teaser line + "Follow for a new scary story every night." + hashtags `#scarystory #horrorstories #creepy #shorts`
- tags: scary stories, horror, creepy, scary story, horror shorts, short horror story
- category ENTERTAINMENT, madeForKids false, type "short", privacy "public"
