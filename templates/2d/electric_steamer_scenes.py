"""电蒸锅分集 · 纪录片手绘风 2D。蒸汽在食物上变回水，把热交出去。"""

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
POT = (232, 236, 240)
WATER = (96, 168, 206)
FOOD = (214, 164, 72)
HEAT = (198, 92, 52)


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


def _puffs(d, x, y, s, ts, n=4, alpha=1.0):
    if alpha <= 0.02:
        return
    for i in range(n):
        ph = (ts * 0.55 + i * 0.23) % 1.0
        yy = y - ph * 86 * s
        xx = x + math.sin(ts * 1.6 + i * 1.7) * 14 * s
        r = (5 + ph * 9) * s * alpha
        if r < 2:
            continue
        d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=(214, 228, 234), outline=(150, 176, 188), width=2)


def _pot(d, cx, cy, *, scale=1.0, ts=0.0, boil=0.8, dry=0.0, caption=""):
    """水在下面烧开。蒸汽穿过蒸格，在食物上变回水。"""
    s = scale
    _rr(d, (cx - 150 * s, cy - 36 * s, cx + 150 * s, cy + 168 * s), 18 * s, fill=POT, outline=INK, width=3)
    plate = (210, 64, 46) if dry > 0.5 else (HEAT if boil > 0.25 else METAL)
    d.rectangle((cx - 118 * s, cy + 118 * s, cx + 118 * s, cy + 146 * s), fill=plate, outline=INK, width=2)
    heat = (cx, cy + 132 * s)
    water_pt = (cx - 80 * s, cy + 96 * s)
    if dry < 0.5:
        d.rectangle((cx - 128 * s, cy + 78 * s, cx + 128 * s, cy + 118 * s), fill=WATER)
        if boil > 0.35:
            _puffs(d, cx, cy + 74 * s, s, ts, n=3, alpha=0.7)
    holes = (cx - 40 * s, cy + 48 * s)
    _rr(d, (cx - 112 * s, cy - 8 * s, cx + 112 * s, cy + 78 * s), 8 * s, fill=WHITE, outline=INK, width=2)
    for i in range(4):
        hx = cx - 78 * s + i * 42 * s
        d.ellipse((hx, cy + 40 * s, hx + 14 * s, cy + 54 * s), fill=WATER if boil > 0.45 and dry < 0.5 else LINE, outline=INK, width=1)
    food = (cx, cy + 16 * s)
    _rr(d, (cx - 40 * s, cy - 2 * s, cx + 40 * s, cy + 32 * s), 6 * s, fill=FOOD, outline=INK, width=2)
    if boil > 0.45 and dry < 0.5:
        for i in range(3):
            dx = cx - 18 * s + i * 16 * s
            d.ellipse((dx, cy + 2 * s, dx + 6 * s, cy + 8 * s), fill=WATER)
        _puffs(d, cx, cy - 8 * s, s, ts + 0.3, n=3)
    d.polygon(
        [(cx - 136 * s, cy - 24 * s), (cx + 136 * s, cy - 24 * s), (cx + 96 * s, cy - 86 * s), (cx - 96 * s, cy - 86 * s)],
        fill=(236, 240, 244),
        outline=INK,
    )
    d.rectangle((cx + 78 * s, cy - 78 * s, cx + 108 * s, cy - 30 * s), fill=PAPER)
    vent = (cx + 92 * s, cy - 58 * s)
    if boil > 0.4 and dry < 0.5:
        _puffs(d, vent[0], vent[1], s * 0.85, ts + 0.15, n=3)
    if dry > 0.5 and s >= 0.55:
        d.text((cx, cy + 96 * s), "干烧", font=FONT_XS, fill=ACCENT, anchor="mm")
    if caption and s >= 0.55:
        d.text((cx, cy + 214 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
    return {"heat": heat, "water": water_pt, "holes": holes, "food": food, "vent": vent}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=HEAT if active else WHITE, outline=HEAT, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else HEAT, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=HEAT, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 4301).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：电蒸锅怎样把食物蒸熟", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _pot(d, 520 + dx, int(860 + (1 - show) * 12), scale=0.78, ts=time_sec, boil=0.9, caption="蒸汽往上走")
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是盖上就变成压力锅", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  蒸汽变回水时交出热", font=FONT_L, fill=WATER, anchor="mm")
            d.text((540, 1660), "盖子留缝，锅里不加压", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4303).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：加热盘、蒸格和盖缝", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _pot(d, 520, 820, scale=0.95, ts=time_sec, boil=0.85)
        if t > 0.18:
            _callout(d, parts["heat"], (parts["heat"][0] - 40, parts["heat"][1] + 70), "加热盘", HEAT, _spring(t, 0.18, 0.2), anchor="mm")
        if t > 0.36:
            _callout(d, parts["water"], (140, parts["water"][1]), "水", WATER, _spring(t, 0.36, 0.2), anchor="rm")
        if t > 0.54:
            _callout(d, parts["holes"], (parts["holes"][0] - 20, parts["holes"][1] + 80), "小孔", INK, _spring(t, 0.54, 0.2), anchor="mm")
        if t > 0.72:
            _callout(d, parts["vent"], (min(980, parts["vent"][0] + 30), parts["vent"][1] - 40), "盖缝", ACCENT, _spring(t, 0.72, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "食物在水的上面", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "蒸汽变回水，这个变回叫凝结", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4307).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "食物怎样被蒸汽蒸熟", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _pot(d, 520, 720, scale=0.82, ts=time_sec, boil=0.2 if active <= 0 else 0.95)
    steps = ["烧开", "上孔", "变水", "离缝"]
    tips = [
        "① 加热盘先把水烧开",
        "② 蒸汽从蒸格的孔往上走",
        "③ 蒸汽变回水，热交出来",
        "④ 多余蒸汽从盖缝离开",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "锅里没有被加压到更高", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4309).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(boil=0.9, dry=0.0), "为什么蒸好的表面是湿的？", "蒸汽在食物上变回了水"),
        (0.32, dict(boil=0.7, dry=0.0), "为什么通常比压力锅慢？", "盖缝开着，停在烧开附近"),
        (0.55, dict(boil=0.0, dry=1.0), "为什么水干了会自己停？", "盘底变烫，开关断开干烧"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _pot(d, 540, y + 240, scale=0.42, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "蒸汽上来变成水，热交给食物", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4311).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _pot(d, 520, int(640 + (1 - a) * 12), scale=0.78, ts=time_sec, boil=0.9)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "电蒸锅不加压", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "变回水时，把热交出去", font=FONT_L, fill=WATER, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1520, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1600), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1670), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1760),
            "评论区：冲牙器，还是换个别的？",
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
