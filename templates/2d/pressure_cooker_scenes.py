"""电压力锅分集 · 纪录片手绘风 2D。密封抬高沸点；浮子锁盖，限压阀稳压。不是把食物压碎。"""

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
HOT_LT = (240, 190, 150)
WATER = (70, 130, 175)
WATER_LT = (186, 216, 232)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (226, 230, 234)
GASKET = (196, 122, 86)
BRASS = (196, 154, 74)
FOOD = (214, 168, 96)


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


def _steam_puff(d, x, y, ts, n=3, s=1.0, rise=36):
    for i in range(n):
        u = (ts * 0.45 + i / max(n, 1)) % 1.0
        sx = x + math.sin(ts * 2 + i) * 8 * s
        sy = y - u * rise * s
        rad = (3 + 6 * u) * s
        d.arc((sx, sy, sx + 14 * s, sy + 12 * s), 200, 340, fill=MUTED, width=2)
        if rad > 0:
            d.ellipse((sx - rad * 0.2, sy, sx + rad, sy + rad * 0.7), outline=MUTED, width=1)


def _cooker(d, cx, cy, *, scale=1.0, ts=0.0, pressure=0.65, vent=0.25, heat=0.8, open_lid=0.0, water=0.7):
    """密封内胆、密封圈、浮子阀、限压阀、底部加热盘。"""
    s = scale
    bw, bh = 280 * s, 250 * s
    x0 = cx - bw / 2
    y0 = cy - bh / 2
    d.rounded_rectangle((x0, y0 + 48 * s, x0 + bw, y0 + bh), radius=22 * s, fill=BODY, outline=INK, width=3)
    plate = (x0 + 34 * s, y0 + bh - 34 * s, x0 + bw - 34 * s, y0 + bh - 12 * s)
    d.rounded_rectangle(plate, radius=6 * s, fill=HOT if heat > 0.35 else METAL_DK, outline=INK, width=2)
    pot = (x0 + 26 * s, y0 + 78 * s, x0 + bw - 26 * s, y0 + bh - 40 * s)
    d.rounded_rectangle(pot, radius=10 * s, fill=(236, 238, 242), outline=METAL_DK, width=2)
    if water > 0.08:
        wy = _lerp(pot[3] - 16 * s, pot[1] + 18 * s, 0.25 + 0.45 * water)
        d.rectangle((pot[0] + 8 * s, wy, pot[2] - 8 * s, pot[3] - 8 * s), fill=WATER_LT)
        for i in range(4):
            gx = pot[0] + 22 * s + (i % 4) * 36 * s
            gy = wy + 16 * s
            d.ellipse((gx, gy, gx + 16 * s, gy + 10 * s), fill=FOOD)
    if pressure > 0.15 and open_lid < 0.35:
        _steam_puff(d, cx, pot[1] + 8 * s, ts, n=4, s=s, rise=28)

    lift = open_lid * 78 * s
    lid = (x0 + 6 * s, y0 + 10 * s - lift, x0 + bw - 6 * s, y0 + 78 * s - lift)
    d.rounded_rectangle(lid, radius=16 * s, fill=WHITE, outline=INK, width=3)
    gasket = (x0 + 16 * s, lid[3] - 8 * s, x0 + bw - 16 * s, lid[3] + 8 * s)
    d.rounded_rectangle(gasket, radius=4 * s, fill=GASKET, outline=INK, width=1)

    float_up = (22 * s * pressure) if open_lid < 0.4 else 0
    fx = cx - 46 * s
    fy = lid[1] + 8 * s - float_up
    d.rounded_rectangle((fx - 5 * s, fy + 8 * s, fx + 5 * s, lid[1] + 36 * s), radius=3 * s, fill=METAL_DK)
    d.ellipse((fx - 9 * s, fy - 6 * s, fx + 9 * s, fy + 12 * s), fill=BRASS if pressure > 0.45 else METAL, outline=INK, width=2)

    vx = cx + 52 * s
    wobble = math.sin(ts * 7) * 5 * s * vent
    d.rectangle((vx - 6 * s, lid[1] + 16 * s, vx + 6 * s, lid[1] + 34 * s), fill=METAL_DK)
    d.ellipse((vx - 16 * s + wobble, lid[1] - 8 * s, vx + 16 * s + wobble, lid[1] + 16 * s), fill=METAL, outline=INK, width=2)
    if vent > 0.35 and open_lid < 0.4:
        _steam_puff(d, vx, lid[1] - 10 * s, ts, n=3, s=s, rise=26)

    if open_lid > 0.45:
        _steam_puff(d, cx, lid[3] + 6 * s, ts, n=3, s=s, rise=20)

    deg = "110°C" if pressure > 0.55 and open_lid < 0.3 else "100°C"
    if s >= 0.55:
        d.text((cx, y0 + bh + 22 * s), deg, font=FONT_XS, fill=HOT if pressure > 0.55 and open_lid < 0.3 else WATER, anchor="mm")
    return {
        "gasket": (gasket[2], (gasket[1] + gasket[3]) / 2),
        "float": (fx + 10 * s, fy),
        "valve": (vx + 16 * s + wobble, lid[1]),
        "heat": (plate[2], (plate[1] + plate[3]) / 2),
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=HOT if active else WHITE, outline=HOT, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else HOT, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=HOT, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 2301).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：电压力锅为什么煮得更快", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _cooker(d, 540 + dx, int(1040 + (1 - show) * 20), scale=1.05, ts=time_sec, pressure=0.8, vent=0.55, heat=1, water=0.75)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是把食物压碎的大力锅", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  密封把沸点抬高", font=FONT_L, fill=HOT, anchor="mm")
            d.text((540, 1660), "水要更热，才会沸腾", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2303).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：密封、浮子和限压", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _cooker(d, 430, 900, scale=1.25, ts=time_sec, pressure=0.85, vent=0.7, heat=1, water=0.7)
        if t > 0.2:
            _callout(d, parts["gasket"], (min(980, parts["gasket"][0] + 40), parts["gasket"][1] + 30), "密封圈", GASKET, _spring(t, 0.2, 0.22))
        if t > 0.38:
            _callout(d, parts["float"], (parts["float"][0] + 180, parts["float"][1] - 36), "浮子阀", BRASS, _spring(t, 0.38, 0.22))
        if t > 0.54:
            _callout(d, parts["valve"], (min(990, parts["valve"][0] + 70), parts["valve"][1] - 20), "限压阀", METAL_DK, _spring(t, 0.54, 0.22))
        if t > 0.7:
            _callout(d, parts["heat"], (min(980, parts["heat"][0] + 30), parts["heat"][1] + 36), "加热盘", HOT, _spring(t, 0.7, 0.22))
    if t > 0.8:
        d.rounded_rectangle((70, 1580, 1010, 1780), radius=14, fill=(255, 253, 248))
        d.text((540, 1640), "压力高了，水要到一百一十度上下才沸", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1710), "电饭煲敞着排气，还停在一百度附近", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2307).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "沸点是怎样被抬高的", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _cooker(
        d,
        540,
        640,
        scale=1.0,
        ts=time_sec,
        pressure=0.15 if active < 1 else (0.45 if active < 2 else 0.9),
        vent=0.85 if active >= 3 else 0.05,
        heat=0.3 if active < 0 else 1,
        water=0.8,
    )
    steps = ["加热", "密封", "沸点升", "稳压"]
    tips = [
        "① 加热盘把内胆里的水烧热",
        "② 密封圈把蒸汽留在锅里",
        "③ 压力升高，沸腾温度跟着升",
        "④ 限压阀放掉多余蒸汽，压力稳住",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1180, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1340, 1010, 1460), radius=14, fill=(255, 253, 248))
        d.text((540, 1400), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1560), "浮子落下之前，锅盖拧不开", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2309).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, "lock", "为什么盖子拧不动？", "浮子被气压顶起，卡住了锁"),
        (0.32, "vent", "为什么会嘶地排气？", "限压阀在维持设定压力"),
        (0.55, "boil", "为什么能超过一百度？", "开盖停在沸点，密封把沸点抬高"),
    ]
    for idx, (start, kind, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        if kind == "lock":
            _cooker(d, 540, y + 250, scale=0.55, ts=time_sec, pressure=0.95, vent=0.1, heat=0.8)
        elif kind == "vent":
            _cooker(d, 540, y + 250, scale=0.55, ts=time_sec, pressure=0.8, vent=1, heat=0.7)
        else:
            _cooker(d, 360, y + 250, scale=0.42, ts=time_sec, pressure=0.1, vent=0, heat=0.6, open_lid=0.85, water=0.6)
            _cooker(d, 720, y + 250, scale=0.42, ts=time_sec, pressure=0.9, vent=0.3, heat=0.9, water=0.6)
    if t > 0.82:
        d.text((540, 1480), "密封抬高压力，压力抬高沸点", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2311).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _cooker(d, 540, int(620 + (1 - a) * 16), scale=1.05, ts=time_sec, pressure=0.85, vent=0.4, heat=0.9, water=0.7)
    if t > 0.2:
        d.rounded_rectangle((70, 1120, 1010, 1340), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1180), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1245), "密封让压力升高", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1310), "水要更热，才会沸腾", font=FONT_L, fill=HOT, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1480, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1560), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1630), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1740),
            "评论区：干衣机，还是换个别的？",
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
