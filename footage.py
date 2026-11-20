#!/usr/bin/env python3
"""FOUND-FOOTAGE style renderer for scary Shorts.

Looks like recovered camera footage: night-vision camcorder, CCTV, flashlight phone video or dashcam,
with handheld shake, tape noise, glitches, REC/timecode overlays and yellow subtitle captions.
Narration, sound effects and audio mixing are shared with make_short.py.

story.json  (story-level keys)
  "style": "footage"
  "title", "description"
  "tape": {"start": "03:14:22", "date": "NOV 20 2026", "label": "TAPE 3"}   # optional
  "ambience": "tape" | "wind" | "rain" | "drone" | "crickets" | "quiet"
  "beats": [ {
     "text": "...",                       # narration (1 short sentence)
     "scene": "hallway",                  # see SCENES below
     "mode": "nv",                        # nv (night vision) | cctv | flash (flashlight) | dash (dashcam) | card (black evidence card)
     "card": "FOOTAGE RECOVERED 11/21/2026",  # text for mode "card" (typed out)
     "figure": "far" | "near" | "approach" | "vanish" | false,
     "people": 0-3,                       # friends/family silhouettes in frame
     "walk": true,                        # walking-forward camera bob
     "zoom": true,                        # camera zooms toward the figure
     "shake": true,                       # violent shake + boom
     "glitch": true,                      # tape glitch on this cut
     "cam": "CAM 03 - BASEMENT",          # label for cctv
     "hook": "card" | "glitch" | "cold",  # first beat only
     "sfx": [...]                          # extra sounds (see sfx.BANK)
  } ]
"""
import math, os, random, re, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_short as ms  # noqa: E402  (narration, captions timing, sfx mixing)
import sfx  # noqa: E402

W, H, FPS = 1080, 1920, 30
OVER = 1.14   # scenes are drawn larger for handheld moves
SS = 2
FONTS = os.path.join(HERE, "fonts")
MONO = os.path.join(FONTS, "AnonymousPro-Bold.ttf")


def mono(size):
    return ImageFont.truetype(MONO, size)


