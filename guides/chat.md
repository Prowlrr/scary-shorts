# Format: chat (text-message story)

A Short that looks like a phone chat thread. Bubbles pop in one by one with a typing indicator, and two voices read them. **No title/hook banner at the start** (owner, 2026-11-22): the video opens straight on the chat, with the first message already on screen at frame 0. It ends with a big end banner. Renderer: `formats.py` (`"style": "chat"`). Full example: `guides/examples/chat.json`.

## Writing
- **12–20 messages, 30–55 s.** Every message is short, like a real text: 3–12 words. No long paragraphs.
- Never set `"hook"`. The FIRST MESSAGE is the hook and the most important line: it must be strange or alarming on its own, 3–12 words, so the opening frame stops the scroll (e.g. Mom: "Who is sitting next to you right now?", Unknown Number: "Don't open the door. It isn't him."). No small talk like "Are you home yet?" first.
- Escalate fast: something is off by message 3, getting worse by message 8, and the twist lands in the last 2–3 messages or in the `"end"` banner.
- Rotate the GENRE (check posted.md): scary (impostor, wrong number, someone watching), funny (a misunderstanding that keeps getting worse, a parent who can't use their phone), wholesome (a wrong number that turns into something kind), drama (a twist reveal). At least 1 in 3 chat videos should NOT be scary.
- **Series "Unknown Number" (see EXPERIMENTS.md Rules 4):** if posted.md shows the series is under 3/3 and this chat is scary, write the next part: same contact "Unknown Number", same voices, a new escalation that follows from the previous part's ending. Parts 1–2 end with a teaser (`"end": "Part 2 tomorrow."`). Part 3 resolves it. Add " (Part N)" before the hashtags in the title.
- **Loop ending (about 1 in 3 chats):** the last message or end banner leads straight back into the first message, so a replay feels like the next beat (e.g. ends "…then my phone buzzed." and the video restarts on the first text).
- Vary the length across the full 30–55 s range and the message count across 12–20. Don't always land at ~45 s.
- No real people, brands or app names. Contact names are generic ("Mom", "Unknown Number", "Jake", "Landlord").
- PG-13.

## JSON
```
{"style": "chat", "title": "... #shorts #textstory", "description": "...", "tags": [...],
 "contact": "Mom", "avatar_color": "#c2185b", "theme": "dark | light | green",
 "ambience": "drone | quiet | rain | wind | none", "music": "tense | upbeat | (leave out)",
 "voices": {"me": "male", "them": "female", "narrator": "narrator"},   (optional; presets from voice.py)
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
- Pick voices that fit the characters from the voice.py presets: female, female2, british_f, narrator_f (women); male, male2, british_m, narrator (men). Use two different presets for the two people. Funny chats: `"theme": "light"`, `"music": "upbeat"`, `"ambience": "none"`, `"scary": false`.

## Title / description
- Title ≤ 70 chars + ` #shorts #textstory` (+ `#scarystories` if scary). Patterns: "My Mom Texted Me While…", "Wrong Number Texted Me At 3AM…", "My Landlord Sent the Weirdest Text…".
- Description: 1 teaser line + "\n\nFollow for new stories every day.\n\n#textstory #shorts" + 1–2 genre hashtags.
- `tags`: 5–7 tags, e.g. ["text story","text message story","scary texts","funny texts","shorts"].
