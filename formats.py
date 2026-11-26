#!/usr/bin/env python3
"""Experimental Short formats: chat (text-message story), quiz (riddles with countdown) and wyr (would you rather).

Called from make_short.py when story["style"] is chat | quiz | wyr. Voices come from voice.py.
Each renderer builds a list of voice segments, renders frames with Pillow and encodes with ffmpeg.
"""
import math, os, re, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import sfx

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
SR_V = 24000


# ------------------------------------------------------------------ fonts / text
_fc = {}


def font(name, size, wght=None):
    key = (name, size, wght)
    if key not in _fc:
        p = {"anton": "Anton-Regular.ttf", "mont": "Montserrat[wght].ttf", "mono": "AnonymousPro-Bold.ttf"}[name]
        f = ImageFont.truetype(os.path.join(FONTS, p), size)
        if wght and name == "mont":
            try:
                f.set_variation_by_axes([wght])
            except Exception:
                pass
        _fc[key] = f
    return _fc[key]


_tmpd = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def tw(s, f): return _tmpd.textlength(s, font=f)


def wrap(text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if tw(t, f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_font(text, name, maxw, maxh, big, small, wght=None, lh=1.15):
    for s in range(big, small - 1, -4):
        f = font(name, s, wght)
        ls = wrap(text, f, maxw)
        if len(ls) * s * lh <= maxh and all(tw(l, f) <= maxw for l in ls):
            return f, ls
    f = font(name, small, wght)
    return f, wrap(text, f, maxw)


def ease(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def back(x):  # ease-out-back (overshoot pop)
    x = max(0.0, min(1.0, x)); c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def hexc(s, a=255):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def vgrad(c1, c2, w=W, h=H):
    t = np.linspace(0, 1, h)[:, None, None]
    a = (np.array(c1[:3])[None, None, :] * (1 - t) + np.array(c2[:3])[None, None, :] * t)
    a = np.repeat(a, w, axis=1).astype(np.uint8)
    return Image.fromarray(a, "RGB").convert("RGBA")


def paste_scaled(img, layer, cx, cy, s, alpha=1.0):
    if s <= 0.01 or alpha <= 0.01:
        return
    if abs(s - 1) > 0.01:
        layer = layer.resize((max(1, int(layer.width * s)), max(1, int(layer.height * s))), Image.BILINEAR)
    if alpha < 0.99:
        a = np.asarray(layer).copy(); a[..., 3] = (a[..., 3] * alpha).astype(np.uint8); layer = Image.fromarray(a)
    img.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


# ------------------------------------------------------------------ audio
import voice as V


def speak(models, text, voice, speed):
    return V.speak(models, text, voice, speed)


class Track:
    """Voice timeline at 24 kHz plus sound events at 48 kHz."""

    def __init__(self, models, lead=0.25):
        self.models, self.t, self.pieces, self.events = models, lead, [np.zeros(int(SR_V * lead), np.float32)], []

    def say(self, text, voice, speed=1.05):
        a = speak(self.models, text, voice, speed)
        t0 = self.t
        self.pieces.append(a); self.t += len(a) / SR_V
        return t0, self.t

    def gap(self, d):
        self.pieces.append(np.zeros(int(SR_V * d), np.float32)); self.t += d
        return self.t

    def fx(self, name, at, gain=1.0):
        self.events.append((name, at, gain))

    def write(self, work, bed="quiet", music=None, tail=0.8):
        import soundfile as sf
        self.gap(tail)
        dur = self.t
        vw = os.path.join(work, "voice.wav"); sf.write(vw, np.concatenate(self.pieces), SR_V)
        SR = sfx.SR
        n = int(SR * dur) + SR
        x = np.zeros(n, np.float32)
        if bed and bed != "none":
            a = sfx.ambience(dur, bed); x[:len(a)] += a * 0.5
        if music:
            m = MUSIC[music](dur); x[:len(m)] += m
        for name, at, g in self.events:
            s = (EXTRA[name]() if name in EXTRA else sfx.BANK[name]() * sfx.GAIN[name]) * g
            o = int(at * SR)
            if 0 <= o < n:
                seg = x[o:o + len(s)]; seg += s[:len(seg)]
        aw = os.path.join(work, "bed.wav"); sf.write(aw, x[:int(SR * dur)], SR)
        return vw, aw, dur


def _t(d): return np.arange(int(sfx.SR * d)) / sfx.SR


def tick():
    t = _t(0.05); n = np.random.default_rng(3).standard_normal(len(t))
    return (sfx._bp_fast(n, 2500, 7000) * np.exp(-t * 160) * 0.5).astype(np.float32)


def pop():
    t = _t(0.09); f = 500 + 900 * (t / 0.09)
    return (np.sin(2 * np.pi * np.cumsum(f) / sfx.SR) * np.exp(-t * 45) * 0.35).astype(np.float32)


def typing():
    out = np.zeros(int(sfx.SR * 0.6), np.float32); r = np.random.default_rng(5)
    for k in range(5):
        o = int(sfx.SR * (0.03 + k * 0.11 + r.random() * 0.03)); s = tick() * 0.35; out[o:o + len(s)] += s
    return out


def correct():
    t = _t(0.7); x = np.zeros(len(t), np.float32)
    for i, f in enumerate((660, 880, 1320)):
        o = int(sfx.SR * i * 0.08); tt = t[:len(t) - o]
        x[o:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 7) * 0.22
    return x


def swoosh():
    return sfx.BANK["whoosh"]() * 0.3


EXTRA = {"tick": tick, "pop": pop, "typing": typing, "correct": correct, "swoosh": swoosh}


def music_upbeat(dur, bpm=104):
    SR = sfx.SR; t = _t(dur); x = np.zeros(len(t), np.float32)
    beat = 60 / bpm; scale = [261.6, 293.7, 329.6, 392.0, 440.0, 523.3]
    prog = [0, 2, 4, 3, 0, 2, 5, 3]
    r = np.random.default_rng(11)
    nstep = int(dur / (beat / 2))
    for i in range(nstep):
        o = int(i * beat / 2 * SR)
        f = scale[(prog[(i // 8) % len(prog)] + [0, 2, 4, 2][i % 4]) % len(scale)]
        L = int(SR * 0.35); tt = np.arange(L) / SR
        note = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 9) * 0.05
        x[o:o + L] += note[:len(x) - o]
        if i % 2 == 0:  # soft kick
            L = int(SR * 0.18); tt = np.arange(L) / SR
            k = np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 18) * 0.13
            x[o:o + L] += k[:len(x) - o]
        if i % 4 == 2:  # hat
            L = int(SR * 0.05); h = sfx._bp_fast(r.standard_normal(L), 6000, 12000) * np.exp(-np.arange(L) / SR * 80) * 0.05
            x[o:o + L] += h[:len(x) - o]
    fade = int(SR * 1.0); x[-fade:] *= np.linspace(1, 0, fade)
    return x


def music_tense(dur):
    SR = sfx.SR; t = _t(dur)
    pulse = (np.sin(2 * np.pi * 55 * t) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 1.6 * t))) * 0.05)
    pad = sum(np.sin(2 * np.pi * f * t + 2 * np.sin(2 * np.pi * 0.07 * t + f)) for f in (110, 130.8, 164.8)) * 0.025
    x = (pulse + pad * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t))).astype(np.float32)
    fade = int(SR * 1.0); x[:fade] *= np.linspace(0, 1, fade); x[-fade:] *= np.linspace(1, 0, fade)
    return x


