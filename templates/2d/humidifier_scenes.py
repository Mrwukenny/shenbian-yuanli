"""加湿器分集 · 纪录片手绘风 2D。超声波液滴对比蒸发式水蒸气。"""

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
WATER = (70, 130, 175)
WATER_LT = (186, 216, 232)
MIST = (214, 226, 232)
DUST = (236, 236, 230)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (236, 238, 242)
PIEZO = (196, 154, 74)
WICK = (186, 170, 140)
SCALE_C = (168, 160, 146)


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


def _flat_round(d, box, radius, fill, outline=INK, width=2):
    d.rounded_rectangle(box, radius=radius, fill=fill)
    if outline is not None:
        d.rounded_rectangle(box, radius=radius, outline=outline, width=width)


def _fan_disc(d, cx, cy, s, ts, spin=1.0):
    r = 22 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=METAL_DK, outline=INK, width=2)
    ang = ts * 8 * max(spin, 0.05)
    for k in range(3):
        a = ang + k * math.tau / 3
        d.line((cx, cy, cx + math.cos(a) * r * 0.75, cy + math.sin(a) * r * 0.75), fill=WHITE, width=2)


def _hum(d, cx, cy, *, scale=1.0, ts=0.0, kind="ultra", mist=1.0, dust=0.0):
    """kind=ultra 压电片震出液滴；kind=evap 风穿过湿网，出来的是看不见的水蒸气。"""
    s = scale
    bw, base_h = 210 * s, 100 * s
    tank_h = 230 * s
    x0 = cx - bw / 2
    y0 = cy - (tank_h + base_h) / 2
    base = (x0, y0 + tank_h - 8 * s, x0 + bw, y0 + tank_h + base_h)
    d.rounded_rectangle(base, radius=16 * s, fill=BODY, outline=INK, width=2)
    tank = (x0 + 22 * s, y0, x0 + bw - 22 * s, y0 + tank_h)
    d.rounded_rectangle(tank, radius=14 * s, fill=WHITE, outline=INK, width=2)
    water = (tank[0] + 12 * s, tank[1] + 36 * s, tank[2] - 12 * s, tank[3] - 14 * s)
    _flat_round(d, water, 8 * s, WATER_LT, None, 0)
    fan = (x0 + 42 * s, (base[1] + base[3]) / 2 + 6 * s)
    _fan_disc(d, fan[0], fan[1], s, ts, 1.0 if mist > 0.2 else 0.2)

    piezo = ((tank[0] + tank[2]) / 2, water[3] - 16 * s)
    wick_box = (cx - 28 * s, water[1] + 8 * s, cx + 28 * s, water[3] - 6 * s)
    nozzle = (x0 + bw - 28 * s, base[1] + 8 * s)
    if kind == "ultra":
        d.ellipse((piezo[0] - 22 * s, piezo[1] - 8 * s, piezo[0] + 22 * s, piezo[1] + 8 * s), fill=PIEZO, outline=INK, width=2)
        if mist > 0.2:
            for i in range(3):
                ripple = (8 + i * 7) * s * (0.85 + 0.15 * math.sin(ts * 6 + i))
                d.ellipse(
                    (piezo[0] - ripple, piezo[1] - 3 * s, piezo[0] + ripple, piezo[1] + 4 * s),
                    outline=WATER,
                    width=2,
                )
            for i in range(7):
                u = (ts * 0.7 * mist + i / 7) % 1.0
                px = nozzle[0] + math.sin(ts * 3 + i) * 8 * s
                py = _lerp(nozzle[1], nozzle[1] - 150 * s, u)
                rad = (3 + 4 * (1 - u)) * s
                d.ellipse((px - rad, py - rad, px + rad, py + rad), fill=MIST)
            if dust > 0.05:
                for i in range(6):
                    u = (ts * 0.35 + i / 6) % 1.0
                    px = nozzle[0] + 20 * s + u * 70 * s
                    py = nozzle[1] - 20 * s + u * 90 * s
                    rad = 3.5 * s
                    d.ellipse((px - rad, py - rad, px + rad, py + rad), fill=DUST)
    else:
        d.rectangle(wick_box, fill=_mix(WICK, SCALE_C, 0.35), outline=INK, width=2)
        for k in range(5):
            yy = _lerp(wick_box[1] + 6, wick_box[3] - 6, k / 4)
            d.line((wick_box[0] + 4, yy, wick_box[2] - 4, yy), fill=SCALE_C, width=2)
        if mist > 0.2:
            for i in range(4):
                u = (ts * 0.55 + i / 4) % 1.0
                px = _lerp(fan[0] + 16 * s, tank[2] + 8 * s, u)
                py = cy - 10 * s + math.sin(i + ts) * 6 * s
                d.ellipse((px - 4 * s, py - 4 * s, px + 4 * s, py + 4 * s), fill=(176, 196, 210))
        if s >= 0.65:
            d.text((cx, tank[1] + 18 * s), "水蒸气看不见", font=FONT_XS, fill=MUTED, anchor="mm")

    if s >= 0.75:
        tag = "超声波" if kind == "ultra" else "蒸发式"
        d.text((cx, base[3] + 22 * s), tag, font=FONT_XS, fill=INK, anchor="mm")
    return {
        "tank": (tank[2], (tank[1] + tank[3]) / 2),
        "piezo": (piezo[0] + 22 * s, piezo[1]),
        "fan": (fan[0] - 8 * s, fan[1]),
        "nozzle": nozzle,
        "wick": (wick_box[2], (wick_box[1] + wick_box[3]) / 2),
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=WATER if active else WHITE, outline=WATER, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WATER, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=WATER, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 811).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：加湿器的白雾是什么", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _hum(
            d,
            540 + dx,
            int(1000 + (1 - show) * 30),
            scale=1.05,
            ts=time_sec,
            kind="ultra",
            mist=0.95 if t > 0.45 else 0.2,
            dust=0.8 if t > 0.62 else 0.0,
        )
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((90, 1480, 990, 1580), radius=12, fill=(255, 240, 235))
            d.text((540, 1530), "❌ 白雾不等于烧开的蒸汽", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1460, 1010, 1660), radius=14, fill=(255, 245, 240))
            d.text((540, 1520), "✓  超声波喷的是小液滴", font=FONT_L, fill=WATER, anchor="mm")
            d.text((540, 1600), "液滴会把矿物质一起带出来", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 813).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：两条路", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        left = _hum(d, 300, 820, scale=0.82, ts=time_sec, kind="ultra", mist=1, dust=0.7)
        right = _hum(d, 780, 820, scale=0.82, ts=time_sec, kind="evap", mist=1, dust=0)
        if t > 0.22:
            _callout(d, left["piezo"], (210, 980), "压电片", PIEZO, _spring(t, 0.22, 0.22), anchor="rm")
        if t > 0.38:
            _callout(d, left["fan"], (210, 1160), "小风扇", WATER, _spring(t, 0.38, 0.22), anchor="rm")
        if t > 0.52:
            _callout(d, left["nozzle"], (470, 560), "液滴", MUTED, _spring(t, 0.52, 0.22))
        if t > 0.66:
            _callout(d, right["wick"], (980, 760), "湿滤网", WICK, _spring(t, 0.66, 0.22), anchor="rm")
    if t > 0.8:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "超声波震出液滴，风扇只负责送", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "蒸发式的矿物质留在网上", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 817).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "白雾和白灰，不是一回事", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    kind = "evap" if active >= 3 else "ultra"
    _hum(
        d,
        540,
        560,
        scale=1.0,
        ts=time_sec,
        kind=kind,
        mist=0.3 if active < 0 else 1.0,
        dust=0.9 if active == 2 else (0.2 if kind == "ultra" else 0.0),
    )
    steps = ["压电振动", "撕成液滴", "吹出白灰", "蒸发式"]
    tips = [
        "① 压电片每秒振动上百万次",
        "② 雾是液体小水滴，不是气体",
        "③ 钙和镁留下，家具上就是白灰",
        "④ 湿网直接蒸发，蒸气看不见",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1080, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1240, 1010, 1360), radius=14, fill=(255, 253, 248))
        d.text((540, 1300), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1480), "房间越潮蒸发越慢；超声波还会继续喷", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 819).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, "ultra", 0.9, "为什么桌面会起一层白？", "自来水里的矿物质跟着液滴走"),
        (0.32, "evap", 0.0, "为什么看不见雾，湿度却升？", "水蒸气是气体，本来就透明"),
        (0.55, "ultra", 0.2, "为什么水箱要勤洗？", "不靠煮水，白雾也不等于无菌"),
    ]
    for idx, (start, kind, dust, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 340 + (1 - a) * 40
        d.rounded_rectangle((70, y, 1010, y + 310), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _hum(d, 540, y + 210, scale=0.48, ts=time_sec, kind=kind, mist=1, dust=dust)
    if t > 0.78:
        d.text((540, 1280), "超声波喷液滴，蒸发式送蒸气", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1360), "白灰来自矿物质", font=FONT_M, fill=ACCENT, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 821).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _hum(d, 320, int(620 + (1 - a) * 20), scale=0.85, ts=time_sec, kind="ultra", mist=1, dust=0.75)
    _hum(d, 760, int(620 + (1 - a) * 20), scale=0.85, ts=time_sec, kind="evap", mist=1, dust=0)
    if t > 0.2:
        d.rounded_rectangle((70, 1140, 1010, 1360), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1190), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1255), "超声波震出液滴", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1315), "蒸发式吹出水蒸气 · 白灰来自矿物质", font=FONT_M, fill=WATER, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1480, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1560), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1630), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1740),
            "评论区：咖啡机，还是换个别的？",
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
