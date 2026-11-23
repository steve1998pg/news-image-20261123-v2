#!/usr/bin/env python3
"""Render the Monday 23 November 2026 one-page newspaper image (1024x1024).

Follows the 22 Nov v4 recipe (date masthead, numbers strip, region colour
bar, dark UTC strip, 3 big + 12 small illustrated stories with red topic
bars, ALSO ON list, world map with numbered pins, DATE CHECK box, footer)
with a fresh set of stories and freshly drawn flat-vector scenes for 23 Nov.

Lead: COP31 collapses with no deal (UN News, Reuters, The Times). All 36
stories are dated from the latest reporting as of Monday 23 Nov 2026; the
DATE CHECK box says so and lists the stories left out on purpose.

Usage: python3 render.py stories.json news.png
"""
import json
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
BG = (248, 244, 232)
INK = (17, 17, 17)
RED = (163, 18, 18)
SALMON = (232, 110, 100)
MUTED = (90, 84, 70)
RULE = (60, 55, 45)
LIGHT = (226, 219, 198)
NAVY = (24, 32, 56)
MAP_LAND = (206, 214, 196)
MAP_LINE = (120, 118, 108)

BADGE = {
    "CONFIRMED": (46, 125, 50),
    "OFFICIAL": (29, 78, 216),
    "REPORTED": (55, 65, 81),
    "CLAIM": (180, 83, 9),
    "FORECAST": (107, 114, 128),
    "PENDING": (29, 78, 216),
}

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_I = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size, fallback=None):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype(fallback or SERIF, size)


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, lines, fnt, fill, lh):
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def chip(d, x_right, y, text, size=9):
    """Badge chip, right-aligned at x_right. Returns its left edge."""
    f = font(SANS_B, size)
    tw = d.textlength(text, font=f)
    pad_x, pad_y = 5, 2
    h = size + 2 * pad_y + 3
    x0 = x_right - int(tw) - 2 * pad_x
    d.rounded_rectangle([x0, y, x_right, y + h], radius=3,
                        fill=BADGE.get(text, (55, 65, 81)))
    d.text((x0 + pad_x, y + pad_y), text, font=f, fill=(255, 255, 255))
    return x0


