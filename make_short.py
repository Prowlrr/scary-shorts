#!/usr/bin/env python3
"""Flat-illustration scary-story YouTube Short builder.

Usage: python3 make_short.py story.json out.mp4 [--models DIR] [--preview DIR]

story.json
{
  "title": "...",                      # YouTube title (not drawn)
  "season": "autumn",                  # autumn | summer | rain | fog (winter exists but isn't used)
  "beats": [                           # one scene per beat, 1-2 short sentences each
    {"text": "If every phone in your town gets the same alert...",
     "scene": "street",                # see SCENES: street town livingroom phone door window hallway bedroom forest
                                       #   road lake cabin basement kitchen cemetery bathroom campsite
     "overlay": {"type": "alert", "lines": ["DO NOT OPEN YOUR DOOR.", "NOT EVEN FOR FAMILY."], "red": [1]},
     "mood": "scared",                 # optional: character face (neutral/scared)
     "figure": true,                   # optional: show the lurking figure (window/door/hallway/bedroom/forest/livingroom)
     "shake": true,                    # optional: camera shake + boom (knocks, bangs, twist)
     "hook": true,                     # FIRST beat only: cold-open teaser (overlay instant, red flash, stinger)
     "sfx": ["knock", {"name": "creak", "at": 0.5}]}  # optional extra sounds (see sfx.BANK); auto sounds are added from overlays/keywords
  ]
}
overlay types:
  alert {lines, red:[idx], header?}     clock {time}      sign {name, sub}
  text  {from, message}                 label {text}      none
Needs ffmpeg+libass, pip: kokoro-onnx soundfile pillow numpy; models/ with
kokoro-v1.0.int8.onnx + voices-v1.0.bin; fonts/ with Anton + Montserrat.
"""
import json, math, os, random, re, subprocess, sys, tempfile
import numpy as np
sys_path = __import__('sys').path
sys_path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import sfx
SFXBANK = sfx.BANK
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
SS = 2            # supersampling for static art
ZOOM = 1.08       # art is drawn this much larger for slow push-ins
VOICE, SPEED = "am_echo", 1.08
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

SKY_T, SKY_B = (24, 30, 56), (64, 70, 98)
SNOW_T, SNOW_B = (226, 230, 240), (196, 202, 218)
WALL, WALL2 = (98, 104, 122), (120, 126, 144)
ROOF = (58, 62, 80)
WIN_D, WIN_L = (52, 56, 72), (250, 212, 128)
DOOR = (72, 74, 90)
INK = (24, 26, 36)
SKIN, HAIR, JACKET, PANTS = (236, 200, 168), (34, 30, 34), (58, 74, 112), (36, 40, 56)


def font(name, size, weight=None):
    path = {"anton": "Anton-Regular.ttf", "mont": "Montserrat[wght].ttf"}[name]
    f = ImageFont.truetype(os.path.join(FONTS, path), size)
    if weight:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


