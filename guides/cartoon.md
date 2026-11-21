# Scary Short: story-writing guide

See EXPERIMENTS.md for slots and which format runs when. Each video is `stories/<SLOT>.json` → `videos/<SLOT>.mp4`, where SLOT = `YYYY-MM-DD-HHMM` in Berlin time (older files are plain dates). Read `posted.md` first and never reuse a premise, twist, setting combo, character name or title already listed there.

**Keep only these the same every time:** the flat-illustration art style and the caption style. The voice is set with `"voice"` (narrator default, or narrator_f, male2, british_m; see voice.py), mostly narrator; `"speed"` 0.95–1.05. **Everything else should change from video to video:** story type and structure, intro style, settings, scenes, season, background sound, sound effects, overlays and pacing. Look at the last ~8 entries in posted.md (they log story type, hook style and ambience) and pick a different combination.

## Story (must be COMPLETE, 40–60 seconds)
- **14–20 beats, 110–160 words** (~40–60 s). Shorter is better: viewers must reach the end. Mostly one short sentence per beat, so the picture changes every 2–4 seconds. Use simple words that land when read aloud.
- It needs a full arc (setup → escalation → climax → resolution that answers the mystery → final chilling line). Never end on "to be continued", "part 2" or an unexplained cliffhanger. No moral, no "the end", no question to the audience.
- **Rotate the story TYPE**, never the same type twice in a row:
  first-person confession · "rules" job (night guard, babysitter, motel clerk) · text-message thread / wrong number · urban legend told as fact · second-person "you" scenario · found diary or voicemail · creepy neighbor · road trip / gas station / hitchhiker · camping or lake trip · haunted house move-in · twin, doppelgänger or mimic · missing time · kid's imaginary friend · something in the mirror · sleep paralysis · small-town tradition · a "true" story from someone's grandpa
- **Rotate the TWIST type:** the narrator was wrong about who is who · it was inside the whole time · it's still happening · the helper was the monster · the rule was a lie · a time loop · a reveal in the last text message · a quiet, sad ending · a hopeful but eerie ending.
- Keep it PG-13: dread and suspense, no gore, no self-harm, no real people, places or brands, no copyrighted characters.

## Opening (vary it; never the same style twice in a row)
- Beat 1 must hook within 2 seconds, but HOW changes:
  - `"hook": "flash"`: cold open on the scariest moment, red flash, shake, stinger.
  - `"hook": "glitch"`: VHS/static glitch, good for found footage, cameras, phones.
  - `"hook": "fade"`: slow fade from black with a heartbeat, good for quiet dread.
  - `"hook": "text"`: opens on a phone message popping in (use the `phone` scene with a `text` overlay).
  - `"hook": "quiet"`: no effect, just a striking line with a riser underneath.
  - …or no hook flag at all: start straight in with a punchy first line (e.g. "My neighbor has waved at me every night for 11 years. He died in 2019.").
- Hook lines can be a statement, a rule, a confession, a message or a question.

## Visuals (same art style, different look)
- `"season"`: autumn | summer | rain | fog. Never winter/snow, never a snowy mountain town. Don't repeat the previous video's season.
- Scenes: street, town, road, lake, cabin, forest, cemetery, campsite (outdoor) · livingroom, kitchen, bedroom, hallway, basement, bathroom, door, window, phone (indoor) · face (jump-scare close-up).
  - Use 7+ different scenes per story, fitted to the setting. Don't build every story around phone, door and window: some should barely use the phone, others should be mostly outdoors, and so on.
- People: `"people": N` adds varied background characters (street 4, campsite 3, livingroom 2, kitchen 2, lake 2, cabin 2, cemetery 3, town 3, bedroom 1). Scenes shouldn't feel empty except in deliberately lonely moments (`"people": 0`). Show the other characters the story mentions.
- `figure: true/false` shows the lurking silhouette; `mood: "scared"` changes the character's face.
- Use these as the story calls for them, not all in every video:
  - `"scene": "face"` jump scare (in about half the videos at most);
  - `"shake": true` (2–6 times);
  - `"flicker": true` (lights failing);
  - `"transition"`: fade | flash | glitch on a few beats (default is a hard cut).
- Overlays (0–6 per story, mix them differently each time): `text` {from, message}, `alert` {header, lines, red}, `clock` {time}, `sign` {name, sub}, `label` {text}. Not every story needs an alert or a phone.

## Sound (vary it)
- `"ambience"`: wind | crickets | rain | drone | musicbox | quiet. The default follows the season (summer = crickets, rain = rain, fog = drone, otherwise wind); override it for variety. Don't repeat the previous video's ambience.
- Automatic effects: alert tone on `alert`, buzz and ding on `text`, whooshes on scene changes, a boom on `shake`, a stinger on `face`, a riser into the last beat, and keyword sounds ("knock", "creak", "footsteps", "heart", "static", "buzz").
- Add extras with `"sfx": ["knock", {"name": "creak", "at": 0.5}]`. Bank: boom riser whoosh alert notify buzz ding knock creak heartbeat static footsteps stinger. Pick the ones that fit; don't stack them.

## YouTube metadata (put in the story JSON)
- `title`: ≤ 70 chars, curiosity-driven, + ` #shorts #scarystories`. Vary the title pattern too (not always "I took a…" / "If you…").
- `description`: 1 creepy teaser line + "\n\nFollow for new scary stories every day.\n\n#scarystory #horrorstories #creepy #shorts"
