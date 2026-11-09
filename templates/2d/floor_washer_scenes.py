"""洗地机分集 · 纪录片手绘风 2D。清水只送到滚刷，脏水被吸进另一只污水箱。"""

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
BODY = (214, 216, 220)
WATER = (72, 164, 204)
DIRTY = (122, 92, 58)
TEAL = (32, 128, 122)
HAIR = (74, 60, 48)
CARPET = (196, 174, 138)


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


def _drop(d, x, y, s, color):
    r = max(2.0, 4 * s)
    d.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=INK, width=1)


def _washer(d, cx, cy, *, scale=1.0, ts=0.0, mode="wash", flow=0.8, dirty=0.45, suction=1.0, hair=0.0, caption=""):
    """清水箱在后，污水箱在旁。滚刷只擦，吸缝把脏水抽走。"""
    s = scale
    fy = cy + 168 * s
    if mode == "carpet":
        d.rectangle((cx - 230 * s, fy, cx + 230 * s, fy + 28 * s), fill=CARPET, outline=INK, width=2)
        if flow > 0.3:
            d.rectangle((cx - 30 * s, fy, cx + 80 * s, fy + 28 * s), fill=_mix(CARPET, WATER, 0.55))
        for i in range(9):
            x = cx - 200 * s + i * 46 * s
            d.line((x, fy + 4 * s, x + 12 * s, fy + 24 * s), fill=(150, 124, 86), width=2)
    else:
        d.line((cx - 250 * s, fy, cx + 250 * s, fy), fill=INK, width=max(2, int(4 * s)))
        if suction < 0.35 and flow > 0.3:
            d.ellipse((cx - 16 * s, fy - 10 * s, cx + 124 * s, fy + 16 * s), fill=WATER, outline=INK, width=2)

    _rr(d, (cx - 70 * s, cy - 150 * s, cx + 74 * s, cy + 78 * s), 16 * s, fill=BODY, outline=INK, width=3)
    d.line((cx + 4 * s, cy - 150 * s, cx + 4 * s, cy - 230 * s), fill=INK, width=max(3, int(6 * s)))
    _rr(d, (cx - 36 * s, cy - 258 * s, cx + 46 * s, cy - 226 * s), 8 * s, fill=METAL, outline=INK, width=2)

    _rr(d, (cx - 148 * s, cy - 120 * s, cx - 70 * s, cy + 8 * s), 8 * s, fill=WATER, outline=INK, width=2)
    d.rectangle((cx - 138 * s, cy - 78 * s, cx - 80 * s, cy - 2 * s), fill=_mix(WATER, WHITE, 0.35))
    clean = (cx - 109 * s, cy - 124 * s)

    _rr(d, (cx + 74 * s, cy - 96 * s, cx + 158 * s, cy + 36 * s), 8 * s, fill=WHITE, outline=INK, width=2)
    level = _clamp01(dirty)
    if level > 0.04:
        top = _lerp(cy + 24 * s, cy - 84 * s, level)
        d.rectangle((cx + 82 * s, top, cx + 150 * s, cy + 26 * s), fill=DIRTY)
    dirty_pt = (cx + 116 * s, cy - 100 * s)

    _rr(d, (cx - 108 * s, cy + 70 * s, cx + 128 * s, cy + 150 * s), 12 * s, fill=METAL_DK, outline=INK, width=3)
    rx, ry, rr = cx - 10 * s, cy + 118 * s, 28 * s
    d.ellipse((rx - rr, ry - rr, rx + rr, ry + rr), fill=(58, 64, 72), outline=INK, width=2)
    ang = ts * 8
    for k in range(4):
        a = ang + k * math.pi / 2
        d.line((rx, ry, rx + math.cos(a) * rr * 0.85, ry + math.sin(a) * rr * 0.85), fill=WHITE, width=2)
    roller = (rx, ry)
    if hair > 0.4:
        d.arc((rx - 18 * s, ry - 48 * s, rx + 6 * s, ry - 8 * s), 200, 30, fill=HAIR, width=3)
        d.arc((rx + 2 * s, ry - 42 * s, rx + 30 * s, ry - 4 * s), 210, 10, fill=HAIR, width=2)

    d.line((cx + 78 * s, cy + 96 * s, cx + 98 * s, fy), fill=INK, width=max(2, int(4 * s)))
    suction_pt = (cx + 88 * s, cy + 112 * s)
    d.line((cx + 40 * s, cy + 78 * s, cx + 78 * s, cy + 6 * s), fill=METAL, width=max(3, int(7 * s)))

    if flow > 0.15:
        for i in range(3):
            u = (ts * 1.3 + i / 3.0) % 1.0
            _drop(d, _lerp(cx - 90 * s, rx, u), _lerp(cy - 20 * s, ry - rr, u), s, WATER)
    if suction > 0.4:
        for i in range(3):
            u = (ts * 1.1 + i / 3.0) % 1.0
            _drop(d, _lerp(suction_pt[0], dirty_pt[0] - 8 * s, u), _lerp(suction_pt[1], cy + 10 * s, u), s, DIRTY)
    if caption and s >= 0.55:
        d.text((cx, fy + 46 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
    return {"clean": clean, "roller": roller, "suction": suction_pt, "dirty": dirty_pt}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=TEAL if active else WHITE, outline=TEAL, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else TEAL, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=TEAL, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 3801).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：洗地机怎样不把脏水涂回去", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _washer(d, 520 + dx, int(980 + (1 - show) * 12), scale=0.62, ts=time_sec, dirty=0.55, caption="清水擦，脏水收回")
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是把脏水存在刷里", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  清水去擦，脏水另进一箱", font=FONT_L, fill=TEAL, anchor="mm")
            d.text((540, 1660), "刷负责擦，吸负责收", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3803).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：清水箱、滚刷、污水箱", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _washer(d, 500, 900, scale=0.7, ts=time_sec, dirty=0.6)
        if t > 0.18:
            _callout(d, parts["clean"], (parts["clean"][0] - 20, parts["clean"][1] - 36), "清水", WATER, _spring(t, 0.18, 0.2), anchor="rm")
        if t > 0.36:
            _callout(d, parts["roller"], (parts["roller"][0] - 150, parts["roller"][1] + 10), "滚刷", INK, _spring(t, 0.36, 0.2), anchor="rm")
        if t > 0.54:
            _callout(d, parts["suction"], (min(1020, parts["suction"][0] + 20), parts["suction"][1] + 36), "刮条", ACCENT, _spring(t, 0.54, 0.2))
        if t > 0.72:
            _callout(d, parts["dirty"], (min(1040, parts["dirty"][0] + 8), parts["dirty"][1] - 28), "污水", DIRTY, _spring(t, 0.72, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "水泵只送清水，脏水进另一只箱", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "刮条贴地，吸缝才收得走水", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3807).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "脏水怎样被收走", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _washer(
        d,
        520,
        700,
        scale=0.64,
        ts=time_sec,
        flow=0.35 if active <= 0 else 0.9,
        suction=0.1 if active < 2 else 1,
        dirty=0.12 if active < 2 else (0.48 if active == 2 else 0.86),
    )
    steps = ["出水", "搅开", "吸入", "留下"]
    tips = [
        "① 清水被小水泵送到滚刷",
        "② 滚刷把污渍搅进水里",
        "③ 刮条赶水，吸缝把脏水抽走",
        "④ 污水留在箱里，不再涂回去",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "没有吸力，滚刷就只是在涂", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3809).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(hair=1, dirty=0.92, suction=1, flow=0.4), "为什么拖完还有脏水味？", "污水和头发留在箱里、刷上"),
        (0.32, dict(suction=0, flow=1, dirty=0.2), "为什么地面会留下水痕？", "出水比吸回多，刮条没贴住"),
        (0.55, dict(mode="carpet", suction=0.15, flow=0.85, dirty=0.15), "为什么不适合洗地毯？", "水渗进纤维，吸缝收不回"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _washer(d, 540, y + 250, scale=0.34, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "清水去擦，脏水进另一只箱", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3811).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _washer(d, 520, int(700 + (1 - a) * 12), scale=0.6, ts=time_sec, dirty=0.7)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "滚刷只负责擦", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "脏水吸进污水箱", font=FONT_L, fill=TEAL, anchor="mm")
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
