"""电视分集 · 纪录片手绘风 2D。液晶自己不发光，它决定背后的光过还是挡住。"""

from __future__ import annotations

import math
import random
from typing import Callable

from PIL import Image, ImageDraw

from pipeline.fonts import load_cjk_font as _font

PAPER = (248, 245, 238)
WALL = (242, 238, 230)
FLOOR = (218, 214, 206)
INK = (38, 36, 34)
MUTED = (110, 105, 98)
ACCENT = (180, 75, 45)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
RED = (196, 72, 64)
GREEN = (52, 146, 96)
BLUE = (56, 108, 186)
GLOW = (255, 214, 120)
SCREEN = (28, 30, 34)


FONT_HERO, FONT_L, FONT_M, FONT_S, FONT_XS = _font(62, True), _font(44, True), _font(34), _font(28), _font(24)


def _clamp01(t):
    return max(0.0, min(1.0, t))


def _ease(t):
    t = _clamp01(t)
    return t * t * (3 - 2 * t)


def _spring(t, s=0.0, d=0.3):
    if t < s:
        return 0.0
    p = _clamp01((t - s) / d)
    return 1 - math.exp(-6 * p) * math.cos(p * math.pi * 2.5)


def _lerp(a, b, t):
    return a + (b - a) * _clamp01(t)


def _mix(a, b, t):
    t = _clamp01(t)
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _scene_t(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    return (t - a) / (b - a)


def _pulse(ts, sp=2.5, lo=0.85, hi=1.0):
    return lo + (hi - lo) * (0.5 + 0.5 * math.sin(ts * sp * math.tau))


def _wobble(x, y, seed, amp=1.2):
    return x + math.sin(seed * 1.7) * amp, y + math.cos(seed * 2.3) * amp


def _cam_drift(ts, ax=5.0, ay=3.0):
    return math.sin(ts * 0.7) * ax, math.cos(ts * 0.55) * ay


def _paper_bg(w, h, seed=7):
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, int(h * 0.62)), fill=WALL)
    d.rectangle((0, int(h * 0.62), w, h), fill=FLOOR)
    d.line((0, int(h * 0.62), w, int(h * 0.62)), fill=LINE, width=2)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(int(w * h * 0.008)):
        x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
        r, g, b = px[x, y]
        n = rng.randint(-5, 5)
        px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    return img


def _sketch_line(d, p1, p2, color=INK, width=2, seed=0):
    x1, y1 = p1
    x2, y2 = p2
    steps = max(int(math.hypot(x2 - x1, y2 - y1) / 12), 2)
    pts = []
    for i in range(steps + 1):
        f = i / steps
        pts.append(_wobble(_lerp(x1, x2, f), _lerp(y1, y2, f), seed + i, 0.8))
    for i in range(len(pts) - 1):
        d.line((pts[i], pts[i + 1]), fill=color, width=width)


def _callout(d, tip, label, text, color=INK, alpha=1.0, anchor="lm"):
    if alpha <= 0.01:
        return
    _sketch_line(d, tip, label, color, 2, int(tip[0] + tip[1]))
    d.ellipse((tip[0] - 5, tip[1] - 5, tip[0] + 5, tip[1] + 5), fill=color)
    d.text(label, text, font=FONT_S, fill=(*color, int(255 * _clamp01(alpha))), anchor=anchor)


def _fade_text(d, xy, text, font, color, alpha, anchor="mm", dy=0.0):
    if alpha <= 0.01:
        return
    d.text((xy[0], xy[1] + dy), text, font=font, fill=(*color, int(255 * _clamp01(alpha))), anchor=anchor)


