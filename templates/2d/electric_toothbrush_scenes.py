"""电动牙刷分集 · 纪录片手绘风 2D。只讲刷毛的机械清扫：旋转摆动或听得见的高频振动。"""

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
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (186, 198, 206)
HEAD = (230, 236, 240)
BRISTLE = (86, 116, 150)
TOOTH = (244, 240, 232)
GUM = (214, 164, 160)


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


def _tooth_row(d, cx, top, s, gap=0.35):
    span = 46 * s
    d.rounded_rectangle((cx - span, top, cx - gap * 10 * s, top + 36 * s), radius=10 * s, fill=TOOTH, outline=INK, width=2)
    d.rounded_rectangle((cx + gap * 10 * s, top, cx + span, top + 36 * s), radius=10 * s, fill=TOOTH, outline=INK, width=2)
    d.rectangle((cx - span - 6 * s, top + 28 * s, cx + span + 6 * s, top + 42 * s), fill=GUM)


def _brush(d, cx, cy, *, scale=1.0, ts=0.0, kind="osc", press=0.15, contact=1.0, gap=0.35):
    """手柄电机、刷头和刷毛。contact 低时刷毛离开牙面。"""
    s = scale
    handle = (cx - 26 * s, cy + 10 * s, cx + 26 * s, cy + 230 * s)
    d.rounded_rectangle(handle, radius=18 * s, fill=BODY, outline=INK, width=3)
    motor = (cx - 14 * s, cy + 90 * s, cx + 14 * s, cy + 122 * s)
    d.ellipse(motor, fill=WHITE, outline=METAL_DK, width=2)
    d.line((cx, cy + 90 * s, cx, cy + 8 * s), fill=METAL, width=max(2, int(3 * s)))
    spin = ts * (8 if kind == "sonic" else 4)
    d.line((cx, cy + 106 * s, cx + math.cos(spin) * 8 * s, cy + 106 * s + math.sin(spin) * 8 * s), fill=ACCENT, width=2)

    lift = (1 - _clamp01(contact)) * 54 * s
    hy = cy - 48 * s - lift
    ang = math.sin(ts * (26 if kind == "sonic" else 9)) * (0.22 if kind == "sonic" else 0.55)
    head_w = 40 * s
    d.rounded_rectangle((cx - head_w, hy - 18 * s, cx + head_w, hy + 24 * s), radius=12 * s, fill=HEAD, outline=INK, width=2)
    if kind == "osc":
        d.ellipse((cx - 16 * s, hy - 8 * s, cx + 16 * s, hy + 16 * s), outline=LINE, width=2)

    splay = _clamp01(press)
    full = 40 * s
    length = full * (1 - 0.5 * splay)
    tooth_bottom = hy - 24 * s - full
    if contact > 0.2:
        _tooth_row(d, cx, tooth_bottom - 36 * s, s, gap=gap)

    base_y = hy - 16 * s
    swing = math.sin(ang) * (20 * s if kind == "osc" else 7 * s)
    for i in range(7):
        bx = cx + (-24 * s + i * 8 * s)
        spread = (i - 3) * splay * 12 * s
        d.line((bx, base_y, bx + swing + spread, base_y - length), fill=BRISTLE, width=max(2, int(3 * s)))
    if s >= 0.7:
        tag = "声波" if kind == "sonic" else "旋转摆动"
        d.text((cx, handle[3] + 16 * s), tag, font=FONT_XS, fill=MUTED, anchor="mm")
    return {
        "motor": (motor[2] + 6 * s, (motor[1] + motor[3]) / 2),
        "bristle": (cx + head_w, hy - 10 * s),
        "head": (cx + head_w, hy),
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=WATER if active else WHITE, outline=WATER, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WATER, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=WATER, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 2601).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：电动牙刷靠什么刷干净", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _brush(d, 400 + dx, int(860 + (1 - show) * 12), scale=1.05, ts=time_sec, kind="osc", contact=1)
        _brush(d, 700 + dx, int(860 + (1 - show) * 12), scale=1.05, ts=time_sec, kind="sonic", contact=1)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是隔空把牙震干净", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  刷毛贴着牙面扫", font=FONT_L, fill=WATER, anchor="mm")
            d.text((540, 1660), "声波只是摆得快，听得见", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2603).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：电机、刷毛和牙面", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        osc = _brush(d, 340, 780, scale=1.05, ts=time_sec, kind="osc", contact=1, press=0.1)
        sonic = _brush(d, 740, 780, scale=1.05, ts=time_sec, kind="sonic", contact=1, press=0.1)
        if t > 0.2:
            _callout(d, osc["motor"], (osc["motor"][0] - 120, osc["motor"][1] + 20), "电机", METAL_DK, _spring(t, 0.2, 0.22), anchor="rm")
        if t > 0.4:
            _callout(d, osc["bristle"], (min(520, osc["bristle"][0] + 10), osc["bristle"][1] - 70), "刷毛", BRISTLE, _spring(t, 0.4, 0.22))
        if t > 0.58:
            _callout(d, sonic["head"], (min(1000, sonic["head"][0] + 16), sonic["head"][1] + 40), "声波刷头", WATER, _spring(t, 0.58, 0.22))
        if t > 0.74:
            _callout(d, sonic["bristle"], (min(1000, sonic["bristle"][0] + 10), sonic["bristle"][1] - 80), "尖端", INK, _spring(t, 0.74, 0.22))
    if t > 0.82:
        d.rounded_rectangle((70, 1580, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1640), "两边都是刷毛在动", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1705), "计时只提醒换一块牙面，不增加力气", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2607).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "软垢怎样离开牙面", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _brush(
        d,
        540,
        620,
        scale=1.0,
        ts=time_sec,
        kind="sonic" if active >= 2 else "osc",
        press=0.85 if active < 0 else 0.12,
        contact=0.15 if active < 1 else 1,
    )
    steps = ["电机", "贴住", "扫过", "移开"]
    tips = [
        "① 电机转起来，刷头跟着动",
        "② 刷毛轻轻贴上牙面",
        "③ 旋转或高频颤动，刮松软垢",
        "④ 移到下一块，没贴住的不会自己干净",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1240, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1400, 1020, 1520), radius=14, fill=(255, 253, 248))
        d.text((540, 1460), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1620), "压太重，刷毛倒伏，扫过的距离变短", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2609).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(kind="sonic", contact=0.05, press=0.1), "为什么有声音却没刷干净？", "刷毛离开牙面，就只剩下振动"),
        (0.32, dict(kind="osc", contact=1, press=0.95), "为什么越用力不一定更干净？", "刷毛被压弯，尖端路程变短"),
        (0.55, dict(kind="osc", contact=1, press=0.1, gap=1.15), "为什么牙缝里还会残留？", "比刷毛更窄的缝，摆动进不去"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _brush(d, 540, y + 250, scale=0.48, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "电机带动刷毛，贴住牙面才算刷到", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2611).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _brush(d, 380, int(560 + (1 - a) * 12), scale=0.85, ts=time_sec, kind="osc", contact=1)
    _brush(d, 720, int(560 + (1 - a) * 12), scale=0.85, ts=time_sec, kind="sonic", contact=1)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "刷毛贴着牙面扫", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1370), "声波是摆得快，不是隔空洗", font=FONT_L, fill=WATER, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1520, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1600), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1670), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1780),
            "评论区：燃气灶，还是换个别的？",
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
