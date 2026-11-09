"""智能门锁分集 · 纪录片手绘风 2D。比对在锁里，对上了电机才把锁舌收回。"""

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
WOOD = (186, 150, 112)
OK = (36, 140, 96)
FRAME = (120, 116, 110)


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


def _lock(d, cx, cy, *, scale=1.0, ts=0.0, bolt=1.0, match=0.0, power=1.0, wet=0.0, show_key=0.0, offline=0.0, caption=""):
    """锁舌是机械的。比对通过，电机才把它拉回来。"""
    s = scale
    d.rectangle((cx - 210 * s, cy - 190 * s, cx + 36 * s, cy + 190 * s), fill=WOOD, outline=INK, width=3)
    d.rectangle((cx + 48 * s, cy - 190 * s, cx + 108 * s, cy + 190 * s), fill=FRAME, outline=INK, width=3)
    d.rectangle((cx + 56 * s, cy - 22 * s, cx + 96 * s, cy + 22 * s), fill=(70, 68, 64))
    end = _lerp(cx + 24 * s, cx + 88 * s, bolt)
    _rr(d, (cx + 6 * s, cy - 14 * s, end, cy + 14 * s), 3 * s, fill=METAL_DK, outline=INK, width=2)
    bolt_pt = (end, cy)

    sx, sy = cx - 78 * s, cy - 36 * s
    _rr(d, (sx - 46 * s, sy - 58 * s, sx + 46 * s, sy + 78 * s), 10 * s, fill=BODY, outline=INK, width=3)
    d.ellipse((sx - 24 * s, sy - 30 * s, sx + 24 * s, sy + 22 * s), fill=WHITE, outline=INK, width=2)
    for i in range(3):
        d.arc((sx - 16 * s + i * 3 * s, sy - 22 * s, sx + 16 * s, sy + 12 * s), 200, 340, fill=INK, width=2)
    sensor = (sx, sy - 4 * s)
    if wet > 0.5:
        d.ellipse((sx - 8 * s, sy + 6 * s, sx + 4 * s, sy + 16 * s), fill=(72, 164, 204))
        d.ellipse((sx + 8 * s, sy - 8 * s, sx + 16 * s, sy), fill=(72, 164, 204))
    if match > 0.5 and power > 0.5:
        d.ellipse((sx + 28 * s, sy - 48 * s, sx + 44 * s, sy - 32 * s), fill=OK, outline=INK, width=1)

    mx, my = cx - 24 * s, cy + 48 * s
    d.ellipse((mx - 22 * s, my - 22 * s, mx + 22 * s, my + 22 * s), fill=METAL, outline=INK, width=2)
    spinning = match > 0.5 and power > 0.5 and bolt < 0.95
    ang = ts * (8 if spinning else 0.4)
    d.line((mx, my, mx + math.cos(ang) * 14 * s, my + math.sin(ang) * 14 * s), fill=OK if spinning else METAL_DK, width=3)
    motor = (mx, my)
    if power < 0.4:
        d.rectangle((mx - 46 * s, my + 28 * s, mx - 16 * s, my + 46 * s), outline=ACCENT, width=2)
        d.rectangle((mx - 14 * s, my + 34 * s, mx - 10 * s, my + 40 * s), fill=ACCENT)

    kx, ky = sx, sy + 48 * s
    d.ellipse((kx - 8 * s, ky - 8 * s, kx + 8 * s, ky + 8 * s), outline=INK, width=2)
    key_pt = (kx, ky)
    if show_key > 0.5:
        d.line((kx - 8 * s, ky, kx - 42 * s, ky), fill=(196, 164, 64), width=3)
        d.line((kx - 30 * s, ky, kx - 30 * s, ky + 10 * s), fill=(196, 164, 64), width=2)
        d.line((kx - 38 * s, ky, kx - 38 * s, ky + 10 * s), fill=(196, 164, 64), width=2)
    if offline > 0.5 and s >= 0.45:
        d.text((cx - 150 * s, cy - 160 * s), "没网也能对", font=FONT_XS, fill=MUTED, anchor="mm")
    if caption and s >= 0.55:
        d.text((cx - 40 * s, cy + 220 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
    return {"sensor": sensor, "motor": motor, "bolt": bolt_pt, "key": key_pt}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=OK if active else WHITE, outline=OK, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else OK, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=OK, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 4101).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：智能门锁怎样收回锁舌", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _lock(d, 560 + dx, int(980 + (1 - show) * 12), scale=0.62, ts=time_sec, bolt=1, match=0, power=1)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是没电就自己弹开", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  对上了，电机才拉锁舌", font=FONT_L, fill=OK, anchor="mm")
            d.text((540, 1660), "比对在锁里，锁舌是机械的", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4103).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：指纹、电机和锁舌", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _lock(d, 520, 900, scale=0.72, ts=time_sec, bolt=1, match=0, power=1, show_key=1)
        if t > 0.18:
            _callout(d, parts["sensor"], (parts["sensor"][0] - 160, parts["sensor"][1]), "指纹", INK, _spring(t, 0.18, 0.2), anchor="rm")
        if t > 0.36:
            _callout(d, parts["motor"], (parts["motor"][0] - 10, parts["motor"][1] + 130), "电机", OK, _spring(t, 0.36, 0.2), anchor="mm")
        if t > 0.54:
            _callout(d, parts["bolt"], (min(980, parts["bolt"][0] + 48), parts["bolt"][1] - 72), "锁舌", METAL_DK, _spring(t, 0.54, 0.2))
        if t > 0.72:
            _callout(d, parts["key"], (parts["key"][0] - 160, parts["key"][1] + 8), "钥匙", ACCENT, _spring(t, 0.72, 0.2), anchor="rm")
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "对上，才给电机通电", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "没电时锁舌保持伸出", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4107).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "怎样才把锁舌收回", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    bolt = 1.0 if active < 2 else (0.45 if active == 2 else 0.05)
    match = 1 if active >= 1 else 0
    _lock(d, 540, 720, scale=0.62, ts=time_sec, bolt=bolt, match=match, power=1)
    steps = ["读取", "比对", "转动", "收回"]
    tips = [
        "① 指纹头读下纹路的高低",
        "② 锁里面比对，对上才算认出",
        "③ 小电机通电，开始拉动",
        "④ 锁舌离开门框，门才能开",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "对不上，电机不转，锁舌还在外面", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4109).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(bolt=0.05, match=1, power=1, offline=1), "为什么没网，指纹也能开？", "比对就存在锁里面"),
        (0.32, dict(bolt=1, match=0, power=1, wet=1), "为什么湿手容易失败？", "纹路被水弄糊，这一次没读清"),
        (0.55, dict(bolt=1, match=0, power=0, show_key=1), "为什么没电，门还锁着？", "电机拉不动，钥匙仍能转锁舌"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _lock(d, 620, y + 240, scale=0.32, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "对上了，电机才把锁舌收回", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4111).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _lock(d, 560, int(700 + (1 - a) * 12), scale=0.58, ts=time_sec, bolt=0.08, match=1, power=1)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "比对发生在锁里面", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "对上，电机才收回锁舌", font=FONT_L, fill=OK, anchor="mm")
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