class Canvas:
    """Draws in unit coords (0..1 of the zoomed art) at supersampled resolution."""

    def __init__(self, top, bot=None):
        self.w, self.h = int(W * ZOOM * SS), int(H * ZOOM * SS)
        bot = bot or top
        t = np.linspace(0, 1, self.h)[:, None, None]
        g = np.array(top, float) * (1 - t) + np.array(bot, float) * t
        self.img = Image.fromarray(np.repeat(g, self.w, axis=1).astype(np.uint8))
        self.d = ImageDraw.Draw(self.img)

    @property
    def ar(self): return self.w / self.h

    def X(self, x): return x * self.w

    def Y(self, y): return y * self.h

    def P(self, pts): return [(self.X(x), self.Y(y)) for x, y in pts]

    def rect(self, x0, y0, x1, y1, fill, r=0):
        box = [self.X(min(x0, x1)), self.Y(min(y0, y1)), self.X(max(x0, x1)), self.Y(max(y0, y1))]
        if r:
            self.d.rounded_rectangle(box, radius=r * self.w, fill=fill)
        else:
            self.d.rectangle(box, fill=fill)

    def poly(self, pts, fill): self.d.polygon(self.P(pts), fill=fill)

    def ell(self, cx, cy, rx, ry, fill):
        self.d.ellipse([self.X(cx - rx), self.Y(cy - ry), self.X(cx + rx), self.Y(cy + ry)], fill=fill)

    def line(self, pts, fill, wd): self.d.line(self.P(pts), fill=fill, width=max(1, int(wd * self.w)))

    def glow(self, cx, cy, r, color, strength=120):
        m = Image.new("L", (self.w // 4, self.h // 4), 0)
        rx, ry = r * m.width, r * m.width
        ImageDraw.Draw(m).ellipse([cx * m.width - rx, cy * m.height - ry, cx * m.width + rx, cy * m.height + ry], fill=strength)
        m = m.filter(ImageFilter.GaussianBlur(max(1, rx * 0.45))).resize((self.w, self.h), Image.BILINEAR)
        self.img.paste(color, mask=m)
        self.d = ImageDraw.Draw(self.img)

    def stars(self, n, ymax, rng):
        for _ in range(n):
            x, y, r = rng.random(), rng.random() * ymax, rng.uniform(0.0012, 0.0026)
            b = rng.randint(170, 240)
            self.ell(x, y, r, r * self.ar, (b, b, b + 10))

    def gradient_band(self, y, top, bot):
        hh = self.h - int(self.Y(y))
        t = np.linspace(0, 1, hh)[:, None, None]
        g = np.array(top, float) * (1 - t) + np.array(bot, float) * t
        self.img.paste(Image.fromarray(np.repeat(g, self.w, axis=1).astype(np.uint8)), (0, int(self.Y(y))))
        self.d = ImageDraw.Draw(self.img)

    def done(self):
        return self.img.resize((int(W * ZOOM), int(H * ZOOM)), Image.LANCZOS)


# ------------------------------------------------------------------ props
def house(c, x, base, w, h, lit=False, snow=True):
    c.rect(x - w / 2, base - h, x + w / 2, base, WALL2 if lit else WALL)
    peak = base - h - w * 0.3 * c.ar
    c.poly([(x - w / 2 - w * 0.06, base - h), (x, peak), (x + w / 2 + w * 0.06, base - h)], ROOF)
    if snow and SEASON["caps"]:
        c.line([(x - w / 2 - w * 0.06, base - h), (x, peak), (x + w / 2 + w * 0.06, base - h)], (240, 242, 248), w * 0.035)
    ww, wh = w * 0.14, h * 0.24
    for wx in (x - w * 0.28, x + w * 0.28):
        if lit:
            c.glow(wx, base - h * 0.55, ww * 1.4, (255, 210, 130), 70)
        c.rect(wx - ww / 2, base - h * 0.55 - wh / 2, wx + ww / 2, base - h * 0.55 + wh / 2, WIN_L if lit else WIN_D)
        c.line([(wx, base - h * 0.55 - wh / 2), (wx, base - h * 0.55 + wh / 2)], WALL, w * 0.012)
    c.rect(x - w * 0.08, base - h * 0.5, x + w * 0.08, base, DOOR)
    if lit:
        c.glow(x, base - h * 0.62, w * 0.06, (255, 215, 140), 200)
        c.ell(x, base - h * 0.62, w * 0.012, w * 0.012 * c.ar, (255, 230, 170))


def pine(c, x, base, h, col):
    w = h * 0.42 / c.ar
    for i in range(3):
        y0 = base - h * (0.25 + i * 0.25)
        c.poly([(x - w * (0.55 - i * 0.12), y0 + h * 0.3), (x, y0 - h * 0.12), (x + w * (0.55 - i * 0.12), y0 + h * 0.3)], col)
    c.rect(x - w * 0.06, base - h * 0.08, x + w * 0.06, base, (50, 44, 44))


def lamp_post(c, x, base, h):
    c.line([(x, base), (x, base - h)], (40, 42, 52), 0.004)
    c.glow(x, base - h, 0.05, (255, 214, 140), 80)
    c.ell(x, base - h, 0.008, 0.008 * c.ar, (255, 232, 170))


def person(c, x, base, h, mood="neutral"):
    ar = c.ar
    hw = h * 0.21 / ar * 1.0
    head_r = h * 0.085
    c.rect(x - hw * 0.42, base - h * 0.42, x - hw * 0.06, base - h * 0.01, PANTS)
    c.rect(x + hw * 0.06, base - h * 0.42, x + hw * 0.42, base - h * 0.01, PANTS)
    c.rect(x - hw * 0.5, base - h * 0.03, x - hw * 0.02, base, INK)
    c.rect(x + hw * 0.02, base - h * 0.03, x + hw * 0.5, base, INK)
    c.rect(x - hw * 0.55, base - h * 0.8, x + hw * 0.55, base - h * 0.4, JACKET, r=0.01)
    for s in (-1, 1):
        c.rect(x + s * hw * 0.56, base - h * 0.78, x + s * hw * 0.8, base - h * 0.46, (50, 64, 98), r=0.006)
        c.ell(x + s * hw * 0.68, base - h * 0.45, hw * 0.13, hw * 0.13 * ar, SKIN)
    c.rect(x - hw * 0.12, base - h * 0.85, x + hw * 0.12, base - h * 0.78, SKIN)
    hy = base - h * 0.84 - head_r
    c.ell(x, hy, head_r / ar, head_r, SKIN)
    c.ell(x, hy - head_r * 0.45, head_r / ar * 1.05, head_r * 0.62, HAIR)
    c.ell(x, hy + head_r * 0.12, head_r / ar * 0.96, head_r * 0.72, SKIN)
    ex, ey = head_r / ar * 0.36, hy + head_r * 0.08
    er = head_r * (0.14 if mood == "scared" else 0.09)
    for s in (-1, 1):
        if mood == "scared":
            c.ell(x + s * ex, ey, er / ar, er, (255, 255, 255))
            c.ell(x + s * ex, ey, er / ar * 0.45, er * 0.45, INK)
        else:
            c.ell(x + s * ex, ey, er / ar * 0.6, er * 0.6, INK)
    if mood == "scared":
        c.ell(x, hy + head_r * 0.52, head_r / ar * 0.12, head_r * 0.14, (110, 46, 46))
    else:
        c.line([(x - ex * 0.4, hy + head_r * 0.5), (x + ex * 0.4, hy + head_r * 0.5)], (150, 90, 80), 0.002)


def shadow_figure(c, x, base, h, col=(14, 14, 22), eyes=False):
    ar = c.ar
    r = h * 0.11
    c.ell(x, base - h + r, r / ar, r, col)
    c.poly([(x - r / ar * 0.9, base - h + r * 1.8), (x + r / ar * 0.9, base - h + r * 1.8),
            (x + r / ar * 1.5, base - h * 0.35), (x + r / ar * 1.1, base), (x - r / ar * 1.1, base),
            (x - r / ar * 1.5, base - h * 0.35)], col)
    if eyes:
        for s in (-1, 1):
            c.ell(x + s * r / ar * 0.35, base - h + r * 0.95, r / ar * 0.13, r * 0.09, (240, 240, 240))


def night_sky(c, rng):
    c.stars(110, 0.5, rng)
    c.glow(0.5, 0.06, 0.4, (90, 96, 130), 50)


# ------------------------------------------------------------------ scenes
def sc_street(c, beat, rng):
    night_sky(c, rng)
    base = 0.5
    c.gradient_band(base, SNOW_T, SNOW_B)
    lit_i = rng.choice([1, 2, 3])
    for i, x in enumerate([-0.05, 0.22, 0.5, 0.78, 1.05]):
        house(c, x, base, 0.26, 0.1, lit=(i == lit_i))
    for x in (0.08, 0.36, 0.64, 0.92):
        lamp_post(c, x, base + 0.055, 0.1)
    c.rect(0, base + 0.06, 1, base + 0.14, (170, 176, 194))
    for x in np.arange(0.02, 1, 0.12):
        c.rect(x, base + 0.097, x + 0.06, base + 0.103, (215, 220, 232))
    if beat.get("figure"):
        shadow_figure(c, 0.6, base + 0.13, 0.11, eyes=True)


def sc_town(c, beat, rng):
    night_sky(c, rng)
    c.ell(0.78, 0.13, 0.055, 0.055 * c.ar, (226, 228, 220))
    c.poly([(-0.1, 0.36)] + [(x, 0.31 - 0.03 * math.sin(x * 5 + 1)) for x in np.arange(-0.1, 1.15, 0.05)] + [(1.1, 0.36)], (34, 40, 56))
    c.gradient_band(0.35, SNOW_T, SNOW_B)
    for x in np.arange(0.0, 1.05, 0.05):
        pine(c, x + rng.uniform(-0.01, 0.01), 0.36, rng.uniform(0.03, 0.045), (26, 30, 42))
    # water tower + church
    c.rect(0.12, 0.27, 0.125, 0.36, (40, 44, 60)); c.rect(0.175, 0.27, 0.18, 0.36, (40, 44, 60))
    c.ell(0.1525, 0.26, 0.05, 0.022, (70, 76, 96))
    c.rect(0.8, 0.3, 0.86, 0.37, (70, 74, 92)); c.poly([(0.8, 0.3), (0.83, 0.25), (0.86, 0.3)], (50, 54, 70))
    c.line([(0.83, 0.25), (0.83, 0.23)], (50, 54, 70), 0.003)
    pts = [(rng.uniform(0.03, 0.97), rng.uniform(0.39, 0.54)) for _ in range(24)]
    for x, y in sorted(pts, key=lambda p: p[1]):
        s_ = 0.5 + (y - 0.37) * 3.5
        house(c, x, y, 0.07 * s_, 0.025 * s_, lit=rng.random() < 0.3)


def interior_wall(c, warm=True):
    top, bot = ((232, 218, 190), (214, 196, 164)) if warm else ((70, 72, 96), (52, 54, 74))
    c.gradient_band(0, top, bot)
    for x in np.arange(0.0, 1.0, 0.07):
        c.rect(x, 0, x + 0.002, 0.62, (220, 204, 174) if warm else (64, 66, 88))
    c.rect(0, 0.62, 1, 1, (120, 84, 54) if warm else (44, 40, 46))
    c.rect(0, 0.615, 1, 0.625, (150, 112, 76) if warm else (60, 56, 62))


def mini_window(c, x0, y0, x1, y1, rng, figure=False):
    frame = (110, 80, 56)
    c.rect(x0 - 0.014, y0 - 0.008, x1 + 0.014, y1 + 0.008, frame)
    c.rect(x0, y0, x1, y1, SKY_T)
    gy = y0 + (y1 - y0) * 0.58
    t = np.linspace(0, 1, int(c.Y(gy) - c.Y(y0)))[:, None, None]
    g = np.array(SKY_T, float) * (1 - t) + np.array(SKY_B, float) * t
    c.img.paste(Image.fromarray(np.repeat(g, int(c.X(x1) - c.X(x0)), axis=1).astype(np.uint8)), (int(c.X(x0)), int(c.Y(y0))))
    c.d = ImageDraw.Draw(c.img)
    for _ in range(14):
        sx, sy = rng.uniform(x0, x1), rng.uniform(y0, gy - 0.03)
        c.ell(sx, sy, 0.0018, 0.0018 * c.ar, (220, 220, 235))
    c.rect(x0, gy, x1, y1, SNOW_T)
    for i in range(3):
        hx = x0 + (x1 - x0) * (i + 0.5) / 3
        house(c, hx, gy, (x1 - x0) / 3 * 0.86, (y1 - y0) * 0.17, lit=(i == 1))
    c.rect(x0, gy + (y1 - y0) * 0.14, x1, gy + (y1 - y0) * 0.2, (176, 182, 200))
    if figure:
        shadow_figure(c, x0 + (x1 - x0) * 0.62, y0 + (y1 - y0) * 0.92, (y1 - y0) * 0.32, eyes=True)
    c.rect((x0 + x1) / 2 - 0.005, y0, (x0 + x1) / 2 + 0.005, y1, frame)
    c.rect(x0, (y0 + y1) / 2 - 0.003, x1, (y0 + y1) / 2 + 0.003, frame)


def door_shape(c, x0, y0, x1, y1, col=(122, 82, 50)):
    c.rect(x0 - 0.014, y0 - 0.008, x1 + 0.014, y1, tuple(max(0, v - 30) for v in col))
    c.rect(x0, y0, x1, y1, col)
    for a, b in ((0.1, 0.45), (0.55, 0.92)):
        c.rect(x0 + (x1 - x0) * 0.15, y0 + (y1 - y0) * a, x1 - (x1 - x0) * 0.15, y0 + (y1 - y0) * b, tuple(max(0, v - 12) for v in col))
    c.ell(x1 - (x1 - x0) * 0.13, y0 + (y1 - y0) * 0.55, 0.012, 0.012 * c.ar, (214, 176, 90))


def sc_livingroom(c, beat, rng):
    interior_wall(c)
    mini_window(c, 0.05, 0.27, 0.43, 0.5, rng, figure=beat.get("figure", False))
    door_shape(c, 0.6, 0.3, 0.9, 0.62)
    c.rect(-0.03, 0.56, 0.32, 0.66, (106, 150, 160), r=0.02)
    c.rect(-0.03, 0.52, 0.32, 0.58, (94, 136, 146), r=0.02)
    c.line([(0.48, 0.63), (0.48, 0.47)], (60, 50, 40), 0.004)
    c.rect(0.45, 0.625, 0.51, 0.635, (60, 50, 40))
    c.glow(0.48, 0.45, 0.1, (255, 236, 180), 70)
    c.poly([(0.44, 0.47), (0.52, 0.47), (0.505, 0.425), (0.455, 0.425)], (246, 236, 206))
    person(c, 0.2, 0.8, 0.26, beat.get("mood", "neutral"))


def sc_phone(c, beat, rng):
    c.glow(0.5, 0.42, 0.55, (70, 62, 90), 90)
    c.rect(0.14, 0.08, 0.86, 0.84, (22, 24, 32), r=0.07)
    c.rect(0.165, 0.093, 0.835, 0.826, (40, 52, 82), r=0.055)
    c.rect(0.42, 0.105, 0.58, 0.118, (22, 24, 32), r=0.01)
    for s in (-1, 1):
        c.poly([(0.5 + s * 0.62, 1.05), (0.5 + s * 0.4, 1.05), (0.5 + s * 0.31, 0.8), (0.5 + s * 0.42, 0.74)], (52, 64, 98))
        c.ell(0.5 + s * 0.345, 0.73, 0.055, 0.04, SKIN)
        c.ell(0.5 + s * 0.31, 0.69, 0.022, 0.03, SKIN)


def sc_door(c, beat, rng):
    interior_wall(c, warm=False)
    door_shape(c, 0.22, 0.1, 0.78, 0.8, col=(96, 66, 46))
    c.ell(0.5, 0.3, 0.018, 0.018 * c.ar, (16, 16, 20))
    c.line([(0.74, 0.38), (0.67, 0.42), (0.74, 0.46)], (190, 190, 200), 0.005)
    c.glow(0.5, 0.82, 0.32, (255, 210, 140), 70)
    c.rect(0.22, 0.795, 0.78, 0.81, (255, 222, 150))
    if beat.get("figure", True):
        for x in (0.4, 0.55):
            c.rect(x, 0.795, x + 0.05, 0.81, (18, 16, 18))
    c.rect(0, 0.81, 1, 1, (44, 40, 46))


def sc_window(c, beat, rng):
    interior_wall(c, warm=False)
    mini_window(c, 0.12, 0.14, 0.88, 0.56, rng, figure=beat.get("figure", True))
    c.rect(0.08, 0.56, 0.92, 0.585, (90, 70, 56))
    c.poly([(0.02, 0.1), (0.13, 0.12), (0.12, 0.6), (0.02, 0.64)], (120, 60, 64))
    c.poly([(0.98, 0.1), (0.87, 0.12), (0.88, 0.6), (0.98, 0.64)], (120, 60, 64))


def sc_hallway(c, beat, rng):
    c.gradient_band(0, (30, 28, 40), (24, 22, 30))
    vx, vy, dw, dh = 0.5, 0.42, 0.12, 0.12
    c.poly([(0, 0), (vx - dw, vy - dh), (vx - dw, vy + dh), (0, 1)], (62, 60, 82))
    c.poly([(1, 0), (vx + dw, vy - dh), (vx + dw, vy + dh), (1, 1)], (52, 50, 70))
    c.poly([(0, 1), (vx - dw, vy + dh), (vx + dw, vy + dh), (1, 1)], (80, 62, 52))
    c.poly([(0, 0), (vx - dw, vy - dh), (vx + dw, vy - dh), (1, 0)], (40, 38, 54))
    c.rect(vx - dw, vy - dh, vx + dw, vy + dh, (46, 44, 62))
    c.glow(vx, vy, 0.12, (255, 200, 140), 80)
    c.rect(vx - dw * 0.45, vy - dh * 0.85, vx + dw * 0.45, vy + dh, (20, 16, 18))
    c.rect(vx + dw * 0.28, vy - dh * 0.85, vx + dw * 0.45, vy + dh, (255, 214, 150))
    if beat.get("figure", True):
        shadow_figure(c, vx - 0.02, vy + dh, dh * 1.4, col=(6, 4, 6), eyes=True)
    for side in (-1, 1):
        c.poly([(vx + side * 0.36, 0.3), (vx + side * 0.25, 0.34), (vx + side * 0.25, 0.56), (vx + side * 0.36, 0.64)], (90, 66, 48))


def sc_bedroom(c, beat, rng):
    interior_wall(c, warm=False)
    c.rect(0.06, 0.46, 0.12, 0.74, (90, 66, 48))
    c.rect(0.06, 0.52, 0.7, 0.72, (60, 74, 110), r=0.02)
    c.rect(0.13, 0.5, 0.33, 0.56, (220, 224, 236), r=0.015)
    ar = c.ar
    c.ell(0.23, 0.5, 0.05, 0.05 * ar, SKIN)
    c.ell(0.23, 0.48, 0.053, 0.03 * ar, HAIR)
    scared = beat.get("mood") == "scared"
    for s in (-1, 1):
        if scared:
            c.ell(0.23 + s * 0.017, 0.505, 0.009, 0.009 * ar, (255, 255, 255))
        c.ell(0.23 + s * 0.017, 0.505, 0.004, 0.004 * ar, INK)
    c.rect(0.12, 0.535, 0.7, 0.72, (80, 96, 140), r=0.02)
    door_shape(c, 0.76, 0.3, 0.98, 0.64, col=(70, 52, 40))
    c.rect(0.76, 0.3, 0.81, 0.64, (12, 10, 14))
    if beat.get("figure", True):
        shadow_figure(c, 0.785, 0.64, 0.28, col=(4, 4, 6), eyes=True)


def sc_forest(c, beat, rng):
    night_sky(c, rng)
    c.gradient_band(0.55, SNOW_T, SNOW_B)
    for layer, (col, hh, y) in enumerate((((70, 78, 104), 0.12, 0.56), ((48, 54, 76), 0.2, 0.62), ((28, 32, 46), 0.36, 0.76))):
        for x in np.arange(-0.05, 1.1, 0.09 + layer * 0.07):
            if layer == 2 and 0.3 < x < 0.7:
                continue
            pine(c, x + rng.uniform(-0.02, 0.02), y + rng.uniform(0, 0.03), hh * rng.uniform(0.85, 1.1), col)
    if beat.get("figure", True):
        shadow_figure(c, 0.52, 0.64, 0.09, eyes=True)


def sc_road(c, beat, rng):
    night_sky(c, rng)
    c.gradient_band(0.42, SNOW_T, SNOW_B)
    for x in np.arange(-0.05, 1.1, 0.06):
        pine(c, x + rng.uniform(-0.01, 0.01), 0.43, rng.uniform(0.05, 0.08), (40, 46, 62))
    c.poly([(0.48, 0.42), (0.52, 0.42), (1.1, 1.0), (-0.1, 1.0)], (58, 60, 72))
    for i in range(10):
        t0, t1 = (i / 10) ** 2, ((i + 0.5) / 10) ** 2
        y0, y1 = 0.42 + 0.58 * t0, 0.42 + 0.58 * t1
        c.poly([(0.5 - 0.002 - 0.02 * t0, y0), (0.5 + 0.002 + 0.02 * t0, y0), (0.5 + 0.002 + 0.02 * t1, y1), (0.5 - 0.002 - 0.02 * t1, y1)], (226, 196, 110))
    c.poly([(0.34, 1.0), (0.48, 0.58), (0.52, 0.58), (0.66, 1.0)], (120, 116, 100))
    c.glow(0.5, 0.75, 0.25, (255, 240, 190), 40)
    c.rect(0.08, 0.84, 0.92, 1.02, (30, 32, 42), r=0.03)  # dashboard
    c.rect(0.3, 0.86, 0.5, 0.9, (60, 64, 80), r=0.01)
    if beat.get("figure", True):
        shadow_figure(c, 0.5, 0.6, 0.08, eyes=True)


def sc_lake(c, beat, rng):
    night_sky(c, rng)
    c.ell(0.72, 0.14, 0.06, 0.06 * c.ar, (226, 228, 220))
    c.gradient_band(0.4, (30, 40, 70), (18, 24, 44))
    for x in np.arange(-0.05, 1.1, 0.05):
        pine(c, x + rng.uniform(-0.01, 0.01), 0.405, rng.uniform(0.05, 0.08), (22, 28, 40))
    for i in range(12):
        y = rng.uniform(0.43, 0.7)
        c.rect(0.72 - 0.05 - y * 0.05, y, 0.72 + 0.05 + y * 0.05, y + 0.003, (120, 130, 160))
    c.poly([(0.3, 1.0), (0.44, 0.55), (0.56, 0.55), (0.7, 1.0)], (96, 72, 54))
    for i in range(12):
        y = 0.55 + 0.45 * (i / 12) ** 1.3
        w = 0.06 + 0.14 * (y - 0.55) / 0.45
        c.rect(0.5 - w, y, 0.5 + w, y + 0.004, (70, 52, 40))
    if beat.get("figure", True):
        shadow_figure(c, 0.5, 0.57, 0.08, eyes=True)


def sc_cabin(c, beat, rng):
    night_sky(c, rng)
    c.gradient_band(0.55, SNOW_T, SNOW_B)
    for x in list(np.arange(-0.05, 0.25, 0.07)) + list(np.arange(0.78, 1.1, 0.07)):
        pine(c, x, 0.6 + rng.uniform(0, 0.04), rng.uniform(0.25, 0.35), (24, 28, 40))
    x, base, w, h = 0.5, 0.58, 0.46, 0.13
    c.rect(x - w / 2, base - h, x + w / 2, base, (96, 66, 48))
    for i in range(6):
        c.rect(x - w / 2, base - h + i * h / 6, x + w / 2, base - h + i * h / 6 + 0.003, (76, 52, 38))
    c.poly([(x - w / 2 - 0.03, base - h), (x, base - h - 0.1), (x + w / 2 + 0.03, base - h)], (50, 40, 36))
    if SEASON["caps"]:
        c.line([(x - w / 2 - 0.03, base - h), (x, base - h - 0.1), (x + w / 2 + 0.03, base - h)], (240, 242, 248), 0.012)
    c.glow(x - 0.12, base - h * 0.55, 0.06, (255, 200, 120), 90)
    c.rect(x - 0.16, base - h * 0.7, x - 0.08, base - h * 0.4, WIN_L)
    c.rect(x + 0.04, base - h * 0.75, x + 0.12, base, (50, 36, 28))
    if beat.get("figure", False):
        shadow_figure(c, x - 0.12, base - h * 0.4, 0.05, col=(60, 36, 20))


def sc_basement(c, beat, rng):
    c.gradient_band(0, (34, 34, 40), (20, 20, 24))
    for i in range(10):
        y = 0.25 + i * 0.045
        c.rect(0.05 + i * 0.045, y, 0.6 + i * 0.01, y + 0.012, (80, 62, 48))
        c.rect(0.05 + i * 0.045, y + 0.012, 0.6 + i * 0.01, y + 0.045, (48, 40, 34))
    c.rect(0, 0.7, 1, 1, (30, 30, 34))
    c.line([(0.75, 0), (0.75, 0.22)], (60, 60, 60), 0.002)
    c.glow(0.75, 0.24, 0.14, (255, 220, 150), 90)
    c.ell(0.75, 0.24, 0.015, 0.015 * c.ar, (255, 236, 180))
    c.rect(0.7, 0.55, 0.95, 0.72, (70, 60, 50))
    if beat.get("figure", True):
        shadow_figure(c, 0.3, 0.72, 0.22, col=(4, 4, 6), eyes=True)


def sc_kitchen(c, beat, rng):
    interior_wall(c)
    c.rect(0, 0.5, 1, 0.66, (220, 222, 226))
    c.rect(0, 0.49, 1, 0.51, (170, 172, 180))
    for x in np.arange(0.02, 1, 0.24):
        c.rect(x, 0.52, x + 0.22, 0.64, (196, 200, 206))
        c.rect(x + 0.09, 0.55, x + 0.13, 0.556, (140, 144, 150))
    for x in np.arange(0.02, 1, 0.24):
        c.rect(x, 0.12, x + 0.22, 0.3, (196, 200, 206))
    c.rect(0.62, 0.3, 0.92, 0.49, (230, 232, 236))
    c.rect(0.4, 0.34, 0.58, 0.47, (60, 64, 80))  # microwave
    mini_window(c, 0.1, 0.33, 0.34, 0.47, rng, figure=beat.get("figure", False))
    person(c, 0.8, 0.86, 0.22, beat.get("mood", "neutral"))


def sc_cemetery(c, beat, rng):
    night_sky(c, rng)
    c.ell(0.25, 0.15, 0.06, 0.06 * c.ar, (226, 228, 220))
    c.gradient_band(0.5, SNOW_T, SNOW_B)
    c.rect(0, 0.42, 1, 0.5, (30, 34, 48))
    for x in np.arange(0.0, 1.0, 0.03):
        c.rect(x, 0.36, x + 0.006, 0.5, (30, 32, 42))
    c.rect(0, 0.38, 1, 0.386, (30, 32, 42))
    for row, (y, s) in enumerate(((0.56, 0.6), (0.68, 0.8), (0.84, 1.1))):
        for x in np.arange(0.08 + row * 0.05, 1.0, 0.26):
            w, h = 0.07 * s, 0.09 * s
            c.rect(x - w / 2, y - h * 0.7, x + w / 2, y, (110, 114, 130))
            c.ell(x, y - h * 0.7, w / 2, w / 2 * c.ar * 0.8, (110, 114, 130))
            c.rect(x - w * 0.3, y - h * 0.45, x + w * 0.3, y - h * 0.4, (80, 84, 100))
    if beat.get("figure", True):
        shadow_figure(c, 0.62, 0.62, 0.12, eyes=True)


def sc_bathroom(c, beat, rng):
    c.gradient_band(0, (180, 196, 200), (150, 166, 172))
    for x in np.arange(0, 1, 0.08):
        c.rect(x, 0, x + 0.002, 1, (160, 176, 180))
    for y in np.arange(0, 1, 0.045):
        c.rect(0, y, 1, y + 0.002, (160, 176, 180))
    c.rect(0.18, 0.12, 0.82, 0.52, (90, 96, 104), r=0.02)
    c.rect(0.2, 0.13, 0.8, 0.51, (56, 66, 78), r=0.015)
    c.poly([(0.22, 0.14), (0.4, 0.14), (0.22, 0.4)], (70, 82, 96))
    person_mirror = beat.get("figure", True)
    if person_mirror:
        shadow_figure(c, 0.62, 0.51, 0.26, col=(14, 16, 22), eyes=True)
    c.rect(0.15, 0.6, 0.85, 0.66, (236, 238, 240), r=0.01)
    c.rect(0.25, 0.66, 0.75, 1.0, (210, 214, 218))
    c.rect(0.47, 0.56, 0.53, 0.6, (170, 174, 180))


def sc_campsite(c, beat, rng):
    night_sky(c, rng)
    c.gradient_band(0.5, SNOW_T, SNOW_B)
    for x in np.arange(-0.05, 1.1, 0.07):
        pine(c, x + rng.uniform(-0.01, 0.01), 0.52 + rng.uniform(0, 0.03), rng.uniform(0.18, 0.26), (22, 26, 38))
    c.poly([(0.08, 0.75), (0.3, 0.56), (0.52, 0.75)], (190, 110, 60))
    c.poly([(0.26, 0.75), (0.3, 0.6), (0.34, 0.75)], (60, 36, 24))
    c.glow(0.7, 0.76, 0.22, (255, 150, 60), 110)
    for a in (-0.03, 0.03):
        c.line([(0.7 - 0.05, 0.79 + a * 0.2), (0.7 + 0.05, 0.77 - a * 0.2)], (80, 50, 30), 0.012)
    c.poly([(0.66, 0.78), (0.7, 0.7), (0.74, 0.78)], (255, 170, 60))
    c.poly([(0.68, 0.78), (0.7, 0.73), (0.72, 0.78)], (255, 230, 140))
    if beat.get("figure", True):
        shadow_figure(c, 0.86, 0.6, 0.1, col=(10, 10, 14), eyes=True)


SCENES = {"street": sc_street, "town": sc_town, "livingroom": sc_livingroom, "phone": sc_phone,
          "door": sc_door, "window": sc_window, "hallway": sc_hallway, "bedroom": sc_bedroom, "forest": sc_forest,
          "road": sc_road, "lake": sc_lake, "cabin": sc_cabin, "basement": sc_basement, "kitchen": sc_kitchen,
          "cemetery": sc_cemetery, "bathroom": sc_bathroom, "campsite": sc_campsite}
OUTDOOR = {"street", "town", "forest", "road", "lake", "cabin", "cemetery", "campsite"}
SNOWY = OUTDOOR  # scenes that get weather particles

# season changes the outdoor ground, roof caps and the falling particles
SEASONS = {
    "winter": dict(ground=((226, 230, 240), (196, 202, 218)), caps=True, particle="snow"),
    "autumn": dict(ground=((128, 86, 54), (92, 60, 40)), caps=False, particle="leaves"),
    "summer": dict(ground=((52, 86, 66), (32, 56, 44)), caps=False, particle="fireflies"),
    "rain":   dict(ground=((70, 78, 92), (44, 50, 62)), caps=False, particle="rain"),
    "fog":    dict(ground=((96, 104, 112), (66, 72, 80)), caps=False, particle="none"),
}
SEASON = SEASONS["winter"]


def set_season(name):
    global SNOW_T, SNOW_B, SEASON
    SEASON = SEASONS.get(name, SEASONS["winter"])
    SNOW_T, SNOW_B = SEASON["ground"]


def draw_scene(beat, seed):
    rng = random.Random(seed)
    name = beat.get("scene", "street")
    c = Canvas(SKY_T, SKY_B) if name in OUTDOOR else Canvas((30, 28, 40), (20, 18, 28))
    SCENES.get(name, sc_street)(c, beat, rng)
    return c.done()


# ------------------------------------------------------------------ overlays
_tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))


