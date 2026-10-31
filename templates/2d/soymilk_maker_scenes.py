"""豆浆机分集 · 纪录片手绘风 2D。刀片把豆子打开，加热煮到沸腾附近，浆才算熟。"""

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
WATER = (70, 130, 175)
WATER_LT = (186, 214, 232)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (214, 216, 220)

BEAN = (214, 186, 120)
SLURRY = (236, 226, 196)
MESH = (120, 128, 136)
BRASS = (196, 154, 74)

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



def _cup(d, cx, cy, *, scale=1.0, ts=0.0, grind=0.7, boil=0.5, foam=0.25, mesh=0.0):
    """杯体、刀片、加热管和防溢探针。grind 低时还能看见整颗豆子。"""
    s = scale
    top = cy - 210 * s
    bot = cy + 150 * s
    d.ellipse((cx - 118 * s, top - 16 * s, cx + 118 * s, top + 36 * s), fill=METAL, outline=INK, width=2)
    d.rounded_rectangle((cx - 100 * s, top, cx + 100 * s, bot), radius=26 * s, fill=BODY, outline=INK, width=3)
    inner = (cx - 70 * s, top + 28 * s, cx + 70 * s, bot - 36 * s)
    d.rounded_rectangle(inner, radius=10 * s, fill=WHITE, outline=LINE, width=2)
    level = _lerp(inner[3] - 24 * s, inner[1] + 36 * s, 0.58)
    d.rectangle((inner[0] + 6 * s, level, inner[2] - 6 * s, inner[3] - 6 * s), fill=_mix(WATER_LT, SLURRY, grind))
    if grind < 0.55:
        for i in range(6):
            bx = cx - 46 * s + (i % 3) * 30 * s
            by = level + 18 * s + (i // 3) * 26 * s
            d.ellipse((bx, by, bx + 18 * s, by + 12 * s), fill=BEAN, outline=INK, width=1)
    blade_y = inner[3] - 26 * s
    ang = ts * (9 if grind > 0.2 else 0.5)
    d.line(
        (cx - math.cos(ang) * 42 * s, blade_y, cx + math.cos(ang) * 42 * s, blade_y),
        fill=METAL_DK,
        width=max(3, int(4 * s)),
    )
    d.line((cx, blade_y - 16 * s, cx, blade_y + 14 * s), fill=METAL, width=3)
    heat = (cx - 78 * s, bot - 28 * s, cx + 78 * s, bot - 10 * s)
    d.rectangle(heat, fill=HOT if boil > 0.35 else METAL_DK)
    d.rounded_rectangle((cx - 40 * s, bot - 2 * s, cx + 40 * s, bot + 42 * s), radius=10 * s, fill=METAL_DK, outline=INK, width=2)
    spin = ts * 7
    d.line((cx, bot + 16 * s, cx + math.cos(spin) * 14 * s, bot + 22 * s + math.sin(spin) * 8 * s), fill=ACCENT, width=2)
    probe_tip = level - 6 * s if foam > 0.55 else level + 28 * s
    d.line((inner[2] - 14 * s, top + 6 * s, inner[2] - 14 * s, probe_tip), fill=BRASS, width=max(2, int(3 * s)))
    d.ellipse((inner[2] - 20 * s, probe_tip - 5 * s, inner[2] - 8 * s, probe_tip + 6 * s), fill=BRASS, outline=INK, width=1)
    if foam > 0.2:
        for i in range(6):
            fx = inner[0] + 10 * s + i * 20 * s
            fy = level - 8 * s - (i % 2) * 12 * s
            d.ellipse((fx, fy, fx + 16 * s, fy + 11 * s), outline=MUTED, width=2)
    if mesh > 0.4:
        d.rectangle((inner[0] + 8 * s, level + 10 * s, cx - 4 * s, inner[3] - 18 * s), outline=MESH, width=2)
    if boil > 0.4:
        for i in range(3):
            u = (ts * 0.8 + i / 3) % 1.0
            sx = cx - 24 * s + i * 20 * s
            sy = level - 26 * s - u * 24 * s
            d.arc((sx, sy, sx + 16 * s, sy + 12 * s), 200, 340, fill=MUTED, width=2)
    return {
        "motor": (cx + 46 * s, bot + 18 * s),
        "blade": (cx + 40 * s, blade_y),
        "heat": (heat[2], (heat[1] + heat[3]) / 2),
        "probe": (inner[2] - 8 * s, probe_tip),
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=WATER if active else WHITE, outline=WATER, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WATER, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=WATER, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 2901).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：豆浆机怎样做出豆浆", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _cup(d, 540 + dx, int(1040 + (1 - show) * 16), scale=0.95, ts=time_sec, grind=0.75, boil=0.7, foam=0.45)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((70, 1560, 1010, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是打碎了就能喝", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  先打碎，再煮开", font=FONT_L, fill=WATER, anchor="mm")
            d.text((540, 1660), "没到沸腾附近，还不能当豆浆", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2903).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：刀片、加热和防溢", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _cup(d, 500, 900, scale=1.0, ts=time_sec, grind=0.8, boil=0.75, foam=0.55, mesh=0.6)
        if t > 0.18:
            _callout(d, parts["motor"], (parts["motor"][0] - 150, parts["motor"][1] + 10), "电机", METAL_DK, _spring(t, 0.18, 0.2), anchor="rm")
        if t > 0.36:
            _callout(d, parts["blade"], (min(980, parts["blade"][0] + 20), parts["blade"][1] - 30), "刀片", INK, _spring(t, 0.36, 0.2))
        if t > 0.54:
            _callout(d, parts["heat"], (min(1000, parts["heat"][0] + 16), parts["heat"][1] + 28), "加热管", HOT, _spring(t, 0.54, 0.2))
        if t > 0.72:
            _callout(d, parts["probe"], (min(1000, parts["probe"][0] + 16), parts["probe"][1] - 24), "防溢针", BRASS, _spring(t, 0.72, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "刀片把豆子里的东西放进水里", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "加热煮到沸腾附近，浆才算熟", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2907).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "豆子怎样变成能喝的浆", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _cup(
        d,
        540,
        700,
        scale=0.82,
        ts=time_sec,
        grind=0.15 if active < 1 else 0.85,
        boil=0.1 if active < 2 else 0.8,
        foam=0.7 if active >= 3 else 0.1,
        mesh=0.5 if active >= 1 else 0,
    )
    steps = ["泡豆", "打碎", "煮开", "防溢"]
    tips = [
        "① 豆子先泡软，再和水一起进杯",
        "② 刀片把豆粒切开，浆慢慢变浑",
        "③ 加热管把浆烧到沸腾附近",
        "④ 泡沫顶到针，加热先暂停",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "只打碎、不煮开，还不能当豆浆喝", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2909).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(grind=0.9, boil=0.05, foam=0), "为什么只打碎不能喝？", "内容物进了水，怕热的成分还在"),
        (0.32, dict(grind=0.85, boil=0.8, foam=0.9), "为什么煮着会突然停？", "泡沫顶到防溢针，加热先暂停"),
        (0.55, dict(grind=0.2, boil=0.2, foam=0), "为什么没泡会打得很粗？", "干豆子硬，刀片切不开细胞"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _cup(d, 540, y + 250, scale=0.38, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "先打碎释放，再煮开才能喝", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2911).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _cup(d, 540, int(700 + (1 - a) * 12), scale=0.9, ts=time_sec, grind=0.8, boil=0.7, foam=0.35)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "刀片把豆子打开", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "煮到沸腾附近，浆才算熟", font=FONT_L, fill=WATER, anchor="mm")
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
