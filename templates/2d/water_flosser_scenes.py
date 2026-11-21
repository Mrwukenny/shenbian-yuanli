"""冲牙器分集 · 纪录片手绘风 2D。水泵把水一股股推出，够得着才冲得走。"""

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
WATER = (72, 156, 204)
TOOTH = (244, 240, 230)
BODY = (226, 234, 238)


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


def _teeth(d, cx, cy, s, gap):
    gw = max(6 * s, (10 + 22 * gap) * s)
    _rr(d, (cx - 78 * s, cy - 30 * s, cx - gw / 2, cy + 40 * s), 10 * s, fill=TOOTH, outline=INK, width=2)
    _rr(d, (cx + gw / 2, cy - 30 * s, cx + 78 * s, cy + 40 * s), 10 * s, fill=TOOTH, outline=INK, width=2)
    return (cx, cy + 4 * s)


def _flosser(d, cx, cy, *, scale=1.0, ts=0.0, power=0.65, gap=1.0, splash=0.0, empty=0.0, caption=""):
    """水泵一下一下把水推出细喷嘴。更窄的缝，水过不去。"""
    s = scale
    _rr(d, (cx - 78 * s, cy + 10 * s, cx + 78 * s, cy + 168 * s), 14 * s, fill=BODY, outline=INK, width=3)
    if empty < 0.5:
        d.rectangle((cx - 58 * s, cy + 78 * s, cx + 58 * s, cy + 150 * s), fill=WATER)
    tank = (cx, cy + 110 * s)
    phase = (math.sin(ts * 9) + 1) / 2
    py = cy + 28 * s + phase * 22 * s
    _rr(d, (cx - 30 * s, py - 16 * s, cx + 30 * s, py + 16 * s), 6 * s, fill=METAL, outline=INK, width=2)
    pump = (cx, py)
    d.line((cx, cy + 10 * s, cx, cy - 70 * s), fill=METAL_DK, width=max(6, int(10 * s)))
    d.line((cx, cy - 70 * s, cx + 86 * s, cy - 128 * s), fill=METAL_DK, width=max(5, int(8 * s)))
    nozzle = (cx + 86 * s, cy - 128 * s)
    d.ellipse((nozzle[0] - 8 * s, nozzle[1] - 8 * s, nozzle[0] + 8 * s, nozzle[1] + 8 * s), fill=METAL, outline=INK, width=2)
    gap_pt = (cx + 168 * s, cy - 132 * s)
    if s >= 0.34:
        gap_pt = _teeth(d, cx + 168 * s, cy - 132 * s, s * 0.95, gap)
    if power > 0.05 and empty < 0.5:
        for i in range(4):
            ph = (ts * 1.5 + i / 4) % 1.0
            if gap < 0.35 and ph > 0.7:
                continue
            x = _lerp(nozzle[0] + 10 * s, gap_pt[0] - 18 * s, ph)
            y = _lerp(nozzle[1], gap_pt[1], ph)
            if splash > 0.5 and ph > 0.62:
                x += math.sin(i * 2 + ts * 6) * 28 * s
                y -= (ph - 0.62) * 56 * s
            r = (8 + 5 * power) * s * (0.75 + 0.25 * ph)
            if r < 2:
                continue
            d.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=WATER, outline=INK, width=1)
    if caption and s >= 0.55:
        d.text((cx + 40 * s, cy + 214 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
    return {"tank": tank, "pump": pump, "nozzle": nozzle, "gap": gap_pt}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=WATER if active else WHITE, outline=WATER, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WATER, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=WATER, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 4401).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：冲牙器怎样把碎屑冲走", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _flosser(d, 460 + dx, int(900 + (1 - show) * 12), scale=0.72, ts=time_sec, power=0.7, caption="一股一股")
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是超声波隔空洗牙", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  水泵把水一股股推出", font=FONT_L, fill=WATER, anchor="mm")
            d.text((540, 1660), "够得着的碎屑，才被水推开", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4403).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：水箱、水泵和喷嘴", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _flosser(d, 390, 860, scale=0.9, ts=time_sec, power=0.75)
        if t > 0.18:
            _callout(d, parts["tank"], (parts["tank"][0] - 30, parts["tank"][1] + 90), "水箱", WATER, _spring(t, 0.18, 0.2), anchor="mm")
        if t > 0.36:
            _callout(d, parts["pump"], (120, parts["pump"][1]), "水泵", INK, _spring(t, 0.36, 0.2), anchor="rm")
        if t > 0.54:
            _callout(d, parts["nozzle"], (parts["nozzle"][0], parts["nozzle"][1] - 50), "喷嘴", METAL_DK, _spring(t, 0.54, 0.2), anchor="mm")
        if t > 0.72:
            _callout(d, parts["gap"], (min(1000, parts["gap"][0] + 20), parts["gap"][1] - 70), "牙缝", INK, _spring(t, 0.72, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "泵一下，喷嘴吐出一股", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "挡位改的是用力，不是换一种水", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4407).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "碎屑怎样被水冲开", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _flosser(
        d,
        400,
        820,
        scale=0.78,
        ts=time_sec,
        power=0.15 if active <= 0 else (0.95 if active >= 2 else 0.6),
        empty=1 if active < 0 else 0,
    )
    steps = ["推水", "细口", "打到", "流走"]
    tips = [
        "① 水泵一伸一缩，把水推出",
        "② 细喷嘴把这一股挤得更冲",
        "③ 水打到它够得着的缝",
        "④ 没碰到的，不会自己离开",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1240, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1400, 1020, 1520), radius=14, fill=(255, 253, 248))
        d.text((540, 1460), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1620), "更冲，也不等于每条缝都进得去", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4409).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(power=0.55, gap=1.0), "为什么是一股一股的？", "泵一下，喷嘴才吐出一股"),
        (0.32, dict(power=1.0, splash=1.0), "为什么调高了更容易溅？", "细口里的水被推得更快"),
        (0.55, dict(power=0.8, gap=0.15), "为什么有的缝还留着？", "比水更窄的地方过不去"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _flosser(d, 470, y + 250, scale=0.38, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "脉冲把水推出，够得着才冲得走", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4411).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _flosser(d, 450, int(700 + (1 - a) * 12), scale=0.72, ts=time_sec, power=0.7)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "冲牙器推的是水", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "打到的地方，才可能带走", font=FONT_L, fill=WATER, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1520, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1600), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1670), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1760),
            "评论区：晾衣架，还是换个别的？",
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
