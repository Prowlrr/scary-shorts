# Scary Short: story-writing guide (FOUND-FOOTAGE style)

The channel posts **2 Shorts a day**, at **18:00 and 00:00 Europe/Berlin** (12 PM and 6 PM US Eastern). Each video is `stories/<SLOT>.json` → `videos/<SLOT>.mp4`, where SLOT = `YYYY-MM-DD-HHMM` in Berlin time. Read `posted.md` first and never reuse a premise, twist, setting, character name or title already listed there.

**The look is FOUND FOOTAGE** (renderer: `footage.py`; the story JSON must have `"style": "footage"`). Every video looks like recovered camera footage: night-vision camcorder, security cameras, flashlight phone video and dashcam, with handheld shake, tape glitches, REC/timecode overlays and yellow subtitle captions. The narrator voice stays the same. Don't use the old cartoon style (`make_short.py` scenes, alert cards, phone mockups).

## Story (must be COMPLETE, 1–2 minutes)
- **20–30 beats, 190–290 words** (~70–115 s). Mostly one short sentence per beat (the camera cuts every 2–4 s). Use simple words that sound good read aloud.
- Full arc: hook → setup (who is filming, where, why) → escalation (3+ incidents caught on camera, getting worse) → climax → resolution that explains what happened → final chilling line. No cliffhangers, no "part 2", no morals, no questions to the audience.
- It's told by the person who filmed it, or as a recovered tape. Give a reason the camera is rolling: a baby monitor, home security, a ghost-hunting trip, a dashcam, a night-shift job, a vlog, a trail camera, a camcorder found in an attic, filming a sibling's sleepwalking, and so on.
- **Rotate the story TYPE** (check posted.md): security-camera mystery · ghost-hunting friends · night-shift job (guard, motel, gas station) · sleepwalking/self-recording · baby monitor · road trip dashcam · camping trail cam · abandoned building exploration · haunted move-in · mimic or doppelgänger · missing-person tape · neighbor surveillance.
- **Rotate the TWIST type:** the filmer is the one being watched · it's been in the house the whole time · the footage timestamps are wrong · a friend wasn't who they seemed · it follows the camera · the tape itself is the danger · a quiet, sad reveal.
- Keep it PG-13: dread and suspense, no gore, no self-harm, no real people, places or brands, no copyrighted characters.

## Beats: camera modes and scenes
- `"mode"`: `nv` (green night-vision camcorder, default) · `cctv` (grey security cam, choppy frame rate; set `"cam": "CAM 02 - KITCHEN"`) · `flash` (dark, warm flashlight beam) · `dash` (dashcam) · `card` (black screen with typed white text: use it for the opening "recovered tape" note or a found note; put the shown text in `"card"`).
- Mix at least 3 modes per video and vary the mix between videos (e.g. one mostly cctv, another mostly flashlight).
- `"scene"`: hallway, room (bedroom), stairs (basement), door, window, forest, livingroom, kitchen, attic, road, tent, yard, face (extreme close-up of the creature: use once at most, as a jump scare), black.
- Figure: `"figure": "far" | "near" | "approach" | "vanish"` (approach = walks toward the camera; vanish = glitches away). Leave it out in calm shots, and build up to it.
- People: `"people": 1-3` shows family or friends in frame (livingroom, kitchen, hallway, forest, tent, room, yard, attic). Use people in the setup and calm parts so it doesn't feel empty.
- Camera: `"walk": true` (walking bob), `"zoom": true` (pushes in on the figure or a detail), `"shake": true` (panic + boom), `"glitch": true` (tape glitch into the shot). Small random glitches happen automatically.
- `"hook"` on beat 1: `card` (typed "TAPE FOUND…" note), `glitch` (static burst into footage) or `cold` (open straight on the scariest shot). Vary it between videos.
- `"sfx": [...]`: extra sounds (boom riser whoosh alert notify buzz ding knock creak heartbeat static footsteps stinger). Keyword sounds ("knock", "creak", "footsteps", "heart", "static") are automatic.

## Story-level keys
- `"style": "footage"` (required)
- `"tape": {"start": "03:14:22", "date": "OCT 14 2026"}`: on-screen timecode start and date (vary them; dates can be in the past)
- `"ambience"`: tape (camcorder hiss, default) · wind · rain · drone · crickets · quiet. Vary it.

## YouTube metadata (in the story JSON)
- `title`: ≤ 70 chars, curiosity-driven, + ` #shorts #scarystories`. Vary the patterns ("My Security Camera Caught…", "This Tape Was Found…", "Why I Stopped Filming My…").
- `description`: 1 creepy teaser line + "\n\nFollow for new scary stories every day.\n\n#scarystory #foundfootage #creepy #shorts"