# ------------------------------------------------------------------ grayscale canvas
class G:
    def __init__(self, bg=10):
        self.w, self.h = int(W * OVER * SS), int(H * OVER * SS)
        self.img = Image.new("L", (self.w, self.h), bg)
        self.d = ImageDraw.Draw(self.img)
        self.ar = self.w / self.h

    def P(self, pts): return [(x * self.w, y * self.h) for x, y in pts]

    def poly(self, pts, v): self.d.polygon(self.P(pts), fill=int(v))

    def rect(self, x0, y0, x1, y1, v, r=0):
        b = [x0 * self.w, y0 * self.h, x1 * self.w, y1 * self.h]
        (self.d.rounded_rectangle(b, radius=r * self.w, fill=int(v)) if r else self.d.rectangle(b, fill=int(v)))

    def ell(self, cx, cy, rx, ry, v):
        self.d.ellipse([(cx - rx) * self.w, (cy - ry) * self.h, (cx + rx) * self.w, (cy + ry) * self.h], fill=int(v))

    def line(self, pts, v, wd): self.d.line(self.P(pts), fill=int(v), width=max(1, int(wd * self.w)))

    def glow(self, cx, cy, r, v):
        m = Image.new("L", (self.w // 4, self.h // 4), 0)
        ImageDraw.Draw(m).ellipse([(cx - r) * m.width, cy * m.height - r * m.width, (cx + r) * m.width, cy * m.height + r * m.width], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(max(1, r * m.width * 0.5))).resize((self.w, self.h), Image.BILINEAR)
        self.img = Image.composite(Image.new("L", self.img.size, int(v)), self.img, m.point(lambda p: p * 0.6))
        self.d = ImageDraw.Draw(self.img)

    def vgrad(self, y0, y1, v0, v1, x0=0, x1=1):
        h = int((y1 - y0) * self.h); w = int((x1 - x0) * self.w)
        if h <= 0 or w <= 0:
            return
        g = np.linspace(v0, v1, h)[:, None].repeat(w, 1).astype(np.uint8)
        self.img.paste(Image.fromarray(g), (int(x0 * self.w), int(y0 * self.h)))
        self.d = ImageDraw.Draw(self.img)

    def done(self):
        return self.img.resize((int(W * OVER), int(H * OVER)), Image.LANCZOS)


def figure(c, x, base, h, v=6, eyes=True):
    ar = c.ar; r = h * 0.1
    c.ell(x, base - h + r, r / ar, r, v)
    c.poly([(x - r / ar * 0.8, base - h + r * 1.7), (x + r / ar * 0.8, base - h + r * 1.7), (x + r / ar * 1.25, base - h * 0.45),
            (x + r / ar * 0.9, base), (x - r / ar * 0.9, base), (x - r / ar * 1.25, base - h * 0.45)], v)
    # long arms
    c.line([(x - r / ar * 1.1, base - h + r * 2.2), (x - r / ar * 1.6, base - h * 0.2)], v, h * 0.035 / ar * 0.7)
    c.line([(x + r / ar * 1.1, base - h + r * 2.2), (x + r / ar * 1.6, base - h * 0.2)], v, h * 0.035 / ar * 0.7)
    if eyes:
        for s in (-1, 1):
            c.ell(x + s * r / ar * 0.33, base - h + r * 0.95, r / ar * 0.13, r * 0.08, 255)


def human(c, x, base, h, v=150, rng=None, light=False):
    """A friend / family member: lighter silhouette with some detail (IR-bright skin)."""
    rng = rng or random.Random(1)
    ar = c.ar; hr = h * 0.085; hw = h * 0.2 / ar
    body = v - rng.randint(30, 60)
    c.rect(x - hw * 0.45, base - h * 0.45, x - hw * 0.05, base, body - 30)
    c.rect(x + hw * 0.05, base - h * 0.45, x + hw * 0.45, base, body - 30)
    c.rect(x - hw * 0.6, base - h * 0.82, x + hw * 0.6, base - h * 0.42, body, r=0.008)
    c.rect(x - hw * 0.85, base - h * 0.8, x - hw * 0.6, base - h * 0.48, body - 10)
    c.rect(x + hw * 0.6, base - h * 0.8, x + hw * 0.85, base - h * 0.48, body - 10)
    c.ell(x, base - h * 0.84 - hr, hr / ar, hr, v + 40)
    c.ell(x, base - h * 0.84 - hr * 1.5, hr / ar * 1.05, hr * 0.6, max(10, v - 100))
    if light:  # holding a flashlight: beam
        c.glow(x + hw * 1.6, base - h * 0.5, 0.05, 230)


# ------------------------------------------------------------------ scenes (return art, figure anchor (x, base, h))
def sc_hallway(c, b, rng):
    vx, vy, dw, dh = 0.5, 0.43, 0.11, 0.1
    c.poly([(0, 0), (vx - dw, vy - dh), (vx - dw, vy + dh), (0, 1)], 70)
    c.poly([(1, 0), (vx + dw, vy - dh), (vx + dw, vy + dh), (1, 1)], 58)
    c.poly([(0, 1), (vx - dw, vy + dh), (vx + dw, vy + dh), (1, 1)], 95)
    c.poly([(0, 0), (vx - dw, vy - dh), (vx + dw, vy - dh), (1, 0)], 40)
    c.rect(vx - dw, vy - dh, vx + dw, vy + dh, 22)
    c.rect(vx - dw * 0.45, vy - dh * 0.8, vx + dw * 0.45, vy + dh, 8)
    for sd in (-1, 1):
        for i, t in enumerate((0.25, 0.55)):
            xa = vx + sd * (dw + (0.5 - dw) * (1 - t)); xb = vx + sd * (dw + (0.5 - dw) * (1 - t - 0.12))
            c.poly([(xa, vy - dh - 0.33 * (1 - t)), (xb, vy - dh - 0.33 * (1 - t - 0.12)), (xb, vy + dh + 0.45 * (1 - t - 0.12)), (xa, vy + dh + 0.45 * (1 - t))], 30 + i * 10)
    for i in range(1, 8):  # floor boards
        t = (i / 8) ** 1.6
        c.line([(vx - dw - (0.5 - dw) * t * 1.2, vy + dh + (1 - vy - dh) * t), (vx + dw + (0.5 - dw) * t * 1.2, vy + dh + (1 - vy - dh) * t)], 80, 0.002)
    return (vx, vy + dh, dh * 1.6), (vx - 0.2, 0.9, 0.42)


def sc_room(c, b, rng):
    c.rect(0, 0, 1, 0.62, 52); c.rect(0, 0.62, 1, 1, 80)
    c.rect(0.06, 0.46, 0.62, 0.72, 120, r=0.01)   # bed
    c.rect(0.06, 0.4, 0.12, 0.74, 70)
    c.rect(0.12, 0.44, 0.3, 0.5, 170, r=0.01)     # pillow
    c.rect(0.66, 0.12, 0.96, 0.62, 40)            # closet
    c.rect(0.66, 0.12, 0.74, 0.62, 4)             # gap
    c.rect(0.2, 0.1, 0.48, 0.32, 95); c.rect(0.335, 0.1, 0.345, 0.32, 40); c.rect(0.2, 0.205, 0.48, 0.215, 40)
    return (0.70, 0.62, 0.42), (0.35, 0.95, 0.4)


def sc_stairs(c, b, rng):
    c.rect(0, 0, 1, 1, 18)
    for i in range(12):
        t = i / 12; y = 0.35 + t * 0.62; w = 0.18 + t * 0.4
        c.rect(0.5 - w, y, 0.5 + w, y + 0.05, 110 - i * 7)
        c.rect(0.5 - w, y + 0.012, 0.5 + w, y + 0.05, 70 - i * 4)
    c.poly([(0, 0), (0.3, 0.35), (0.3, 1), (0, 1)], 45); c.poly([(1, 0), (0.7, 0.35), (0.7, 1), (1, 1)], 38)
    c.rect(0.3, 0.12, 0.7, 0.36, 3)
    c.line([(0.12, 0.3), (0.32, 0.95)], 120, 0.006)
    return (0.5, 0.36, 0.2), (0.5, 0.98, 0.3)


def sc_door(c, b, rng):
    c.rect(0, 0, 1, 1, 50)
    c.rect(0.18, 0.06, 0.82, 0.86, 85); c.rect(0.22, 0.09, 0.78, 0.86, 105)
    for a, bb in ((0.13, 0.42), (0.5, 0.83)):
        c.rect(0.28, a, 0.72, bb, 95)
    c.ell(0.5, 0.27, 0.02, 0.012, 10)
    c.ell(0.72, 0.5, 0.018, 0.011, 190)
    c.rect(0, 0.86, 1, 1, 70)
    c.rect(0.22, 0.86, 0.78, 0.875, 210)  # light under door
    if b.get("figure"):
        for x in (0.4, 0.55):
            c.rect(x, 0.86, x + 0.05, 0.875, 10)
    return None, None


def sc_window(c, b, rng):
    c.rect(0, 0, 1, 1, 40)
    c.rect(0.1, 0.12, 0.9, 0.62, 30)
    c.vgrad(0.12, 0.4, 25, 60, 0.1, 0.9)
    c.rect(0.1, 0.4, 0.9, 0.62, 75)
    for i in range(6):  # fence
        c.rect(0.1 + i * 0.14, 0.38, 0.12 + i * 0.14, 0.45, 50)
    c.rect(0.1, 0.4, 0.9, 0.41, 50)
    for x in (0.18, 0.78):
        c.rect(x, 0.2, x + 0.03, 0.42, 20); c.ell(x + 0.015, 0.2, 0.08, 0.05, 22)
    c.rect(0.49, 0.12, 0.51, 0.62, 90); c.rect(0.1, 0.36, 0.9, 0.375, 90)
    c.rect(0.06, 0.08, 0.94, 0.12, 100); c.rect(0.06, 0.62, 0.94, 0.66, 100)
    return (0.62, 0.55, 0.16), (0.3, 0.98, 0.35)


def sc_forest(c, b, rng):
    c.rect(0, 0, 1, 1, 8)
    c.vgrad(0.55, 1.0, 30, 95)
    c.poly([(0.42, 0.55), (0.58, 0.55), (0.9, 1), (0.1, 1)], 110)
    for layer, (v, wmin, n) in enumerate(((22, 0.012, 14), (40, 0.025, 8), (70, 0.06, 4))):
        for _ in range(n):
            x = rng.uniform(-0.05, 1.05)
            if layer == 2 and 0.3 < x < 0.7:
                continue
            w = wmin * rng.uniform(0.8, 1.4)
            c.rect(x - w, 0, x + w, 0.56 + layer * 0.12 + rng.uniform(0, 0.05), v)
    return (0.52, 0.6, 0.13), (0.25, 0.97, 0.36)


def sc_livingroom(c, b, rng):
    c.rect(0, 0, 1, 0.6, 55); c.rect(0, 0.6, 1, 1, 85)
    c.rect(0.05, 0.42, 0.62, 0.62, 100, r=0.02); c.rect(0.05, 0.36, 0.62, 0.46, 115, r=0.02)
    c.rect(0.7, 0.36, 0.98, 0.52, 12); c.rect(0.72, 0.38, 0.96, 0.5, 35)  # TV
    c.rect(0.82, 0.52, 0.86, 0.62, 60)
    c.rect(0.15, 0.08, 0.45, 0.28, 30); c.rect(0.3, 0.08, 0.31, 0.28, 70)
    c.line([(0.66, 0.6), (0.66, 0.3)], 90, 0.004); c.poly([(0.63, 0.3), (0.69, 0.3), (0.68, 0.26), (0.64, 0.26)], 200)
    return (0.3, 0.32, 0.12), (0.2, 0.62, 0.3)


def sc_kitchen(c, b, rng):
    c.rect(0, 0, 1, 0.55, 60); c.rect(0, 0.55, 1, 1, 90)
    c.rect(0, 0.4, 0.7, 0.58, 120); c.rect(0, 0.38, 0.7, 0.41, 160)
    for x in np.arange(0.02, 0.7, 0.17):
        c.rect(x, 0.43, x + 0.15, 0.56, 105)
        c.rect(x, 0.08, x + 0.15, 0.26, 100)
    c.rect(0.74, 0.08, 0.98, 0.58, 135)  # fridge
    c.rect(0.76, 0.3, 0.78, 0.4, 90)
    c.rect(0.45, 0.12, 0.66, 0.34, 6)    # open back door (black)
    return (0.555, 0.34, 0.2), (0.25, 0.9, 0.3)


def sc_attic(c, b, rng):
    c.rect(0, 0, 1, 1, 15)
    c.poly([(0.5, 0.05), (1.1, 0.7), (-0.1, 0.7)], 45)
    for i in range(7):
        x = i / 6
        c.line([(0.5, 0.05), (x * 1.2 - 0.1, 0.7)], 85, 0.01)
    c.rect(0, 0.68, 1, 1, 70)
    for (x, y, w, h) in ((0.12, 0.6, 0.16, 0.1), (0.2, 0.55, 0.12, 0.07), (0.72, 0.62, 0.18, 0.08)):
        c.rect(x, y, x + w, y + h, 110)
    c.line([(0.55, 0.7), (0.6, 0.55)], 100, 0.006); c.line([(0.64, 0.7), (0.66, 0.55)], 100, 0.006)
    c.rect(0.56, 0.54, 0.68, 0.57, 110); c.line([(0.55, 0.72), (0.68, 0.72)], 100, 0.006)  # rocking chair
    return (0.4, 0.68, 0.16), (0.3, 0.95, 0.3)


def sc_road(c, b, rng):
    c.rect(0, 0, 1, 1, 6)
    c.poly([(0.47, 0.45), (0.53, 0.45), (1.1, 1), (-0.1, 1)], 70)
    for i in range(9):
        t0, t1 = (i / 9) ** 2, ((i + 0.45) / 9) ** 2
        y0, y1 = 0.45 + 0.55 * t0, 0.45 + 0.55 * t1
        c.poly([(0.5 - 0.002 - 0.02 * t0, y0), (0.5 + 0.002 + 0.02 * t0, y0), (0.5 + 0.002 + 0.02 * t1, y1), (0.5 - 0.002 - 0.02 * t1, y1)], 200)
    c.glow(0.5, 0.7, 0.3, 120)
    for side in (-1, 1):
        for i in range(7):
            t = (i + 1) / 8
            x = 0.5 + side * (0.06 + 0.5 * t ** 1.5)
            c.rect(x - 0.01 * t * 3, 0.45 - 0.35 * t, x + 0.01 * t * 3, 0.45 + 0.55 * t ** 2, 25 + 40 * t)
    return (0.56, 0.56, 0.1), (0.5, 1.0, 0.25)


def sc_tent(c, b, rng):
    c.rect(0, 0, 1, 1, 90)
    c.poly([(0, 0), (0.5, 0.0), (0.2, 1)], 110); c.poly([(1, 0), (0.5, 0.0), (0.8, 1)], 100)
    c.poly([(0.32, 0.25), (0.68, 0.25), (0.8, 1), (0.2, 1)], 10)   # open flap to dark forest
    for x in (0.36, 0.45, 0.6, 0.66):
        c.rect(x, 0.25, x + 0.012, 0.75, 22)
    c.rect(0, 0.82, 1, 1, 120)
    return (0.52, 0.72, 0.18), (0.2, 1.0, 0.3)


def sc_yard(c, b, rng):
    c.rect(0, 0, 1, 1, 10)
    c.rect(0, 0.6, 1, 1, 60)
    c.rect(0.2, 0.25, 0.8, 0.6, 45); c.poly([(0.15, 0.25), (0.5, 0.1), (0.85, 0.25)], 35)
    for (x, lit) in ((0.3, False), (0.62, True)):
        c.rect(x, 0.32, x + 0.1, 0.42, 220 if lit else 20)
    c.rect(0.45, 0.45, 0.55, 0.6, 25)
    return (0.67, 0.42, 0.08), (0.25, 0.95, 0.3)


def sc_face(c, b, rng):
    c.rect(0, 0, 1, 1, 4)
    c.ell(0.5, 0.42, 0.4, 0.26, 18)
    c.poly([(0.0, 1.0), (0.18, 0.62), (0.82, 0.62), (1.0, 1.0)], 14)
    for s in (-1, 1):
        c.glow(0.5 + s * 0.13, 0.38, 0.07, 255)
        c.ell(0.5 + s * 0.13, 0.38, 0.045, 0.016, 255)
    c.d.arc([0.33 * c.w, 0.43 * c.h, 0.67 * c.w, 0.53 * c.h], 10, 170, fill=200, width=int(0.008 * c.w))
    return None, None


def sc_black(c, b, rng):
    return None, None


SCENES = {"hallway": sc_hallway, "room": sc_room, "bedroom": sc_room, "stairs": sc_stairs, "basement": sc_stairs,
          "door": sc_door, "window": sc_window, "forest": sc_forest, "livingroom": sc_livingroom, "kitchen": sc_kitchen,
          "attic": sc_attic, "road": sc_road, "tent": sc_tent, "yard": sc_yard, "face": sc_face, "black": sc_black}


def draw_scene(b, seed):
    rng = random.Random(seed)
    c = G()
    fig, ppl = SCENES.get(b.get("scene", "hallway"), sc_hallway)(c, b, rng)
    n = int(b.get("people", 0))
    if ppl and n:
        px, pb, ph = ppl
        for k in range(min(3, n)):
            human(c, px + (k - (n - 1) / 2) * 0.22, pb + k * 0.01, ph * (1 - 0.08 * k), v=150 + rng.randint(-20, 20), rng=rng,
                  light=(b.get("mode") == "flash"))
    return c.done(), fig


def figure_layer(fig, scale=1.0):
    """Figure on its own transparent layer so it can approach / vanish."""
    if not fig:
        return None
    x, base, h = fig
    c = G(0)
    m = G(0)
    figure(m, x, base, h * scale, v=255, eyes=False)
    figure(c, x, base, h * scale, v=6, eyes=True)
    lum = c.done(); alpha = m.done()
    return lum, alpha


# ------------------------------------------------------------------ post FX
def _vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    return np.clip(1.22 - 0.62 * r ** 1.7, 0.05, 1).astype(np.float32)


VIG = None
NOISE = None
SCAN = None


def _init_fx():
    global VIG, NOISE, SCAN
    if VIG is None:
        VIG = _vignette()
        r = np.random.default_rng(5)
        # coarse grain (upscaled from 1/3 res) compresses far better than per-pixel noise
        NOISE = [np.asarray(Image.fromarray(((r.normal(0, 1, (H // 3, W // 3)) * 40) + 128).clip(0, 255).astype(np.uint8))
                            .resize((W, H), Image.BILINEAR), np.float32) / 40 - 3.2 for _ in range(4)]
        SCAN = np.ones((H, 1), np.float32); SCAN[::4] = 0.78; SCAN[1::4] = 0.9


def colorize(L, mode, f):
    """L: float32 HxW 0..255 -> RGB uint8 per camera mode."""
    n = NOISE[f % len(NOISE)]
    if mode == "nv":
        L = L * 1.15 + n * 14 + 8
        L = L * VIG * SCAN
        rgb = np.stack([L * 0.32, L * 1.0 + 10, L * 0.38], 2)
    elif mode == "cctv":
        L = L * 1.05 + n * 16 + 12
        L = L * (0.55 + 0.45 * VIG) * SCAN
        rgb = np.stack([L * 0.92, L * 0.96, L * 1.04], 2)
    elif mode == "dash":
        L = L * 1.0 + n * 10
        L = L * (0.5 + 0.5 * VIG)
        rgb = np.stack([L * 0.95, L * 0.9, L * 0.8], 2)
    else:  # flash / card / default: warm, very dark outside the beam (beam applied by caller)
        L = L + n * 12
        rgb = np.stack([L * 1.0, L * 0.9, L * 0.74], 2)
    return np.clip(rgb, 0, 255).astype(np.uint8)


def glitch(a, f, strength=1.0):
    r = np.random.default_rng(f * 31 + 7)
    for _ in range(int(6 * strength)):
        y0 = r.integers(0, H - 60); hh = r.integers(6, 70)
        a[y0:y0 + hh] = np.roll(a[y0:y0 + hh], int(r.integers(-120, 120) * strength), axis=1)
    sh = int(10 * strength)
    a[..., 0] = np.roll(a[..., 0], sh, axis=1); a[..., 2] = np.roll(a[..., 2], -sh, axis=1)
    y = int(r.integers(0, H)); a[y:y + 24] = np.clip(a[y:y + 24].astype(int) + 90, 0, 255)
    return a


# ------------------------------------------------------------------ overlays + captions
def tc(start, t):
    h, m, s = (int(x) for x in start.split(":"))
    tot = h * 3600 + m * 60 + s + int(t)
    return f"{tot // 3600 % 24:02d}:{tot // 60 % 60:02d}:{tot % 60:02d}"


def hud(img, mode, t, tape, b):
    d = ImageDraw.Draw(img)
    f = mono(46); fs = mono(38)
    white = (236, 236, 236)
    if mode in ("nv", "flash"):
        if int(t * 2) % 2 == 0:
            d.ellipse([70, 112, 100, 142], fill=(240, 40, 40))
        d.text((116, 100), "REC", font=f, fill=white)
        d.text((W - 270, 100), tc(tape["start"], t), font=f, fill=white)
        d.text((70, H - 140), tape["date"], font=fs, fill=white)
        d.rectangle([W - 200, H - 140, W - 100, H - 100], outline=white, width=4)
        d.rectangle([W - 194, H - 134, W - 150, H - 106], fill=white)
        d.rectangle([W - 100, H - 128, W - 92, H - 112], fill=white)
        for (x, y) in ((60, 60), (W - 60, 60), (60, H - 60), (W - 60, H - 60)):
            dx = 44 if x < W / 2 else -44; dy = 44 if y < H / 2 else -44
            d.line([(x, y), (x + dx, y)], fill=white, width=5); d.line([(x, y), (x, y + dy)], fill=white, width=5)
        if mode == "nv":
            d.text((W - 200, 160), "NV", font=fs, fill=white)
    elif mode == "cctv":
        d.text((60, 70), b.get("cam", "CAM 02"), font=f, fill=white)
        d.text((60, H - 130), f"{tape['iso']} {tc(tape['start'], t)}", font=fs, fill=white)
    elif mode == "dash":
        d.text((60, H - 130), f"{tape['iso']}  {tc(tape['start'], t)}  {int(52 + 4 * math.sin(t))} KM/H", font=fs, fill=white)
        d.text((60, 70), "DASHCAM 1080P", font=fs, fill=white)
    return img


def card_frame(text, lt):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    f = mono(56)
    shown = text[: int(lt * 22)]
    lines, cur = [], ""
    for word in shown.split(" "):
        if d.textlength((cur + " " + word).strip(), font=f) > W - 180:
            lines.append(cur); cur = word
        else:
            cur = (cur + " " + word).strip()
    lines.append(cur)
    y = H / 2 - len(lines) * 40
    for l in lines:
        d.text((90, y), l, font=f, fill=(230, 230, 230)); y += 80
    if int(lt * 2.5) % 2 == 0:
        d.rectangle([90 + d.textlength(lines[-1], font=f) + 8, y - 70, 90 + d.textlength(lines[-1], font=f) + 40, y - 14], fill=(230, 230, 230))
    return img


def write_ass(timing, beats, path):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Anonymous Pro,58,&H0078ECFF,&H0078ECFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,3,14,0,2,90,90,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for b, tm in zip(beats, timing):
        if b.get("mode") == "card":
            continue
        for s, t0, t1 in tm["sents"]:
            cs = ms.chunks_of(s.split(), 6)
            tot = sum(len(" ".join(c)) + 3 for c in cs)
            t = t0
            for j, c in enumerate(cs):
                d = (t1 - t0) * (len(" ".join(c)) + 3) / tot
                end = t + d if j < len(cs) - 1 else t1 + 0.15
                ev.append(f"Dialogue: 0,{ms.ass_time(t)},{ms.ass_time(end)},Sub,,0,0,0,,{' '.join(c).upper()}")
                t += d
    open(path, "w").write(head + "\n".join(ev) + "\n")


# ------------------------------------------------------------------ render
def render(story, out, models, preview_dir=None):
    _init_fx()
    beats = story["beats"]
    for b in beats:
        b.setdefault("mode", "nv")
        if b.get("scene") == "black":
            b["mode"] = "card"
        if b["mode"] == "card":
            b.setdefault("scene", "black")
    tape = dict({"start": "03:14:22", "date": "NOV 20 2026", "label": "TAPE 1"}, **story.get("tape", {}))
    try:
        import datetime
        dt = datetime.datetime.strptime(tape["date"].title(), "%b %d %Y")
        tape["iso"] = dt.strftime("%Y-%m-%d")
    except Exception:
        tape["iso"] = "2026-11-20"
    work = tempfile.mkdtemp(prefix="ff_")
    wav, ass, amb = (os.path.join(work, n) for n in ("voice.wav", "subs.ass", "amb.wav"))
    timing, dur = ms.narrate(beats, models, wav)
    timing[0]["start"] = 0.0
    write_ass(timing, beats, ass)

    # sound: reuse the shared engine, mapping footage hooks/glitches to its names
    shadow = []
    for b in beats:
        sb = dict(b)
        if b.get("hook"):
            sb["hook"] = {"card": "quiet", "cold": "flash", "glitch": "glitch"}.get(b["hook"], "glitch")
        if b.get("glitch"):
            sb["transition"] = "glitch"
        if b.get("figure") == "vanish":
            sb.setdefault("sfx", []).append({"name": "static", "at": 0.9})
        if b.get("figure") == "approach":
            sb.setdefault("sfx", []).append({"name": "riser", "at": 0.0})
        if b.get("mode") == "card":
            sb.setdefault("sfx", []).append({"name": "static", "at": 0.0})
        shadow.append(sb)
    ms.AMBIENCE[0] = story.get("ambience", "tape")
    ms.mix_audio(shadow, timing, dur, wav, amb)

    seed0 = sum(map(ord, story.get("title", "x")))
    arts, figs = [], []
    for i, b in enumerate(beats):
        art, fig = draw_scene(b, seed0 + i)
        arts.append(np.asarray(art, np.float32))
        f = b.get("figure", False)
        figs.append(figure_layer(fig) if (fig and f) else None)
    n = int(round(dur * FPS))
    bidx = np.zeros(n, int)
    for i, tm in enumerate(timing):
        bidx[min(n - 1, int(tm["start"] * FPS)):] = i
    rngg = np.random.default_rng(seed0)
    auto_glitch = set()
    for _ in range(int(dur / 7)):
        s = int(rngg.integers(0, n - 6)); auto_glitch.update(range(s, s + int(rngg.integers(2, 6))))

    def frame(f):
        t = f / FPS
        i = bidx[f]; b = beats[i]; tm = timing[i]
        lt = t - tm["start"]; span = max(0.5, tm["end"] - tm["start"]); p = min(1.0, lt / span)
        mode = b["mode"]
        if mode == "card":
            img = card_frame(b.get("card", b["text"]), lt)
            a = np.asarray(img).copy()
            if lt < 0.25 or (span - lt) < 0.2:
                a = glitch(a, f, 1.4)
            return a
        if mode == "cctv":  # low frame-rate security camera
            f_eff = f - (f % 5); t_eff = f_eff / FPS
        else:
            f_eff, t_eff = f, t
        A = arts[i]
        ah, aw = A.shape
        # handheld / camera motion
        amp = 0 if mode == "cctv" else (14 if mode != "dash" else 5)
        ox = amp * (math.sin(t_eff * 1.3) + 0.6 * math.sin(t_eff * 2.9 + 1) + 0.3 * math.sin(t_eff * 7.1))
        oy = amp * (math.sin(t_eff * 1.1 + 2) + 0.5 * math.sin(t_eff * 3.7))
        k = 1 / OVER
        if b.get("walk"):
            oy += 12 * math.sin(t_eff * 2 * math.pi * 1.7); k *= 1 - 0.08 * p
        if b.get("zoom"):
            k *= 1 - 0.25 * (1 - (1 - p) ** 2)
        if (b.get("shake") or (b.get("hook") == "cold")) and lt < 1.0:
            ox += 30 * (1 - lt) * math.sin(lt * 80); oy += 30 * (1 - lt) * math.cos(lt * 63)
        cw, ch = aw * k, ah * k
        cx, cy = aw / 2, ah / 2
        fg = figs[i]
        if b.get("zoom") and b.get("figure") and fg is not None:
            fx, fy = fg_center(beats[i], A)
            cx = cx + (fx - cx) * 0.6 * p; cy = cy + (fy - cy) * 0.6 * p
        x0 = min(max(0, cx - cw / 2 + ox), aw - cw); y0 = min(max(0, cy - ch / 2 + oy), ah - ch)
        base_img = Image.fromarray(A.astype(np.uint8))
        L = base_img.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)
        if fg is not None:
            fv = b.get("figure")
            vis = 1.0
            if fv == "vanish" and lt > 0.9:
                vis = 0.0
            if vis > 0:
                lum = fg[0].transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)
                al = fg[1].transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)
                if fv == "approach":  # scale up around its feet
                    s = 1 + 1.4 * p ** 2
                    lum = lum.resize((int(W * s), int(H * s)), Image.BILINEAR).crop(((W * s - W) / 2, (H * s - H) * 0.75, (W * s - W) / 2 + W, (H * s - H) * 0.75 + H))
                    al = al.resize((int(W * s), int(H * s)), Image.BILINEAR).crop(((W * s - W) / 2, (H * s - H) * 0.75, (W * s - W) / 2 + W, (H * s - H) * 0.75 + H))
                L = Image.composite(lum, L, al)
        La = np.asarray(L, np.float32)
        if lt < 0.22 and i > 0:  # autofocus hunt on cuts
            small = L.resize((W // 6, H // 6), Image.BILINEAR).resize((W, H), Image.BILINEAR)
            La = La * (lt / 0.22) + np.asarray(small, np.float32) * (1 - lt / 0.22)
        if mode == "flash":
            yy = (np.arange(H) - (H * 0.48 + oy * 2))[:, None]; xx = (np.arange(W) - (W * 0.5 + ox * 2))[None, :]
            beam = np.clip(1.15 - np.sqrt(xx ** 2 + (yy * 0.75) ** 2) / 520, 0.08, 1.0)
            La = La * beam * 1.25
        a = colorize(La, mode, f_eff)
        if (b.get("glitch") and lt < 0.4) or (b.get("hook") == "glitch" and lt < 0.9) or f in auto_glitch \
                or (b.get("figure") == "vanish" and 0.8 < lt < 1.05):
            a = glitch(a.copy(), f, 1.0 if f not in auto_glitch else 0.5)
        img = hud(Image.fromarray(a), mode, t, tape, b)
        return np.asarray(img)

    def fg_center(b, A):
        sc = SCENES.get(b.get("scene", "hallway"))
        c = G(); fig, _ = sc(c, b, random.Random(0))
        x, base, h = fig
        return x * A.shape[1], (base - h * 0.6) * A.shape[0]

    if preview_dir:
        os.makedirs(preview_dir, exist_ok=True)
        paths = []
        for i, tm in enumerate(timing):
            f = min(n - 1, int((tm["start"] + min(1.4, (tm["end"] - tm["start"]) * 0.7)) * FPS))
            p = os.path.join(preview_dir, f"b{i:02d}.png")
            Image.fromarray(frame(f)).save(p)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-vf", f"setpts=PTS+{f / FPS}/TB,ass={ass}:fontsdir={FONTS}",
                            "-update", "1", p + ".c.png"], check=True)
            os.replace(p + ".c.png", p)
            paths.append(p)
        return paths, dur

    tmp = out[:-4] + ".part.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-i", amb, "-filter_complex",
           f"[0:v]ass={ass}:fontsdir={FONTS},format=yuv420p[v];"
           f"[1:a]aresample=48000,highpass=f=90,aecho=0.8:0.5:35:0.1[vo];[2:a]volume=0.55[am];"
           f"[vo][am]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]",
           "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-maxrate", "6M", "-bufsize", "12M",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmp]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        pr.stdin.write(frame(f).tobytes())
    pr.stdin.close()
    if pr.wait() != 0:
        sys.exit("ffmpeg failed")
    os.replace(tmp, out)
    return out, dur
