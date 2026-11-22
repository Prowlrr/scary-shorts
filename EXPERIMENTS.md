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

## Active formats (rotate; never the same format twice in a row)
Each run picks the format from the ROTATION below (the next one after the format of the last line in posted.md), reads its guide, writes `stories/SLOT.json` and renders with `python3 make_short.py stories/SLOT.json videos/SLOT.mp4`.

ROTATION: chat, cartoon, quiz, cartoon

| Format | `"style"` | Guide | Topic | Length |
|---|---|---|---|---|
| cartoon | (none) | guides/cartoon.md | scary story, flat illustration (proven: 224–764 views) | 40–60 s |
| chat | chat | guides/chat.md | text-message thread story (scary, funny or drama) | 30–55 s |
| quiz | quiz | guides/quiz.md | riddles / brain teasers with countdown, not scary | 25–45 s |

## Evaluating
Each run, call Metricool getAnalyticsDataByMetrics (brandId 8217087, metrics YTVP17 title, YTVP02 published, YTVP06 views, YTVP08 avg view duration, YTVP09 likes, YTVP11 comments, YTVP12 shares) for the last 10 days and update the RESULTS table below (YouTube stats lag ~48 h; only judge videos older than 48 h). After a format has 3+ judged videos:
- if its median views are under half the best format's median → drop it from ROTATION (move it to Retired with the reason) and add a new experimental format idea from the Backlog;
- the best format gets an extra place in ROTATION (e.g. `cartoon, chat, cartoon, quiz`).
Always keep at least one experimental (unproven) format in ROTATION so we keep learning.

## RESULTS (views / avg view duration, filled by the runs)
| Slot | Format | Title | Views | Avg dur | Likes |
|---|---|---|---|---|---|
| 2026-11-19 | cartoon | Lake campground rules | n/a* | n/a | n/a |
| 2026-11-20 | cartoon | Man in the basement counting | n/a* | n/a | n/a |
| 2026-11-20-1800 | footage | Trail camera | n/a* | n/a | n/a |
| 2026-11-21-0000 | footage | Baby monitor | n/a* | n/a | n/a |

*2026-11-21 21:10 check: Metricool YTVP metrics returned the 4 videos but null views/duration/likes (sync lag). No new-format video is older than 48 h yet; ROTATION unchanged.
*2026-11-22 15:10 check: still null views/duration/likes for all 4 listed videos; 11-21 18:00 and newer not yet in Metricool. Nothing judgeable; ROTATION unchanged.

## Backlog of ideas to try
- "Would you rather" with a creepy twist, split-screen choices
- Unsolved-mystery / weird-history explainers (facts must be web-verified)
- Loop stories (last line flows into the first line to boost replays)
- Satisfying procedural animation background + short story text

## Retired
- kinetic typography (two-sentence horror / rules lists): scrapped by the owner on 2026-11-21 before it was posted. Don't bring it back.
- found footage (guides/footage.md): 117–141 views, 3 videos, 90+ s each.
