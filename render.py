#!/usr/bin/env python3
"""Render Monday 23 November 2026 as a one-page illustrated newspaper.

Reads stories.json (researched from live news for 23 Nov 2026) and draws a
1024x1024 front page with PIL: date masthead, numbers strip, region colour
bar, dark UTC strip, 3 big illustrated stories + 12 small illustrated
stories (flat vector scenes, one accent colour per scene, a red topic bar
on every illustration), an ALSO ON list, a world map with numbered pins,
a DATE CHECK box and a sources footer. Deterministic: no randomness, no
clock reads, fixed fonts and geometry.

Usage: python3 render.py stories.json news.png
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
M = 24                      # outer margin
CW = W - 2 * M              # content width = 976
PAPER = (245, 240, 230)
INK = (26, 26, 26)
RED = (139, 26, 26)
NAVY = (22, 33, 58)
GREY = (107, 114, 128)

TRUNCATED = 0               # counts any text that had to be cut to fit

FONT_DIR = "/usr/share/fonts/truetype"
SERIF = os.path.join(FONT_DIR, "dejavu/DejaVuSerif.ttf")
SERIF_B = os.path.join(FONT_DIR, "dejavu/DejaVuSerif-Bold.ttf")
SERIF_I = os.path.join(FONT_DIR, "liberation/LiberationSerif-Italic.ttf")
SANS = os.path.join(FONT_DIR, "dejavu/DejaVuSans.ttf")
SANS_B = os.path.join(FONT_DIR, "dejavu/DejaVuSans-Bold.ttf")


def font(path, size):
    return ImageFont.truetype(path, int(round(size)))


def wrap(text, fnt, width, draw):
    """Greedy word wrap; returns a list of lines that fit `width`."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_lines(text, fnt, width, max_lines, draw):
    """Wrap text to at most max_lines; cut with an ellipsis if it overflows.

    Every cut is counted in the global TRUNCATED tally so the render can
    prove it printed nothing mid-sentence.
    """
    global TRUNCATED
    lines = wrap(text, fnt, width, draw)
    if len(lines) <= max_lines:
        return lines
    TRUNCATED += 1
    kept = lines[:max_lines]
    last = kept[-1]
    while last and draw.textlength(last + "…", font=fnt) > width:
        last = last[:-1]
    kept[-1] = last + "…"
    return kept


def fit_one_line(text, fnt, width, draw):
    """Shrink one line to `width` with an ellipsis; count it if cut."""
    global TRUNCATED
    if draw.textlength(text, font=fnt) <= width:
        return text
    TRUNCATED += 1
    cut = text
    while cut and draw.textlength(cut + "…", font=fnt) > width:
        cut = cut[:-1]
    return cut + "…"


def text_block(draw, x, y, text, fnt, width, max_lines, fill=INK, leading=None):
    """Draw wrapped text; returns the y just below the block."""
    if leading is None:
        leading = int(fnt.size * 1.18)
    lines = fit_lines(text, fnt, width, max_lines, draw)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


BADGE_FILL = {
    "CONFIRMED": (21, 128, 61),
    "OFFICIAL": (29, 78, 216),
    "REPORTED": (146, 64, 14),
    "CLAIM": (180, 83, 9),
    "FORECAST": (107, 114, 128),
}


def badge(draw, x, y, label, small=False):
    """Coloured chip with the verification badge; returns its width."""
    size = 8 if small else 9
    fnt = font(SANS_B, size)
    tw = draw.textlength(label, font=fnt)
    w = int(tw + 10 if small else tw + 12)
    h = 11 if small else 14
    draw.rounded_rectangle([x, y, x + w, y + h], radius=3,
                           fill=BADGE_FILL.get(label, (107, 114, 128)))
    draw.text((x + 5, y + 2 if small else y + 2.5), label, font=fnt,
              fill=(255, 255, 255))
    return w


def topic_bar(draw, x, y, w, text, accent):
    """Small red bar above an illustration holding the topic / key fact."""
    h = 14
    draw.rectangle([x, y, x + w, y + h], fill=RED)
    fnt = font(SANS_B, 9)
    label = fit_one_line(text, fnt, w - 8, draw)
    draw.text((x + 4, y + 2.5), label, font=fnt, fill=(255, 255, 255))
    return h


