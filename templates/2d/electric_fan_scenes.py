"""电风扇分集 · 纪录片手绘风 2D。"""

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
AIR = (70, 130, 175)
AIR_LT = (180, 210, 235)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (226, 230, 234)
BRASS = (196, 154, 74)
DUST = (150, 142, 130)
BLUE = (62, 102, 146)


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


def _fan(d, cx, cy, *, scale=1.0, ts=0.0, spin=1.0, oscillate=0.0, dusty=0.0, airflow=1.0):
    """正视扇头：斜叶、网罩、蜗杆摇头。晃动表示摇头，不是第二台电机。"""
    s = scale
    r = 120 * s
    pole_b = cy + r + 150 * s
    d.line((cx, cy + r - 4 * s, cx, pole_b), fill=METAL_DK, width=max(6, int(10 * s)))
    d.rounded_rectangle((cx - 78 * s, pole_b, cx + 78 * s, pole_b + 28 * s), radius=8 * s, fill=METAL_DK, outline=INK, width=2)
    shift = math.sin(ts * 1.3) * 42 * s * oscillate
    hx = cx + shift
    d.ellipse((hx - r, cy - r, hx + r, cy + r), fill=BODY)
    d.ellipse((hx - r, cy - r, hx + r, cy + r), outline=INK, width=4)
    ang = ts * 7 * max(spin, 0.05)
    blade = _mix(WHITE, DUST, dusty)
    for k in range(3):
        a = ang + k * math.tau / 3
        tip = (hx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78)
        left = (hx + math.cos(a + 0.55) * r * 0.26, cy + math.sin(a + 0.55) * r * 0.26)
        right = (hx + math.cos(a - 0.4) * r * 0.2, cy + math.sin(a - 0.4) * r * 0.2)
        d.polygon([tip, left, right], fill=blade, outline=INK)
        if dusty > 0.25:
            d.ellipse((tip[0] - 7 * s, tip[1] - 7 * s, tip[0] + 6 * s, tip[1] + 6 * s), fill=DUST)
    d.ellipse((hx - 20 * s, cy - 20 * s, hx + 20 * s, cy + 20 * s), fill=METAL_DK, outline=INK, width=2)
    for i in range(-3, 4):
        yy = cy + i * r * 0.22
        half = math.sqrt(max(r * r - (yy - cy) ** 2, 1))
        d.line((hx - half, yy, hx + half, yy), fill=METAL_DK, width=2)
    if airflow > 0.15:
        for i in range(5):
            u = (ts * 0.9 * airflow + i / 5) % 1.0
            px = hx + r + 10 * s + u * 70 * s
            py = cy - 36 * s + (i % 3) * 28 * s
            rad = 5 * s
            d.ellipse((px - rad, py - rad, px + rad, py + rad), fill=AIR_LT)
    neck = (cx, cy + r + 6 * s)
    d.arc((cx - 46 * s, neck[1] - 10 * s, cx + 46 * s, neck[1] + 36 * s), 200, 340, fill=ACCENT if oscillate > 0.2 else MUTED, width=3)
    gear = (cx, neck[1] + 28 * s)
    d.ellipse((gear[0] - 16 * s, gear[1] - 12 * s, gear[0] + 2 * s, gear[1] + 10 * s), outline=INK, width=2)
    d.ellipse((gear[0] - 2 * s, gear[1] - 6 * s, gear[0] + 16 * s, gear[1] + 14 * s), outline=BRASS, width=3)
    return {
        "blade": (hx + r * 0.45, cy - r * 0.35),
        "guard": (hx + r, cy),
        "hub": (hx, cy),
        "gear": (gear[0] + 16 * s, gear[1]),
        "air": (hx + r + 48 * s, cy),
    }


def _motor(d, cx, cy, *, scale=1.0, ts=0.0, spin=1.0):
    """罩极铜环让磁通滞后；电容让两条绕组错相。都是交流感应电机。"""
    s = scale
    rad = 92 * s
    box = (cx - rad, cy - rad, cx + rad, cy + rad)
    d.ellipse(box, fill=(72, 76, 84))
    d.ellipse(box, outline=INK, width=3)
    for k in range(4):
        a = -math.pi / 2 + k * math.pi / 2
        inner = 46 * s
        outer = rad * 0.9
        d.line(
            (cx + math.cos(a) * inner, cy + math.sin(a) * inner, cx + math.cos(a) * outer, cy + math.sin(a) * outer),
            fill=METAL,
            width=max(8, int(16 * s)),
        )
    ring = (cx + 22 * s, cy - rad * 0.62)
    d.arc((ring[0] - 18 * s, ring[1] - 16 * s, ring[0] + 18 * s, ring[1] + 16 * s), 10, 200, fill=BRASS, width=5)
    rr = 26 * s
    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=METAL_DK, outline=INK, width=2)
    ang = ts * 5 * max(spin, 0.05)
    for k in range(6):
        a = ang + k * math.tau / 6
        d.line((cx, cy, cx + math.cos(a) * rr * 0.82, cy + math.sin(a) * rr * 0.82), fill=WHITE, width=2)
    cap = (cx + rad + 18 * s, cy - 10 * s)
    d.rounded_rectangle((cap[0], cap[1], cap[0] + 34 * s, cap[1] + 56 * s), radius=6 * s, fill=BLUE, outline=INK, width=2)
    d.line((cap[0] + 10 * s, cap[1], cap[0] + 10 * s, cap[1] - 14 * s), fill=METAL, width=2)
    d.line((cap[0] + 24 * s, cap[1], cap[0] + 24 * s, cap[1] - 14 * s), fill=METAL, width=2)
    return {"ring": ring, "rotor": (cx + rr, cy), "cap": (cap[0] + 34 * s, cap[1] + 20 * s)}


