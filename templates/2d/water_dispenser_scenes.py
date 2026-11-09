"""饮水机分集 · 纪录片手绘风 2D。电热管只加热小胆，整桶水并不在烧。"""

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
HOT = (198, 92, 52)
WARM = (232, 176, 64)


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


def _dispenser(d, cx, cy, *, scale=1.0, ts=0.0, pour="hot", glug=0.0, heat=0.85, caption=""):
    """倒扣水桶只负责补水。热着的是机身里那只小胆。"""
    s = scale
    _rr(d, (cx - 118 * s, cy - 20 * s, cx + 118 * s, cy + 210 * s), 14 * s, fill=BODY, outline=INK, width=3)
    _rr(d, (cx - 78 * s, cy - 250 * s, cx + 78 * s, cy - 46 * s), 18 * s, fill=(214, 232, 240), outline=INK, width=3)
    d.polygon(
        [(cx - 26 * s, cy - 46 * s), (cx + 26 * s, cy - 46 * s), (cx + 14 * s, cy - 16 * s), (cx - 14 * s, cy - 16 * s)],
        fill=(214, 232, 240),
        outline=INK,
    )
    d.rectangle((cx - 66 * s, cy - 150 * s, cx + 66 * s, cy - 54 * s), fill=WATER)
    d.line((cx - 66 * s, cy - 150 * s, cx + 66 * s, cy - 150 * s), fill=INK, width=2)
    bottle = (cx, cy - 250 * s)
    if glug > 0.5:
        rise = (ts * 36) % 40
        by = cy - 70 * s - rise * s
        d.ellipse((cx - 9 * s, by - 9 * s, cx + 9 * s, by + 9 * s), outline=INK, width=2)
        d.ellipse((cx + 16 * s, by + 16 * s, cx + 28 * s, by + 28 * s), outline=WATER, width=2)
    tank_col = _mix(WATER, HOT, heat)
    _rr(d, (cx - 52 * s, cy + 24 * s, cx + 28 * s, cy + 138 * s), 8 * s, fill=tank_col, outline=INK, width=2)
    elem = WARM if heat > 0.55 else METAL
    d.arc((cx - 34 * s, cy + 78 * s, cx + 10 * s, cy + 122 * s), 200, 350, fill=elem, width=max(2, int(3 * s)))
    tank = (cx - 12 * s, cy + 80 * s)
    _rr(d, (cx + 70 * s, cy + 40 * s, cx + 132 * s, cy + 62 * s), 4 * s, fill=HOT, outline=INK, width=2)
    _rr(d, (cx + 70 * s, cy + 104 * s, cx + 132 * s, cy + 126 * s), 4 * s, fill=WATER, outline=INK, width=2)
    hot_tap = (cx + 132 * s, cy + 51 * s)
    warm_tap = (cx + 132 * s, cy + 115 * s)
    if pour == "hot":
        d.line((hot_tap[0], hot_tap[1], hot_tap[0] + 8 * s, hot_tap[1] + 48 * s), fill=HOT, width=max(2, int(4 * s)))
    elif pour == "warm":
        d.line((warm_tap[0], warm_tap[1], warm_tap[0] + 8 * s, warm_tap[1] + 42 * s), fill=WATER, width=max(2, int(4 * s)))
    if caption and s >= 0.55:
        d.text((cx, cy + 246 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
    return {"bottle": bottle, "tank": tank, "hot": hot_tap, "warm": warm_tap}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=HOT if active else WHITE, outline=HOT, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else HOT, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=HOT, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 3901).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：饮水机怎样把热水备着", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _dispenser(d, 520 + dx, int(980 + (1 - show) * 12), scale=0.58, ts=time_sec, pour="hot", heat=0.9)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是按下才烧整桶", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  小胆提前保温", font=FONT_L, fill=HOT, anchor="mm")
            d.text((540, 1660), "整桶不烧，常温不进这只胆", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3903).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：水桶、小胆和龙头", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _dispenser(d, 480, 900, scale=0.68, ts=time_sec, pour="hot", glug=1, heat=0.88)
        if t > 0.18:
            _callout(d, parts["bottle"], (parts["bottle"][0] - 80, parts["bottle"][1] - 28), "水桶", INK, _spring(t, 0.18, 0.2), anchor="rm")
        if t > 0.36:
            _callout(d, parts["tank"], (parts["tank"][0] - 160, parts["tank"][1]), "小胆", HOT, _spring(t, 0.36, 0.2), anchor="rm")
        if t > 0.54:
            _callout(d, parts["hot"], (min(1020, parts["hot"][0] + 16), parts["hot"][1] - 28), "热水", ACCENT, _spring(t, 0.54, 0.2))
        if t > 0.72:
            _callout(d, parts["warm"], (min(1020, parts["warm"][0] + 16), parts["warm"][1] + 20), "常温", WATER, _spring(t, 0.72, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "电热管只加热这一只小胆", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "咕噜一声，是空气补进桶里", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3907).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "热水是哪一杯", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _dispenser(
        d,
        500,
        720,
        scale=0.58,
        ts=time_sec,
        pour="none" if active < 2 else "hot",
        glug=1 if active in (0, 3) else 0,
        heat=0.9 if active < 3 else 0.38,
    )
    steps = ["进胆", "保温", "接出", "补水"]
    tips = [
        "① 水从桶里补进小胆",
        "② 电热管加热，热了就暂停",
        "③ 龙头放出的是胆里的热水",
        "④ 凉水补进来，下一杯就没那么烫",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "提前热着的，一直是那一小胆", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3909).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(pour="hot", heat=0.32, glug=1), "为什么连着接，后面变温？", "小胆有限，凉水补进来了"),
        (0.32, dict(pour="none", heat=0.85, glug=1), "为什么水桶会咕噜响？", "空气补进去，水才下得来"),
        (0.55, dict(pour="warm", heat=0.9, glug=0), "为什么常温水并不凉？", "这一路不进小胆，也不制冷"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _dispenser(d, 540, y + 250, scale=0.3, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "小胆提前保温，整桶并不在烧", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3911).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _dispenser(d, 520, int(700 + (1 - a) * 12), scale=0.55, ts=time_sec, pour="hot", heat=0.9)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "电热管只加热小胆", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "整桶不烧", font=FONT_L, fill=HOT, anchor="mm")
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
