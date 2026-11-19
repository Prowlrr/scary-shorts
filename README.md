# Quiet horror stories: daily YouTube Shorts generator

`setup.sh` installs dependencies and the free Kokoro TTS model. `make_short.py story.json out.mp4` renders a 1080x1920 Short.
Stories live in `stories/`, finished videos in `videos/` (served publicly so Metricool can fetch them), and the history is in `posted.md`.
See `STORY_GUIDE.md` for the story format and style.
