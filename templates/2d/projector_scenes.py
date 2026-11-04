"""投影仪分集 · 纪录片手绘风 2D。小镜子决定亮暗，镜头把光打到墙上，墙只负责把光弹回来。"""

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
YELLOW = (232, 176, 64)
CHIP = (36, 98, 156)
BEAM = (255, 214, 120)


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


def _proj(d, cx, cy, *, scale=1.0, ts=0.0, beam=0.85, focus=1.0, ambient=0.0, wall="light"):
    """灯、色轮、微镜芯片、镜头和墙。墙只把光弹回来。"""
    s = scale
    d.rounded_rectangle((cx - 250 * s, cy - 78 * s, cx + 8 * s, cy + 86 * s), radius=16 * s, fill=BODY, outline=INK, width=3)
    lamp = (cx - 196 * s, cy + 4 * s)
    d.ellipse((lamp[0] - 26 * s, lamp[1] - 26 * s, lamp[0] + 26 * s, lamp[1] + 26 * s), fill=YELLOW if beam > 0.25 else METAL, outline=INK, width=2)
    wx, wy, wr = cx - 112 * s, cy + 4 * s, 32 * s
    base = (ts * 90) % 360
    box = (wx - wr, wy - wr, wx + wr, wy + wr)
    for i, col in enumerate(((196, 64, 58), (52, 140, 78), (52, 96, 176))):
        d.pieslice(box, base + i * 120, base + (i + 1) * 120, fill=col, outline=INK)
    wheel = (wx, wy - wr)
    chip_box = (cx - 62 * s, cy - 30 * s, cx - 8 * s, cy + 38 * s)
    d.rounded_rectangle(chip_box, radius=3 * s, fill=CHIP, outline=INK, width=2)
    for i in range(4):
        for j in range(3):
            on = math.sin(ts * 5 + i * 1.3 + j) > (0.15 if beam > 0.45 else 0.75)
            x = cx - 56 * s + i * 12 * s
            y = cy - 22 * s + j * 18 * s
            d.rectangle((x, y, x + 8 * s, y + 10 * s), fill=WHITE if on else METAL_DK)
    chip = (chip_box[2], cy)
    d.ellipse((cx - 16 * s, cy - 42 * s, cx + 58 * s, cy + 50 * s), fill=_mix(METAL, (190, 214, 226), 0.55), outline=INK, width=3)
    d.ellipse((cx + 8 * s, cy - 18 * s, cx + 40 * s, cy + 18 * s), fill=WHITE, outline=METAL_DK, width=2)
    lens = (cx + 36 * s, cy)
    wall_fill = (232, 228, 220)
    img_col = (196, 92, 64)
    if wall == "dark":
        wall_fill = (74, 72, 70)
        img_col = (110, 72, 64)
    if ambient > 0.5:
        wall_fill = (198, 198, 194)
        img_col = (168, 160, 154)
    wx0 = cx + 176 * s
    if beam > 0.25:
        d.polygon([(lens[0], cy - 16 * s), (lens[0], cy + 16 * s), (wx0, cy + 96 * s), (wx0, cy - 96 * s)], fill=(*BEAM, 90))
    d.rectangle((wx0, cy - 150 * s, wx0 + 78 * s, cy + 150 * s), fill=wall_fill, outline=INK, width=3)
    jitter = (1 - _clamp01(focus)) * 12 * s
    d.rectangle((wx0 + 14 * s + jitter, cy - 78 * s, wx0 + 60 * s, cy - 24 * s), fill=img_col)
    d.rectangle((wx0 + 16 * s - jitter, cy - 6 * s, wx0 + 50 * s, cy + 42 * s), fill=_mix(img_col, WHITE, 0.3 if wall != "dark" else 0.08))
    if focus < 0.55:
        d.rectangle((wx0 + 8 * s, cy - 86 * s, wx0 + 68 * s, cy - 16 * s), outline=MUTED, width=2)
    if ambient > 0.5:
        d.ellipse((wx0 + 18 * s, cy - 196 * s, wx0 + 48 * s, cy - 166 * s), fill=YELLOW, outline=INK, width=2)
    return {"lamp": lamp, "wheel": wheel, "chip": chip, "lens": lens, "wall": (wx0 + 78 * s, cy - 40 * s)}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=CHIP if active else WHITE, outline=CHIP, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else CHIP, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=CHIP, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 3501).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：投影仪怎样把画面打上墙", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _proj(d, 430 + dx, int(1040 + (1 - show) * 12), scale=0.82, ts=time_sec, beam=0.9)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是墙自己变成屏幕", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  投的是光，墙负责弹回", font=FONT_L, fill=CHIP, anchor="mm")
            d.text((540, 1660), "画面先在小芯片上成形", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3503).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：灯、色轮和小镜子", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _proj(d, 420, 980, scale=0.78, ts=time_sec, beam=0.9)
        if t > 0.18:
            _callout(d, parts["lamp"], (parts["lamp"][0] - 20, parts["lamp"][1] + 70), "光源", YELLOW, _spring(t, 0.18, 0.2), anchor="rm")
        if t > 0.36:
            _callout(d, parts["wheel"], (parts["wheel"][0] - 10, parts["wheel"][1] - 36), "色轮", ACCENT, _spring(t, 0.36, 0.2), anchor="mm")
        if t > 0.54:
            _callout(d, parts["chip"], (parts["chip"][0] + 8, parts["chip"][1] - 70), "小镜子", CHIP, _spring(t, 0.54, 0.2))
        if t > 0.72:
            _callout(d, parts["lens"], (parts["lens"][0] + 10, parts["lens"][1] + 64), "镜头", INK, _spring(t, 0.72, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "镜子决定亮暗，镜头只负责放大", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "墙把打过来的光弹回眼睛", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3507).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "画面怎样打到墙上", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    beam = 0.25 if active < 0 else (0.5 if active < 2 else 0.95)
    _proj(d, 430, 700, scale=0.72, ts=time_sec, beam=beam, focus=1)
    steps = ["给光", "上色", "亮暗", "投墙"]
    tips = [
        "① 灯先发出很亮的光",
        "② 色轮让红绿蓝飞快轮流出现",
        "③ 小镜子决定这一点亮还是暗",
        "④ 镜头把光放大，打到墙上",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "投影仪在投光，不是在墙上画画", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3509).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(ambient=1, beam=0.8), "为什么白天看着发灰？", "别的光也打在同一面墙上"),
        (0.32, dict(wall="dark", beam=0.85), "为什么深色墙看起来闷？", "深色把更多的光吃掉了"),
        (0.55, dict(focus=0.05, beam=0.85), "为什么要对焦？", "调的是清楚，不是像素变多"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _proj(d, 500, y + 250, scale=0.32, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "芯片决定亮暗，镜头把光打到墙上", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3511).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _proj(d, 430, int(700 + (1 - a) * 12), scale=0.7, ts=time_sec, beam=0.9)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "画面先在小芯片上成形", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "镜头投光，墙负责弹回", font=FONT_L, fill=CHIP, anchor="mm")
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
