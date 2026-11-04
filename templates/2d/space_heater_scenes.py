"""电暖器分集 · 纪录片手绘风 2D。油汀加热空气，小太阳的红外线先烤到人和物。"""

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
HOT = (195, 90, 55)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (214, 216, 220)
OIL = (92, 62, 36)
YELLOW = (232, 176, 64)
SKIN = (232, 196, 174)


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


def _heater(d, cx, cy, *, scale=1.0, ts=0.0, mode="oil", heat=0.8, caption="", sealed=0.0):
    """oil 是密封油汀，sun 是带反射罩的小太阳。油不燃烧。"""
    s = scale
    if mode == "oil":
        d.rounded_rectangle((cx - 150 * s, cy + 124 * s, cx + 150 * s, cy + 176 * s), radius=10 * s, fill=METAL_DK, outline=INK, width=3)
        element = (cx + 78 * s, cy + 150 * s)
        d.rounded_rectangle((cx - 100 * s, cy + 136 * s, cx + 100 * s, cy + 162 * s), radius=4 * s, fill=HOT if heat > 0.35 else METAL, outline=INK, width=2)
        for i in range(5):
            x0 = cx - 132 * s + i * 54 * s
            d.rounded_rectangle((x0, cy - 150 * s, x0 + 40 * s, cy + 124 * s), radius=8 * s, fill=_mix((186, 188, 192), HOT, 0.42 * heat), outline=INK, width=2)
        oil = (cx + 4 * s, cy + 12 * s)
        d.rounded_rectangle((cx - 16 * s, cy - 18 * s, cx + 20 * s, cy + 42 * s), radius=6 * s, fill=OIL, outline=INK, width=2)
        d.arc((cx - 8 * s, cy - 2 * s, cx + 14 * s, cy + 28 * s), 40, 320, fill=WHITE, width=2)
        if sealed > 0.5:
            d.ellipse((cx - 34 * s, cy - 36 * s, cx + 38 * s, cy + 58 * s), outline=OIL, width=max(2, int(3 * s)))
        fin = (cx + 122 * s, cy - 90 * s)
        if heat > 0.35 and sealed < 0.5:
            for i in range(4):
                u = (ts * 0.55 + i / 4) % 1
                x = cx - 90 * s + i * 56 * s
                y = _lerp(cy - 16 * s, cy - 214 * s, u)
                d.polygon([(x, y), (x + 16 * s, y), (x + 8 * s, y - 18 * s)], fill=HOT)
        tube = element
        shade = fin
        person = (cx, cy - 190 * s)
    else:
        d.rounded_rectangle((cx - 70 * s, cy + 112 * s, cx + 96 * s, cy + 160 * s), radius=8 * s, fill=METAL_DK, outline=INK, width=2)
        d.polygon(
            [(cx - 36 * s, cy - 96 * s), (cx + 48 * s, cy - 132 * s), (cx + 48 * s, cy + 118 * s), (cx - 36 * s, cy + 86 * s)],
            fill=METAL,
            outline=INK,
        )
        shade = (cx - 20 * s, cy - 20 * s)
        d.rounded_rectangle((cx + 58 * s, cy - 74 * s, cx + 86 * s, cy + 82 * s), radius=12 * s, fill=YELLOW if heat > 0.35 else METAL, outline=INK, width=2)
        tube = (cx + 72 * s, cy)
        px = cx + 196 * s
        person = (px, cy - 8 * s)
        d.ellipse((px - 16 * s, cy - 58 * s, px + 16 * s, cy - 26 * s), fill=SKIN, outline=INK, width=2)
        d.line((px, cy - 26 * s, px, cy + 52 * s), fill=INK, width=max(2, int(4 * s)))
        d.line((px, cy - 2 * s, px - 24 * s, cy + 18 * s), fill=INK, width=2)
        d.line((px, cy - 2 * s, px + 22 * s, cy + 10 * s), fill=INK, width=2)
        if heat > 0.35:
            for i in range(4):
                y0 = cy - 48 * s + i * 28 * s
                d.line((cx + 86 * s, y0, px - 22 * s, cy - 28 * s + i * 14 * s), fill=YELLOW, width=2)
        element = tube
        oil = tube
        fin = person
    if caption and s >= 0.55:
        d.text((cx, cy + 198 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
    return {"element": element, "oil": oil, "fin": fin, "tube": tube, "shade": shade, "person": person}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=HOT if active else WHITE, outline=HOT, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else HOT, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=HOT, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 3401).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：电暖器怎样让房间变暖", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        y = int(1020 + (1 - show) * 12)
        _heater(d, 300 + dx, y, scale=0.66, ts=time_sec, mode="oil", caption="油汀")
        _heater(d, 790 + dx, y, scale=0.66, ts=time_sec, mode="sun", caption="小太阳")
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是油汀里的油在烧", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  油汀暖空气，小太阳烤人", font=FONT_L, fill=HOT, anchor="mm")
            d.text((540, 1660), "油不燃烧，只负责把热传出去", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3403).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：导热油和红外线", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        oil = _heater(d, 300, 900, scale=0.7, ts=time_sec, mode="oil", caption="油汀")
        sun = _heater(d, 790, 900, scale=0.7, ts=time_sec, mode="sun", caption="小太阳")
        if t > 0.18:
            _callout(d, oil["element"], (oil["element"][0] - 150, oil["element"][1] + 28), "电热管", HOT, _spring(t, 0.18, 0.2), anchor="rm")
        if t > 0.36:
            _callout(d, oil["oil"], (oil["oil"][0] - 150, oil["oil"][1] - 16), "导热油", OIL, _spring(t, 0.36, 0.2), anchor="rm")
        if t > 0.54:
            _callout(d, sun["tube"], (min(1020, sun["tube"][0] + 20), sun["tube"][1] - 70), "灯管", YELLOW, _spring(t, 0.54, 0.2))
        if t > 0.72:
            _callout(d, sun["shade"], (sun["shade"][0] - 20, sun["shade"][1] - 80), "反射罩", INK, _spring(t, 0.72, 0.2), anchor="rm")
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "油把热带到散热片，空气自己上升", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "红外线先打到人和家具，不靠发光本身", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3407).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "热怎样进到房间", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _heater(
        d,
        540,
        680,
        scale=0.78,
        ts=time_sec,
        mode="sun" if active >= 3 else "oil",
        heat=0.2 if active < 1 else 0.92,
    )
    steps = ["选路", "发热", "对流", "辐射"]
    tips = [
        "① 先看是油汀，还是小太阳",
        "② 电热管通电，开始发热",
        "③ 油把散热片烤热，空气上升",
        "④ 红外线打到人和附近的家具",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "一个暖空气，一个烤人和物", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3409).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(mode="oil", heat=0.9), "为什么不发红也会暖？", "热空气贴着散热片往上走"),
        (0.32, dict(mode="sun", heat=0.9), "为什么对着才觉得暖？", "红外线差不多走直线"),
        (0.55, dict(mode="oil", heat=0.45, sealed=1), "为什么油不会越用越少？", "油被封住，只负责传热"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _heater(d, 540, y + 250, scale=0.36, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "油汀加热空气，小太阳烤到人和物", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3411).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    y = int(700 + (1 - a) * 12)
    _heater(d, 300, y, scale=0.58, ts=time_sec, mode="oil", caption="油汀")
    _heater(d, 780, y, scale=0.58, ts=time_sec, mode="sun", caption="小太阳")
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "油汀先加热空气", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "小太阳先烤到人和物", font=FONT_L, fill=HOT, anchor="mm")
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
