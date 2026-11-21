"""Shared, more natural-sounding Kokoro TTS for every format.

What makes it sound less like AI (2026-11-22):
- the full-precision model (kokoro-v1.0.onnx) instead of the int8 one when it is present;
- only the best-rated Kokoro voices, blended 2-way (a blend of two voices sounds less synthetic than either alone);
- normal speaking speed (~1.0) with small per-sentence speed variation and varied pauses, like a person reading;
- a clean "voice in a room" chain in ffmpeg (VOICE_FX) instead of the old echo.
Old voice names in story files (am_echo, am_onyx, ...) are mapped to the better voices automatically.
"""
import os, re, random
import numpy as np

SR = 24000
# name -> blend of (voice, weight). Only A/B-grade Kokoro voices.
VOICES = {
    "narrator": [("am_michael", 0.6), ("am_fenrir", 0.4)],          # default male storyteller
    "narrator_f": [("af_heart", 0.7), ("af_bella", 0.3)],           # default female storyteller
    "male": [("am_michael", 0.7), ("am_puck", 0.3)],
    "male2": [("am_fenrir", 0.65), ("am_michael", 0.35)],
    "female": [("af_heart", 0.75), ("af_nicole", 0.25)],
    "female2": [("af_bella", 0.7), ("af_heart", 0.3)],
    "british_m": [("bm_george", 0.7), ("bm_fable", 0.3)],
    "british_f": [("bf_emma", 0.7), ("bf_isabella", 0.3)],
}
# old / weak voice names -> better replacements
ALIAS = {"am_echo": "narrator", "am_onyx": "male2", "am_adam": "male", "am_liam": "male", "am_eric": "male",
         "am_michael": "male", "am_fenrir": "male2", "am_puck": "male",
         "af_heart": "female", "af_bella": "female2", "af_nicole": "female", "af_sarah": "female2",
         "af_sky": "female2", "af_nova": "female", "bm_george": "british_m", "bm_lewis": "british_m",
         "bf_emma": "british_f", "bf_alice": "british_f"}

# ffmpeg chain for the voice track: high-pass, tame harshness, warm low-mids, gentle compression,
# and a very short, quiet room reflection so it sounds recorded rather than generated.
VOICE_FX = (",highpass=f=75,equalizer=f=220:t=q:w=1:g=1.5,equalizer=f=3200:t=q:w=1.2:g=-1.5,"
            "treble=g=-2.5:f=7500,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,"
            "aecho=0.9:0.35:14|27:0.10|0.06")

_k = {}


def model(models):
    if "k" not in _k:
        from kokoro_onnx import Kokoro
        full = os.path.join(models, "kokoro-v1.0.onnx")
        path = full if os.path.exists(full) and os.path.getsize(full) > 200_000_000 else os.path.join(models, "kokoro-v1.0.int8.onnx")
        _k["k"] = Kokoro(path, os.path.join(models, "voices-v1.0.bin"))
    return _k["k"]


def style(models, name):
    """Voice spec: a preset name, an old Kokoro name (mapped), or 'a:0.6,b:0.4'."""
    k = model(models)
    name = name or "narrator"
    name = ALIAS.get(name, name)
    if name in VOICES:
        mix = VOICES[name]
    elif ":" in name:
        mix = [(p.split(":")[0].strip(), float(p.split(":")[1])) for p in name.split(",")]
    else:
        mix = [(name, 1.0)]
    tot = sum(w for _, w in mix)
    return sum(k.get_voice_style(v) * (w / tot) for v, w in mix).astype(np.float32)


def sentences(text):
    return [x for x in re.split(r"(?<=[.!?…])[\"”']?\s+", text.strip()) if x]


def say_sentence(models, s, voice, speed=1.0, rng=None):
    """One sentence -> trimmed float32 audio at 24 kHz."""
    rng = rng or random
    k = model(models)
    sp = speed * (1 + rng.uniform(-0.035, 0.035))
    if s.rstrip().endswith("?"):
        sp *= 0.97
    a, _ = k.create(s, voice=style(models, voice), speed=sp, lang="en-us")
    a = np.asarray(a, np.float32)
    nz = np.where(np.abs(a) > 0.01)[0]
    if len(nz):
        a = a[max(0, nz[0] - 400): nz[-1] + 900]
    return a


def pause_after(s, rng=None):
    """Natural gap after a sentence: longer after ... and questions, a little random."""
    rng = rng or random
    base = 0.22
    if s.endswith("…") or s.endswith("..."):
        base = 0.45
    elif s.endswith("?"):
        base = 0.3
    elif s.endswith("!"):
        base = 0.2
    return base + rng.uniform(-0.05, 0.08)


def speak(models, text, voice="narrator", speed=1.0, rng=None):
    parts = []
    ss = sentences(text)
    for i, s in enumerate(ss):
        parts.append(say_sentence(models, s, voice, speed, rng))
        if i < len(ss) - 1:
            parts.append(np.zeros(int(SR * pause_after(s, rng)), np.float32))
    return np.concatenate(parts) if parts else np.zeros(1, np.float32)
