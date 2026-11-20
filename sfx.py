"""Procedural horror sound effects (48 kHz mono float32), no downloads needed."""
import numpy as np

SR = 48000
_rng = np.random.default_rng(7)


def _t(d): return np.arange(int(SR * d)) / SR


def _env(n, a=0.005, r=0.2, shape=3.0):
    t = np.arange(n) / SR
    att = np.clip(t / max(a, 1e-4), 0, 1)
    dec = np.exp(-shape * t / max(r, 1e-4))
    return att * dec


def _lp(x, cutoff):
    # one-pole low-pass, applied twice
    a = np.exp(-2 * np.pi * cutoff / SR)
    for _ in range(2):
        y = np.empty_like(x); acc = 0.0
        for i in range(len(x)):
            acc = (1 - a) * x[i] + a * acc; y[i] = acc
        x = y
    return x


def _lp_fast(x, cutoff):
    # FFT brickwall-ish low-pass (fast)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x)).astype(np.float32)


def _bp_fast(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= (1 / (1 + (lo / np.maximum(f, 1)) ** 4)) * (1 / (1 + (f / hi) ** 4))
    return np.fft.irfft(X, len(x)).astype(np.float32)


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return (x / m * peak).astype(np.float32)


def boom(d=2.2):
    t = _t(d)
    f = 30 + 70 * np.exp(-t * 6)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    hit = _lp_fast(_rng.standard_normal(len(t)), 900) * np.exp(-t * 18) * 0.8
    tail = _lp_fast(_rng.standard_normal(len(t)), 200) * np.exp(-t * 2.5) * 0.3
    return norm(sub + hit + tail)


def riser(d=2.0):
    t = _t(d)
    n = _bp_fast(_rng.standard_normal(len(t)), 400, 6000) * (t / d) ** 2.5
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * (t / d) ** 2) / SR) * (t / d) ** 3 * 0.4
    x = n + tone
    x[-int(SR * 0.02):] *= np.linspace(1, 0, int(SR * 0.02))
    return norm(x, 0.7)


def whoosh(d=0.7):
    t = _t(d)
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return norm(_bp_fast(_rng.standard_normal(len(t)), 300, 3000) * env, 0.5)


def alert(d=2.2):
    # US-style EAS attention tone: 853 Hz + 960 Hz, harsh, with on/off pulses
    t = _t(d)
    x = np.sign(np.sin(2 * np.pi * 853 * t)) * 0.5 + np.sign(np.sin(2 * np.pi * 960 * t)) * 0.5
    x = _lp_fast(x, 4000)
    gate = ((t % 0.55) < 0.42).astype(float)
    gate = np.convolve(gate, np.ones(200) / 200, "same")
    return norm(x * gate * np.clip(t / 0.01, 0, 1), 0.55)


def buzz(d=0.9):
    # phone vibration: two pulses of a 160 Hz rattle
    t = _t(d)
    x = np.sign(np.sin(2 * np.pi * 160 * t)) * (0.6 + 0.4 * np.sin(2 * np.pi * 37 * t))
    gate = ((t < 0.35) | ((t > 0.5) & (t < 0.85))).astype(float)
    gate = np.convolve(gate, np.ones(240) / 240, "same")
    return norm(_lp_fast(x, 1200) * gate, 0.5)


def ding(d=0.8):
    t = _t(d)
    x = np.zeros_like(t)
    for st, f in ((0.0, 1568), (0.12, 2093)):
        tt = np.clip(t - st, 0, None)
        x += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 9) * (t >= st)
    return norm(x, 0.45)


def notify(d=1.2):
    b, g = buzz(), ding()
    x = np.zeros(int(SR * d), np.float32)
    x[:len(b)] += b * 0.8
    o = int(SR * 0.1); x[o:o + len(g)] += g[:len(x) - o]
    return x


def knock(n=3, gap=0.42):
    one_d = 0.25
    t = _t(one_d)
    thump = np.sin(2 * np.pi * 110 * t) * np.exp(-t * 30)
    wood = _bp_fast(_rng.standard_normal(len(t)), 300, 2500) * np.exp(-t * 60)
    k1 = norm(thump + wood * 0.9)
    x = np.zeros(int(SR * (gap * n + 0.3)), np.float32)
    for i in range(n):
        o = int(SR * i * gap); x[o:o + len(k1)] += k1 * (0.85 + 0.15 * (i == n - 1))
    return norm(x, 0.8)


def creak(d=1.6):
    t = _t(d)
    f = 90 + 60 * np.sin(2 * np.pi * 0.6 * t) + 25 * _lp_fast(_rng.standard_normal(len(t)), 8)
    pulses = (np.sin(2 * np.pi * np.cumsum(f) / SR) > 0.97).astype(float)
    x = _bp_fast(pulses, 400, 3500) * np.sin(np.pi * t / d)
    return norm(x, 0.5)


def heartbeat(beats=4, bpm=70):
    per = 60 / bpm
    t = _t(0.25)
    lub = np.sin(2 * np.pi * 55 * t) * np.exp(-t * 22)
    x = np.zeros(int(SR * per * beats), np.float32)
    for i in range(beats):
        for off, a in ((0, 1.0), (0.22, 0.7)):
            o = int(SR * (i * per + off)); seg = x[o:o + len(lub)]; seg += (lub * a)[:len(seg)]
    return norm(x, 0.9)