MUSIC = {"upbeat": music_upbeat, "tense": music_tense}


# ------------------------------------------------------------------ encode
def encode(frame, n, vw, aw, out, voice_fx=None):
    voice_fx = V.VOICE_FX if voice_fx is None else voice_fx
    tmp = out[:-4] + ".part.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", vw, "-i", aw, "-filter_complex",
           f"[1:a]aresample=48000{voice_fx}[vo];[2:a]volume=0.6[am];"
           "[vo][am]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]",
           "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmp]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        pr.stdin.write(frame(f).convert("RGB").tobytes())
    pr.stdin.close()
    if pr.wait() != 0:
        sys.exit("ffmpeg failed")
    os.replace(tmp, out)


def run(frame, n, vw, aw, out, preview, times, voice_fx=None):
    if preview:
        os.makedirs(preview, exist_ok=True)
        ps = []
        for i, t in enumerate(times):
            p = os.path.join(preview, f"p{i:02d}.png"); frame(min(n - 1, int(t * FPS))).convert("RGB").save(p); ps.append(p)
        return ps
    encode(frame, n, vw, aw, out, voice_fx)
    return out


def hook_banner(text, w=980, fill=(255, 255, 255, 255), bg=(0, 0, 0, 215), accent=None):
    f, ls = fit_font(text.upper(), "anton", w - 80, 520, 112, 60)
    lh = int(f.size * 1.12)
    hgt = lh * len(ls) + 70
    im = Image.new("RGBA", (w, hgt), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, hgt - 1], 36, fill=bg)
    if accent:
        d.rounded_rectangle([0, 0, w - 1, hgt - 1], 36, outline=accent, width=8)
    for i, l in enumerate(ls):
        d.text((w / 2, 35 + i * lh + lh / 2), l, font=f, fill=fill, anchor="mm")
    return im