def tlen(s, f): return _tmp.textlength(s, font=f)


def text_center(d, cx, y, txt, f, fill):
    d.text((cx - tlen(txt, f) / 2, y), txt, font=f, fill=fill)


def card(w, h, r, fill, shadow=110):
    im = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([30, 40, w + 30, h + 40], r, fill=(0, 0, 0, shadow))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(im).rounded_rectangle([30, 30, w + 30, h + 30], r, fill=fill)
    return im


def ov_alert(o, width):
    lines = [l.upper() for l in o.get("lines", [])]
    red = set(o.get("red", [len(lines) - 1] if len(lines) > 1 else []))
    size = 60
    while size > 30 and any(tlen(l, font("mont", size, 800)) > width - 80 for l in lines):
        size -= 3
    f = font("mont", size, 800)
    lh, hh = int(size * 1.3), 74
    h = hh + 44 + lh * len(lines) + 30
    im = card(width, h, 28, (245, 241, 237))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([30, 30, width + 30, 30 + hh], 28, fill=(212, 52, 60))
    d.rectangle([30, 30 + hh - 30, width + 30, 30 + hh], fill=(212, 52, 60))
    hf = font("mont", 32, 800)
    head = o.get("header", "EMERGENCY ALERT").upper()
    tw = tlen(head, hf) + 54
    x = 30 + width / 2 - tw / 2
    tri = [(x, 30 + hh / 2 + 15), (x + 34, 30 + hh / 2 + 15), (x + 17, 30 + hh / 2 - 15)]
    d.polygon(tri, fill=(255, 255, 255))
    d.text((x + 9 + 3, 30 + hh / 2 - 10), "!", font=font("mont", 20, 900), fill=(212, 52, 60))
    d.text((x + 54, 30 + hh / 2 - hf.size * 0.62), head, font=hf, fill=(255, 255, 255))
    y = 30 + hh + 34
    for i, l in enumerate(lines):
        text_center(d, 30 + width / 2, y, l, f, (212, 46, 56) if i in red else (32, 32, 38))
        y += lh
    return im