def _ken_badge(d, y, alpha=1.0, scale=1.0):
    if alpha <= 0:
        return
    a = int(255 * _clamp01(alpha))
    bw = int(400 * scale)
    d.rounded_rectangle((540 - bw // 2, y - 36, 540 + bw // 2, y + 36), radius=18, fill=(255, 253, 248, a), outline=ACCENT, width=2)
    d.text((540, y), "身边原理 · Ken", font=FONT_S, fill=(*ACCENT, a), anchor="mm")


def _rr(d, box, radius, **kw):
    x0, y0, x1, y1 = box
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    rad = min(float(radius), max(0.0, (x1 - x0) / 2 - 0.8), max(0.0, (y1 - y0) / 2 - 0.8))
    if rad < 1 or (x1 - x0) < 2 or (y1 - y0) < 2:
        d.rectangle((x0, y0, x1, y1), **kw)
        return
    d.rounded_rectangle((x0, y0, x1, y1), radius=rad, **kw)


def _eye(d, x, y, s):
    d.ellipse((x - 16 * s, y - 22 * s, x + 16 * s, y + 10 * s), fill=(232, 196, 174), outline=INK, width=2)
    d.ellipse((x - 10 * s, y - 8 * s, x + 10 * s, y + 8 * s), fill=WHITE, outline=INK, width=2)
    d.ellipse((x - 4 * s, y - 4 * s, x + 4 * s, y + 4 * s), fill=INK)


def _front(d, cx, cy, s, wash=0.0, oled=0.0):
    _rr(d, (cx - 168 * s, cy - 108 * s, cx + 168 * s, cy + 112 * s), 12 * s, fill=SCREEN, outline=INK, width=3)
    cols = (RED, GREEN, BLUE)
    for r in range(4):
        for c in range(8):
            black = oled > 0.5 and (r + c) % 4 == 0
            col = (12, 12, 14) if black else cols[c % 3]
            if wash > 0.05 and not black:
                col = _mix(col, (176, 176, 176), wash)
            x = cx - 140 * s + c * 34 * s
            y = cy - 78 * s + r * 40 * s
            d.rectangle((x, y, x + 26 * s, y + 30 * s), fill=col)
    d.rectangle((cx - 18 * s, cy + 112 * s, cx + 18 * s, cy + 156 * s), fill=METAL_DK)
    d.ellipse((cx - 52 * s, cy + 146 * s, cx + 52 * s, cy + 168 * s), fill=METAL_DK, outline=INK, width=2)
    return (cx, cy - 108 * s)


def _layers(d, cx, cy, s, open_amt, oled=0.0):
    if oled > 0.5:
        light = (cx - 70 * s, cy)
        cols = (RED, GREEN, BLUE, (12, 12, 14))
        for r in range(4):
            for c in range(4):
                col = cols[(r + c) % 4]
                x = cx - 90 * s + c * 42 * s
                y = cy - 70 * s + r * 36 * s
                d.rectangle((x, y, x + 32 * s, y + 28 * s), fill=col, outline=INK, width=1)
        crystal = (cx, cy)
        color = (cx + 40 * s, cy)
    else:
        d.rectangle((cx - 150 * s, cy - 70 * s, cx - 78 * s, cy + 70 * s), fill=GLOW, outline=INK, width=2)
        for i in range(4):
            d.ellipse((cx - 138 * s, cy - 52 * s + i * 28 * s, cx - 118 * s, cy - 34 * s + i * 28 * s), fill=WHITE)
        light = (cx - 114 * s, cy)
        ang = _lerp(1.15, 0.25, open_amt)
        for i in range(7):
            y = cy - 60 * s + i * 18 * s
            x2 = cx - 20 * s + math.cos(ang) * 34 * s
            y2 = y + math.sin(ang) * 10 * s
            d.line((cx - 48 * s, y, x2, y2), fill=(186, 198, 196), width=max(3, int(5 * s)))
        crystal = (cx - 20 * s, cy)
        cols = (RED, GREEN, BLUE)
        for i in range(6):
            y = cy - 66 * s + i * 22 * s
            d.rectangle((cx + 28 * s, y, cx + 62 * s, y + 18 * s), fill=cols[i % 3], outline=INK, width=1)
        color = (cx + 45 * s, cy)
    eye = (cx + 130 * s, cy - 6 * s)
    _eye(d, eye[0], eye[1], s)
    return {"light": light, "crystal": crystal, "color": color, "eye": eye}


def _tv(d, cx, cy, *, scale=1.0, ts=0.0, mode="front", open_amt=0.7, wash=0.0, caption=""):
    """front 是整机。lcd / oled 是从灯到眼睛的剖面。"""
    s = scale
    if mode == "front":
        top = _front(d, cx, cy, s, wash=wash, oled=0)
        parts = {"light": (cx - 40 * s, cy), "crystal": (cx, cy), "color": (cx + 40 * s, cy), "eye": (cx + 150 * s, cy)}
        anchor = top
    elif mode == "angle":
        _front(d, cx - 30 * s, cy, s, wash=0.55, oled=0)
        _eye(d, cx + 150 * s, cy + 70 * s, s * 1.1)
        parts = {"light": (cx - 70 * s, cy), "crystal": (cx, cy), "color": (cx + 30 * s, cy), "eye": (cx + 150 * s, cy + 70 * s)}
        anchor = (cx, cy - 80 * s)
    else:
        parts = _layers(d, cx, cy, s, open_amt, oled=1 if mode == "oled" else 0)
        anchor = parts["light"]
    if caption and s >= 0.55:
        d.text((cx, cy + 190 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
    parts["top"] = anchor
    return parts


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=BLUE if active else WHITE, outline=BLUE, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else BLUE, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=BLUE, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 4201).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：电视怎样自己亮出画面", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _tv(d, 520 + dx, int(980 + (1 - show) * 12), scale=0.85, ts=time_sec, mode="front", caption="光从屏幕出来")
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是把光打到墙上", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  液晶放行背后的光", font=FONT_L, fill=BLUE, anchor="mm")
            d.text((540, 1660), "墙不接这束光，光直接进眼睛", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4203).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：背光、液晶和滤色片", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _tv(d, 500, 900, scale=0.95, ts=time_sec, mode="lcd", open_amt=0.72)
        if t > 0.18:
            _callout(d, parts["light"], (parts["light"][0] - 40, parts["light"][1] - 110), "背光", (186, 140, 48), _spring(t, 0.18, 0.2), anchor="mm")
        if t > 0.36:
            _callout(d, parts["crystal"], (parts["crystal"][0] + 8, parts["crystal"][1] + 86), "液晶", INK, _spring(t, 0.36, 0.2), anchor="mm")
        if t > 0.54:
            _callout(d, parts["color"], (min(1000, parts["color"][0] + 20), parts["color"][1] - 100), "滤色", RED, _spring(t, 0.54, 0.2))
        if t > 0.72:
            _callout(d, parts["eye"], (min(1040, parts["eye"][0] + 10), parts["eye"][1] - 40), "眼睛", INK, _spring(t, 0.72, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "液晶自己不发光", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "红、绿、蓝三个小点，合成一个彩色点", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4207).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "一个亮点怎样出现", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _tv(
        d,
        520,
        760,
        scale=0.85,
        ts=time_sec,
        mode="oled" if active >= 3 else "lcd",
        open_amt=0.15 if active <= 0 else (0.55 if active == 1 else 0.9),
    )
    steps = ["背光", "放行", "上色", "入眼"]
    tips = [
        "① 背后的灯先把光打出来",
        "② 液晶决定这一点过不过",
        "③ 滤色片把通过的光变成彩色",
        "④ 自发光的屏，黑就是这个点没亮",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "墙没有接住这束光", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4209).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(mode="lcd", open_amt=0.12), "为什么液晶的黑看起来发灰？", "背光还亮着，这一层挡不严"),
        (0.32, dict(mode="oled"), "为什么有的屏黑得更干净？", "小点自己发光，要黑就关掉"),
        (0.55, dict(mode="angle"), "为什么侧着看容易发灰？", "液晶和滤色片对着正前方"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _tv(d, 540, y + 230, scale=0.42, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "液晶放行背光，有的点自己发光", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4211).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _tv(d, 520, int(700 + (1 - a) * 12), scale=0.8, ts=time_sec, mode="lcd", open_amt=0.75)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "液晶自己不发光", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "它决定光过还是挡住", font=FONT_L, fill=BLUE, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1520, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1600), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1670), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1760),
            "评论区：还想拆哪一件？",
            font=FONT_S,
            fill=(*MUTED, int(255 * (0.6 + 0.4 * _pulse(time_sec, 2)))),
            anchor="mm",
        )
    return img.convert("RGB")


SCENE_DRAWERS: dict[str, Callable[..., Image.Image]] = {
    "hook": draw_hook,
    "cutaway": draw_cutaway,
    "cycle": draw_cycle,
    "analogy": draw_analogy,
    "outro": draw_outro,
}


def draw_scene(scene_name, t, width=1080, height=1920, *, time_sec=None):
    ts = time_sec if time_sec is not None else t * 120.0
    return SCENE_DRAWERS.get(scene_name, draw_hook)(_clamp01(t), width, height, ts)