def fact_bar(draw, x, y, w, text):
    """Thin white bar under a big illustration holding a secondary fact."""
    h = 13
    draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255),
                   outline=(200, 190, 175))
    fnt = font(SANS_B, 8.5)
    label = fit_one_line(text, fnt, w - 8, draw)
    draw.text((x + 4, y + 2), label, font=fnt, fill=INK)
    return h


def location_tag(draw, x, y, w, number, place):
    """Dark bar: story number + place, under the illustration."""
    h = 14
    draw.rectangle([x, y, x + w, y + h], fill=(31, 41, 55))
    fnt = font(SANS_B, 9)
    label = fit_one_line("%d  %s" % (number, place), fnt, w - 8, draw)
    draw.text((x + 4, y + 2.5), label, font=fnt, fill=(255, 255, 255))
    return h

# ---------------------------------------------------------------- scenes
# Flat vector scenes, one accent colour each. Every scene is drawn from
# simple PIL shapes: sky, ground, silhouettes, a few props.

def _sky(draw, x, y, w, h, top, bottom):
    """Vertical two-stop sky gradient (drawn as thin horizontal bands)."""
    for i in range(h):
        t = i / max(1, h - 1)
        c = tuple(int(top[j] + (bottom[j] - top[j]) * t) for j in range(3))
        draw.line([(x, y + i), (x + w, y + i)], fill=c)


def _sun(draw, cx, cy, r, colour):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour)


def _building(draw, x, y, w, h, colour, lit=True):
    draw.rectangle([x, y, x + w, y + h], fill=colour)
    if lit:
        for wy in range(y + 6, y + h - 4, 10):
            for wx in range(x + 5, x + w - 4, 9):
                if (wx * 7 + wy * 13) % 5:
                    draw.rectangle([wx, wy, wx + 3, wy + 4],
                                   fill=(250, 204, 21))