def redbar(d, x, y, size, text, h=16, max_w=None):
    """Red topic bar at the top-left of an illustration (rank 1 style)."""
    f = font(SANS_B, size)
    while max_w is not None and d.textlength(text, font=f) + 12 > max_w and f.size > 6:
        f = font(SANS_B, f.size - 1)
    tw = d.textlength(text, font=f)
    bw = int(tw) + 12
    d.rectangle([x, y, x + bw, y + h], fill=RED)
    d.text((x + 6, y + (h - f.size) // 2 - 1), text, font=f, fill=(255, 255, 255))
    return bw


def whitebar(d, x_right, y, size, text, h=16):
    """White secondary bar at the top-right of a big illustration."""
    f = font(SANS_B, size)
    tw = d.textlength(text, font=f)
    bw = int(tw) + 12
    d.rectangle([x_right - bw, y, x_right, y + h], fill=(255, 255, 255))
    d.text((x_right - bw + 6, y + (h - f.size) // 2 - 1), text, font=f,
           fill=(30, 30, 40))
    return bw


# Rough continent outlines (lon, lat) for the WHERE IT HAPPENED map.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 66), (-75, 62), (-65, 60), (-55, 52), (-60, 47), (-70, 44), (-75, 40), (-80, 32), (-85, 30), (-90, 21), (-95, 19), (-100, 16), (-105, 20), (-110, 23), (-115, 30), (-125, 40), (-125, 49), (-135, 58), (-150, 60), (-165, 60)],
    [(-80, 10), (-75, 7), (-65, 5), (-55, 5), (-50, 0), (-40, -5), (-35, -10), (-40, -20), (-48, -28), (-55, -35), (-65, -45), (-70, -55), (-73, -40), (-72, -20), (-78, -5)],
    [(-10, 36), (-5, 44), (0, 50), (5, 55), (10, 58), (18, 56), (20, 60), (25, 65), (30, 70), (35, 68), (40, 60), (30, 55), (25, 50), (20, 45), (15, 44), (10, 38), (0, 36)],
    [(-10, 35), (0, 36), (10, 37), (20, 32), (30, 31), (35, 28), (40, 20), (48, 11), (51, 10), (45, 0), (40, -10), (35, -20), (30, -30), (20, -35), (15, -28), (12, -18), (10, -5), (5, 5), (-5, 5), (-10, 15), (-15, 25)],
    [(35, 68), (50, 70), (70, 72), (100, 75), (130, 72), (160, 70), (178, 65), (170, 60), (160, 55), (140, 50), (135, 45), (130, 35), (125, 30), (120, 25), (110, 20), (105, 10), (100, 8), (95, 15), (90, 22), (85, 20), (80, 10), (75, 8), (70, 25), (60, 25), (55, 28), (50, 30), (45, 35), (40, 38)],
    [(113, -22), (120, -15), (130, -12), (135, -15), (140, -17), (145, -15), (150, -22), (153, -28), (150, -37), (145, -38), (140, -38), (135, -35), (130, -32), (125, -32), (120, -35), (115, -33), (113, -25)],
]


# ---------------------------------------------------------------- big scenes
def scene_summit(d, x, y, w, h):
    """COP31 plenary hall, empty: warm wall with a row of flags, a long
    desk with a gavel, rows of empty chairs, a clock stopped at the top."""
    d.rectangle([x, y, x + w, y + h], fill=(196, 172, 132))
    d.rectangle([x, y + int(h * 0.62), x + w, y + h], fill=(120, 96, 66))
    # row of small flags along the top, below the red topic bar
    flag_cols = [(163, 18, 18), (47, 93, 138), (74, 125, 58), (192, 122, 30),
                 (107, 79, 161), (46, 125, 107)]
    for i, col in enumerate(flag_cols):
        fx = x + 12 + i * 48
        d.rectangle([fx, y + 22, fx + 34, y + 34], fill=col)
        d.line([(fx, y + 22), (fx, y + 40)], fill=(60, 55, 45), width=2)
    # wall clock, stopped, top right
    cx, cy = x + w - 34, y + 30
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(248, 244, 232),
              outline=(60, 55, 45), width=2)
    d.line([(cx, cy), (cx, cy - 8)], fill=(30, 30, 30), width=2)
    d.line([(cx, cy), (cx + 6, cy + 2)], fill=(30, 30, 30), width=2)
    # long desk with papers and a gavel at its centre
    d.rectangle([x + 18, y + int(h * 0.52), x + w - 18, y + int(h * 0.62)],
                fill=(88, 62, 40))
    for px in (40, 110, 180, 240):
        d.rectangle([x + px, y + int(h * 0.54), x + px + 26, y + int(h * 0.58)],
                    fill=(248, 244, 232))
    gx = x + w // 2
    d.rectangle([gx - 16, y + int(h * 0.47), gx + 16, y + int(h * 0.52)],
                fill=(60, 40, 22))
    d.line([(gx + 16, y + int(h * 0.50)), (gx + 34, y + int(h * 0.46))],
           fill=(120, 85, 50), width=3)
    d.ellipse([gx - 22, y + int(h * 0.46), gx - 14, y + int(h * 0.53)],
              fill=(120, 85, 50))
    # two rows of empty chairs in front of the desk
    for row, ry in enumerate((0.68, 0.84)):
        for i in range(6):
            cx0 = x + 16 + i * 48
            d.rectangle([cx0, y + int(h * ry), cx0 + 30, y + int(h * ry) + 12],
                        fill=(52, 48, 44) if row == 0 else (74, 68, 60))
            d.rectangle([cx0 + 4, y + int(h * ry) + 12, cx0 + 26,
                         y + int(h * ry) + 16], fill=(52, 48, 44))


def scene_dymer(d, x, y, w, h):
    """Dymer at night: dark sky and stars, a five-storey block broken in
    the middle, a leaning slab, rubble, a crane arm and a searchlight."""
    d.rectangle([x, y, x + w, y + h], fill=(16, 22, 44))
    for sx, sy in [(0.06, 0.12), (0.20, 0.07), (0.34, 0.16), (0.50, 0.09),
                   (0.64, 0.14), (0.78, 0.06), (0.90, 0.18), (0.44, 0.24)]:
        d.ellipse([x + int(w * sx) - 1, y + int(h * sy) - 1,
                   x + int(w * sx) + 1, y + int(h * sy) + 1], fill=(255, 255, 255))
    base = y + h
    # searchlight beam from the left roof, sweeping up right
    d.polygon([(x + 30, base - 58), (x + 44, base - 58),
               (x + 210, y + 8), (x + 190, y + 8)], fill=(70, 72, 90))
    d.polygon([(x + 34, base - 58), (x + 40, base - 58),
               (x + 202, y + 8), (x + 196, y + 8)], fill=(210, 210, 180))
    # standing left section of the block, a few windows lit
    d.rectangle([x + 18, base - 58, x + 118, base], fill=(40, 40, 56))
    for wy in range(4):
        for wx in range(4):
            lit = (wy, wx) in [(0, 1), (2, 3), (3, 0)]
            col = (255, 214, 110) if lit else (20, 20, 30)
            d.rectangle([x + 26 + wx * 22, base - 52 + wy * 13,
                         x + 34 + wx * 22, base - 45 + wy * 13], fill=col)
    # broken middle: a leaning slab and a rubble pile
    d.polygon([(x + 118, base - 30), (x + 150, base - 52), (x + 168, base - 26),
               (x + 140, base - 6)], fill=(70, 70, 82))
    d.polygon([(x + 130, base), (x + 150, base - 22), (x + 178, base - 12),
               (x + 196, base), (x + 168, base)], fill=(90, 88, 84))
    d.polygon([(x + 160, base), (x + 186, base - 14), (x + 214, base),
               (x + 196, base)], fill=(70, 68, 66))
    # standing right section, dark with one lit window
    d.rectangle([x + 216, base - 44, x + w - 14, base], fill=(40, 40, 56))
    d.rectangle([x + 228, base - 36, x + 238, base - 29], fill=(255, 214, 110))
    d.rectangle([x + 258, base - 22, x + 268, base - 15], fill=(20, 20, 30))
    # crane arm over the rubble with a hanging hook
    d.line([(x + 150, y + 22), (x + 250, y + 22)], fill=(200, 160, 60), width=3)
    d.line([(x + 150, y + 22), (x + 150, base - 52)], fill=(200, 160, 60), width=3)
    d.line([(x + 210, y + 22), (x + 210, y + 38)], fill=(200, 160, 60), width=2)
    d.rectangle([x + 204, y + 38, x + 216, y + 46], fill=(200, 160, 60))
    # small orange glow in the rubble
    d.ellipse([x + 158, base - 10, x + 172, base + 2], fill=(255, 140, 40))
    # two drones with dotted trails, upper right
    for dx, dy, s in [(0.72, 0.22, 6), (0.86, 0.32, 5)]:
        cx, cy = x + int(w * dx), y + int(h * dy)
        d.line([(cx - s, cy - s), (cx + s, cy + s)], fill=(255, 220, 130), width=2)
        d.line([(cx - s, cy + s), (cx + s, cy - s)], fill=(255, 220, 130), width=2)
        for k in range(1, 4):
            d.ellipse([cx - s - k * 9 - 1, cy + k * 4 - 1,
                       cx - s - k * 9 + 1, cy + k * 4 + 1], fill=(255, 220, 130))


def scene_gulf(d, x, y, w, h):
    """Persian Gulf at dusk: purple-to-orange sky bands, crescent moon, a
    tanker with containers, a radar dish on a platform, a dotted arc."""
    d.rectangle([x, y, x + w, y + int(h * 0.34)], fill=(58, 48, 96))
    d.rectangle([x, y + int(h * 0.34), x + w, y + int(h * 0.58)], fill=(214, 106, 59))
    d.rectangle([x, y + int(h * 0.58), x + w, y + int(h * 0.72)], fill=(240, 180, 90))
    sea = y + int(h * 0.72)
    d.rectangle([x, sea, x + w, y + h], fill=(28, 68, 110))
    # crescent moon, top right, clear of the white bar
    d.ellipse([x + int(w * 0.82), y + 6, x + int(w * 0.82) + 16, y + 22],
              fill=(240, 230, 200))
    d.ellipse([x + int(w * 0.82) + 5, y + 6, x + int(w * 0.82) + 19, y + 22],
              fill=(58, 48, 96))
    # radar platform on the left: mast, rotating dish, blinking light
    d.rectangle([x + 22, sea - 26, x + 62, sea], fill=(125, 130, 140))
    d.line([(x + 42, sea - 26), (x + 42, sea - 44)], fill=(90, 95, 105), width=3)
    d.pieslice([x + 26, sea - 56, x + 58, sea - 30], start=180, end=360,
               fill=(200, 205, 215))
    d.ellipse([x + 40, sea - 48, x + 44, sea - 44], fill=(255, 80, 60))
    # dotted arc above the platform, arcing toward the tanker
    for k in range(7):
        t = k / 6.0
        ax = x + int(w * (0.20 + 0.30 * t))
        ay = y + int(h * (0.30 + 0.18 * t * t))
        d.ellipse([ax - 2, ay - 2, ax + 2, ay + 2], fill=(255, 255, 255))
    # tanker on the right: hull, three containers, bridge tower
    tx0 = x + int(w * 0.52)
    d.polygon([(tx0, sea + 4), (tx0 + int(w * 0.42), sea + 4),
               (tx0 + int(w * 0.38), sea + 14), (tx0 + 6, sea + 14)],
              fill=(20, 20, 28))
    d.rectangle([tx0 + 10, sea - 6, tx0 + 34, sea + 4], fill=(150, 60, 50))
    d.rectangle([tx0 + 38, sea - 6, tx0 + 58, sea + 4], fill=(70, 110, 160))
    d.rectangle([tx0 + 62, sea - 6, tx0 + 82, sea + 4], fill=(150, 150, 140))
    d.rectangle([tx0 + 66, sea - 20, tx0 + 82, sea - 6], fill=(220, 220, 210))
    d.rectangle([tx0 + 69, sea - 17, tx0 + 79, sea - 13], fill=(40, 80, 120))
    # wake lines and sun reflection dashes on the sea
    d.line([(tx0 - 24, sea + 18), (tx0 + int(w * 0.40), sea + 18)],
           fill=(150, 190, 220), width=1)
    d.line([(x + 20, sea + 8), (x + 120, sea + 8)], fill=(255, 180, 100), width=2)
    d.line([(x + 50, sea + 14), (x + 140, sea + 14)], fill=(255, 180, 100), width=1)


# ---------------------------------------------------------------- small scenes
def _bg(d, x, y, w, h, color):
    d.rectangle([x, y, x + w, y + h], fill=color)


def scene_ballot(d, x, y, w, h):
    _bg(d, x, y, w, h, (233, 227, 204))
    for fx, fw, fh in [(0.02, 0.10, 0.30), (0.14, 0.08, 0.42), (0.24, 0.10, 0.26),
                       (0.36, 0.09, 0.36), (0.48, 0.08, 0.28)]:
        d.rectangle([x + int(w * fx), y + int(h * 0.55) - int(h * fh),
                     x + int(w * fx) + int(w * fw), y + int(h * 0.55)],
                    fill=(190, 182, 158))
    d.rectangle([x, y + int(h * 0.55), x + w, y + h], fill=(214, 206, 180))
    # voting booth: white box, ballot paper, green check
    d.rectangle([x + 52, y + 12, x + 100, y + 44], fill=(255, 255, 255),
                outline=(60, 55, 45), width=2)
    d.rectangle([x + 66, y + 12, x + 86, y + 16], fill=(163, 18, 18))
    d.line([(x + 58, y + 34), (x + 68, y + 42), (x + 92, y + 20)],
           fill=(46, 125, 50), width=3)
    # ballot box with a red slot band
    d.rectangle([x + 12, y + 30, x + 34, y + 44], fill=(255, 255, 255),
                outline=(60, 55, 45), width=1)
    d.rectangle([x + 12, y + 30, x + 34, y + 34], fill=(163, 18, 18))
    # three voter dots queuing
    for vx, vy in [(112, 40), (124, 42), (136, 40)]:
        d.ellipse([x + vx, y + vy, x + vx + 7, y + vy + 7], fill=(60, 55, 45))
        d.ellipse([x + vx - 1, y + vy + 8, x + vx + 8, y + vy + 13],
                  fill=(60, 55, 45))


def scene_football(d, x, y, w, h):
    _bg(d, x, y, w, h, (74, 140, 74))
    # pitch stripes
    for i in range(4):
        d.rectangle([x + i * (w // 4), y, x + (i + 1) * (w // 4), y + h],
                    fill=(66, 128, 66) if i % 2 else (74, 140, 74))
    # centre line, centre circle, penalty box
    d.line([(x + w // 2, y), (x + w // 2, y + h)], fill=(255, 255, 255), width=2)
    d.ellipse([x + w // 2 - 12, y + 15, x + w // 2 + 12, y + 39],
              outline=(255, 255, 255), width=2)
    d.rectangle([x + w - 34, y + 10, x + w, y + 44], outline=(255, 255, 255), width=2)
    # goal on the right with net lines
    d.rectangle([x + w - 10, y + 16, x + w - 4, y + 38], outline=(255, 255, 255),
                width=2)
    for gy in range(20, 36, 6):
        d.line([(x + w - 10, y + gy), (x + w - 4, y + gy)], fill=(255, 255, 255), width=1)
    # ball mid-air near the goal, with a motion arc
    d.ellipse([x + 96, y + 12, x + 112, y + 28], fill=(255, 255, 255),
              outline=(40, 40, 40), width=1)
    d.ellipse([x + 102, y + 18, x + 106, y + 22], fill=(40, 40, 40))
    d.arc([x + 78, y + 8, x + 110, y + 30], start=200, end=340,
          fill=(255, 255, 255), width=1)
    # two player dots sprinting, one sliding
    d.ellipse([x + 30, y + 30, x + 38, y + 38], fill=(180, 30, 30))
    d.rectangle([x + 28, y + 38, x + 40, y + 48], fill=(180, 30, 30))
    d.ellipse([x + 58, y + 34, x + 66, y + 42], fill=(255, 255, 255))
    d.rectangle([x + 56, y + 42, x + 68, y + 50], fill=(255, 255, 255))
    # floodlight dots along the top
    for lx in (16, 44, 72):
        d.ellipse([x + lx, y + 4, x + lx + 4, y + 8], fill=(255, 240, 180))


def scene_tennis(d, x, y, w, h):
    _bg(d, x, y, w, h, (52, 96, 168))
    # hard court: lighter inner court, white lines
    d.rectangle([x + 10, y + 6, x + w - 10, y + h - 6], fill=(70, 130, 200))
    d.rectangle([x + 10, y + 6, x + w - 10, y + h - 6], outline=(255, 255, 255),
                width=2)
    d.line([(x + w // 2, y + 6), (x + w // 2, y + h - 6)], fill=(255, 255, 255),
           width=1)
    # net across the middle
    d.line([(x + 10, y + h // 2), (x + w - 10, y + h // 2)], fill=(20, 20, 28),
           width=3)
    d.line([(x + 10, y + h // 2), (x + w - 10, y + h // 2)], fill=(255, 255, 255),
           width=1)
    # yellow ball over the net with a trail
    d.ellipse([x + 96, y + 10, x + 108, y + 22], fill=(220, 230, 60),
              outline=(120, 130, 30), width=1)
    d.arc([x + 84, y + 6, x + 108, y + 26], start=200, end=340,
          fill=(255, 255, 255), width=1)
    # player silhouette serving, left side
    d.ellipse([x + 34, y + 26, x + 42, y + 34], fill=(40, 40, 40))
    d.polygon([(x + 36, y + 34), (x + 42, y + 34), (x + 46, y + 48), (x + 32, y + 48)],
              fill=(40, 40, 40))
    d.line([(x + 42, y + 36), (x + 54, y + 24)], fill=(40, 40, 40), width=3)
    d.ellipse([x + 52, y + 18, x + 62, y + 28], outline=(40, 40, 40), width=2)
    # second player dot at the baseline, right side
    d.ellipse([x + 126, y + 38, x + 134, y + 46], fill=(200, 60, 40))
    d.rectangle([x + 124, y + 46, x + 136, y + 52], fill=(200, 60, 40))


def scene_exam(d, x, y, w, h):
    _bg(d, x, y, w, h, (238, 232, 210))
    d.rectangle([x, y + 40, x + w, y + h], fill=(190, 180, 150))
    # blackboard strip at the top, below the red topic bar
    d.rectangle([x + 8, y + 18, x + w - 8, y + 30], fill=(52, 68, 60))
    d.line([(x + 14, y + 24), (x + 60, y + 24)], fill=(255, 255, 255), width=1)
    d.line([(x + 70, y + 24), (x + 110, y + 24)], fill=(255, 255, 255), width=1)
    # three desks with papers and a candidate dot each
    for dx in (14, 62, 110):
        d.rectangle([x + dx, y + 36, x + dx + 32, y + 42], fill=(150, 110, 70))
        d.rectangle([x + dx + 6, y + 32, x + dx + 26, y + 36], fill=(255, 255, 255))
        d.ellipse([x + dx + 12, y + 44, x + dx + 20, y + 52], fill=(60, 55, 45))
    # a phone on the middle desk, crossed out in red
    d.rectangle([x + 70, y + 30, x + 78, y + 38], fill=(30, 30, 40))
    d.line([(x + 66, y + 28), (x + 82, y + 40)], fill=(200, 30, 30), width=2)
    d.line([(x + 82, y + 28), (x + 66, y + 40)], fill=(200, 30, 30), width=2)
    # smart glasses on the right desk, also crossed
    d.ellipse([x + 118, y + 31, x + 126, y + 37], outline=(30, 30, 40), width=2)
    d.ellipse([x + 128, y + 31, x + 136, y + 37], outline=(30, 30, 40), width=2)
    d.line([(x + 116, y + 29), (x + 140, y + 39)], fill=(200, 30, 30), width=2)


def scene_strike(d, x, y, w, h):
    _bg(d, x, y, w, h, (200, 220, 235))
    d.rectangle([x, y + 42, x + w, y + h], fill=(120, 125, 135))
    # control tower, top below the red topic bar
    d.rectangle([x + 8, y + 20, x + 16, y + 42], fill=(90, 95, 105))
    d.rectangle([x + 4, y + 14, x + 20, y + 20], fill=(70, 75, 85))
    d.rectangle([x + 7, y + 16, x + 17, y + 19], fill=(150, 200, 230))
    # departure board with two red CANCELLED lines
    d.rectangle([x + 118, y + 8, x + 148, y + 22], fill=(20, 20, 28))
    d.line([(x + 121, y + 12), (x + 145, y + 12)], fill=(200, 30, 30), width=2)
    d.line([(x + 121, y + 18), (x + 145, y + 18)], fill=(200, 30, 30), width=2)
    # grounded plane silhouette
    d.ellipse([x + 40, y + 26, x + 110, y + 38], fill=(70, 75, 85))
    d.polygon([(x + 60, y + 28), (x + 84, y + 16), (x + 92, y + 28)], fill=(70, 75, 85))
    d.polygon([(x + 96, y + 28), (x + 108, y + 18), (x + 112, y + 28)], fill=(70, 75, 85))
    # red diagonal cross over the plane, starting below the red bar
    d.line([(x + 18, y + 15), (x + 134, y + 48)], fill=(200, 30, 30), width=3)
    # suitcase on the tarmac
    d.rectangle([x + 118, y + 38, x + 134, y + 48], fill=(150, 60, 50),
                outline=(60, 55, 45), width=1)
    d.line([(x + 123, y + 38), (x + 129, y + 38)], fill=(60, 55, 45), width=2)


def scene_ship(d, x, y, w, h):
    _bg(d, x, y, w, h, (60, 110, 160))
    for gx, gy in [(20, 6), (40, 10), (120, 6), (138, 10)]:
        d.line([(x + gx, y + gy), (x + gx + 4, y + gy + 2), (x + gx + 8, y + gy)],
               fill=(255, 255, 255), width=1)
    d.rectangle([x, y + 34, x + w, y + h], fill=(30, 80, 130))
    d.arc([x + 8, y + 38, x + 48, y + 50], start=180, end=360, fill=(255, 255, 255), width=2)
    d.arc([x + 96, y + 40, x + 140, y + 52], start=180, end=360, fill=(255, 255, 255), width=2)
    # ship hull with three coloured containers
    d.polygon([(x + 18, y + 26), (x + 136, y + 26), (x + 126, y + 40), (x + 28, y + 40)],
              fill=(20, 20, 28))
    d.rectangle([x + 30, y + 12, x + 52, y + 26], fill=(180, 60, 50))
    d.rectangle([x + 56, y + 12, x + 78, y + 26], fill=(70, 110, 160))
    d.rectangle([x + 82, y + 12, x + 104, y + 26], fill=(150, 150, 140))
    # flames and smoke above the deck, clear of the red topic bar
    d.polygon([(x + 88, y + 12), (x + 100, y + 12), (x + 94, y + 2)], fill=(255, 140, 40))
    d.polygon([(x + 92, y + 12), (x + 98, y + 12), (x + 95, y + 6)], fill=(255, 214, 110))
    for sx, sy in [(108, 4), (124, 2), (136, 6)]:
        d.ellipse([x + sx, y + sy, x + sx + 14, y + sy + 8], fill=(200, 200, 200))
    # small rescue boat
    d.polygon([(x + 118, y + 44), (x + 146, y + 44), (x + 140, y + 50), (x + 124, y + 50)],
              fill=(200, 60, 40))


def scene_capitol(d, x, y, w, h):
    _bg(d, x, y, w, h, (222, 214, 190))
    d.rectangle([x, y + 42, x + w, y + h], fill=(150, 140, 110))
    # dome, top below the red topic bar, with antenna and flag
    d.pieslice([x + 60, y + 14, x + 108, y + 48], start=180, end=360,
               fill=(240, 240, 235))
    d.rectangle([x + 80, y + 8, x + 88, y + 16], fill=(240, 240, 235))
    d.line([(x + 84, y + 4), (x + 84, y + 10)], fill=(120, 100, 60), width=2)
    d.rectangle([x + 84, y + 4, x + 96, y + 8], fill=(163, 18, 18))
    # columns flanking the dome
    for cx in (30, 44, 118, 132):
        d.rectangle([x + cx, y + 30, x + cx + 8, y + 42], fill=(250, 248, 240))
    # steps at the base
    d.rectangle([x + 52, y + 42, x + 116, y + 46], fill=(200, 190, 160))
    d.rectangle([x + 44, y + 46, x + 124, y + 50], fill=(180, 170, 140))
    # two small flags at the sides
    for fx, col in [(8, (163, 18, 18)), (138, (47, 93, 138))]:
        d.rectangle([x + fx, y + 22, x + fx + 10, y + 28], fill=col)
        d.line([(x + fx, y + 22), (x + fx, y + 34)], fill=(60, 55, 45), width=1)
    # crowd dots on the steps: head above shoulders
    for i in range(4):
        cx = x + 60 + i * 12
        d.ellipse([cx, y + 47, cx + 6, y + 53], fill=(60, 55, 45))
        d.ellipse([cx - 1, y + 51, cx + 7, y + 56], fill=(60, 55, 45))


def scene_aid(d, x, y, w, h):
    _bg(d, x, y, w, h, (222, 200, 160))
    d.rectangle([x, y + 42, x + w, y + h], fill=(170, 150, 110))
    # dusty sky with a low sun
    d.ellipse([x + 124, y + 6, x + 136, y + 18], fill=(255, 220, 140))
    # white aid truck: cab, cargo box, wheels
    d.rectangle([x + 18, y + 20, x + 104, y + 42], fill=(255, 255, 255),
                outline=(60, 55, 45), width=1)
    d.rectangle([x + 104, y + 26, x + 126, y + 42], fill=(240, 240, 235),
                outline=(60, 55, 45), width=1)
    d.rectangle([x + 108, y + 29, x + 120, y + 35], fill=(150, 200, 230))
    d.ellipse([x + 30, y + 40, x + 40, y + 50], fill=(20, 20, 20))
    d.ellipse([x + 104, y + 40, x + 114, y + 50], fill=(20, 20, 20))
    # boxes stacked on the cargo box
    d.rectangle([x + 30, y + 10, x + 48, y + 20], fill=(200, 160, 90),
                outline=(60, 55, 45), width=1)
    d.rectangle([x + 52, y + 12, x + 68, y + 20], fill=(180, 140, 80),
                outline=(60, 55, 45), width=1)
    # fallen boxes and dust cloud at the rear
    d.rectangle([x + 128, y + 44, x + 142, y + 50], fill=(200, 160, 90))
    d.polygon([(x + 132, y + 38), (x + 146, y + 38), (x + 140, y + 46)],
              fill=(200, 160, 90))
    for sx, sy in [(136, 30), (144, 34)]:
        d.ellipse([x + sx, y + sy, x + sx + 10, y + sy + 6], fill=(210, 195, 165))


def scene_highway(d, x, y, w, h):
    _bg(d, x, y, w, h, (200, 205, 190))
    # road with dashed centre line, running diagonally down
    d.polygon([(x, y + 30), (x + w, y + 18), (x + w, y + 44), (x, y + 54)],
              fill=(70, 70, 78))
    for i in range(6):
        dx = x + 8 + i * 24
        dy = y + 38 - i * 2
        d.line([(dx, dy), (dx + 12, dy - 1)], fill=(255, 255, 255), width=2)
    # bus on the left, tilted
    d.rectangle([x + 12, y + 22, x + 52, y + 36], fill=(70, 110, 160))
    d.rectangle([x + 16, y + 25, x + 30, y + 31], fill=(180, 220, 240))
    d.rectangle([x + 34, y + 25, x + 48, y + 31], fill=(180, 220, 240))
    d.ellipse([x + 18, y + 34, x + 24, y + 40], fill=(20, 20, 20))
    d.ellipse([x + 40, y + 34, x + 46, y + 40], fill=(20, 20, 20))
    # tanker on the right, jackknifed
    d.ellipse([x + 96, y + 14, x + 138, y + 28], fill=(200, 200, 205),
              outline=(60, 55, 45), width=1)
    d.rectangle([x + 136, y + 18, x + 148, y + 30], fill=(180, 60, 40))
    d.ellipse([x + 100, y + 26, x + 106, y + 32], fill=(20, 20, 20))
    # impact star between them, with debris dots
    sx, sy = x + 76, y + 26
    for ang in range(0, 360, 45):
        ex = sx + int(9 * math.cos(math.radians(ang)))
        ey = sy + int(9 * math.sin(math.radians(ang)))
        d.line([(sx, sy), (ex, ey)], fill=(255, 200, 40), width=2)
    d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(255, 140, 40))
    for dx, dy in [(64, 40), (88, 42), (70, 14)]:
        d.ellipse([x + dx, y + dy, x + dx + 3, y + dy + 3], fill=(60, 55, 45))


def scene_clinic(d, x, y, w, h):
    _bg(d, x, y, w, h, (235, 235, 228))
    d.rectangle([x, y + 40, x + w, y + h], fill=(120, 170, 90))
    # white clinic with a green cross sign and lit windows
    d.rectangle([x + 40, y + 12, x + 112, y + 40], fill=(255, 255, 255),
                outline=(60, 55, 45), width=2)
    d.rectangle([x + 70, y + 16, x + 78, y + 32], fill=(46, 125, 50))
    d.rectangle([x + 64, y + 22, x + 84, y + 28], fill=(46, 125, 50))
    for wx in (48, 90):
        d.rectangle([x + wx, y + 18, x + wx + 8, y + 26], fill=(120, 170, 200))
    # triage tent on the lawn
    d.polygon([(x + 116, y + 30), (x + 132, y + 20), (x + 148, y + 30)],
              fill=(240, 230, 200))
    d.rectangle([x + 116, y + 30, x + 148, y + 42], fill=(240, 230, 200))
    # two health-worker dots and a stretcher line
    d.ellipse([x + 10, y + 44, x + 16, y + 50], fill=(60, 55, 45))
    d.ellipse([x + 22, y + 44, x + 28, y + 50], fill=(255, 255, 255))
    d.line([(x + 8, y + 50), (x + 34, y + 50)], fill=(200, 30, 30), width=2)


def scene_fire(d, x, y, w, h):
    _bg(d, x, y, w, h, (40, 30, 26))
    # dark factory: two blocks and a chimney
    d.rectangle([x + 14, y + 26, x + 60, y + h], fill=(70, 70, 78))
    d.rectangle([x + 66, y + 32, x + 112, y + h], fill=(60, 60, 68))
    d.rectangle([x + 116, y + 20, x + 124, y + 40], fill=(70, 70, 78))
    # grey smoke columns above the chimney, clear of the red topic bar
    d.ellipse([x + 118, y + 2, x + 132, y + 12], fill=(180, 180, 180))
    d.ellipse([x + 126, y + 10, x + 140, y + 20], fill=(160, 160, 160))
    # flames at the base, tips starting below the red topic bar
    for fx, fw, fh, col in [(0.14, 0.16, 0.42, (255, 90, 20)), (0.30, 0.13, 0.34, (255, 160, 40)),
                            (0.52, 0.15, 0.40, (255, 120, 30)), (0.68, 0.12, 0.30, (255, 200, 80))]:
        bx = x + int(w * fx)
        d.polygon([(bx, y + h - int(h * fh) + 14), (bx + int(w * fw), y + h - int(h * fh) + 14),
                   (bx + int(w * fw) // 2, y + 14)], fill=col)
    # red fire truck with a ladder, in front of the factory
    d.rectangle([x + 6, y + 42, x + 36, y + 51], fill=(200, 30, 30))
    d.rectangle([x + 28, y + 36, x + 42, y + 42], fill=(200, 30, 30))
    d.line([(x + 8, y + 38), (x + 38, y + 28)], fill=(180, 180, 180), width=2)
    d.ellipse([x + 12, y + 49, x + 18, y + 54], fill=(20, 20, 20))
    d.ellipse([x + 30, y + 49, x + 36, y + 54], fill=(20, 20, 20))
    # two white water-spray arcs from the ladder toward the flames
    d.arc([x + 38, y + 20, x + 70, y + 36], start=270, end=360, fill=(255, 255, 255), width=2)
    d.arc([x + 56, y + 24, x + 88, y + 40], start=270, end=360, fill=(255, 255, 255), width=2)


def scene_protest(d, x, y, w, h):
    _bg(d, x, y, w, h, (214, 206, 180))
    # grey city blocks at the back
    for fx, fw, fh in [(0.02, 0.12, 0.34), (0.18, 0.10, 0.44), (0.82, 0.12, 0.30)]:
        d.rectangle([x + int(w * fx), y + int(h * 0.50) - int(h * fh),
                     x + int(w * fx) + int(w * fw), y + int(h * 0.50)],
                    fill=(170, 162, 140))
    d.rectangle([x, y + int(h * 0.50), x + w, y + h], fill=(150, 140, 115))
    # banner held across the middle, below the red topic bar
    d.rectangle([x + 34, y + 20, x + 118, y + 30], fill=(255, 255, 255),
                outline=(60, 55, 45), width=1)
    d.line([(x + 40, y + 25), (x + 112, y + 25)], fill=(163, 18, 18), width=2)
    # placards on sticks, left and right of the banner
    for px, col in [(14, (163, 18, 18)), (128, (47, 93, 138))]:
        d.line([(x + px + 6, y + 30), (x + px + 6, y + 44)], fill=(60, 55, 45), width=2)
        d.rectangle([x + px, y + 18, x + px + 12, y + 30], fill=col)
    # crowd of dots along the bottom
    for i in range(9):
        cx = x + 8 + i * 16
        d.ellipse([cx, y + 44, cx + 7, y + 51], fill=(60, 55, 45))
        d.ellipse([cx - 1, y + 38, cx + 8, y + 45], fill=(40, 40, 40) if i % 3 else (90, 60, 40))


SCENES_BIG = {"summit": scene_summit, "dymer": scene_dymer, "gulf": scene_gulf}
SCENES_SMALL = {"ballot": scene_ballot, "football": scene_football,
                "tennis": scene_tennis, "exam": scene_exam,
                "strike": scene_strike, "ship": scene_ship,
                "capitol": scene_capitol, "aid": scene_aid,
                "highway": scene_highway, "clinic": scene_clinic,
                "fire": scene_fire, "protest": scene_protest}


def render(data, out_path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    m = 26
    d.rectangle([10, 10, W - 11, H - 11], outline=RULE, width=2)
    d.rectangle([15, 15, W - 16, H - 16], outline=RULE, width=1)
    warnings = []

    # --- kicker + meta -------------------------------------------------
    y = 24
    f_kick = font(SANS_B, 11)
    d.text((m, y), "THE WORLD IN ONE DAY", font=f_kick, fill=RED)
    f_meta = font(SANS, 10)
    meta = data["meta"]
    d.text((W - m - d.textlength(meta, font=f_meta), y), meta, font=f_meta, fill=MUTED)

    # --- masthead: the date --------------------------------------------
    f_mast = font(SERIF_B, 64)
    title = data["date_label"]
    while d.textlength(title, font=f_mast) > W - 2 * m and f_mast.size > 40:
        f_mast = font(SERIF_B, f_mast.size - 2)
    d.text(((W - d.textlength(title, font=f_mast)) / 2, 40), title, font=f_mast, fill=INK)
    f_red = font(SERIF_I, 13, fallback=SERIF)
    red_line = data["red_line"]
    d.text(((W - d.textlength(red_line, font=f_red)) / 2, 108), red_line,
           font=f_red, fill=RED)
    d.line([(m, 130), (W - m, 130)], fill=RULE, width=2)

    # --- numbers strip --------------------------------------------------
    y = 136
    nums = data["numbers"]
    cell_w = (W - 2 * m) // len(nums)
    f_num = font(SERIF_B, 20)
    f_lab = font(SANS, 8.5)
    for i, (num, lab) in enumerate(nums):
        cx = m + i * cell_w + cell_w // 2
        if i:
            d.line([(m + i * cell_w, y + 4), (m + i * cell_w, y + 40)], fill=LIGHT, width=1)
        d.text((cx - d.textlength(num, font=f_num) / 2, y), num, font=f_num, fill=RED)
        lab_lines = wrap(d, lab, f_lab, cell_w - 10)
        ly = y + 26
        for ln in lab_lines[:2]:
            d.text((cx - d.textlength(ln, font=f_lab) / 2, ly), ln, font=f_lab, fill=MUTED)
            ly += 10

    # --- region colour bar ----------------------------------------------
    # A segment too narrow for its label gets only its count inside the
    # bar, and a warning, so no text is ever squeezed or dropped.
    y = 184
    bar = data["regions_bar"]
    total = sum(c for _, c, _ in bar)
    bx = m
    f_bar = font(SANS_B, 10)
    f_bar_s = font(SANS_B, 8)
    for name, cnt, color in bar:
        seg_w = int((W - 2 * m) * cnt / total)
        d.rectangle([bx, y, bx + seg_w, y + 20], fill=color)
        label = f"{name} {cnt}"
        tw = d.textlength(label, font=f_bar)
        if tw <= seg_w - 8:
            d.text((bx + (seg_w - tw) / 2, y + 4), label, font=f_bar,
                   fill=(255, 255, 255))
        else:
            tw_s = d.textlength(label, font=f_bar_s)
            if tw_s <= seg_w - 4:
                d.text((bx + (seg_w - tw_s) / 2, y + 5), label, font=f_bar_s,
                       fill=(255, 255, 255))
            else:
                warnings.append(f"region {name} label does not fit {seg_w}px")
                num_s = d.textlength(str(cnt), font=f_bar_s)
                d.text((bx + (seg_w - num_s) / 2, y + 5), str(cnt), font=f_bar_s,
                       fill=(255, 255, 255))
        bx += seg_w

    # --- dark UTC strip ---------------------------------------------------
    y = 208
    d.rectangle([m, y, W - m, y + 20], fill=NAVY)
    f_utc_l = font(SANS_B, 10)
    f_utc = font(SANS, 10)
    label = "THE DAY IN UTC"
    parts = [(label, f_utc_l, SALMON)]
    for t, ev in data["utc"]:
        parts.append(("  ·  " + t + " ", f_utc_l, SALMON))
        parts.append((ev, f_utc, (255, 255, 255)))
    total_w = sum(d.textlength(t, font=f) for t, f, _ in parts)
    while total_w > W - 2 * m - 8 and f_utc.size > 8:
        f_utc = font(SANS, f_utc.size - 1)
        f_utc_l = font(SANS_B, f_utc_l.size - 1)
        total_w = sum(d.textlength(t, font=f) for t, f, _ in parts)
    tx = m + (W - 2 * m - total_w) / 2
    for t, f, col in parts:
        d.text((tx, y + 4), t, font=f, fill=col)
        tx += d.textlength(t, font=f)

    # --- 3 big illustrated stories ---------------------------------------
    y = 234
    big_w = (W - 2 * m - 2 * 12) // 3
    f_tag = font(SANS_B, 10.5)
    f_bhead = font(SERIF_B, 19)
    f_bsum = font(SANS, 11)
    f_bsrc = font(SANS, 9.5)
    for i, st in enumerate(data["big"]):
        x0 = m + i * (big_w + 12)
        SCENES_BIG[st["scene"]](d, x0, y, big_w, 100)
        # red topic bar top-left + white secondary bar top-right
        wb = whitebar(d, x0 + big_w, y, 10, st["label2"], h=16) if st.get("label2") else 0
        redbar(d, x0, y, 11, st["label"], h=16, max_w=big_w - wb - 8)
        ty = y + 104
        tag = f"{st['num']}  {st['place']} · {st['topic']}"
        d.text((x0, ty), tag, font=f_tag, fill=INK)
        chip(d, x0 + big_w, ty - 1, st["badge"], size=9)
        hy = ty + 18
        hl = wrap(d, st["headline"], f_bhead, big_w)
        if len(hl) > 3:
            warnings.append(f"big {st['num']} headline {len(hl)} lines")
        hy = draw_wrapped(d, x0, hy, hl[:3], f_bhead, INK, 23)
        sm = wrap(d, st["summary"], f_bsum, big_w)
        if len(sm) > 3:
            warnings.append(f"big {st['num']} summary {len(sm)} lines")
        hy = draw_wrapped(d, x0, hy + 1, sm[:3], f_bsum, MUTED, 14.5)
        d.text((x0, hy + 1), f"({st['source']})", font=f_bsrc, fill=MUTED)

    # --- 12 small illustrated stories, 2 rows x 6 ------------------------
    y = 487
    sm_w = (W - 2 * m - 5 * 10) // 6
    f_stag = font(SANS_B, 8.5)
    f_shead = font(SERIF_B, 12.5)
    f_ssum = font(SANS, 9.5)
    for row in range(2):
        for col in range(6):
            st = data["small"][row * 6 + col]
            x0 = m + col * (sm_w + 10)
            sy = y + row * 125
            SCENES_SMALL[st["scene"]](d, x0, sy, sm_w, 54)
            # red topic bar top-left of the illustration
            redbar(d, x0, sy, 8, st["label"], h=13, max_w=sm_w)
            chip(d, x0 + sm_w - 3, sy + 54 - 15, st["badge"], size=7)
            ty = sy + 58
            tag = f"{st['num']} {st['place']} · {st['topic']}"
            tag_lines = wrap(d, tag, f_stag, sm_w)
            ty = draw_wrapped(d, x0, ty, tag_lines[:1], f_stag, INK, 11)
            hy = ty + 2
            hl = wrap(d, st["headline"], f_shead, sm_w)
            if len(hl) > 2:
                warnings.append(f"small {st['num']} headline {len(hl)} lines")
            hy = draw_wrapped(d, x0, hy, hl[:2], f_shead, INK, 15)
            sm = wrap(d, f"{st['summary']} ({st['source']})", f_ssum, sm_w)
            if len(sm) > 2:
                warnings.append(f"small {st['num']} summary {len(sm)} lines")
            draw_wrapped(d, x0, hy + 1, sm[:2], f_ssum, MUTED, 12)

    # --- bottom: map + ALSO ON -------------------------------------------
    y = 749
    f_sect = font(SANS_B, 12)
    d.text((m, y), "WHERE IT HAPPENED", font=f_sect, fill=RED)
    f_cap = font(SANS, 9)
    d.text((m + 300 - d.textlength("pins match story numbers", font=f_cap), y + 2),
           "pins match story numbers", font=f_cap, fill=MUTED)
    map_x, map_y, map_w, map_h = m, y + 16, 300, 84
    d.rectangle([map_x, map_y, map_x + map_w, map_y + map_h],
                fill=(238, 238, 226), outline=MAP_LINE, width=1)

    def proj(lon, lat):
        return (map_x + (lon + 180) / 360.0 * map_w,
                map_y + (90 - lat) / 150.0 * map_h)

    for poly in CONTINENTS:
        d.polygon([proj(lon, lat) for lon, lat in poly], fill=MAP_LAND, outline=MAP_LINE)
    f_pin = font(SANS_B, 7)
    for num, lon, lat in data["pins"]:
        px, py = proj(lon, lat)
        px = min(max(px, map_x + 7), map_x + map_w - 7)
        py = min(max(py, map_y + 7), map_y + map_h - 7)
        d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=RED, outline=(255, 255, 255), width=1)
        lbl = str(num)
        d.text((px - d.textlength(lbl, font=f_pin) / 2, py - 5), lbl,
               font=f_pin, fill=(255, 255, 255))

    ax = m + 300 + 16
    aw = W - m - ax
    also_title = (f"ALSO ON {data['date_label'].upper()} — "
                  f"{len(data['also'])} MORE STORIES")
    d.text((ax, y), also_title, font=f_sect, fill=RED)
    f_also = font(SANS, 9)
    col_w = (aw - 10) // 2
    items = data["also"]
    for idx, it in enumerate(items):
        col = idx // 11
        row = idx % 11
        ix = ax + col * (col_w + 10)
        iy = y + 18 + row * 11
        line = f"{it['num']} {it['region']}: {it['text']} ({it['source']})"
        if d.textlength(line, font=f_also) > col_w:
            warnings.append(f"also {it['num']} line too long: {len(line)} chars")
        d.text((ix, iy), line, font=f_also, fill=INK)

    # --- DATE CHECK box (footer placed relative to its height) ------------
    dy = 890
    dc = data["date_check"]
    f_dc_t = font(SANS_B, 11)
    f_dc = font(SANS, 10)
    dc_lines = wrap(d, dc, f_dc, W - 2 * m - 130)
    if len(dc_lines) > 3:
        warnings.append(f"date_check {len(dc_lines)} lines")
    dc_h = 12 + len(dc_lines) * 13 + 8
    d.rectangle([m, dy, W - m, dy + dc_h], outline=RED, width=1)
    d.text((m + 8, dy + 6), "DATE CHECK", font=f_dc_t, fill=RED)
    draw_wrapped(d, m + 118, dy + 6, dc_lines, f_dc, INK, 13)

    # --- footer -------------------------------------------------------------
    fy = dy + dc_h + 6
    d.line([(m, fy), (W - m, fy)], fill=RULE, width=1)
    f_foot = font(SANS, 9.5)
    legend = data["legend"]
    d.text(((W - d.textlength(legend, font=f_foot)) / 2, fy + 4), legend,
           font=f_foot, fill=MUTED)
    foot = data["footer"]
    d.text(((W - d.textlength(foot, font=f_foot)) / 2, fy + 16), foot,
           font=f_foot, fill=MUTED)

    # --- bottom navy bar -----------------------------------------------------
    d.rectangle([15, 984, W - 16, 1004], fill=NAVY)
    f_bar = font(SANS_B, 9)
    d.text((m, 990), "THE WORLD IN ONE DAY", font=f_bar, fill=(255, 255, 255))
    tail = f"{data['date_label'].upper()}  ·  ONE PAGE"
    d.text((W - m - d.textlength(tail, font=f_bar), 990), tail, font=f_bar,
           fill=(255, 255, 255))

    img.save(out_path, "PNG", optimize=True)
    for wmsg in sorted(set(warnings)):
        print("TRUNCATED:", wmsg)
    print("warnings:", len(warnings))
    return out_path


if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    render(data, out)
    print("wrote", out, os.path.getsize(out), "bytes")
