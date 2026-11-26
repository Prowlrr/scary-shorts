# Format experiments: what we post and how we decide

Started 2026-11-21 after the found-footage run flopped. Voices: since 2026-11-21 all formats use voice.py (full Kokoro model, best-rated voices blended, natural pacing, room EQ) to sound less like AI; story JSON may set "voice" (narrator, narrator_f, male, male2, female, female2, british_m, british_f) and "speed" (~0.95–1.05). Channel data so far (YouTube views, checked 2026-11-21):

| Video | Format | Length | Views |
|---|---|---|---|
| Lake campground rules (11-19) | cartoon (flat illustration) | 100 s | 224 |
| Man in the basement counting (11-20) | cartoon, red jump-scare face, cold-open hook | 107 s | **764** |
| Trail camera (11-20 18:00) | found footage | 90 s | 141 |
| Baby monitor (11-21 00:00) | found footage | 94 s | 117 |
| Sleepwalking attic (11-21 18:00) | found footage | 93 s | 128 |

Takeaways: found footage is retired. The cartoon style did 2–6x better. All videos were long (90–107 s); Shorts reward completion, so every new format is **20–60 s**.

## Posting slots and openings (owner, 2026-11-22)
- **For the scheduled runs:** use 10:00 and 16:00 Berlin as the slot times. If the run's instructions still say 18:00 and 00:00, that text is outdated; this file wins. Likewise, pick the format with "How to find the next format" below and follow "Rules for every video".
- 2 Shorts a day at **10:00 and 16:00 Europe/Berlin** (was 18:00 and 00:00). Metricool's YouTube best-time data peaks at 16:00 every day of the week, with a second peak at 10:00; evenings after 19:00 and nights are 3–8x weaker.
- **No title/intro card at the start of any video.** Chat opens straight on the thread with the first message on screen; quiz opens on riddle 1. Cartoon already opens straight into the story.

## Active formats (rotate; never the same format twice in a row)
Each run picks the format from the ROTATION below (see "How to find the next format"), reads its guide, writes `stories/SLOT.json` and renders with `python3 make_short.py stories/SLOT.json videos/SLOT.mp4`.

ROTATION: chat, cartoon, chat, quiz, cartoon, wyr

How to find the next format: take the formats of the LAST TWO lines in posted.md, find that pair in the ROTATION (wrapping around), and use the format after it. If the pair isn't in the ROTATION (e.g. right after a rotation change), use the next format after the last line's format that isn't the same format.

