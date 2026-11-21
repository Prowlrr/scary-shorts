# Quiet horror stories: daily YouTube Shorts generator

`setup.sh` installs dependencies and the free Kokoro TTS model. `make_short.py story.json out.mp4` renders a 1080x1920 Short.
Stories live in `stories/`, finished videos in `videos/` (served publicly so Metricool can fetch them), and the history is in `posted.md`.
Formats and the experiment rotation are in `EXPERIMENTS.md`; each format has a guide in `guides/` (`formats.py` renders chat, quiz and kinetic; `make_short.py` renders cartoon and dispatches the rest).
