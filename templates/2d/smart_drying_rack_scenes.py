"""电动晾衣架分集 · 纪录片手绘风 2D。电机收钢丝绳，衣杆才上升。"""

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
ROPE = (90, 94, 102)
OK = (52, 146, 96)
CLOTH = (214, 176, 150)
WET = (150, 186, 206)


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


def _rack(d, cx, cy, *, scale=1.0, ts=0.0, lift=0.35, spin=0.0, fan=0.0, jammed=0.0, tilt=0.0, caption=""):
    """电机收绳，衣杆上升。收到限位就停。风扇只拨空气。"""
    s = scale
    d.line((cx - 230 * s, cy - 210 * s, cx + 230 * s, cy - 210 * s), fill=LINE, width=4)
    _rr(d, (cx - 96 * s, cy - 200 * s, cx + 96 * s, cy - 124 * s), 8 * s, fill=WHITE, outline=INK, width=3)
    motor = (cx - 36 * s, cy - 162 * s)
    turning = spin > 0.5 and jammed < 0.5
    ang = ts * (7 if turning else 0.2)
    d.ellipse((motor[0] - 18 * s, motor[1] - 18 * s, motor[0] + 18 * s, motor[1] + 18 * s), fill=METAL, outline=INK, width=2)
    d.line((motor[0], motor[1], motor[0] + math.cos(ang) * 12 * s, motor[1] + math.sin(ang) * 12 * s), fill=ACCENT if turning else METAL_DK, width=3)
    reel = (cx + 40 * s, cy - 162 * s)
    d.ellipse((reel[0] - 16 * s, reel[1] - 16 * s, reel[0] + 16 * s, reel[1] + 16 * s), outline=INK, width=2)
    d.arc((reel[0] - 10 * s, reel[1] - 10 * s, reel[0] + 10 * s, reel[1] + 10 * s), 20, 300, fill=ROPE, width=2)
    limit = (cx + 74 * s, cy - 150 * s)
    hit = lift > 0.92
    d.ellipse((limit[0] - 8 * s, limit[1] - 8 * s, limit[0] + 8 * s, limit[1] + 8 * s), fill=ACCENT if hit or jammed > 0.5 else OK, outline=INK, width=1)
    lift = _clamp01(lift)
    bar_y = cy + 70 * s - lift * 150 * s
    skew = tilt * 28 * s
    left = (cx - 78 * s, cy - 124 * s)
    right = (cx + 78 * s, cy - 124 * s)
    d.line((left[0], left[1], cx - 78 * s, bar_y + skew), fill=ROPE, width=max(2, int(3 * s)))
    d.line((right[0], right[1], cx + 78 * s, bar_y - skew), fill=ROPE, width=max(2, int(3 * s)))
    rope = (cx - 78 * s, (left[1] + bar_y) / 2)
    d.line((cx - 120 * s, bar_y + skew, cx + 120 * s, bar_y - skew), fill=INK, width=max(4, int(6 * s)))
    bar = (cx, bar_y)
    cloth = WET if fan > 0.5 else CLOTH
    for i, dx in enumerate((-70, -10, 50)):
        x = cx + dx * s
        top = bar_y + (skew if dx < 0 else -skew) * 0.3
        _rr(d, (x, top, x + 34 * s, top + 64 * s), 4 * s, fill=cloth if i != 1 else CLOTH, outline=INK, width=2)
        if fan > 0.5:
            d.ellipse((x + 12 * s, top + 18 * s, x + 20 * s, top + 28 * s), fill=(96, 156, 196))
    if fan > 0.5:
        fx, fy = cx + 168 * s, bar_y
        d.ellipse((fx - 16 * s, fy - 16 * s, fx + 16 * s, fy + 16 * s), outline=INK, width=2)
        d.line((fx + 18 * s, fy, fx + 46 * s, fy - 8 * s), fill=(120, 170, 200), width=2)
        d.line((fx + 18 * s, fy, fx + 46 * s, fy + 8 * s), fill=(120, 170, 200), width=2)
    if caption and s >= 0.55:
        d.text((cx, cy + 200 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
    return {"motor": motor, "rope": rope, "bar": bar, "limit": limit}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=OK if active else WHITE, outline=OK, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else OK, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=OK, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 4501).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：晾衣架怎样把衣杆升起", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        lift = 0.25 + 0.55 * (0.5 + 0.5 * math.sin(time_sec * 0.8))
        _rack(d, 520 + dx, int(860 + (1 - show) * 12), scale=0.72, ts=time_sec, lift=lift, spin=1, caption="收绳上升")
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是衣杆自己往上飞", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  电机收绳才把杆拉高", font=FONT_L, fill=OK, anchor="mm")
            d.text((540, 1660), "衣服上的水，还是靠空气走", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4503).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：电机、钢丝绳和限位", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _rack(d, 520, 780, scale=0.9, ts=time_sec, lift=0.55, spin=1)
        if t > 0.18:
            _callout(d, parts["motor"], (parts["motor"][0] - 80, parts["motor"][1] - 50), "电机", INK, _spring(t, 0.18, 0.2), anchor="rm")
        if t > 0.36:
            _callout(d, parts["rope"], (140, parts["rope"][1]), "钢丝绳", ROPE, _spring(t, 0.36, 0.2), anchor="rm")
        if t > 0.54:
            _callout(d, parts["bar"], (parts["bar"][0] + 40, parts["bar"][1] + 90), "衣杆", INK, _spring(t, 0.54, 0.2), anchor="mm")
        if t > 0.72:
            _callout(d, parts["limit"], (min(1000, parts["limit"][0] + 20), parts["limit"][1] - 36), "限位", ACCENT, _spring(t, 0.72, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "绳子变短，衣杆才上升", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "风扇只拨空气，不是干衣机", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4507).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "衣杆怎样被绳子拉高", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    lifts = [0.12, 0.4, 0.72, 0.98]
    lift = 0.2 if active < 0 else lifts[active]
    _rack(d, 520, 700, scale=0.78, ts=time_sec, lift=lift, spin=0 if active >= 3 else 1)
    steps = ["正转", "绕绳", "拉高", "限位"]
    tips = [
        "① 电机正转，卷轴跟着转",
        "② 钢丝绳一圈圈绕上卷轴",
        "③ 绳子变短，衣杆被拉高",
        "④ 收到限位，电机停下",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "升的是收绳，不是衣杆会飞", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4509).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(lift=0.98, spin=0), "为什么升到顶会自己停？", "绳子收到限位，电机断电"),
        (0.32, dict(lift=0.45, spin=0, jammed=1), "为什么有时升着就停住？", "太重或卡住，转不动就断"),
        (0.55, dict(lift=0.7, spin=0, fan=1), "为什么挂着不会马上干？", "风扇只拨空气，水靠空气走"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _rack(d, 540, y + 230, scale=0.4, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "电机收绳，衣杆才上升", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4511).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _rack(d, 520, int(640 + (1 - a) * 12), scale=0.75, ts=time_sec, lift=0.8, spin=1)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "电动晾衣架在收绳子", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "限位一到，电机就停下", font=FONT_L, fill=OK, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1520, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1600), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1670), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1760),
            "评论区：除螨仪，还是换个别的？",
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