# ================================================================== CHAT
CHAT_THEMES = {
    "dark": dict(bg1="#0b0b0f", bg2="#14141c", head="#1b1b24", me="#2f7bf6", them="#2a2a33", metext="#ffffff",
                 themtext="#f2f2f5", sub="#8b8b98", name="#ffffff"),
    "light": dict(bg1="#f4f4f7", bg2="#e9e9ef", head="#ffffff", me="#2f7bf6", them="#e3e3ea", metext="#ffffff",
                  themtext="#111116", sub="#7a7a86", name="#111116"),
    "green": dict(bg1="#0e1512", bg2="#101c17", head="#16241e", me="#1f9d61", them="#24302b", metext="#ffffff",
                  themtext="#eef5f1", sub="#86a094", name="#ffffff"),
}


def chat_bubble(text, me, th, maxw=700):
    f = font("mont", 50, 560)
    ls = wrap(text, f, maxw - 80)
    lh = 64
    bw = int(max(tw(l, f) for l in ls) + 80); bh = lh * len(ls) + 50
    im = Image.new("RGBA", (bw + 20, bh + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = hexc(th["me"] if me else th["them"])
    x0 = 20 if me else 0
    d.rounded_rectangle([x0, 0, x0 + bw - 1, bh - 1], 40, fill=col)
    # tail
    if me:
        d.polygon([(bw + 2, bh - 30), (bw + 18, bh + 2), (bw - 30, bh - 6)], fill=col)
    else:
        d.polygon([(18, bh - 30), (2, bh + 2), (50, bh - 6)], fill=col)
    tc = hexc(th["metext"] if me else th["themtext"])
    for i, l in enumerate(ls):
        d.text((x0 + 40, 25 + i * lh), l, font=f, fill=tc)
    return im


def chat_system(text, th):
    f = font("mont", 36, 600)
    w = int(tw(text, f) + 60)
    im = Image.new("RGBA", (w, 70), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((w / 2, 35), text, font=f, fill=hexc(th["sub"]), anchor="mm")
    return im


def typing_bubble(th, ph):
    im = Image.new("RGBA", (190, 110), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 170, 100], 45, fill=hexc(th["them"]))
    for k in range(3):
        a = 0.45 + 0.55 * max(0, math.sin(ph * 7 - k * 0.9))
        c = hexc(th["sub"]); r = 12
        cx = 50 + k * 36; cy = 50 - 6 * max(0, math.sin(ph * 7 - k * 0.9))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(c[0], c[1], c[2], int(255 * a)))
    return im


def render_chat(story, out, models, preview=None):
    th = CHAT_THEMES.get(story.get("theme", "dark"), CHAT_THEMES["dark"])
    voices = {"me": "male", "them": "female", "narrator": "narrator"}; voices.update(story.get("voices", {}))
    speed = story.get("speed", 1.0)
    contact = story.get("contact", "Unknown")
    hook = story.get("hook")
    # No hook banner (default since 2026-11-22): the first message is on screen from frame 0, no typing dots, no pop.
    tr = Track(models, lead=0.3 if hook else 0.0)
    items = []  # dict(kind, img, me, t_in, typing_from)
    first = not hook
    if hook:
        tr.fx("pop", 0.05)
        a, b = tr.say(story.get("hook_say", hook), voices.get("narrator", "narrator"), speed)
        tr.gap(0.25)
    hook_end = tr.t
    for m in story["messages"]:
        kind = m.get("from", "them")
        if kind == "system":
            items.append(dict(img=chat_system(m["text"], th), me=None, t_in=tr.t, sys=True, nopop=first)); first = False
            tr.fx("pop", tr.t, 0.5)
            if m.get("say"):
                tr.say(m["say"], voices.get("narrator", "narrator"), speed)
            tr.gap(m.get("pause", 0.5))
            continue
        me = kind == "me"
        typing_from = None
        if not me and m.get("typing", True) and not first:
            typing_from = tr.t; tr.fx("typing", tr.t, 0.8); tr.gap(m.get("typing_time", 0.7))
        t_in = tr.t
        tr.fx("pop", t_in)
        if m.get("sfx"):
            for s in m["sfx"]:
                tr.fx(s, t_in + 0.1)
        items.append(dict(img=chat_bubble(m["text"], me, th), me=me, t_in=t_in, typing_from=typing_from, sys=False, nopop=first)); first = False
        v = voices.get(m.get("voice", kind), voices.get("them"))
        tr.say(m.get("say", m["text"]), v, speed)
        tr.gap(m.get("pause", 0.35))
    end = story.get("end")
    end_t = None
    if end:
        tr.gap(0.3); end_t = tr.t; tr.fx("boom" if story.get("scary", True) else "correct", end_t)
        tr.say(story.get("end_say", end), voices.get("narrator", "narrator"), speed)
    work = tempfile.mkdtemp(prefix="chat_")
    vw, aw, dur = tr.write(work, bed=story.get("ambience", "quiet"), music=story.get("music"))
    n = int(dur * FPS)

    # static chrome
    bg = vgrad(hexc(th["bg1"]), hexc(th["bg2"]))
    head = Image.new("RGBA", (W, 300), hexc(th["head"])); d = ImageDraw.Draw(head)
    d.ellipse([W / 2 - 62, 62, W / 2 + 62, 186], fill=hexc(story.get("avatar_color", "#6b6b7b")))
    ini = (contact.strip()[:1] or "?").upper()
    d.text((W / 2, 124), ini, font=font("mont", 64, 700), fill=(255, 255, 255, 255), anchor="mm")
    d.text((W / 2, 230), contact, font=font("mont", 44, 650), fill=hexc(th["name"]), anchor="mm")
    d.text((70, 124), "‹", font=font("mont", 90, 400), fill=hexc(th["me"]), anchor="mm")
    d.line([(0, 299), (W, 299)], fill=hexc(th["sub"], 80), width=2)
    status = story.get("status")
    if status:
        d.text((W / 2, 275), status, font=font("mont", 28, 500), fill=hexc(th["sub"]), anchor="mm")
    foot = Image.new("RGBA", (W, 170), hexc(th["head"])); d = ImageDraw.Draw(foot)
    d.rounded_rectangle([40, 35, W - 150, 125], 45, outline=hexc(th["sub"], 150), width=3)
    d.text((85, 80), "Text Message", font=font("mont", 38, 500), fill=hexc(th["sub"]), anchor="lm")
    d.ellipse([W - 125, 35, W - 35, 125], fill=hexc(th["me"]))
    d.polygon([(W - 80, 55), (W - 102, 85), (W - 58, 85)], fill=(255, 255, 255, 255))
    d.rectangle([W - 86, 84, W - 74, 108], fill=(255, 255, 255, 255))
    hook_img = hook_banner(hook, accent=hexc(story.get("hook_color", "#e83a3a"))) if hook else None
    end_img = hook_banner(end, accent=hexc(story.get("hook_color", "#e83a3a"))) if end else None
    GAP, BOTTOM, TOP = 28, H - 170 - 40, 320

    def layout(t):
        """y positions for items visible at time t (stacked from top, scrolled so newest stays above the footer)."""
        vis = [it for it in items if it["t_in"] <= t]
        ys, y = [], 0
        for it in vis:
            ys.append(y); y += it["img"].height + GAP
        typing = None
        for it in items:
            if it.get("typing_from") is not None and it["typing_from"] <= t < it["t_in"]:
                typing = y; y += 110 + GAP
        return vis, ys, typing, y

    def frame(f):
        t = f / FPS
        img = bg.copy()
        vis, ys, typing, total = layout(t)
        # smooth scroll: target offset so content bottom sits at BOTTOM
        def off_at(tt):
            _, _, _, tot = layout(tt)
            return max(0, TOP + tot - BOTTOM)
        o_now = off_at(t)
        prev_t = max([it["t_in"] for it in vis] + [it["typing_from"] for it in items if it.get("typing_from") is not None and it["typing_from"] <= t] + [0])
        o_prev = off_at(prev_t - 1e-3)
        k = ease((t - prev_t) / 0.25)
        off = o_prev + (o_now - o_prev) * k
        for it, y in zip(vis, ys):
            yy = TOP + y - off
            if yy + it["img"].height < 300 or yy > H:
                continue
            age = t - it["t_in"]
            s = 0.6 + 0.4 * back(age / 0.22) if (age < 0.22 and not it.get("nopop")) else 1.0
            im = it["img"]
            if it["sys"]:
                x = W / 2
            elif it["me"]:
                x = W - 40 - im.width / 2
            else:
                x = 40 + im.width / 2
            paste_scaled(img, im, x, yy + im.height / 2, s)
        if typing is not None:
            tb = typing_bubble(th, t)
            img.alpha_composite(tb, (40, int(TOP + typing - off)))
        img.alpha_composite(head, (0, 0))
        img.alpha_composite(foot, (0, H - 170))
        if hook_img is not None and t < hook_end + 0.6:
            a = 1.0 if t < hook_end else 1 - (t - hook_end) / 0.6
            s = 0.85 + 0.15 * back(t / 0.3)
            paste_scaled(img, hook_img, W / 2, H * 0.44, s, a)
        if end_img is not None and t >= end_t:
            img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(150 * ease((t - end_t) / 0.3)))))
            paste_scaled(img, end_img, W / 2, H * 0.46, 0.85 + 0.15 * back((t - end_t) / 0.3))
        return img

    times = [0.5] + [it["t_in"] + 0.5 for it in items[::max(1, len(items) // 4)]] + ([end_t + 0.5] if end_t else [dur - 0.5])
    return run(frame, n, vw, aw, out, preview, times), dur


# ================================================================== QUIZ
QUIZ_THEMES = {
    "purple": ("#3a1c71", "#d76d77", "#ffd23f"),
    "teal": ("#0f3443", "#34e89e", "#ffe14d"),
    "orange": ("#f12711", "#f5af19", "#ffffff"),
    "night": ("#0f0c29", "#302b63", "#ff4d6d"),
    "blue": ("#1e3c72", "#2a8bd8", "#ffd23f"),
}


def render_quiz(story, out, models, preview=None):
    c1, c2, acc = QUIZ_THEMES.get(story.get("theme", "purple"), QUIZ_THEMES["purple"])
    voice = story.get("voice", "narrator_f"); speed = story.get("speed", 1.03)
    qs = story["questions"]
    tr = Track(models, lead=0.2)
    segs = []
    intro = story.get("intro")
    if intro:
        tr.fx("pop", 0.05)
        a, b = tr.say(intro, voice, speed); tr.gap(0.3)
        segs.append(dict(kind="intro", t0=0, t1=tr.t))
    for i, q in enumerate(qs):
        t0 = tr.t; tr.fx("swoosh", max(0, t0 - 0.1))
        tr.say(q.get("say", q["q"]), voice, speed); tr.gap(0.2)
        c0 = tr.t; secs = q.get("seconds", 4)
        for s in range(secs):
            tr.fx("tick", c0 + s, 1.0)
        tr.gap(secs)
        r0 = tr.t; tr.fx("correct", r0)
        tr.say(q.get("a_say", q["a"]), voice, speed)
        if q.get("why"):
            tr.gap(0.1); tr.say(q["why"], voice, speed)
        tr.gap(0.5)
        segs.append(dict(kind="q", i=i, q=q, t0=t0, c0=c0, secs=secs, r0=r0, t1=tr.t))
    if not intro and segs:
        segs[0]["t0"] = 0  # riddle 1 covers the lead-in, so frame 0 is never blank
    outro = story.get("outro")
    if outro:
        t0 = tr.t; tr.fx("pop", t0); tr.say(outro, voice, speed)
        segs.append(dict(kind="outro", t0=t0, t1=tr.t + 0.8))
    work = tempfile.mkdtemp(prefix="quiz_")
    vw, aw, dur = tr.write(work, bed="none", music=story.get("music", "upbeat"))
    n = int(dur * FPS)
    bg = vgrad(hexc(c1), hexc(c2))
    # soft floating circles
    rng = np.random.default_rng(len(story.get("title", "")))
    blobs = [(rng.random() * W, rng.random() * H, 60 + rng.random() * 180, rng.random() * 6.28) for _ in range(9)]
    accent = hexc(acc)
    label = story.get("label", "RIDDLE")

    # pre-render question cards
    cards = {}
    for s in segs:
        if s["kind"] != "q":
            continue
        q = s["q"]
        f, ls = fit_font(q["q"], "mont", 860, 560, 84, 50, 800, 1.2)
        lh = int(f.size * 1.2)
        im = Image.new("RGBA", (960, lh * len(ls) + 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, 959, im.height - 1], 50, fill=(255, 255, 255, 245))
        for j, l in enumerate(ls):
            d.text((480, 60 + j * lh + lh / 2), l, font=f, fill=(25, 20, 40, 255), anchor="mm")
        ans_f, ans_l = fit_font(q["a"].upper(), "anton", 820, 300, 110, 60)
        alh = int(ans_f.size * 1.12)
        ai = Image.new("RGBA", (960, alh * len(ans_l) + 140), (0, 0, 0, 0)); d = ImageDraw.Draw(ai)
        d.rounded_rectangle([0, 0, 959, ai.height - 1], 50, fill=(34, 197, 94, 255))
        d.text((480, 42), "ANSWER", font=font("mont", 36, 800), fill=(220, 255, 230, 255), anchor="mm")
        for j, l in enumerate(ans_l):
            d.text((480, 80 + j * alh + alh / 2), l, font=ans_f, fill=(255, 255, 255, 255), anchor="mm")
        opts = []
        for o in q.get("options", []):
            oi = Image.new("RGBA", (440, 150), (0, 0, 0, 0)); od = ImageDraw.Draw(oi)
            of, ol = fit_font(o, "mont", 380, 120, 46, 30, 750)
            olh = int(of.size * 1.15)
            od.rounded_rectangle([0, 0, 439, 149], 34, fill=(255, 255, 255, 60), outline=(255, 255, 255, 200), width=4)
            for j, l in enumerate(ol):
                od.text((220, 75 - (len(ol) - 1) * olh / 2 + j * olh), l, font=of, fill=(255, 255, 255, 255), anchor="mm")
            opts.append((o, oi))
        cards[s["i"]] = (im, ai, opts)

    def big_text(text, size_max=120, color=(255, 255, 255, 255)):
        f, ls = fit_font(text.upper(), "anton", 940, 700, size_max, 60)
        lh = int(f.size * 1.12)
        im = Image.new("RGBA", (W, lh * len(ls) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for j, l in enumerate(ls):
            d.text((W / 2, 20 + j * lh + lh / 2), l, font=f, fill=color, anchor="mm", stroke_width=6, stroke_fill=(20, 10, 40, 255))
        return im
    intro_img = big_text(intro) if intro else None
    outro_img = big_text(outro, 100) if outro else None
    nq = len(qs)

    def frame(f):
        t = f / FPS
        img = bg.copy()
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for (x, y, r, ph) in blobs:
            yy = (y - t * 25) % (H + 400) - 200; xx = x + 40 * math.sin(t * 0.6 + ph)
            od.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(255, 255, 255, 22))
        img.alpha_composite(ov)
        d = ImageDraw.Draw(img)
        seg = next((s for s in segs if s["t0"] <= t < s["t1"]), segs[-1])
        if seg["kind"] == "intro":
            paste_scaled(img, intro_img, W / 2, H * 0.45, 0.7 + 0.3 * back(t / 0.35))
            return img
        if seg["kind"] == "outro":
            paste_scaled(img, outro_img, W / 2, H * 0.45, 0.7 + 0.3 * back((t - seg["t0"]) / 0.35))
            return img
        i, q = seg["i"], seg["q"]
        lt = t - seg["t0"]
        qi, ai, opts = cards[i]
        # header pill + progress dots
        hdr = f"{label} {i + 1}/{nq}"
        hf = font("mont", 46, 850); hw = tw(hdr, hf) + 90
        d.rounded_rectangle([W / 2 - hw / 2, 170, W / 2 + hw / 2, 260], 45, fill=accent)
        d.text((W / 2, 215), hdr, font=hf, fill=(25, 20, 40, 255), anchor="mm")
        for k in range(nq):
            cx = W / 2 + (k - (nq - 1) / 2) * 50
            col = accent if k < i else ((255, 255, 255, 255) if k == i else (255, 255, 255, 90))
            d.ellipse([cx - 12, 300 - 12, cx + 12, 300 + 12], fill=col)
        # question card slides in
        # no intro card (default since 2026-11-22): riddle 1 is fully on screen from frame 0
        k = 1.0 if (i == 0 and not intro) else back(lt / 0.4)
        qy = 360 + qi.height / 2
        paste_scaled(img, qi, W / 2 + (1 - min(1, k)) * W, qy, 1.0)
        y_after = 360 + qi.height + 50
        revealed = t >= seg["r0"]
        if opts:
            for j, (o, oi) in enumerate(opts):
                ox = W / 2 + (-235 if j % 2 == 0 else 235); oy = y_after + 80 + (j // 2) * 175
                ka = back((lt - 0.25 - j * 0.08) / 0.3)
                if ka <= 0:
                    continue
                if revealed:
                    good = o.strip().lower() == q["a"].strip().lower()
                    oi2 = oi.copy(); dd = ImageDraw.Draw(oi2)
                    if good:
                        dd.rounded_rectangle([0, 0, 439, 149], 34, outline=(34, 197, 94, 255), width=12)
                    else:
                        a = np.asarray(oi2).copy(); a[..., 3] = (a[..., 3] * 0.35).astype(np.uint8); oi2 = Image.fromarray(a)
                    paste_scaled(img, oi2, ox, oy, 1.0)
                else:
                    paste_scaled(img, oi, ox, oy, max(0.01, ka))
            y_after += 2 * 175 + 40
        # countdown ring
        cy = max(y_after + 170, 1250) if not opts else y_after + 160
        cy = min(cy, H - 330)
        if seg["c0"] <= t < seg["r0"]:
            el = t - seg["c0"]; left = seg["secs"] - int(el)
            frac = 1 - (el / seg["secs"])
            R = 140
            d.ellipse([W / 2 - R, cy - R, W / 2 + R, cy + R], fill=(0, 0, 0, 70))
            d.arc([W / 2 - R, cy - R, W / 2 + R, cy + R], -90, -90 + 360 * frac, fill=accent, width=22)
            pulse = 1 + 0.12 * max(0, 1 - (el % 1) / 0.25)
            nf = font("anton", int(150 * pulse))
            d.text((W / 2, cy), str(left), font=nf, fill=(255, 255, 255, 255), anchor="mm")
        elif t < seg["c0"]:
            d.text((W / 2, cy), "?", font=font("anton", 200), fill=(255, 255, 255, 160), anchor="mm")
        if revealed:
            ka = back((t - seg["r0"]) / 0.35)
            paste_scaled(img, ai, W / 2, cy, max(0.01, 0.6 + 0.4 * ka))
            if q.get("why") and t - seg["r0"] > 0.8:
                wf, wl = fit_font(q["why"], "mont", 900, 240, 44, 30, 650)
                for j, l in enumerate(wl):
                    d.text((W / 2, cy + ai.height / 2 + 60 + j * int(wf.size * 1.2)), l, font=wf, fill=(255, 255, 255, 235), anchor="mm")
        return img

    times = [0.3] + [s["c0"] + 1.2 for s in segs if s["kind"] == "q"][:2] + [s["r0"] + 0.8 for s in segs if s["kind"] == "q"][:2] + [dur - 0.5]
    return run(frame, n, vw, aw, out, preview, times), dur


WYR_THEMES = {  # (top panel A, bottom panel B, accent)
    "classic": ("#e53935", "#1e88e5", "#ffd54f"),
    "night": ("#4a148c", "#00695c", "#ff5252"),
    "sunset": ("#ef6c00", "#6a1b9a", "#fff176"),
    "mint": ("#00897b", "#c2185b", "#ffffff"),
}


def render_wyr(story, out, models, preview=None):
    """Would You Rather: split screen A (top) vs B (bottom), countdown, then 'THE CATCH' twist on one or both."""
    ca, cb, acc = WYR_THEMES.get(story.get("theme", "classic"), WYR_THEMES["classic"])
    voice = story.get("voice", "narrator"); speed = story.get("speed", 1.03)
    qs = story["questions"]
    tr = Track(models, lead=0.2)
    segs = []
    for i, q in enumerate(qs):
        t0 = tr.t; tr.fx("swoosh", max(0, t0 - 0.1))
        tr.say(q.get("say", f"Would you rather {q['a']}"), voice, speed); tr.gap(0.15)
        b0 = tr.t; tr.fx("pop", b0)
        tr.say(q.get("b_say", f"or {q['b']}?"), voice, speed); tr.gap(0.2)
        c0 = tr.t; secs = q.get("seconds", 3)
        for s in range(secs):
            tr.fx("tick", c0 + s)
        tr.gap(secs)
        r0 = tr.t; ca_t = cb_t = None
        if q.get("a_catch") or q.get("b_catch"):
            tr.fx("stinger" if story.get("scary") else "correct", r0, 0.6)
            tr.say(q.get("catch_say", "But here's the catch."), voice, speed); tr.gap(0.1)
            if q.get("a_catch"):
                ca_t = tr.t; tr.say(q["a_catch"], voice, speed); tr.gap(0.15)
            if q.get("b_catch"):
                cb_t = tr.t; tr.say(q["b_catch"], voice, speed); tr.gap(0.15)
        tr.gap(0.6)
        segs.append(dict(kind="q", i=i, q=q, t0=t0, b0=b0, c0=c0, secs=secs, r0=r0, ca=ca_t, cb=cb_t, t1=tr.t))
    segs[0]["t0"] = 0  # first dilemma fully on screen at frame 0
    outro = story.get("outro", "A or B? Comment your picks.")
    t0 = tr.t; tr.fx("pop", t0); tr.say(outro, voice, speed)
    segs.append(dict(kind="outro", t0=t0, t1=tr.t + 0.8))
    work = tempfile.mkdtemp(prefix="wyr_")
    vw, aw, dur = tr.write(work, bed=story.get("ambience", "none"), music=story.get("music", "upbeat"))
    n = int(dur * FPS)
    accent = hexc(acc)
    top = vgrad(hexc(ca), tuple(int(v * 0.7) for v in hexc(ca)[:3]) + (255,), W, H // 2)
    bot = vgrad(tuple(int(v * 0.7) for v in hexc(cb)[:3]) + (255,), hexc(cb), W, H // 2)
    label = story.get("label", "WOULD YOU RATHER")

    def opt_card(text):
        f, ls = fit_font(text, "mont", 900, 400, 78, 44, 800, 1.18)
        lh = int(f.size * 1.18)
        im = Image.new("RGBA", (W, lh * len(ls) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for j, l in enumerate(ls):
            d.text((W / 2, 10 + j * lh + lh / 2), l, font=f, fill=(255, 255, 255, 255), anchor="mm",
                   stroke_width=3, stroke_fill=(0, 0, 0, 120))
        return im

    def catch_card(text):
        f, ls = fit_font(text, "mont", 820, 260, 50, 32, 750, 1.18)
        lh = int(f.size * 1.18)
        im = Image.new("RGBA", (920, lh * len(ls) + 110), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, 919, im.height - 1], 36, fill=(15, 10, 20, 225), outline=accent, width=6)
        d.text((460, 38), "THE CATCH", font=font("mont", 34, 850), fill=accent, anchor="mm")
        for j, l in enumerate(ls):
            d.text((460, 78 + j * lh + lh / 2), l, font=f, fill=(255, 255, 255, 255), anchor="mm")
        return im

    cards = {s["i"]: (opt_card(s["q"]["a"]), opt_card(s["q"]["b"]),
                      catch_card(s["q"]["a_catch"]) if s["q"].get("a_catch") else None,
                      catch_card(s["q"]["b_catch"]) if s["q"].get("b_catch") else None)
             for s in segs if s["kind"] == "q"}
    of, ol = fit_font(outro.upper(), "anton", 940, 700, 110, 60)
    olh = int(of.size * 1.12)
    outro_img = Image.new("RGBA", (W, olh * len(ol) + 40), (0, 0, 0, 0)); d0 = ImageDraw.Draw(outro_img)
    for j, l in enumerate(ol):
        d0.text((W / 2, 20 + j * olh + olh / 2), l, font=of, fill=(255, 255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(10, 10, 20, 255))
    nq = len(qs)

    def frame(f):
        t = f / FPS
        img = Image.new("RGBA", (W, H)); img.alpha_composite(top, (0, 0)); img.alpha_composite(bot, (0, H // 2))
        d = ImageDraw.Draw(img)
        seg = next((s for s in segs if s["t0"] <= t < s["t1"]), segs[-1])
        if seg["kind"] == "outro":
            paste_scaled(img, outro_img, W / 2, H / 2, 0.7 + 0.3 * back((t - seg["t0"]) / 0.35))
            return img
        i, lt = seg["i"], t - seg["t0"]
        A, B, CA, CB = cards[i]
        first = (i == 0)
        # option A (top) and B (bottom) slide in; B arrives when it is read
        ka = 1.0 if first else back(lt / 0.35)
        kb = 1.0 if first else back((t - seg["b0"] + 0.15) / 0.35)
        revealed = t >= seg["r0"]
        ya = H * 0.25 - (60 if CA is not None and revealed else 0)
        yb = H * 0.75 - (60 if CB is not None and revealed else 0)
        paste_scaled(img, A, W / 2 - (1 - min(1, ka)) * W, ya, 1.0)
        if kb > 0:
            paste_scaled(img, B, W / 2 + (1 - min(1, kb)) * W, yb, 1.0)
        for (ltr, by) in (("A", H / 2 - 85), ("B", H / 2 + 85)):
            bx = 95
            d.ellipse([bx - 48, by - 48, bx + 48, by + 48], fill=(15, 10, 20, 255), outline=(255, 255, 255, 255), width=5)
            d.text((bx, by + 2), ltr, font=font("anton", 62), fill=(255, 255, 255, 255), anchor="mm")
        # header pill
        hdr = f"{label}  {i + 1}/{nq}"
        hf = font("mont", 40, 850); hw = tw(hdr, hf) + 80
        d.rounded_rectangle([W / 2 - hw / 2, 110, W / 2 + hw / 2, 190], 40, fill=(255, 255, 255, 235))
        d.text((W / 2, 150), hdr, font=hf, fill=(20, 15, 30, 255), anchor="mm")
        # centre badge: OR / countdown
        R = 105; cy = H / 2
        d.ellipse([W / 2 - R, cy - R, W / 2 + R, cy + R], fill=(15, 10, 20, 255), outline=(255, 255, 255, 255), width=8)
        if seg["c0"] <= t < seg["r0"]:
            el = t - seg["c0"]
            d.arc([W / 2 - R + 6, cy - R + 6, W / 2 + R - 6, cy + R - 6], -90, -90 + 360 * (1 - el / seg["secs"]), fill=accent, width=16)
            pulse = 1 + 0.12 * max(0, 1 - (el % 1) / 0.25)
            d.text((W / 2, cy), str(seg["secs"] - int(el)), font=font("anton", int(110 * pulse)), fill=(255, 255, 255, 255), anchor="mm")
        else:
            d.text((W / 2, cy), "OR", font=font("anton", 80), fill=(255, 255, 255, 255), anchor="mm")
        if revealed:
            for card, tc, base in ((CA, seg["ca"], H * 0.25), (CB, seg["cb"], H * 0.75)):
                if card is not None and tc is not None and t >= tc - 0.15:
                    k = back((t - tc + 0.15) / 0.3)
                    paste_scaled(img, card, W / 2, base + A.height / 2 + card.height / 2 - 10, max(0.01, 0.6 + 0.4 * k))
        return img

    qsegs = [s for s in segs if s["kind"] == "q"]
    times = [0.3, qsegs[0]["c0"] + 1.2, (qsegs[0]["cb"] or qsegs[0]["ca"] or qsegs[0]["r0"]) + 1.0,
             qsegs[-1]["c0"] + 1.0, dur - 0.5]
    return run(frame, n, vw, aw, out, preview, times), dur


RENDERERS = {"chat": render_chat, "quiz": render_quiz, "wyr": render_wyr}


def render(story, out, models, preview=None):
    return RENDERERS[story["style"]](story, out, models, preview)
