"""空气炸锅分集 · 纪录片手绘风 2D。"""

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
AIR_LT = (180, 210, 235)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (46, 48, 54)
BODY_LT = (72, 76, 84)
BASKET = (210, 214, 220)
OIL = (214, 170, 70)
GREEN = (80, 160, 110)
PALE = (214, 186, 120)
GOLD = (176, 104, 42)


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


def _callout(d, tip, label, text, color=INK, alpha=1.0):
    if alpha <= 0.01:
        return
    _sketch_line(d, tip, label, color, 2, int(tip[0] + tip[1]))
    d.ellipse((tip[0] - 5, tip[1] - 5, tip[0] + 5, tip[1] + 5), fill=color)
    d.text(label, text, font=FONT_S, fill=(*color, int(255 * _clamp01(alpha))), anchor="lm")


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


def _loop_point(u, left, right, top, bot):
    if u < 0.25:
        return _lerp(left, right, u / 0.25), top
    if u < 0.5:
        return right, _lerp(top, bot, (u - 0.25) / 0.25)
    if u < 0.75:
        return _lerp(right, left, (u - 0.5) / 0.25), bot
    return left, _lerp(bot, top, (u - 0.75) / 0.25)


def _food(d, box, ts, crisp, crowded):
    x0, y0, x1, y1 = box
    cols = 4 if not crowded else 6
    rows = 2 if not crowded else 4
    color = _mix(PALE, GOLD, crisp)
    w, h = x1 - x0, y1 - y0
    for i in range(cols * rows):
        c, r = i % cols, i // cols
        px = x0 + w * (c + 0.5) / cols + math.sin(ts * 2 + i) * 1.5
        py = y0 + h * (r + 0.55) / rows
        fw, fh = w / cols * 0.55, h / rows * 0.42
        d.rounded_rectangle((px - fw, py - fh, px + fw, py + fh), radius=4, fill=color, outline=INK, width=1)


