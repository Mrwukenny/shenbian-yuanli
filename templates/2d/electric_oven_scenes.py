"""电烤箱分集 · 纪录片手绘风 2D。"""

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
AIR = (70, 130, 175)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (58, 60, 66)
BODY_LT = (86, 90, 98)
CAVITY = (62, 52, 48)
FOOD = (214, 186, 150)
FOOD_DK = (150, 78, 42)


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


def _coil_h(d, x0, x1, y, s, hot, ts):
    pts = []
    phase = ts * (5.5 if hot else 0.6)
    for k in range(18):
        f = k / 17
        px = _lerp(x0, x1, f)
        py = y + math.sin(f * math.pi * 6 + phase) * 4.5 * s
        pts.append((px, py))
    d.line(pts, fill=HOT if hot else METAL_DK, width=max(3, int(4 * s)))


def _cavity_air(d, cav, ts, mode, s):
    if mode == "off":
        return
    x0, y0, x1, y1 = cav
    if mode == "conv":
        left, right = x0 + 18 * s, x1 - 18 * s
        top, bot = y0 + 46 * s, y1 - 46 * s
        for i in range(8):
            u = (ts * 0.35 + i / 8) % 1.0
            if u < 0.25:
                px, py = _lerp(left, right, u / 0.25), top
            elif u < 0.5:
                px, py = right, _lerp(top, bot, (u - 0.25) / 0.25)
            elif u < 0.75:
                px, py = _lerp(right, left, (u - 0.5) / 0.25), bot
            else:
                px, py = left, _lerp(bot, top, (u - 0.75) / 0.25)
            rad = 5 * s
            d.ellipse((px - rad, py - rad, px + rad, py + rad), fill=HOT_LT)
        return
    for i in range(6):
        u = (ts * 0.4 + i / 6) % 1.0
        side = x0 + 22 * s if i % 2 == 0 else x1 - 22 * s
        py = _lerp(y1 - 36 * s, y0 + 40 * s, u)
        rad = 4.5 * s
        d.ellipse((side - rad, py - rad, side + rad, py + rad), fill=HOT_LT)