def scene_summit(draw, x, y, w, h, accent):
    _sky(draw, x, y, w, h, (249, 115, 22), (124, 45, 18))
    _sun(draw, x + w - 22, y + 18, 11, (253, 224, 71))
    gy = y + int(h * 0.62)
    draw.rectangle([x, gy, x + w, y + h], fill=(41, 37, 36))
    _building(draw, x + 8, gy - 26, 26, 26 + (y + h - gy), (31, 41, 55))
    _building(draw, x + w // 2 - 20, gy - 34, 40, 34 + (y + h - gy),
              (17, 24, 39))
    for i in range(5):
        fx = x + 14 + i * (w - 28) // 4
        draw.polygon([(fx, gy - 8), (fx + 3, gy - 18), (fx + 6, gy - 8)],
                     fill=(248, 113, 113))
        draw.line([(fx + 3, gy - 18), (fx + 3, gy - 8)], fill=(255, 255, 255))
    draw.ellipse([x + w // 2 - 5, gy - 12, x + w // 2 + 5, gy - 2],
                 fill=(255, 255, 255))


def scene_strait(draw, x, y, w, h, accent):
    _sky(draw, x, y, w, h, (30, 58, 95), (147, 197, 253))
    _sun(draw, x + 20, y + 14, 9, (254, 240, 138))
    sea = y + int(h * 0.55)
    draw.rectangle([x, sea, x + w, y + h], fill=(23, 68, 110))
    for i in range(4):
        wy = sea + 6 + i * 7
        draw.line([(x + 6 + i * 5, wy), (x + w - 10 - i * 4, wy)],
                  fill=(96, 165, 250), width=1)
    # two tankers
    draw.rectangle([x + 8, sea - 12, x + w // 2 - 4, sea - 2], fill=(15, 23, 42))
    draw.rectangle([x + 14, sea - 20, x + 26, sea - 12], fill=(15, 23, 42))
    draw.rectangle([x + w // 2 + 2, sea - 10, x + w - 10, sea - 2],
                   fill=(51, 65, 85))
    draw.rectangle([x + w - 30, sea - 17, x + w - 20, sea - 10],
                   fill=(51, 65, 85))
    # missile trails
    draw.line([(x + w - 14, y + 6), (x + w // 2, sea - 12)],
              fill=(255, 255, 255), width=2)
    draw.line([(x + 16, y + 10), (x + w // 3, sea - 10)],
              fill=(252, 211, 77), width=2)


def scene_tennis(draw, x, y, w, h, accent):
    _sky(draw, x, y, w, h, (220, 252, 231), (134, 239, 172))
    draw.rectangle([x, y + int(h * 0.35), x + w, y + h], fill=(22, 163, 74))
    draw.rectangle([x + w // 2 - 2, y + int(h * 0.35), x + w // 2 + 2, y + h],
                   fill=(255, 255, 255))
    draw.line([(x + 6, y + h - 8), (x + w - 6, y + h - 8)],
              fill=(255, 255, 255), width=2)
    # net
    ny = y + int(h * 0.55)
    draw.line([(x, ny), (x + w, ny)], fill=(255, 255, 255), width=3)
    for nx in range(x + 4, x + w - 2, 8):
        draw.line([(nx, ny), (nx, ny + 8)], fill=(226, 232, 240), width=1)
    # player silhouette + ball
    px, py = x + w // 4, y + int(h * 0.62)
    draw.ellipse([px - 5, py - 16, px + 5, py - 6], fill=(17, 24, 39))
    draw.polygon([(px - 6, py - 6), (px + 6, py - 6), (px + 3, py + 12),
                  (px - 3, py + 12)], fill=(17, 24, 39))
    draw.ellipse([x + w - 22, y + 12, x + w - 12, y + 22], fill=(190, 242, 100))
    draw.arc([x + w - 40, y + 26, x + w - 8, y + 52], 200, 340,
             fill=(17, 24, 39), width=2)


def scene_shipfire(draw, x, y, w, h, accent):
    _sky(draw, x, y, w, h, (51, 65, 85), (15, 23, 42))
    sea = y + int(h * 0.6)
    draw.rectangle([x, sea, x + w, y + h], fill=(30, 58, 95))
    # ship hull
    draw.polygon([(x + 8, sea - 4), (x + w - 8, sea - 4), (x + w - 18, sea + 8),
                  (x + 18, sea + 8)], fill=(15, 23, 42))
    draw.rectangle([x + 14, sea - 14, x + 40, sea - 4], fill=(51, 65, 85))
    # flames
    for fx, fh in ((x + 18, 16), (x + 30, 22), (x + 44, 14)):
        draw.polygon([(fx, sea - 12), (fx + 5, sea - 12 - fh),
                      (fx + 10, sea - 12)], fill=(249, 115, 22))
        draw.polygon([(fx + 2, sea - 12), (fx + 5, sea - 12 - fh + 7),
                      (fx + 8, sea - 12)], fill=(253, 224, 71))
    # smoke
    for sx, sy, r in ((x + 24, y + 8, 6), (x + 34, y + 4, 5), (x + 44, y + 9, 4)):
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(148, 163, 184))
    # lifeboat dot
    draw.ellipse([x + w - 18, sea + 2, x + w - 10, sea + 8], fill=(239, 68, 68))


def scene_citynight(draw, x, y, w, h, accent):
    _sky(draw, x, y, w, h, (15, 23, 42), (30, 41, 59))
    for sx, sy in ((x + 10, y + 6), (x + w - 14, y + 10), (x + w // 2, y + 4)):
        draw.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(255, 255, 255))
    base = y + h
    _building(draw, x + 4, y + int(h * 0.35), 18, base - y - int(h * 0.35),
              (31, 41, 55))
    _building(draw, x + 26, y + int(h * 0.2), 22, base - y - int(h * 0.2),
              (17, 24, 39))
    _building(draw, x + 52, y + int(h * 0.45), 16, base - y - int(h * 0.45),
              (51, 65, 85))
    # drone dots with trails
    for dx, dy in ((x + w - 24, y + 12), (x + w - 40, y + 22)):
        draw.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=(251, 146, 60))
        draw.line([(dx, dy), (dx - 10, dy + 8)], fill=(251, 146, 60), width=1)


def scene_factoryfire(draw, x, y, w, h, accent):
    _sky(draw, x, y, w, h, (254, 215, 170), (194, 65, 12))
    base = y + h
    # sawtooth factory
    draw.rectangle([x + 4, y + int(h * 0.5), x + w - 4, base], fill=(68, 64, 60))
    for i in range(3):
        sx = x + 8 + i * ((w - 16) // 3)
        draw.polygon([(sx, y + int(h * 0.5)), (sx + (w - 16) // 6, y + int(h * 0.3)),
                      (sx + (w - 16) // 3, y + int(h * 0.5))], fill=(41, 37, 36))
    draw.rectangle([x + w - 16, y + int(h * 0.25), x + w - 10, y + int(h * 0.5)],
                   fill=(87, 83, 78))
    for fx, fh in ((x + 14, 14), (x + 26, 18), (x + 40, 12)):
        draw.polygon([(fx, y + int(h * 0.5)), (fx + 5, y + int(h * 0.5) - fh),
                      (fx + 10, y + int(h * 0.5))], fill=(250, 204, 21))
    for sx, sy, r in ((x + 20, y + 6, 5), (x + 32, y + 3, 4)):
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(231, 229, 228))


def scene_talks(draw, x, y, w, h, accent):
    _sky(draw, x, y, w, h, (226, 232, 240), (148, 163, 184))
    # table
    draw.rectangle([x + 6, y + int(h * 0.68), x + w - 6, y + h], fill=(120, 53, 15))
    draw.rectangle([x + 6, y + int(h * 0.68), x + w - 6, y + int(h * 0.68) + 4],
                   fill=(146, 64, 14))
    # two heads facing each other
    for hx in (x + w // 4, x + 3 * w // 4):
        draw.ellipse([hx - 8, y + int(h * 0.3), hx + 8, y + int(h * 0.3) + 16],
                     fill=(51, 65, 85))
        draw.polygon([(hx - 10, y + int(h * 0.68)), (hx + 10, y + int(h * 0.68)),
                      (hx + 6, y + int(h * 0.3) + 16),
                      (hx - 6, y + int(h * 0.3) + 16)], fill=(51, 65, 85))
    # flags
    for fx, col in ((x + 8, (29, 78, 216)), (x + w - 14, (220, 38, 38))):
        draw.line([(fx, y + 6), (fx, y + int(h * 0.3))], fill=(71, 85, 105), width=2)
        draw.polygon([(fx, y + 6), (fx + 10, y + 10), (fx, y + 14)], fill=col)


def scene_exam(draw, x, y, w, h, accent):
    _sky(draw, x, y, w, h, (243, 232, 255), (196, 141, 253))
    # desks + papers
    for i in range(3):
        dx = x + 8 + i * ((w - 16) // 3)
        dw = (w - 16) // 3 - 6
        draw.rectangle([dx, y + int(h * 0.6), dx + dw, y + int(h * 0.6) + 5],
                       fill=(146, 64, 14))
        draw.rectangle([dx + 4, y + int(h * 0.45), dx + dw - 4,
                        y + int(h * 0.6)], fill=(255, 255, 255),
                       outline=(203, 213, 225))
        for ly in range(y + int(h * 0.48), y + int(h * 0.58), 4):
            draw.line([(dx + 7, ly), (dx + dw - 7, ly)], fill=(148, 163, 184))
        draw.ellipse([dx + dw // 2 - 4, y + int(h * 0.28),
                      dx + dw // 2 + 4, y + int(h * 0.28) + 8],
                     fill=(51, 65, 85))
    # crossed-out AI chip
    draw.rounded_rectangle([x + w - 26, y + 4, x + w - 4, y + 18], radius=3,
                           fill=(220, 38, 38))
    draw.text((x + w - 23, y + 6), "AI", font=font(SANS_B, 9),
              fill=(255, 255, 255))
    draw.line([(x + w - 26, y + 4), (x + w - 4, y + 18)], fill=(255, 255, 255),
              width=2)


def scene_cricket(draw, x, y, w, h, accent):
    _sky(draw, x, y, w, h, (220, 252, 231), (74, 222, 128))
    draw.rectangle([x, y + int(h * 0.4), x + w, y + h], fill=(21, 128, 61))
    # pitch
    draw.rectangle([x + w // 2 - 8, y + int(h * 0.35), x + w // 2 + 8, y + h],
                   fill=(214, 177, 122))
    # stumps
    for sx in (x + w // 2 - 5, x + w // 2, x + w // 2 + 5):
        draw.line([(sx, y + int(h * 0.4)), (sx, y + int(h * 0.4) + 9)],
                  fill=(253, 224, 71), width=2)
    # batsman
    px, py = x + w // 4, y + int(h * 0.62)
    draw.ellipse([px - 4, py - 12, px + 4, py - 4], fill=(17, 24, 39))
    draw.polygon([(px - 5, py - 4), (px + 5, py - 4), (px + 3, py + 10),
                  (px - 3, py + 10)], fill=(17, 24, 39))
    draw.line([(px + 4, py - 2), (px + 14, py + 8)], fill=(146, 64, 14), width=3)
    # ball
    draw.ellipse([x + w - 18, y + 10, x + w - 10, y + 18], fill=(220, 38, 38))


def scene_health(draw, x, y, w, h, accent):
    _sky(draw, x, y, w, h, (220, 252, 231), (134, 239, 172))
    draw.ellipse([x + 8, y + h - 14, x + w - 8, y + h + 10], fill=(74, 222, 128))
    # clinic
    draw.rectangle([x + w // 2 - 20, y + int(h * 0.4), x + w // 2 + 20, y + h - 6],
                   fill=(255, 255, 255), outline=(148, 163, 184))
    draw.polygon([(x + w // 2 - 24, y + int(h * 0.4)),
                  (x + w // 2 + 24, y + int(h * 0.4)),
                  (x + w // 2, y + int(h * 0.2))], fill=(220, 38, 38))
    cx, cy = x + w // 2, y + int(h * 0.55)
    draw.rectangle([cx - 8, cy - 3, cx + 8, cy + 3], fill=(220, 38, 38))
    draw.rectangle([cx - 3, cy - 8, cx + 3, cy + 8], fill=(220, 38, 38))
    # hills + path
    draw.ellipse([x - 10, y + int(h * 0.75), x + 24, y + h + 6],
                 fill=(21, 128, 61))


def scene_chess(draw, x, y, w, h, accent):
    sq = min(w, h) // 8
    ox, oy = x + (w - sq * 8) // 2, y + (h - sq * 8) // 2
    for r in range(8):
        for c in range(8):
            col = (245, 240, 230) if (r + c) % 2 == 0 else (41, 37, 36)
            draw.rectangle([ox + c * sq, oy + r * sq, ox + (c + 1) * sq,
                            oy + (r + 1) * sq], fill=col)
    # king + queen silhouettes
    for kx, ky, col in ((ox + 2 * sq, oy + 5 * sq, (255, 255, 255)),
                        (ox + 5 * sq, oy + 2 * sq, (17, 24, 39))):
        draw.ellipse([kx - sq // 3, ky - sq // 3, kx + sq // 3, ky + sq // 3],
                     fill=col, outline=(107, 114, 128))
        draw.rectangle([kx - sq // 4, ky, kx + sq // 4, ky + sq // 2], fill=col,
                       outline=(107, 114, 128))


def scene_un(draw, x, y, w, h, accent):
    _sky(draw, x, y, w, h, (219, 234, 254), (59, 130, 246))
    cx, cy = x + w // 2, y + h // 2
    r = min(w, h) // 2 - 4
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(219, 234, 254),
                 outline=(255, 255, 255), width=2)
    for k in range(1, 4):
        ry = r * k // 4
        draw.ellipse([cx - r, cy - ry, cx + r, cy + ry],
                     outline=(147, 197, 253))
    draw.line([(cx, cy - r), (cx, cy + r)], fill=(147, 197, 253))
    # olive branches
    draw.arc([cx - r - 6, cy - r + 6, cx - 4, cy + r + 2], 300, 60,
             fill=(255, 255, 255), width=2)
    draw.arc([cx + 4, cy - r + 6, cx + r + 6, cy + r + 2], 120, 240,
             fill=(255, 255, 255), width=2)


def scene_conflict(draw, x, y, w, h, accent):
    _sky(draw, x, y, w, h, (254, 243, 199), (217, 119, 6))
    _sun(draw, x + w - 16, y + 12, 8, (253, 224, 71))
    draw.rectangle([x, y + int(h * 0.65), x + w, y + h], fill=(180, 83, 9))
    for hx in (x + 8, x + w // 2 - 6):
        draw.polygon([(hx, y + int(h * 0.65)), (hx + 12, y + int(h * 0.35)),
                      (hx + 24, y + int(h * 0.65))], fill=(120, 53, 15))
    for sx, sy, r in ((x + w - 20, y + 14, 5), (x + w - 28, y + 8, 4)):
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(120, 113, 108))


SCENES = {
    "summit": scene_summit,
    "strait": scene_strait,
    "tennis": scene_tennis,
    "shipfire": scene_shipfire,
    "citynight": scene_citynight,
    "factoryfire": scene_factoryfire,
    "talks": scene_talks,
    "exam": scene_exam,
    "cricket": scene_cricket,
    "health": scene_health,
    "chess": scene_chess,
    "un": scene_un,
    "conflict": scene_conflict,
}


def draw_scene(draw, x, y, w, h, kind, accent):
    draw.rectangle([x, y, x + w, y + h], fill=(226, 232, 240))
    SCENES.get(kind, scene_citynight)(draw, x, y, w, h, accent)
    draw.rectangle([x, y, x + w, y + h], outline=(200, 190, 175))

# ---------------------------------------------------------------- map
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 76),
     (-75, 72), (-65, 60), (-55, 52), (-60, 46), (-70, 42), (-75, 35),
     (-80, 26), (-85, 20), (-90, 15), (-95, 16), (-105, 20), (-115, 28),
     (-125, 40), (-125, 49), (-140, 60), (-155, 58), (-165, 60)],
    # Greenland
    [(-55, 60), (-45, 60), (-40, 64), (-30, 68), (-22, 70), (-25, 76),
     (-40, 80), (-55, 76), (-60, 70)],
    # South America
    [(-80, 10), (-75, 5), (-65, 0), (-55, -5), (-40, -5), (-35, -10),
     (-40, -20), (-48, -28), (-55, -35), (-65, -45), (-70, -52), (-73, -40),
     (-72, -25), (-78, -15), (-80, -5)],
    # Africa
    [(-17, 15), (-10, 5), (0, 5), (8, 4), (12, -2), (13, -10), (12, -18),
     (18, -25), (20, -35), (28, -33), (33, -26), (40, -15), (42, -5),
     (48, 10), (43, 12), (38, 18), (33, 28), (25, 32), (15, 32), (10, 37),
     (0, 36), (-6, 35), (-10, 30), (-15, 25)],
    # Eurasia
    [(-10, 36), (-9, 43), (-2, 48), (-5, 50), (0, 51), (5, 53), (8, 57),
     (10, 59), (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (35, 66),
     (45, 68), (55, 68), (65, 69), (75, 72), (90, 75), (105, 77), (120, 73),
     (135, 72), (150, 70), (162, 66), (170, 66), (178, 65), (170, 60),
     (162, 60), (158, 52), (150, 45), (142, 40), (135, 35), (130, 33),
     (127, 35), (122, 30), (120, 25), (115, 22), (108, 18), (105, 10),
     (100, 8), (97, 10), (95, 16), (90, 22), (85, 20), (80, 15), (77, 8),
     (75, 10), (72, 20), (68, 23), (62, 25), (57, 26), (52, 28), (50, 30),
     (48, 30), (44, 29), (40, 32), (36, 36), (30, 36), (27, 37), (23, 36),
     (19, 40), (15, 44), (12, 44), (8, 44), (3, 43), (0, 40), (-2, 37),
     (-5, 36)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32), (130, -32),
     (135, -35), (140, -38), (145, -38), (150, -37), (153, -32), (153, -27),
     (150, -23), (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
     (132, -12), (130, -13), (126, -14), (122, -17), (118, -20)],
    # UK
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51)],
    # Japan
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 37), (140, 39),
     (141, 41), (142, 44), (140, 45), (138, 38), (136, 36), (133, 35)],
    # New Zealand
    [(167, -45), (170, -42), (173, -40), (175, -38), (177, -38), (175, -41),
     (172, -43), (168, -46)],
]


def draw_map(draw, x, y, w, h, pins):
    draw.rectangle([x, y, x + w, y + h], fill=(232, 238, 242),
                   outline=(200, 190, 175))

    def proj(lon, lat):
        return (x + (lon + 180.0) / 360.0 * w,
                y + (90.0 - lat) / 180.0 * h)

    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        draw.polygon(pts, fill=(207, 196, 174), outline=(184, 171, 144))
    for n, lat, lon in pins:
        px, py = proj(lon, lat)
        # nudge the two Geneva pins and the Jerusalem pin apart
        px += {10: -6, 11: -5, 15: 7}.get(n, 0)
        py += {10: 5, 11: -6, 15: 7}.get(n, 0)
        r = 6.5
        draw.ellipse([px - r, py - r, px + r, py + r], fill=RED,
                     outline=(255, 255, 255))
        fnt = font(SANS_B, 7.5)
        label = str(n)
        tw = draw.textlength(label, font=fnt)
        draw.text((px - tw / 2, py - 4.5), label, font=fnt,
                  fill=(255, 255, 255))


# ---------------------------------------------------------------- page
def render(data, out_path):
    global TRUNCATED
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # --- kicker ------------------------------------------------------
    draw.text((M, 10), data["kicker"], font=font(SANS_B, 11), fill=RED)
    meta = font(SANS, 10)
    mw = draw.textlength(data["kicker_meta"], font=meta)
    draw.text((W - M - mw, 11), data["kicker_meta"], font=meta, fill=GREY)

    # --- masthead = the date -----------------------------------------
    draw.text((M, 26), data["date"], font=font(SERIF_B, 54), fill=INK)
    draw.text((M, 90), data["masthead_sub"], font=font(SERIF_I, 16),
              fill=RED)
    draw.line([(M, 110), (W - M, 110)], fill=INK, width=2)

    # --- numbers strip ------------------------------------------------
    nums = data["numbers"]
    cell = CW / len(nums)
    for i, item in enumerate(nums):
        cx = M + i * cell
        vf = font(SERIF_B, 26)
        vw = draw.textlength(item["value"], font=vf)
        draw.text((cx + (cell - vw) / 2, 112), item["value"], font=vf,
                  fill=RED)
        lf = font(SANS, 9)
        lw = draw.textlength(item["label"], font=lf)
        draw.text((cx + (cell - lw) / 2, 140), item["label"], font=lf,
                  fill=INK)
        if i:
            draw.line([(cx, 114), (cx, 150)], fill=(200, 190, 175), width=1)

    # --- region colour bar (equal segments, counts shown) ------------
    regs = data["regions"]
    seg = CW / len(regs)
    for i, reg in enumerate(regs):
        rx = M + i * seg
        rw = seg if i < len(regs) - 1 else W - M - rx
        draw.rectangle([rx, 156, rx + rw, 176], fill=reg["color"])
        rf = font(SANS_B, 9.5)
        label = "%s · %d" % (reg["name"].upper(), reg["count"])
        lw = draw.textlength(label, font=rf)
        draw.text((rx + (rw - lw) / 2, 162), label, font=rf,
                  fill=(255, 255, 255))

    # --- dark UTC strip, two rows ------------------------------------
    draw.rectangle([M, 180, W - M, 212], fill=NAVY)
    title = data["utc_title"]
    tf = font(SANS_B, 9)
    draw.text((M + 8, 185), title, font=tf, fill=(252, 211, 77))
    tw = draw.textlength(title, font=tf)
    items = data["utc"]
    uf = font(SANS, 9)
    row1 = items[:3]
    row2 = items[3:]
    x = M + 8 + tw + 12
    for it in row1:
        draw.text((x, 185), it["time"], font=font(SANS_B, 9),
                  fill=(252, 211, 77))
        x += draw.textlength(it["time"], font=font(SANS_B, 9)) + 4
        draw.text((x, 185), it["event"], font=uf, fill=(255, 255, 255))
        x += draw.textlength(it["event"], font=uf) + 14
    x = M + 8
    for it in row2:
        draw.text((x, 199), it["time"], font=font(SANS_B, 9),
                  fill=(252, 211, 77))
        x += draw.textlength(it["time"], font=font(SANS_B, 9)) + 4
        draw.text((x, 199), it["event"], font=uf, fill=(255, 255, 255))
        x += draw.textlength(it["event"], font=uf) + 14

    # --- 3 big illustrated stories ----------------------------------
    big = data["big"]
    bw = (CW - 2 * 12) // 3
    y0 = 218
    for i, s in enumerate(big):
        bx = M + i * (bw + 12)
        y = y0
        y += topic_bar(draw, bx, y, bw, s["topic"], s["accent"])
        draw_scene(draw, bx, y, bw, 86, s["scene"], s["accent"])
        y += 86
        y += fact_bar(draw, bx, y, bw, s["fact"])
        y += location_tag(draw, bx, y, bw, s["n"], s["place"])
        y += 3
        y = text_block(draw, bx, y, s["headline"], font(SERIF_B, 20), bw, 2,
                       leading=23)
        y += 1
        y = text_block(draw, bx, y, s["summary"], font(SANS, 12.5), bw, 3,
                       leading=14)
        y += 2
        bw_chip = badge(draw, bx, y, s["badge"])
        sf = font(SANS, 9.5)
        draw.text((bx + bw_chip + 6, y + 1), s["source"], font=sf, fill=GREY)

    # --- 12 small illustrated stories, 4 x 3 -------------------------
    # Cell (110 px): red bar 10 + illustration 36 + headline 2 lines
    # + summary 2 lines + badge/source line on its own row, so nothing
    # ever overlaps the text above it.
    small = data["small"]
    sw = (CW - 3 * 10) // 4
    for i, s in enumerate(small):
        row, col = divmod(i, 4)
        sx = M + col * (sw + 10)
        sy = 460 + row * 110
        y = sy
        y += topic_bar(draw, sx, y, sw, s["topic"], s["accent"])
        draw_scene(draw, sx, y, sw, 36, s["scene"], s["accent"])
        y += 36
        y = text_block(draw, sx, y, "%d. %s" % (s["n"], s["headline"]),
                       font(SERIF_B, 11), sw, 2, leading=13)
        y = text_block(draw, sx, y, s["summary"], font(SANS, 9), sw, 2,
                       leading=11)
        bw_chip = badge(draw, sx, sy + 98, s["badge"], small=True)
        sf = font(SANS, 8)
        draw.text((sx + bw_chip + 5, sy + 99), s["source"], font=sf,
                  fill=GREY)

    # --- ALSO ON list + map -------------------------------------------
    ay = 798
    draw.text((M, ay), "ALSO ON MONDAY 23 NOVEMBER — 21 MORE STORIES",
              font=font(SANS_B, 11), fill=RED)
    draw.text((692, ay), "WHERE IT HAPPENED", font=font(SANS_B, 11), fill=RED)
    colw = 322
    for i, s in enumerate(data["also"]):
        col, r = divmod(i, 11)
        lx = M + col * (colw + 12)
        ly = 816 + r * 11.5
        nf = font(SANS_B, 9)
        pf = font(SANS_B, 9)
        sf = font(SANS, 9)
        num = "%d " % s["n"]
        place = "%s — " % s["place"]
        src = " · " + s["source"]
        fixed = (draw.textlength(num, font=nf)
                 + draw.textlength(place, font=pf)
                 + draw.textlength(src, font=sf))
        head = fit_one_line(s["headline"], font(SANS, 9),
                            colw - fixed, draw)
        x = lx
        draw.text((x, ly), num, font=nf, fill=RED)
        x += draw.textlength(num, font=nf)
        draw.text((x, ly), place, font=pf, fill=INK)
        x += draw.textlength(place, font=pf)
        draw.text((x, ly), head, font=font(SANS, 9), fill=INK)
        x += draw.textlength(head, font=font(SANS, 9))
        draw.text((x, ly), src, font=sf, fill=GREY)

    pins = [(s["n"], s["lat"], s["lon"]) for s in data["big"] + data["small"]]
    draw_map(draw, 692, 816, 308, 104, pins)
    draw.text((692, 924), "pins match story numbers 1–15",
              font=font(SANS, 8.5), fill=GREY)

    # --- DATE CHECK ----------------------------------------------------
    draw.rectangle([M, 946, W - M, 984], outline=RED, width=2)
    draw.text((M + 8, 955), "DATE CHECK", font=font(SANS_B, 10), fill=RED)
    dc = data["date_check"]
    prefix = "DATE CHECK — "
    body = dc[len(prefix):] if dc.startswith(prefix) else dc
    text_block(draw, M + 96, 950, body, font(SANS, 9.5), W - M - 96 - 8, 2,
               leading=12)

    # --- footer ---------------------------------------------------------
    text_block(draw, M, 990, data["footer"], font(SANS, 9), CW, 2,
               fill=GREY, leading=12)

    img.save(out_path, optimize=True)
    return img


def main():
    if len(sys.argv) != 3:
        print("usage: python3 render.py stories.json news.png",
              file=sys.stderr)
        return 2
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        data = json.load(fh)
    n_stories = len(data["big"]) + len(data["small"]) + len(data["also"])
    n_regions = len(data["regions"])
    region_total = sum(r["count"] for r in data["regions"])
    assert n_stories == 36, "expected 36 stories, got %d" % n_stories
    assert n_regions == 7, "expected 7 regions, got %d" % n_regions
    assert region_total == 36, "region counts sum to %d" % region_total
    assert len(data["numbers"]) == 6, "expected 6 numbers"
    assert len(data["utc"]) == 6, "expected 6 UTC items"
    render(data, sys.argv[2])
    size = os.path.getsize(sys.argv[2])
    print("wrote %s (%d bytes, 1024x1024)" % (sys.argv[2], size))
    print("stories=%d regions=%d TRUNCATED=%d" % (n_stories, n_regions,
                                                   TRUNCATED))
    if size > 1024 * 1024:
        print("ERROR: image over 1 MiB", file=sys.stderr)
        return 1
    if TRUNCATED:
        print("ERROR: %d truncated text(s)" % TRUNCATED, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