def static(d=0.6):
    t = _t(d)
    x = _rng.standard_normal(len(t)) * (_rng.random(len(t)) > 0.3)
    return norm(_bp_fast(x, 800, 8000) * np.sin(np.pi * t / d) ** 0.5, 0.35)


def footsteps(n=4, gap=0.55):
    t = _t(0.2)
    step = _lp_fast(_rng.standard_normal(len(t)), 500) * np.exp(-t * 35) + np.sin(2 * np.pi * 70 * t) * np.exp(-t * 30) * 0.6
    step = norm(step)
    x = np.zeros(int(SR * (gap * n + 0.3)), np.float32)
    for i in range(n):
        o = int(SR * i * gap); x[o:o + len(step)] += step * (0.6 + 0.1 * i)
    return norm(x, 0.6)


def stinger(d=1.4):
    # dissonant string-like hit for the hook / twist
    t = _t(d)
    x = sum(np.sin(2 * np.pi * f * t + 2 * np.sin(2 * np.pi * 6 * t)) for f in (311, 330, 466, 622))
    x = x * np.exp(-t * 2.2) * np.clip(t / 0.01, 0, 1)
    return norm(x + boom(d) * 1.2, 0.9)


def _crickets(t):
    x = np.zeros_like(t)
    for f0, rate, ph in ((4200, 2.1, 0.0), (4700, 1.6, 1.3), (3900, 2.7, 2.1)):
        chirp = (np.sin(2 * np.pi * rate * t + ph) > 0.6) * (np.sin(2 * np.pi * 28 * t) > 0)
        x += np.sin(2 * np.pi * f0 * t) * np.convolve(chirp.astype(float), np.ones(120) / 120, "same") * 0.05
    return x


def _musicbox(t):
    notes = [659, 622, 659, 494, 587, 523, 440, 0, 330, 392, 440, 0, 494, 415, 494, 523]
    x = np.zeros_like(t); step = 0.55
    for i in range(int(t[-1] / step) + 1):
        f = notes[i % len(notes)] * (0.5 if (i // 16) % 2 else 1)
        if not f:
            continue
        o = int(i * step * SR); tt = t[: min(len(t) - o, int(SR * 1.4))]
        if len(tt) <= 0:
            break
        tone = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 3 * tt)) * np.exp(-tt * 3.5) * 0.06
        x[o:o + len(tt)] += tone * (1 + 0.004 * np.sin(2 * np.pi * 0.3 * tt))
    return x


def ambience(dur, kind="wind"):
    """Background bed. kind: wind | crickets | rain | drone | musicbox | quiet"""
    t = _t(dur)
    n = len(t)
    if kind != "wind":
        hum = (np.sin(2 * np.pi * 55 * t) + 0.8 * np.sin(2 * np.pi * 58.2 * t)) * 0.03
        if kind == "crickets":
            x = _crickets(t) + _bp_fast(_rng.standard_normal(n), 100, 600) * 0.03 + hum
        elif kind == "rain":
            r = _bp_fast(_rng.standard_normal(n), 800, 9000)
            x = r / (np.max(np.abs(r)) or 1) * 0.28 + _bp_fast(_rng.standard_normal(n), 60, 300) * 0.05 + hum
        elif kind == "drone":
            x = sum(np.sin(2 * np.pi * f * t + 3 * np.sin(2 * np.pi * 0.05 * t + f)) for f in (73.4, 110, 155.6, 220.8)) * 0.045 \
                * (0.6 + 0.4 * np.sin(2 * np.pi * 0.04 * t))
        elif kind == "musicbox":
            x = _musicbox(t) + hum + _bp_fast(_rng.standard_normal(n), 200, 900) * 0.02
        else:  # quiet: room tone only
            x = _bp_fast(_rng.standard_normal(n), 80, 500) * 0.02 + hum
        fade = int(SR * 1.5)
        x[:fade] *= np.linspace(0, 1, fade); x[-fade:] *= np.linspace(1, 0, fade)
        return x.astype(np.float32)
    wind = _bp_fast(_rng.standard_normal(n), 150, 1200)
    lfo = 0.55 + 0.45 * np.sin(2 * np.pi * 0.07 * t + 1) * np.sin(2 * np.pi * 0.023 * t)
    wind = wind / (np.max(np.abs(wind)) or 1) * lfo * 0.35
    tone = (np.sin(2 * np.pi * 740 * t) + 0.6 * np.sin(2 * np.pi * 744.5 * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t)) * 0.05
    hum = (np.sin(2 * np.pi * 55 * t) + 0.8 * np.sin(2 * np.pi * 58.2 * t)) * 0.035
    x = wind + tone + hum
    fade = int(SR * 1.5)
    x[:fade] *= np.linspace(0, 1, fade); x[-fade:] *= np.linspace(1, 0, fade)
    return x.astype(np.float32)


BANK = {"boom": boom, "riser": riser, "whoosh": whoosh, "alert": alert, "notify": notify, "buzz": buzz,
        "ding": ding, "knock": knock, "creak": creak, "heartbeat": heartbeat, "static": static,
        "footsteps": footsteps, "stinger": stinger}
GAIN = {"boom": 0.9, "riser": 0.5, "whoosh": 0.22, "alert": 0.35, "notify": 0.55, "buzz": 0.5, "ding": 0.5,
        "knock": 0.85, "creak": 0.45, "heartbeat": 0.7, "static": 0.3, "footsteps": 0.55, "stinger": 0.8}
