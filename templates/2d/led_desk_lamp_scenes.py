"""台灯分集 · 纪录片手绘风 2D。电流过芯片才发光，灯罩把点光散开。"""

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
GLOW = (255, 214, 120)
CHIP = (255, 196, 72)
SHADE = (255, 236, 196)


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


def _glow_amt(ts, on, dim):
    if on < 0.4:
        return 0.0
    if dim > 0.5:
        return 1.0 if (ts * 16) % 1.0 < 0.35 else 0.12
    return 0.92


def _lamp(d, cx, cy, *, scale=1.0, ts=0.0, on=1.0, dim=0.0, shade=1.0, filament=0.0, caption=""):
    """电流过芯片发光。金属带走余热。灯罩把点光散开。"""
    s = scale
    _rr(d, (cx - 78 * s, cy + 96 * s, cx + 78 * s, cy + 140 * s), 10 * s, fill=METAL, outline=INK, width=2)
    d.line((cx, cy + 96 * s, cx, cy - 10 * s), fill=METAL_DK, width=max(6, int(8 * s)))
    d.line((cx, cy - 10 * s, cx + 36 * s, cy - 86 * s), fill=METAL_DK, width=max(6, int(8 * s)))
    hx, hy = cx + 36 * s, cy - 112 * s
    _rr(d, (hx - 96 * s, hy - 40 * s, hx + 96 * s, hy + 40 * s), 14 * s, fill=(240, 242, 244), outline=INK, width=3)
    glow = _glow_amt(ts, on, dim)
    chip_col = _mix((150, 154, 160), CHIP, glow)
    d.rectangle((hx - 18 * s, hy - 12 * s, hx + 18 * s, hy + 12 * s), fill=chip_col, outline=INK, width=2)
    chip = (hx, hy)
    for i in range(4):
        y = hy - 22 * s + i * 12 * s
        d.line((hx + 28 * s, y, hx + 62 * s, y), fill=METAL_DK, width=3)
    fin = (hx + 52 * s, hy)
    _rr(d, (cx - 30 * s, cy + 102 * s, cx + 30 * s, cy + 130 * s), 4 * s, fill=WHITE, outline=INK, width=2)
    driver = (cx, cy + 116 * s)
    shade_pt = (hx, hy + 78 * s)
    if shade > 0.5 and glow > 0.05:
        pool = _mix(PAPER, SHADE, 0.35 + 0.55 * glow)
        d.polygon(
            [
                (hx - 70 * s, hy + 40 * s),
                (hx + 70 * s, hy + 40 * s),
                (hx + 130 * s, hy + 108 * s),
                (hx - 130 * s, hy + 108 * s),
            ],
            fill=pool,
        )
    elif shade < 0.5 and glow > 0.2:
        for i in range(5):
            ang = -0.8 + i * 0.4
            d.line(
                (hx, hy + 40 * s, hx + math.sin(ang) * 90 * s, hy + 40 * s + abs(math.cos(ang)) * 80 * s),
                fill=GLOW,
                width=2,
            )
    if filament > 0.5:
        bx, by = cx - 160 * s, cy - 20 * s
        d.ellipse((bx - 30 * s, by - 40 * s, bx + 30 * s, by + 24 * s), fill=(255, 214, 140), outline=INK, width=2)
        d.rectangle((bx - 12 * s, by + 20 * s, bx + 12 * s, by + 40 * s), fill=METAL_DK)
        d.line((bx - 10 * s, by - 16 * s, bx + 8 * s, by), fill=ACCENT, width=2)
        d.line((bx + 8 * s, by, bx - 6 * s, by + 12 * s), fill=ACCENT, width=2)
    if on < 0.4 and s >= 0.55:
        d.text((hx, hy), "不通", font=FONT_XS, fill=MUTED, anchor="mm")
    if caption and s >= 0.55:
        d.text((cx, cy + 190 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
    return {"chip": chip, "driver": driver, "fin": fin, "shade": shade_pt}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=ACCENT if active else WHITE, outline=ACCENT, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else ACCENT, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=ACCENT, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 4701).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：台灯怎样把电变成光", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _lamp(d, 520 + dx, int(820 + (1 - show) * 12), scale=0.78, ts=time_sec, on=1, caption="芯片在发光")
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是一根烧红的细丝", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  电流过芯片才发光", font=FONT_L, fill=ACCENT, anchor="mm")
            d.text((540, 1660), "护眼两个字，不是医疗结论", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4703).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：芯片、驱动和灯罩", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _lamp(d, 460, 800, scale=0.95, ts=time_sec, on=1)
        if t > 0.18:
            _callout(d, parts["chip"], (parts["chip"][0], parts["chip"][1] - 70), "芯片", ACCENT, _spring(t, 0.18, 0.2), anchor="mm")
        if t > 0.36:
            _callout(d, parts["fin"], (min(1000, parts["fin"][0] + 16), parts["fin"][1] - 20), "金属", METAL_DK, _spring(t, 0.36, 0.2))
        if t > 0.54:
            _callout(d, parts["driver"], (parts["driver"][0] - 80, parts["driver"][1] + 40), "驱动", INK, _spring(t, 0.54, 0.2), anchor="rm")
        if t > 0.72:
            _callout(d, parts["shade"], (parts["shade"][0] - 40, parts["shade"][1] + 30), "灯罩", ACCENT, _spring(t, 0.72, 0.2), anchor="mm")
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "芯片像一扇只往一边开的门", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "反方向过不去，这一颗就不亮", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4707).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "桌面上的光怎样来", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _lamp(d, 480, 700, scale=0.82, ts=time_sec, on=0 if active < 0 else 1, shade=0 if active < 3 else 1)
    steps = ["送电", "过芯", "散热", "散开"]
    tips = [
        "① 驱动送出稳定的小电流",
        "② 电流流过芯片，芯片发光",
        "③ 金属把多余的热带走",
        "④ 灯罩把点光散成一片",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "调暗不用换芯片", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4709).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(on=1, filament=1), "为什么灯壳暖却不像老灯烫？", "芯片更多把能量变成光"),
        (0.32, dict(on=1, dim=1), "为什么调暗了颜色常常不变？", "还是同一颗芯片在发光"),
        (0.55, dict(on=1, shade=0), "为什么拿掉灯罩会刺眼？", "点光没有被散开"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _lamp(d, 540, y + 230, scale=0.4, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "电流过芯片发光，灯罩负责散开", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4711).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _lamp(d, 500, int(620 + (1 - a) * 12), scale=0.78, ts=time_sec, on=1)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "台灯里是芯片在发光", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "灯罩散开，不是在治眼睛", font=FONT_L, fill=ACCENT, anchor="mm")
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