def _oven(d, cx, cy, *, scale=1.0, ts=0.0, mode="bake", power=1.0, cycling=False, doneness=0.45):
    """上管、下管、后壁风扇和感温头。mode: off / bake / grill / conv。"""
    s = scale
    bw, bh = 460 * s, 390 * s
    x0, y0 = cx - bw / 2, cy - bh / 2
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=22 * s, fill=BODY, outline=INK, width=3)
    _flat_round(d, (x0 + 18 * s, y0 + 16 * s, x0 + bw - 18 * s, y0 + 74 * s), 10 * s, BODY_LT, INK, 2)
    names = {"bake": "烘烤", "grill": "烧烤", "conv": "热风", "off": "待机"}
    if s >= 0.72:
        d.text((x0 + 36 * s, y0 + 45 * s), names[mode], font=FONT_XS, fill=WHITE, anchor="lm")
    dial = (x0 + bw - 62 * s, y0 + 45 * s)
    d.ellipse((dial[0] - 18 * s, dial[1] - 18 * s, dial[0] + 18 * s, dial[1] + 18 * s), fill=WHITE, outline=INK, width=2)
    needle = {"off": -2.2, "bake": -0.4, "grill": 0.5, "conv": 1.1}[mode]
    d.line(
        (dial[0], dial[1], dial[0] + math.cos(needle) * 12 * s, dial[1] + math.sin(needle) * 12 * s),
        fill=ACCENT,
        width=3,
    )

    cav = (x0 + 28 * s, y0 + 96 * s, x0 + bw - 28 * s, y0 + bh - 34 * s)
    _flat_round(d, cav, 12 * s, CAVITY, INK, 2)
    heat_on = power > 0.25 and (not cycling or math.sin(ts * 3.2) > -0.2)
    top_on = heat_on and mode in ("bake", "grill", "conv")
    bot_on = heat_on and mode in ("bake", "conv")
    top_y = cav[1] + 28 * s
    bot_y = cav[3] - 26 * s
    if top_on:
        d.ellipse((cav[0] + 24 * s, top_y - 18 * s, cav[2] - 24 * s, top_y + 24 * s), fill=(*HOT_LT, int(80 * _pulse(ts, 3, 0.55, 1))))
    _coil_h(d, cav[0] + 34 * s, cav[2] - 34 * s, top_y, s, top_on, ts)
    _coil_h(d, cav[0] + 34 * s, cav[2] - 34 * s, bot_y, s, bot_on, ts)

    fan_c = ((cav[0] + cav[2]) / 2, (cav[1] + cav[3]) / 2 - 6 * s)
    spinning = mode == "conv" and power > 0.2
    ring_r = 34 * s
    d.ellipse(
        (fan_c[0] - ring_r, fan_c[1] - ring_r, fan_c[0] + ring_r, fan_c[1] + ring_r),
        outline=HOT if spinning else METAL_DK,
        width=3,
    )
    ang = ts * (8 if spinning else 0.4)
    for k in range(4):
        a = ang + k * math.pi / 2
        d.line(
            (fan_c[0], fan_c[1], fan_c[0] + math.cos(a) * ring_r * 0.72, fan_c[1] + math.sin(a) * ring_r * 0.72),
            fill=WHITE,
            width=3,
        )
    _cavity_air(d, cav, ts, mode if heat_on else "off", s)

    rack_y = cav[3] - 62 * s
    d.line((cav[0] + 18 * s, rack_y, cav[2] - 18 * s, rack_y), fill=METAL, width=3)
    for k in range(4):
        xx = _lerp(cav[0] + 28 * s, cav[2] - 28 * s, k / 3)
        d.line((xx, rack_y - 8 * s, xx, rack_y + 8 * s), fill=METAL, width=2)
    food = (cx - 78 * s, rack_y - 40 * s, cx + 78 * s, rack_y - 8 * s)
    crust = _mix(FOOD, FOOD_DK, doneness)
    _flat_round(d, food, 7 * s, crust, INK, 2)
    if mode == "grill":
        d.rectangle((food[0] + 6, food[1] + 4, food[2] - 6, food[1] + 14 * s), fill=_mix(FOOD_DK, (90, 40, 28), doneness))

    sensor = (cav[2] - 20 * s, cav[1] + 78 * s)
    d.ellipse((sensor[0] - 7 * s, sensor[1] - 7 * s, sensor[0] + 7 * s, sensor[1] + 7 * s), fill=ACCENT, outline=INK, width=2)
    d.rounded_rectangle((cx - 50 * s, y0 + bh - 6 * s, cx + 50 * s, y0 + bh + 18 * s), radius=8 * s, fill=BODY_LT, outline=INK, width=2)
    return {
        "top": (cav[2] - 6 * s, top_y),
        "bottom": (cav[0] + 6 * s, bot_y),
        "fan": (fan_c[0] + ring_r, fan_c[1]),
        "sensor": sensor,
        "dial": dial,
        "door": (x0 + bw - 8 * s, y0 + bh * 0.72),
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=HOT if active else WHITE, outline=HOT, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else HOT, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=HOT, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 411).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：电烤箱怎么把食物烤熟", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _oven(
            d,
            540 + dx,
            int(980 + (1 - show) * 40),
            scale=1.05,
            ts=time_sec,
            mode="conv" if t > 0.66 else "grill",
            power=0.95 if t > 0.5 else 0.2,
            doneness=0.8 if t > 0.66 else 0.35,
        )
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((90, 1460, 990, 1560), radius=12, fill=(255, 240, 235))
            d.text((540, 1510), "❌ 旋钮拧大，烤管并不会一直更烫", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1440, 1010, 1640), radius=14, fill=(255, 245, 240))
            d.text((540, 1505), "✓  满功率通断，温控器负责开关", font=FONT_L, fill=HOT, anchor="mm")
            d.text((540, 1580), "烧烤靠上管辐射，热风靠风扇", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 413).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：热从哪来", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _oven(d, 400, 780, scale=1.05, ts=time_sec, mode="conv", power=0.95, doneness=0.55)
        if t > 0.18:
            _callout(d, parts["top"], (820, 520), "上电热管", HOT, _spring(t, 0.18, 0.22))
        if t > 0.32:
            _callout(d, parts["fan"], (820, 680), "热风风扇", AIR, _spring(t, 0.32, 0.22))
        if t > 0.46:
            _callout(d, parts["sensor"], (820, 840), "感温头", ACCENT, _spring(t, 0.46, 0.22))
        if t > 0.6:
            _callout(d, parts["bottom"], (820, 1000), "下电热管", HOT, _spring(t, 0.6, 0.22))
        if t > 0.72:
            _callout(d, parts["door"], (820, 1160), "门封", MUTED, _spring(t, 0.72, 0.22))
    if t > 0.8:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "电阻丝发热，上管偏辐射", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "风扇搅匀热空气，感温头告诉温控器", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 417).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "烤熟，就这四步", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    modes = ("bake", "bake", "grill", "conv")
    mode = "off" if active < 0 else modes[active]
    _oven(
        d,
        540,
        560,
        scale=1.02,
        ts=time_sec,
        mode=mode,
        power=0.2 if active < 0 else 1.0,
        cycling=t > 0.84,
        doneness=0.2 if active < 2 else (0.55 if active == 2 else 0.85),
    )
    steps = ["电阻发热", "自然对流", "上管烧烤", "风扇热风"]
    tips = [
        "① 电阻把电变成热，管壁发出红外辐射",
        "② 辐射烤表面，热空气上升是自然对流",
        "③ 烧烤靠上管近距离辐射，里面未必熟",
        "④ 风扇搅匀热空气，吹薄表面凉空气",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1120, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1280, 1010, 1400), radius=14, fill=(255, 253, 248))
        d.text((540, 1340), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1520), "到温停管，掉温再接通，腔温来回晃", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 419).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, "bake", True, 0.35, "为什么要预热？", "先把腔壁和空气带到设定温度"),
        (0.32, "grill", False, 0.7, "为什么烧烤外糊里不熟？", "上管辐射先停在表面"),
        (0.55, "conv", False, 0.8, "为什么热风可以略降温？", "每一面都碰到热空气，传热更快"),
    ]
    for idx, (start, mode, cycling, done, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 340 + (1 - a) * 40
        d.rounded_rectangle((70, y, 1010, y + 310), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _oven(d, 540, y + 200, scale=0.42, ts=time_sec, mode=mode, power=0.9, cycling=cycling, doneness=done)
    if t > 0.78:
        d.text((540, 1280), "烧烤偏辐射，热风偏强制对流", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1360), "温控器只负责到温就停", font=FONT_M, fill=ACCENT, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 421).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _oven(
        d,
        540,
        int(520 + (1 - a) * 30),
        scale=1.05,
        ts=time_sec,
        mode="conv",
        power=0.95,
        cycling=t > 0.45,
        doneness=0.8,
    )
    if t > 0.2:
        d.rounded_rectangle((70, 1080, 1010, 1280), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1135), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1195), "电热管发热 · 温控器开关", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1260), "烧烤靠辐射 · 热风靠风扇", font=FONT_L, fill=HOT, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1400, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1480), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1550), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1660),
            "评论区：电热水壶，还是换个别的？",
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
