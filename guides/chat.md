# Format: chat (text-message story)

A Short that looks like a phone chat thread. Bubbles pop in one by one with a typing indicator, and two voices read them. It opens with a big hook banner and ends with a big end banner. Renderer: `formats.py` (`"style": "chat"`). Full example: `guides/examples/chat.json`.

## Writing
- **12–20 messages, 30–55 s.** Every message is short, like a real text: 3–12 words. No long paragraphs.
- The hook banner (`"hook"`) is the most important line: a strange or impossible situation in ≤ 12 words ("My mom texted me while she was sitting next to me").
- Escalate fast: something is off by message 3, getting worse by message 8, and the twist lands in the last 2–3 messages or in the `"end"` banner.
- Rotate the GENRE (check posted.md): scary (impostor, wrong number, someone watching), funny (a misunderstanding that keeps getting worse, a parent who can't use their phone), wholesome (a wrong number that turns into something kind), drama (a twist reveal). At least 1 in 3 chat videos should NOT be scary.
- No real people, brands or app names. Contact names are generic ("Mom", "Unknown Number", "Jake", "Landlord").
- PG-13.

## JSON
```
{"style": "chat", "title": "... #shorts #textstory", "description": "...", "tags": [...],
 "contact": "Mom", "avatar_color": "#c2185b", "theme": "dark | light | green",
 "ambience": "drone | quiet | rain | wind | none", "music": "tense | upbeat | (leave out)",
 "voices": {"me": "am_michael", "them": "af_heart", "narrator": "am_echo"},   (optional; any Kokoro voice)
 "hook": "big banner text read at the start",
 "messages": [
   {"from": "them", "text": "Are you home yet?"},
   {"from": "me", "text": "Yeah lol", "pause": 0.6},
   {"from": "system", "text": "Knocking at the bedroom door", "sfx": ["knock"]}
 ],
 "end": "big final banner", "end_say": "how the narrator reads it (optional)",
 "scary": true}
```
- `from`: me (right, blue) · them (left, grey) · system (small centered grey line: times, "Message deleted", events).
- Optional per message: `"say"` (what the voice reads, if different), `"pause"`, `"typing": false`, `"typing_time"`, `"sfx"` (knock creak footsteps heartbeat static boom stinger notify ding ...).
- Pick voices that fit the characters: female voices af_heart af_bella af_nicole af_sarah bf_emma; male am_michael am_adam am_echo am_liam bm_george. Funny chats: `"theme": "light"`, `"music": "upbeat"`, `"ambience": "none"`, `"scary": false`.

## Title / description
- Title ≤ 70 chars + ` #shorts #textstory` (+ `#scarystories` if scary). Patterns: "My Mom Texted Me While…", "Wrong Number Texted Me At 3AM…", "My Landlord Sent the Weirdest Text…".
- Description: 1 teaser line + "\n\nFollow for new stories every day.\n\n#textstory #shorts" + 1–2 genre hashtags.
- `tags`: 5–7 tags, e.g. ["text story","text message story","scary texts","funny texts","shorts"].