def _thermo(d, cx, cy, s=1.0):
    d.rounded_rectangle((cx - 18 * s, cy - 46 * s, cx + 18 * s, cy + 36 * s), radius=8 * s, fill=WHITE, outline=INK, width=2)
    d.rectangle((cx - 6 * s, cy - 4 * s, cx + 6 * s, cy + 24 * s), fill=ACCENT)
    d.ellipse((cx - 12 * s, cy + 24 * s, cx + 12 * s, cy + 46 * s), fill=ACCENT, outline=INK, width=2)
    d.text((cx + 36 * s, cy), "室温不变", font=FONT_S, fill=INK, anchor="lm")


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=AIR if active else WHITE, outline=AIR, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else AIR, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=AIR, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 711).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：电风扇为什么让人觉得凉", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _fan(
            d,
            460 + dx,
            int(980 + (1 - show) * 20),
            scale=1.05,
            ts=time_sec,
            spin=0.3 if t < 0.45 else 1.0,
            oscillate=0.0 if t < 0.6 else 1.0,
            airflow=0.2 if t < 0.45 else 1.0,
        )
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((90, 1480, 990, 1580), radius=12, fill=(255, 240, 235))
            d.text((540, 1530), "❌ 风扇并没有把室温吹低", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1460, 1010, 1660), radius=14, fill=(255, 245, 240))
            d.text((540, 1520), "✓  风加快皮肤散热和出汗", font=FONT_L, fill=AIR, anchor="mm")
            d.text((540, 1600), "电机还会多放出一点热", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 713).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：谁在转，谁在摇", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        fan = _fan(d, 300, 560, scale=0.78, ts=time_sec, spin=1, oscillate=1, airflow=0.7)
        motor = _motor(d, 700, 1120, scale=0.95, ts=time_sec, spin=1)
        if t > 0.2:
            _callout(d, fan["blade"], (180, 360), "斜扇叶", INK, _spring(t, 0.2, 0.22), anchor="rm")
        if t > 0.34:
            _callout(d, fan["guard"], (620, 430), "网罩", MUTED, _spring(t, 0.34, 0.22))
        if t > 0.48:
            _callout(d, fan["gear"], (620, 760), "蜗杆摇头", ACCENT, _spring(t, 0.48, 0.22))
        if t > 0.6:
            _callout(d, motor["ring"], (980, 980), "罩极铜环", BRASS, _spring(t, 0.6, 0.22), anchor="rm")
        if t > 0.72:
            _callout(d, motor["cap"], (980, 1240), "电容", BLUE, _spring(t, 0.72, 0.22), anchor="rm")
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "铜环或电容，让磁场转起来", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "摇头是齿轮连杆，不是第二台电机", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 717).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "风是怎么来的", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _fan(
        d,
        390,
        520,
        scale=0.95,
        ts=time_sec,
        spin=0.25 if active < 1 else 1.0,
        oscillate=1.0 if active >= 3 else 0.0,
        airflow=0.2 if active < 2 else 1.0,
    )
    if active <= 1:
        _motor(d, 820, 560, scale=0.7, ts=time_sec, spin=0.4 if active < 1 else 1.0)
    steps = ["磁场旋转", "转子跟随", "斜叶推风", "齿轮摇头"]
    tips = [
        "① 铜环或电容，把磁场做成旋转的",
        "② 转子感应出电流，没有电刷换向",
        "③ 斜叶把空气推向你，背后再补气",
        "④ 蜗杆啮合，连杆把扇头摆开",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1080, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1240, 1010, 1360), radius=14, fill=(255, 253, 248))
        d.text((540, 1300), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1480), "凉快的是皮肤，温度计不会往下掉", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 719).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, "dust", "为什么积灰又吵又没风？", "叶片不平衡，斜面也不干净"),
        (0.32, "cap", "为什么有的风扇要电容？", "副绕组靠它把电流错开相位"),
        (0.55, "room", "为什么空屋吹一夜还是热？", "热没有被搬到室外"),
    ]
    for idx, (start, mode, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 340 + (1 - a) * 40
        d.rounded_rectangle((70, y, 1010, y + 310), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        if mode == "dust":
            _fan(d, 520, y + 200, scale=0.42, ts=time_sec, spin=0.7, dusty=0.85, airflow=0.25, oscillate=0)
        elif mode == "cap":
            _motor(d, 500, y + 200, scale=0.7, ts=time_sec, spin=0.8)
        else:
            _fan(d, 390, y + 200, scale=0.32, ts=time_sec, spin=1, airflow=0.8, oscillate=0.6)
            _thermo(d, 700, y + 190, 0.9)
    if t > 0.78:
        d.text((540, 1280), "感应电机转叶，摇头靠齿轮", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1360), "风扇不降低室温", font=FONT_M, fill=AIR, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 721).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _fan(
        d,
        500,
        int(520 + (1 - a) * 20),
        scale=1.05,
        ts=time_sec,
        spin=1,
        oscillate=1,
        airflow=1,
    )
    if t > 0.2:
        d.rounded_rectangle((70, 1120, 1010, 1320), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1175), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1235), "感应电机转叶 · 齿轮负责摇头", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1300), "风扇不降低室温", font=FONT_L, fill=AIR, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1440, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1520), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1590), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1700),
            "评论区：加湿器，还是换个别的？",
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