def _fryer(d, cx, cy, *, scale=1.0, ts=0.0, power=1.0, flow=1.0, crowded=False, oil=False, crisp=0.4, cutaway=False):
    """篮式空气炸锅：顶上风扇和电热管，带孔炸篮，底部接油盘。"""
    s = scale
    bw, bh = 280 * s, 390 * s
    x0, y0 = cx - bw / 2, cy - bh / 2
    d.rounded_rectangle((x0 + 6, y0 + 8, x0 + bw + 6, y0 + bh + 8), radius=22 * s, fill=(30, 32, 36))
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=22 * s, fill=BODY, outline=INK, width=2)
    # 控制条和温度点
    d.rounded_rectangle((x0 + 16 * s, y0 + 16 * s, x0 + bw - 16 * s, y0 + 58 * s), radius=8 * s, fill=BODY_LT, outline=INK, width=1)
    if scale >= 0.75:
        label = "180°C" if power > 0.35 else "待机"
        d.text((x0 + 36 * s, y0 + 37 * s), label, font=FONT_XS, fill=WHITE, anchor="lm")
    d.ellipse((x0 + bw - 52 * s, y0 + 26 * s, x0 + bw - 30 * s, y0 + 48 * s), fill=GREEN if power > 0.35 else METAL, outline=INK, width=1)
    # 排气狭缝
    for i in range(3):
        vx = x0 + bw - 18 * s
        vy = y0 + 78 * s + i * 14 * s
        d.line((vx, vy, vx + 10 * s, vy), fill=METAL, width=2)

    fan = (cx, y0 + 108 * s)
    d.ellipse((fan[0] - 28 * s, fan[1] - 28 * s, fan[0] + 28 * s, fan[1] + 28 * s), fill=BODY_LT, outline=METAL, width=2)
    ang = ts * 9 * max(flow, 0.05)
    for k in range(4):
        a = ang + k * math.pi / 2
        d.line((fan[0], fan[1], fan[0] + math.cos(a) * 20 * s, fan[1] + math.sin(a) * 20 * s), fill=WHITE, width=max(2, int(3 * s)))

    heater_y = y0 + 156 * s
    if power > 0.25:
        glow = int(90 * power * _pulse(ts, 3, 0.65, 1.0))
        d.ellipse((cx - 90 * s, heater_y - 16 * s, cx + 90 * s, heater_y + 28 * s), fill=(*HOT_LT, glow))
    coil = HOT if power > 0.3 else METAL_DK
    for i in range(3):
        yy = heater_y + i * 12 * s
        pts = []
        for k in range(14):
            f = k / 13
            px = _lerp(x0 + 48 * s, x0 + bw - 48 * s, f)
            py = yy + math.sin(f * math.pi * 5 + ts * (4 if power > 0.3 else 0)) * 3.5 * s
            pts.append((px, py))
        d.line(pts, fill=coil, width=max(2, int(3 * s)))

    basket = (x0 + 36 * s, y0 + 196 * s, x0 + bw - 36 * s, y0 + bh - 62 * s)
    d.rounded_rectangle(basket, radius=10 * s, fill=BASKET, outline=INK, width=2)
    # 篮孔：左右和底部
    hole_col = BODY
    for i in range(5):
        hy = basket[1] + (basket[3] - basket[1]) * (i + 0.5) / 5
        rad = 5 * s
        d.ellipse((basket[0] + 8 * s - rad, hy - rad, basket[0] + 8 * s + rad, hy + rad), fill=hole_col)
        d.ellipse((basket[2] - 8 * s - rad, hy - rad, basket[2] - 8 * s + rad, hy + rad), fill=hole_col)
    for i in range(4):
        hx = basket[0] + (basket[2] - basket[0]) * (i + 0.5) / 4
        rad = 4.5 * s
        d.ellipse((hx - rad, basket[3] - 12 * s - rad, hx + rad, basket[3] - 12 * s + rad), fill=hole_col)
    food_box = (basket[0] + 18 * s, basket[1] + 16 * s, basket[2] - 18 * s, basket[3] - 22 * s)
    _food(d, food_box, ts, crisp, crowded)
    if crowded and scale >= 0.7:
        d.text((cx, (basket[1] + basket[3]) / 2), "堆满", font=FONT_XS, fill=ACCENT, anchor="mm")

    # 强制对流：热风沿腔壁绕一圈，堆满时下半圈进不去
    if flow > 0.15:
        left, right = x0 + 22 * s, x0 + bw - 22 * s
        top, bot = heater_y + 28 * s, y0 + bh - 78 * s
        col = HOT_LT if power > 0.3 else AIR_LT
        for i in range(9):
            u = (ts * 0.28 * flow + i / 9) % 1.0
            if crowded and 0.28 < u < 0.78:
                continue
            px, py = _loop_point(u, left, right, top, bot)
            rad = 5 * s
            d.ellipse((px - rad, py - rad, px + rad, py + rad), fill=col)

    if oil and power > 0.3:
        for i in range(6):
            u = (ts * 0.45 + i / 6) % 1.0
            px = cx + math.sin(ts * 3 + i) * 36 * s
            py = _lerp(basket[3] - 20 * s, basket[1] + 10 * s, u)
            rad = (2 + 3 * (1 - u)) * s
            d.ellipse((px - rad, py - rad, px + rad, py + rad), fill=(*OIL, int(180 * (1 - u * 0.4))))

    tray = (x0 + 48 * s, y0 + bh - 50 * s, x0 + bw - 48 * s, y0 + bh - 18 * s)
    d.rounded_rectangle(tray, radius=6 * s, fill=METAL_DK, outline=INK, width=1)
    if oil:
        d.ellipse((cx - 28 * s, tray[1] + 6 * s, cx + 28 * s, tray[3] - 4 * s), fill=OIL)
    handle = (cx - 34 * s, y0 + bh - 4 * s, cx + 34 * s, y0 + bh + 22 * s)
    d.rounded_rectangle(handle, radius=8 * s, fill=BODY_LT, outline=INK, width=2)

    return {
        "fan": (fan[0], fan[1] - 28 * s),
        "heater": (x0 + bw - 52 * s, heater_y + 12 * s),
        "basket": (basket[0], (basket[1] + basket[3]) / 2),
        "tray": (cx, (tray[1] + tray[3]) / 2),
        "vent": (x0 + bw - 8 * s, y0 + 92 * s),
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=HOT if active else WHITE, outline=HOT, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else HOT, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=HOT, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 211).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 170, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 300), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 390), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 460), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 550), "今天：空气炸锅怎么把食物做脆", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _fryer(
            d,
            540 + dx,
            int(980 + (1 - show) * 40),
            scale=1.05,
            ts=time_sec,
            power=0.95 if t > 0.5 else 0.25,
            flow=0.9 if t > 0.5 else 0.2,
            oil=t > 0.62,
            crisp=0.75 if t > 0.7 else 0.25,
            cutaway=t > 0.55,
        )
    if t > 0.5:
        wrong = _ease(_scene_t(t, 0.5, 0.64))
        right = _spring(t, 0.66, 0.28)
        if wrong > 0 and right < 0.35:
            d.rounded_rectangle((90, 1320, 990, 1420), radius=12, fill=(255, 240, 235))
            d.text((540, 1370), "❌ 不是空气变成油在炸", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((80, 1280, 1000, 1480), radius=14, fill=(255, 245, 240))
            d.text((540, 1350), "✓  电热管加热，风扇高速送热风", font=FONT_L, fill=HOT, anchor="mm")
            d.text((540, 1425), "脆来自表面被吹干，不是油浴", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 213).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 95), "拆开看：热风怎么绕过食物", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    parts = None
    if show > 0:
        parts = _fryer(d, 500, 640, scale=1.2, ts=time_sec, power=0.95, flow=1.0, oil=True, crisp=0.55, cutaway=True)
        if t > 0.22:
            _callout(d, parts["heater"], (790, 560), "电热管", HOT, _spring(t, 0.22, 0.25))
        if t > 0.38:
            _callout(d, parts["fan"], (790, 390), "风扇", AIR, _spring(t, 0.38, 0.25))
        if t > 0.52:
            _callout(d, parts["basket"], (70, 900), "带孔炸篮", INK, _spring(t, 0.52, 0.25))
        if t > 0.64:
            _callout(d, parts["vent"], (790, 740), "排气口", MUTED, _spring(t, 0.64, 0.25))
    if t > 0.72:
        d.rounded_rectangle((90, 1180, 990, 1420), radius=14, fill=(255, 253, 248))
        d.text((540, 1255), "电热管发热，风扇把热风送进篮孔", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1335), "接油盘接油，排气口放走湿气", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 217).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 90), "做脆四步", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    power = 0.25 if active < 0 else 1.0
    flow = 0.2 if active < 1 else 1.0
    crisp = 0.15 if active < 2 else (0.55 if active == 2 else 0.95)
    _fryer(
        d,
        540,
        470,
        scale=1.05,
        ts=time_sec,
        power=power,
        flow=flow,
        oil=active >= 3,
        crisp=crisp,
        cutaway=True,
    )
    steps = ["电热管发热", "风扇送热风", "吹干表面", "美拉德变脆"]
    tips = [
        "① 电热管发热，烤到近处，也加热空气",
        "② 风扇把热风送进篮孔：强制对流",
        "③ 表面的凉空气和水分被吹走",
        "④ 干表面升温变黄变脆，薄油只是帮忙",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 980, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1160, 1010, 1280), radius=14, fill=(255, 253, 248))
        d.text((540, 1220), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1420), "油雾帮忙上色，食物没有泡在油里", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 219).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 90), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, "堆太满为什么不脆？", "风路被堵，底部闷熟"),
        (0.32, "为什么还要薄油？", "帮忙传热上色，不是油浴"),
        (0.55, "为什么比烤箱更快？", "腔小、热管近、风速高"),
    ]
    for idx, (start, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 200 + idx * 300 + (1 - a) * 40
        d.rounded_rectangle((90, y, 990, y + 270), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        if idx == 0:
            _fryer(d, 540, y + 185, scale=0.38, ts=time_sec, power=0.7, flow=0.35, crowded=True, crisp=0.3)
        elif idx == 1:
            _fryer(d, 540, y + 185, scale=0.38, ts=time_sec, power=0.9, flow=0.9, oil=True, crisp=0.8)
        else:
            _fryer(d, 540, y + 185, scale=0.38, ts=time_sec, power=1.0, flow=1.0, crisp=0.7)
    if t > 0.78:
        d.text((540, 1280), "高速热风烤箱", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1360), "不是无油油炸", font=FONT_M, fill=HOT, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 221).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _fryer(
        d,
        540,
        int(500 + (1 - a) * 30),
        scale=1.15,
        ts=time_sec,
        power=0.95,
        flow=1.0,
        oil=True,
        crisp=0.9,
        cutaway=True,
    )
    if t > 0.2:
        d.rounded_rectangle((70, 860, 1010, 1080), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 920), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 985), "电热管加热 · 风扇造热风", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1045), "吹干表面才变脆", font=FONT_L, fill=HOT, anchor="mm")
    if t > 0.5:
        b = _spring(t, 0.5, 0.25)
        _ken_badge(d, 1200, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1290), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1360), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.75:
        d.text(
            (540, 1520),
            "评论区：电烤箱，还是换个别的？",
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