(2026-11-22: owner doubled chat early: first chat Short hit 1k views in ~15 h, the channel's best so far.)
(2026-11-26: added wyr (Would You Rather with a creepy catch) as the experimental format, and a second cartoon slot so the proven story format gets more data; chat stays at 2 of 6. Reason: owner asked for changes based on research into what works for faceless Shorts; wyr was the most-recommended interactive format and cartoon has 3 videos with no data yet.)

| Format | `"style"` | Guide | Topic | Length |
|---|---|---|---|---|
| cartoon | (none) | guides/cartoon.md | scary story, flat illustration (proven: 224–764 views) | 40–60 s |
| chat | chat | guides/chat.md | text-message thread story (scary, funny or drama) | 30–55 s |
| quiz | quiz | guides/quiz.md | riddles / brain teasers with countdown, not scary | 25–45 s |
| wyr | wyr | guides/wyr.md | Would You Rather, split screen + "THE CATCH" twist (experimental, from 2026-11-26) | 30–45 s |

## Rules for every video (2026-11-26, from research on what works and YouTube's 2025–26 crackdown on mass-produced AI content)
YouTube now demonetizes, and under its spam rules can terminate, channels whose videos look template-made: same script skeleton with swapped names, near-identical uploads, AI voice reading generic text. AI voices are allowed; sameness is the risk. So:
1. **Every video must differ in substance, not just names.** Before writing, read the last 6 lines of posted.md and change at least 3 of: story structure, length (use the whole allowed range, not always ~45 s), voice preset, theme/season/colours, music/ambience, hook style, ending type. Never reuse a premise or twist.
2. **Frame 0 = the most striking moment.** The first frame must be a face, a readable alarming message, or the scariest line, never scenery or setup. The first spoken line must open a question in under 2 s ("I found my dead brother's phone. It had videos from after his funeral." not "This happened last summer.").
3. **Loop endings (experiment): about 1 in 3 story videos (cartoon or chat) ends on a line that leads straight back into the first line,** so the replay feels seamless. Note `loop` in the posted.md line.
4. **Series (experiment): "Unknown Number".** The next 3 scary chat videos form a 3-part series with the same contact "Unknown Number" and the same narrator. Each part is a complete, satisfying mini-story, but parts 1 and 2 end with a `system` line or end banner teasing the next part ("Part 2 tomorrow"). Titles: "… (Part 1)". Funny/wholesome chats can be scheduled in between as usual. Log `series Unknown Number N/3` in posted.md. After part 3, compare its views with the single chats before running another series.
5. **Disclosure:** keep `isAiGeneratedContent: false` only because nothing realistic is synthesized (cartoon art, chat UI, quiz cards). If a format ever uses realistic AI people, places or footage, set it to true.
6. Max 2 uploads a day. Don't increase the volume.

## Evaluating
Each run, call Metricool getAnalyticsDataByMetrics (brandId 8217087, metrics YTVP17 title, YTVP02 published, YTVP06 views, YTVP08 avg view duration, YTVP09 likes, YTVP11 comments, YTVP12 shares) for the last 10 days and update the RESULTS table below (YouTube stats lag ~48 h; only judge videos older than 48 h). After a format has 3+ judged videos:
- if its median views are under half the best format's median → drop it from ROTATION (move it to Retired with the reason) and add a new experimental format idea from the Backlog;
- the best format gets an extra place in ROTATION (e.g. `cartoon, chat, cartoon, quiz`).
Always keep at least one experimental (unproven) format in ROTATION so we keep learning.

## RESULTS (views / avg view duration, filled by the runs)
| Slot | Format | Title | Views | Avg dur | Likes |
|---|---|---|---|---|---|
| 2026-11-19 | cartoon | Lake campground rules | 230 | n/a | n/a |
| 2026-11-20 | cartoon | Man in the basement counting | 788 | n/a | n/a |
| 2026-11-20-1800 | footage | Trail camera | 189 | n/a | n/a |
| 2026-11-21-0000 | footage | Baby monitor | 138 | n/a | n/a |
| 2026-11-21-1800 | footage | Sleepwalking attic | 653 | n/a | n/a |
| 2026-11-22-0000 | chat | Mom texted me while sitting next to me | 1,000 (~15 h old) | n/a | n/a |

Views from the owner's YouTube app screenshot, 2026-11-22 ~15:30 Berlin (Metricool per-video stats were still null).
2026-11-22 21:10 check: Metricool per-video YouTube stats (YTVP06/08/09) still null for every video; no new judged data, ROTATION unchanged.
2026-11-23 15:15 check: Metricool per-video YouTube stats (YTVP06/08/09) still null for every video; no new judged data, ROTATION unchanged.
2026-11-23 21:10 check: Metricool per-video YouTube stats still null (only 11-19/11-20 videos listed); no new judged data, ROTATION unchanged.
2026-11-24 15:10 check: Metricool per-video YouTube stats (YTVP06/08/09) still null (only 11-19/11-20 videos listed); no new judged data, ROTATION unchanged.
2026-11-24 21:10 check: Metricool per-video YouTube stats (YTVP06/08/09) still null (only 11-19/11-20 videos listed); no new judged data, ROTATION unchanged.
2026-11-25 15:10 check: Metricool per-video YouTube stats (YTVP06/08/09) still null (only 11-19/11-20 videos listed); no new judged data, ROTATION unchanged.
2026-11-25 21:10 check: Metricool per-video YouTube stats (YTVP06/08/09) still null (only 11-19/11-20 videos listed); no new judged data, ROTATION unchanged.
2026-11-26 15:10 check: Metricool per-video YouTube stats (YTVP06/08/09) still null (only 11-19/11-20 videos listed); no new judged data, ROTATION unchanged.
2026-11-26 21:10 check: Metricool per-video YouTube stats (YTVP06/08/09/11/12) still null (only 11-19/11-20 videos listed); no new judged data, ROTATION unchanged.
Medians: chat 1,000 (1 video), cartoon 509 (2), footage 189 (3). Chat is the leader after one video; the rule to double a format needs 3 judged videos, the owner chose to double chat early anyway (see ROTATION).
Pattern: the three best videos all open on something you instantly read or react to: a readable text thread (chat 1k), a creepy face (basement 788, sleepwalking 653). The three weakest open on scenery (lake 230, trail cam 189, baby monitor 138). Make the first frame a face, a readable message or the hook text, never an empty scene.

## Backlog of ideas to try (next first)
- Unsolved-mystery / weird-history explainers (facts must be web-verified). Research says narrative/history formats hold viewers best.
- "What would you do?" second-person horror scenario with a choice at the end (viewers comment)
- Satisfying procedural animation background + short story text
- (now running: "Would You Rather" → wyr format; loop endings and the "Unknown Number" series → Rules above)

Judging note (2026-11-26): research suggests 60–90 videos before judging a channel, and Shorts stats lag. Don't drop a format on fewer than 3 videos that are each at least 72 h old.

## Retired
- kinetic typography (two-sentence horror / rules lists): scrapped by the owner on 2026-11-21 before it was posted. Don't bring it back.
- found footage (guides/footage.md): 3 videos, 90+ s each. Retired on 117–141 views checked too early; Sleepwalking later reached 653 (2026-11-22), so footage may deserve a 45 s retry with a face/text first frame if a slot opens.
