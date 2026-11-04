"""剃须刀分集 · 纪录片手绘风 2D。网罩把皮留在外面，内刀切断钻进孔的胡茬。"""

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
WATER = (70, 130, 175)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (214, 216, 220)
SKIN = (232, 196, 174)
HAIR = (62, 48, 40)


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


def _shaver(d, cx, cy, *, scale=1.0, ts=0.0, mode="rotary", press=0.0, long_hair=0.0, nib=0.0, spin=1.0, caption=""):
    """网罩在外，内刀在里。rotary 是三只圆网，foil 是一片平网。"""
    s = scale
    bob = 6 * s if press > 0.5 else math.sin(ts * 2.2) * 4 * s
    cy = cy + bob
    d.rectangle((cx - 34 * s, cy - 24 * s, cx + 34 * s, cy + 6 * s), fill=BODY)
    body = (cx - 68 * s, cy - 4 * s, cx + 68 * s, cy + 214 * s)
    d.rounded_rectangle(body, radius=26 * s, fill=BODY, outline=INK, width=3)
    d.rounded_rectangle((cx - 16 * s, cy + 36 * s, cx + 16 * s, cy + 70 * s), radius=6 * s, fill=ACCENT)
    motor = (cx, cy + 140 * s)
    d.ellipse((cx - 26 * s, cy + 114 * s, cx + 26 * s, cy + 166 * s), fill=WHITE, outline=METAL_DK, width=2)
    ang = ts * 9 * max(spin, 0.05)
    d.line((motor[0], motor[1], motor[0] + math.cos(ang) * 16 * s, motor[1] + math.sin(ang) * 16 * s), fill=ACCENT, width=3)
    d.rounded_rectangle((cx - 112 * s, cy - 168 * s, cx + 112 * s, cy - 8 * s), radius=18 * s, fill=METAL, outline=INK, width=3)
    trimmer = (body[0] - 10 * s, cy + 96 * s)
    d.rectangle((body[0] - 18 * s, cy + 64 * s, body[0] - 2 * s, cy + 128 * s), fill=METAL_DK, outline=INK, width=2)
    blade = (cx, cy - 88 * s)
    foil = (cx + 96 * s, cy - 140 * s)
    if mode == "foil":
        for i in range(8):
            y = cy - 150 * s + i * 16 * s
            d.line((cx - 90 * s, y, cx + 90 * s, y), fill=METAL_DK, width=2)
        ox = math.sin(ts * 9 * max(spin, 0.2)) * 22 * s
        d.rounded_rectangle((cx - 40 * s + ox, cy - 108 * s, cx + 40 * s + ox, cy - 86 * s), radius=4 * s, fill=ACCENT if spin > 0.4 else METAL_DK, outline=INK, width=2)
        blade = (cx + ox, cy - 96 * s)
        if press > 0.5:
            rad = max(18, 24 * s)
            d.ellipse((cx - rad, cy - 108 * s - rad * 0.4, cx + rad * 0.8, cy - 96 * s + rad), fill=SKIN, outline=(160, 100, 80), width=2)
        if long_hair > 0.5:
            for i in range(4):
                x = cx - 54 * s + i * 36 * s
                d.line((x, cy - 152 * s, x - 22 * s, cy - 152 * s - max(46, 70 * s)), fill=HAIR, width=max(3, int(4 * s)))
        if nib > 0.5:
            d.line((cx, cy - 186 * s, cx, cy - 118 * s), fill=HAIR, width=3)
    else:
        centers = []
        for i in range(3):
            hx = cx + (i - 1) * 64 * s
            hy = cy - 88 * s
            centers.append((hx, hy))
            d.ellipse((hx - 28 * s, hy - 28 * s, hx + 28 * s, hy + 28 * s), fill=METAL_DK, outline=INK, width=2)
            d.ellipse((hx - 16 * s, hy - 16 * s, hx + 16 * s, hy + 16 * s), outline=WHITE, width=2)
            ca = ts * 7 * max(spin, 0.05) + i
            d.line((hx - math.cos(ca) * 13 * s, hy - math.sin(ca) * 13 * s, hx + math.cos(ca) * 13 * s, hy + math.sin(ca) * 13 * s), fill=ACCENT if spin > 0.4 else METAL, width=3)
        blade = centers[1]
        foil = (centers[2][0] + 6 * s, centers[2][1] - 30 * s)
        if press > 0.5:
            hx, hy = centers[1]
            rad = max(16, 22 * s)
            d.ellipse((hx - rad, hy - rad * 0.75, hx + rad, hy + rad * 0.85), fill=SKIN, outline=(160, 100, 80), width=2)
        if long_hair > 0.5:
            for hx, hy in centers:
                reach = max(42, 72 * s)
                d.line((hx - 6 * s, hy - 24 * s, hx - 18 * s, hy - 24 * s - reach), fill=HAIR, width=max(3, int(4 * s)))
                d.line((hx + 8 * s, hy - 22 * s, hx + 2 * s, hy - 22 * s - reach * 0.85), fill=HAIR, width=max(3, int(4 * s)))
        if nib > 0.5:
            hx, hy = centers[1]
            d.line((hx, hy - 52 * s, hx, hy - 2 * s), fill=HAIR, width=3)
    if caption and s >= 0.55:
        d.text((cx, cy + 242 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
    if s >= 0.75 and press > 0.5:
        d.text((cx, cy - 198 * s), "皮被按进孔", font=FONT_XS, fill=ACCENT, anchor="mm")
    elif s >= 0.75 and long_hair > 0.5:
        d.text((cx, cy - 198 * s), "胡子太长", font=FONT_XS, fill=MUTED, anchor="mm")
    return {"foil": foil, "blade": blade, "motor": motor, "trimmer": trimmer}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=ACCENT if active else WHITE, outline=ACCENT, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else ACCENT, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=ACCENT, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 3301).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：剃须刀怎样切断胡茬", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        y = int(1040 + (1 - show) * 16)
        _shaver(d, 300 + dx, y, scale=0.72, ts=time_sec, mode="rotary", caption="圆网")
        _shaver(d, 780 + dx, y, scale=0.72, ts=time_sec, mode="foil", caption="平网")
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是刀片贴着脸刮", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  网罩挡皮，内刀去切", font=FONT_L, fill=ACCENT, anchor="mm")
            d.text((540, 1660), "贴着走，别把皮按进孔里", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3303).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：网罩、内刀和电机", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _shaver(d, 500, 860, scale=1.0, ts=time_sec, mode="rotary", caption="圆网")
        if t > 0.18:
            _callout(d, parts["foil"], (min(1000, parts["foil"][0] + 16), parts["foil"][1] - 36), "网罩", INK, _spring(t, 0.18, 0.2))
        if t > 0.36:
            _callout(d, parts["blade"], (parts["blade"][0] - 180, parts["blade"][1] - 10), "内刀", ACCENT, _spring(t, 0.36, 0.2), anchor="rm")
        if t > 0.54:
            _callout(d, parts["motor"], (min(1000, parts["motor"][0] + 80), parts["motor"][1]), "电机", METAL_DK, _spring(t, 0.54, 0.2))
        if t > 0.72:
            _callout(d, parts["trimmer"], (parts["trimmer"][0] - 120, parts["trimmer"][1] - 10), "修剪器", INK, _spring(t, 0.72, 0.2), anchor="rm")
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "网在外，刀在内，两边都一样", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "刀头浮动是为了贴脸，不是为了按瘪", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3307).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "胡茬怎样被切断", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _shaver(
        d,
        540,
        640,
        scale=0.86,
        ts=time_sec,
        mode="rotary",
        spin=0.15 if active < 0 else 1,
        nib=1 if active >= 1 else 0,
    )
    steps = ["内刀", "进孔", "切断", "留外"]
    tips = [
        "① 电机带动内刀转动或来回",
        "② 又细又硬的胡茬钻进小孔",
        "③ 内刀从孔边切过，把茬剪断",
        "④ 皮肤被网托住，留在外面",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "贴着走，别把网罩按瘪", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3309).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(mode="rotary", press=1), "为什么按痛也不更干净？", "皮肤鼓进孔，刀碰到的是皮"),
        (0.32, dict(mode="foil"), "为什么平网圆网都能用？", "都是网在外，刀在里面切"),
        (0.55, dict(mode="rotary", long_hair=1), "为什么长胡子会打滑？", "太长会倒伏，进不了小孔"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _shaver(d, 540, y + 250, scale=0.38, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "网罩挡住皮，内刀切断钻进来的胡子", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3311).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _shaver(d, 540, int(680 + (1 - a) * 12), scale=0.78, ts=time_sec, mode="rotary", nib=0.8)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "网罩把皮留在外面", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "钻进孔的，才被切断", font=FONT_L, fill=ACCENT, anchor="mm")
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