def ov_clock(o):
    f = font("mont", 46, 800)
    t = o.get("time", "3:00 AM").upper()
    w, h = int(tlen(t, f) + 120), 86
    im = card(w, h, 43, (24, 24, 32, 240), shadow=90)
    d = ImageDraw.Draw(im)
    d.ellipse([30 + 30, 30 + h / 2 - 13, 30 + 56, 30 + h / 2 + 13], fill=(226, 52, 58))
    d.text((30 + 74, 30 + h / 2 - f.size * 0.66), t, font=f, fill=(255, 255, 255))
    return im


def ov_sign(o):
    nf, sf_ = font("mont", 42, 800), font("mont", 30, 700)
    name, sub = o.get("name", "").upper(), o.get("sub", "").upper()
    w = int(max(tlen(name, nf), tlen(sub, sf_)) + 80)
    im = Image.new("RGBA", (w, 460), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([w / 2 - 24, 140, w / 2 + 24, 460], fill=(38, 38, 48))
    d.rounded_rectangle([0, 0, w - 1, 156], 10, fill=(234, 230, 220), outline=(86, 86, 96), width=4)
    text_center(d, w / 2, 26, name, nf, (40, 40, 48))
    text_center(d, w / 2, 90, sub, sf_, (96, 96, 106))
    return im


def ov_text(o, width=880):
    mf, nf = font("mont", 44, 600), font("mont", 34, 800)
    words, lines, cur = o.get("message", "").split(), [], ""
    for wd in words:
        if cur and tlen(cur + " " + wd, mf) > width - 90:
            lines.append(cur); cur = wd
        else:
            cur = (cur + " " + wd).strip()
    lines.append(cur)
    h = 116 + len(lines) * 58 + 34
    im = card(width, h, 36, (246, 246, 250, 248))
    d = ImageDraw.Draw(im)
    ox = oy = 30
    d.ellipse([ox + 30, oy + 26, ox + 92, oy + 88], fill=(110, 124, 160))
    who = o.get("from", "Unknown")
    text_center(d, ox + 61, oy + 37, who[:1].upper(), nf, (255, 255, 255))
    d.text((ox + 112, oy + 36), who, font=nf, fill=(30, 30, 36))
    d.text((ox + width - 110, oy + 42), "now", font=font("mont", 30, 500), fill=(130, 130, 140))
    y = oy + 112
    for l in lines:
        d.text((ox + 40, y), l, font=mf, fill=(40, 40, 46)); y += 58
    return im


def ov_label(o):
    f = font("mont", 44, 800)
    t = o.get("text", "").upper()
    w = int(tlen(t, f) + 60)
    im = card(w, 88, 12, (212, 52, 60), shadow=90)
    text_center(ImageDraw.Draw(im), 30 + w / 2, 30 + 16, t, f, (255, 255, 255))
    return im


def build_overlay(beat):
    """Returns (static_layer or None, popping_overlay or None, (x, y) top-left)."""
    o = beat.get("overlay") or {}
    typ = o.get("type", "none")
    if beat.get("scene") == "phone":
        base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        t = re.sub(r"\s*[AP]M", "", o.get("time", "3:00"), flags=re.I)
        text_center(ImageDraw.Draw(base), W / 2, H * 0.145, t, font("mont", 170, 800), (255, 255, 255))
        if typ == "alert":
            ov = ov_alert(o, 660)
        elif typ == "text":
            ov = ov_text(o, 660)
        else:
            return base, None, None
        return base, ov, (int(W / 2 - ov.width / 2), int(H * 0.3))
    if typ == "alert":
        ov = ov_alert(o, 900); pos = (W / 2 - ov.width / 2, H * 0.06)
    elif typ == "clock":
        ov = ov_clock(o); pos = (W / 2 - ov.width / 2, H * 0.17)
    elif typ == "sign":
        ov = ov_sign(o); pos = (70, H * 0.71)
    elif typ == "text":
        ov = ov_text(o); pos = (W / 2 - ov.width / 2, H * 0.07)
    elif typ == "label":
        ov = ov_label(o); pos = (W - ov.width - 40, H * 0.7)
    else:
        return None, None, None
    return None, ov, (int(pos[0]), int(pos[1]))


# ------------------------------------------------------------------ narration
def narrate(beats, models, wav_path):
    from kokoro_onnx import Kokoro
    import soundfile as sf
    k = Kokoro(os.path.join(models, "kokoro-v1.0.int8.onnx"), os.path.join(models, "voices-v1.0.bin"))
    lead = 0.7 if beats and beats[0].get("hook") else 0.2
    sr, t = 24000, lead
    pieces, out = [np.zeros(int(sr * lead), np.float32)], []
    for b in beats:
        start, sents = t, []
        for s in [x for x in re.split(r"(?<=[.!?…])[\"”']?\s+", b["text"].strip()) if x]:
            a, sr = k.create(s, voice=VOICE, speed=SPEED, lang="en-us")
            a = np.asarray(a, np.float32)
            nz = np.where(np.abs(a) > 0.01)[0]
            if len(nz):
                a = a[max(0, nz[0] - 500): nz[-1] + 1000]
            d = len(a) / sr
            sents.append((s, t, t + d))
            pieces += [a, np.zeros(int(sr * 0.2), np.float32)]
            t += d + 0.2
        pieces.append(np.zeros(int(sr * 0.1), np.float32))
        t += 0.1
        out.append({"start": start, "end": t, "sents": sents})
    pieces.append(np.zeros(int(sr * 1.0), np.float32))
    t += 1.0
    out[-1]["end"] = t
    sf.write(wav_path, np.concatenate(pieces), sr)
    return out, t


# ------------------------------------------------------------------ captions
def ass_time(s):
    cs = int(round(s * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def chunks_of(words, n=5):
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= n or (len(cur) >= 3 and re.search(r"[,;:—–]$", w)):
            out.append(cur); cur = []
    if cur:
        if out and len(cur) <= 1:
            out[-1] += cur
        else:
            out.append(cur)
    return out


LOW_CAPS = {"livingroom", "bedroom", "door", "phone", "kitchen"}


def write_ass(timing, beats, path):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Anton,96,&H00FFFFFF,&H00FFFFFF,&H00141414,&H78000000,0,0,0,0,100,100,1,0,1,5,4,5,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for b, tm in zip(beats, timing):
        y = 1520 if b.get("scene") in LOW_CAPS else 1250
        for s, t0, t1 in tm["sents"]:
            cs = chunks_of(s.split())
            tot = sum(len(" ".join(c)) + 3 for c in cs)
            t = t0
            for j, c in enumerate(cs):
                d = (t1 - t0) * (len(" ".join(c)) + 3) / tot
                end = t + d if j < len(cs) - 1 else t1 + 0.18
                ev.append(f"Dialogue: 0,{ass_time(t)},{ass_time(end)},Cap,,0,0,0,,{{\\pos(540,{y})}}{' '.join(c).upper()}")
                t += d
    open(path, "w").write(head + "\n".join(ev) + "\n")


KEYWORD_SFX = [(r"\bknock", "knock"), (r"\bcreak|door (slowly )?open|opened the door", "creak"),
               (r"footstep|\bsteps\b", "footsteps"), (r"heart", "heartbeat"), (r"static|radio|tv\b", "static"),
               (r"buzz", "buzz")]


def sound_events(beats, timing):
    """Pick sound effects automatically from each beat (plus explicit beat['sfx'])."""
    ev = []
    for i, (b, tm) in enumerate(zip(beats, timing)):
        s = tm["start"]
        o = (b.get("overlay") or {}).get("type")
        if b.get("hook"):
            ev.append(("stinger", 0.0))
        elif i > 0 and b.get("scene") != beats[i - 1].get("scene"):
            ev.append(("whoosh", max(0, s - 0.25)))
        if o == "alert":
            ev.append(("alert", s + 0.1))
        elif o == "text":
            ev.append(("notify", s + 0.1))
        if b.get("shake") and not b.get("hook"):
            ev.append(("boom", s))
        low = b["text"].lower()
        if "sfx" not in b:
            for pat, name in KEYWORD_SFX:
                if re.search(pat, low) and not (name == "buzz" and o == "text"):
                    ev.append((name, s + 0.25)); break
        for x in b.get("sfx", []):
            name, at = (x, 0.1) if isinstance(x, str) else (x.get("name"), x.get("at", 0.1))
            if name in SFXBANK:
                ev.append((name, s + at))
        if i == len(beats) - 1 and len(beats) > 1:
            ev.append(("riser", max(0, s - 2.0)))
            if not b.get("shake"):
                ev.append(("boom", s))
    return ev


def mix_audio(beats, timing, dur, voice_wav, out_wav):
    import soundfile as sf
    SR = sfx.SR
    n = int(SR * dur) + SR
    bed = np.zeros(n, np.float32)
    amb = sfx.ambience(dur)
    bed[:len(amb)] += amb * 0.55
    for name, at in sound_events(beats, timing):
        x = SFXBANK[name]() * sfx.GAIN[name]
        o = int(at * SR)
        if o < n:
            seg = bed[o:o + len(x)]; seg += x[:len(seg)]
    sf.write(out_wav, bed[:int(SR * dur)], SR)


# ------------------------------------------------------------------ render
class Snow:
    def __init__(self, seed, n=110):
        r = np.random.default_rng(seed)
        self.x, self.y = r.random(n) * W, r.random(n) * H
        self.s, self.v, self.ph = r.uniform(2.5, 6.5, n), r.uniform(40, 110, n), r.random(n) * 6.28

    def draw(self, img, t):
        kind = SEASON["particle"]
        if kind == "none":
            return
        d = ImageDraw.Draw(img, "RGBA")
        if kind == "rain":
            ys = (self.y + self.v * 14 * t) % H
            xs = (self.x - 0.25 * self.v * 14 * t) % W
            for x, y, s in zip(xs, ys, self.s):
                d.line([(x, y), (x - 8, y + 34 + 4 * s)], fill=(190, 200, 220, 150), width=2)
            return
        if kind == "fireflies":
            for j, (x, y, s, ph) in enumerate(zip(self.x, self.y, self.s, self.ph)):
                if y < H * 0.45 or j % 3:
                    continue
                a = int(120 + 120 * math.sin(t * 2 + ph * 3))
                xx, yy = x + 30 * math.sin(t * 0.5 + ph), y + 20 * math.cos(t * 0.7 + ph)
                d.ellipse([xx - s * 2.2, yy - s * 2.2, xx + s * 2.2, yy + s * 2.2], fill=(255, 230, 120, max(0, a // 4)))
                d.ellipse([xx - s * 0.7, yy - s * 0.7, xx + s * 0.7, yy + s * 0.7], fill=(255, 240, 160, max(0, a)))
            return
        ys = (self.y + self.v * t) % H
        xs = (self.x + 18 * np.sin(t * 0.8 + self.ph)) % W
        if kind == "leaves":
            cols = [(200, 110, 50), (170, 70, 40), (220, 160, 60)]
            for j, (x, y, s) in enumerate(zip(xs, ys, self.s)):
                a = t * 2 + self.ph[j]
                dx, dy = s * 1.8 * math.cos(a), s * 0.9 * math.sin(a)
                d.polygon([(x - dx, y - dy), (x + dy, y - dx * 0.4), (x + dx, y + dy), (x - dy, y + dx * 0.4)], fill=cols[j % 3])
            return
        for x, y, s in zip(xs, ys, self.s):
            d.ellipse([x - s, y - s, x + s, y + s], fill=(240, 242, 250))


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def render(story, out, models, preview_dir=None):
    beats = story["beats"]
    set_season(story.get("season", "autumn"))
    work = tempfile.mkdtemp(prefix="short_")
    wav, ass, amb = (os.path.join(work, n) for n in ("voice.wav", "caps.ass", "amb.wav"))
    timing, dur = narrate(beats, models, wav)
    write_ass(timing, beats, ass)
    mix_audio(beats, timing, dur, wav, amb)
    seed0 = sum(map(ord, story.get("title", "x")))
    arts = [draw_scene(b, seed0 + i) for i, b in enumerate(beats)]
    last_time = "3:00"
    for b in beats:  # phone clock carries the last time mentioned
        o = b.get("overlay") or {}
        if o.get("time"):
            last_time = o["time"]
        elif b.get("scene") == "phone":
            b.setdefault("overlay", {})["time"] = last_time
    ovs = [build_overlay(b) for b in beats]
    snow = Snow(seed0)
    n = int(round(dur * FPS))
    timing[0]["start"] = 0.0
    bidx = np.zeros(n, int)
    for i, tm in enumerate(timing):
        bidx[min(n - 1, int(tm["start"] * FPS)):] = i

    def frame(f):
        t = f / FPS
        i = bidx[f]
        b, tm = beats[i], timing[i]
        lt = t - tm["start"]
        p = min(1.0, lt / max(0.5, tm["end"] - tm["start"]))
        art = arts[i]
        z = (1 - 1 / ZOOM)
        k = 1 - z * (0.1 + 0.9 * p) if i % 2 == 0 else 1 - z * (1 - 0.9 * p)
        cw, ch = art.width * k, art.height * k
        x0, y0 = (art.width - cw) / 2, (art.height - ch) / 2
        if (b.get("shake") or b.get("hook")) and lt < 1.0:
            a = 16 * (1.0 - lt)
            x0 = min(max(0, x0 + a * math.sin(lt * 70)), art.width - cw)
            y0 = min(max(0, y0 + a * math.cos(lt * 53)), art.height - ch)
        img = art.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR).convert("RGBA")
        if b.get("scene", "street") in SNOWY:
            snow.draw(img, t)
        base, ov, pos = ovs[i]
        if base is not None:
            img.alpha_composite(base)
        if ov is not None:
            e = 1.0 if b.get("hook") else ease((lt - 0.1) / 0.3)
            if e > 0:
                s = 0.88 + 0.12 * e
                o2 = ov if e >= 1 else ov.resize((max(1, int(ov.width * s)), max(1, int(ov.height * s))), Image.BILINEAR)
                if e < 1:
                    a = np.asarray(o2).copy(); a[..., 3] = (a[..., 3] * e).astype(np.uint8); o2 = Image.fromarray(a)
                img.alpha_composite(o2, (int(pos[0] + (ov.width - o2.width) / 2), int(pos[1] + (ov.height - o2.height) / 2)))
        if b.get("hook") and lt < 0.9:  # red flash pulses on the cold open
            a = int(150 * (1 - lt / 0.9) * (0.6 + 0.4 * math.cos(lt * 25)))
            img.alpha_composite(Image.new("RGBA", img.size, (170, 0, 0, max(0, a))))
        return img.convert("RGB")

    if preview_dir:
        os.makedirs(preview_dir, exist_ok=True)
        paths = []
        for i, tm in enumerate(timing):
            f = min(n - 1, int((tm["start"] + min(1.0, (tm["end"] - tm["start"]) * 0.6)) * FPS))
            p = os.path.join(preview_dir, f"b{i:02d}.png")
            frame(f).save(p)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-vf",
                            f"setpts=PTS+{f / FPS}/TB,ass={ass}:fontsdir={FONTS}", "-update", "1", p + ".c.png"], check=True)
            os.replace(p + ".c.png", p)
            paths.append(p)
        return paths, dur

    tmp = out[:-4] + ".part.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-i", amb, "-filter_complex",
           f"[0:v]ass={ass}:fontsdir={FONTS},format=yuv420p[v];"
           f"[1:a]aresample=48000,aecho=0.8:0.6:45:0.12,volume=1.0[vo];[2:a]volume=0.5[am];"
           f"[vo][am]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]",
           "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmp]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        pr.stdin.write(frame(f).tobytes())
    pr.stdin.close()
    if pr.wait() != 0:
        sys.exit("ffmpeg failed")
    os.replace(tmp, out)
    return out, dur


if __name__ == "__main__":
    a = sys.argv[1:]
    models, prev = os.path.join(HERE, "models"), None
    if "--models" in a:
        i = a.index("--models"); models = a[i + 1]; del a[i:i + 2]
    if "--preview" in a:
        i = a.index("--preview"); prev = a[i + 1]; del a[i:i + 2]
    story = json.load(open(a[0]))
    res, dur = render(story, a[1] if len(a) > 1 else "out.mp4", models, prev)
    print(f"duration {dur:.1f}s")
