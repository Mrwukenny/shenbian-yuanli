"""电熨斗分集 · 纪录片手绘风 2D。热和水松开纤维，底板压在烫板上把新形状定住。"""

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
WATER_LT = (186, 214, 232)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (214, 216, 220)
BOARD = (196, 168, 132)
CLOTH = (236, 232, 224)
BRASS = (196, 154, 74)
SCORCH = (146, 84, 46)


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


def _iron(d, cx, cy, *, scale=1.0, ts=0.0, heat=0.75, steam=0.7, lift=0.0, scorch=0.0):
    """底板、温控、水箱和蒸汽孔。lift 越大，熨斗离烫板越远。"""
    s = scale
    board_y = cy + (78 + lift * 46) * s
    d.rounded_rectangle((cx - 230 * s, board_y, cx + 250 * s, board_y + 26 * s), radius=4 * s, fill=BOARD, outline=INK, width=2)
    cloth = (cx - 180 * s, board_y - 10 * s, cx + 200 * s, board_y + 2 * s)
    d.rectangle(cloth, fill=CLOTH, outline=LINE, width=1)
    amp = (1 - _clamp01(heat) * (1 - lift)) * 7 * s
    if amp > 1:
        for i in range(3):
            yy = cloth[1] + 3 * s + i * 3 * s
            pts = []
            for k in range(9):
                x = _lerp(cloth[0] + 8 * s, cloth[2] - 8 * s, k / 8)
                pts.append((x, yy + math.sin(k * 1.2 + i + ts) * amp))
            d.line(pts, fill=MUTED, width=2)
    if scorch > 0.4:
        d.ellipse((cx + 20 * s, cloth[1] - 2 * s, cx + 58 * s, cloth[3] + 2 * s), fill=SCORCH)

    sole = _mix(METAL, HOT, heat)
    if scorch > 0.4:
        sole = _mix(sole, SCORCH, 0.45)
    d.polygon(
        [
            (cx - 78 * s, cy + 8 * s),
            (cx + 108 * s, cy - 6 * s),
            (cx + 108 * s, cy + 22 * s),
            (cx - 58 * s, cy + 34 * s),
        ],
        fill=sole,
        outline=INK,
    )
    d.polygon(
        [
            (cx - 52 * s, cy + 6 * s),
            (cx + 78 * s, cy - 16 * s),
            (cx + 48 * s, cy - 62 * s),
            (cx - 36 * s, cy - 42 * s),
        ],
        fill=BODY,
        outline=INK,
    )
    d.arc((cx - 10 * s, cy - 128 * s, cx + 86 * s, cy - 18 * s), 200, 10, fill=METAL_DK, width=max(3, int(7 * s)))
    d.ellipse((cx + 6 * s, cy - 40 * s, cx + 30 * s, cy - 16 * s), fill=WHITE, outline=BRASS, width=2)
    d.rounded_rectangle((cx - 34 * s, cy - 36 * s, cx - 10 * s, cy - 6 * s), radius=3 * s, fill=WATER_LT, outline=WATER, width=2)

    holes = []
    for i in range(4):
        hx = cx - 24 * s + i * 26 * s
        hy = cy + 16 * s
        holes.append((hx, hy))
        d.ellipse((hx, hy, hx + 7 * s, hy + 5 * s), fill=INK)
        if steam > 0.35 and heat > 0.4:
            u = (ts * 0.7 + i * 0.22) % 1.0
            sy = hy - (10 + u * 22) * s
            d.arc((hx - 4 * s, sy, hx + 16 * s, sy + 14 * s), 200, 340, fill=MUTED, width=2)
    if s >= 0.7 and heat < 0.35:
        d.text((cx, cy + 52 * s), "底板未热", font=FONT_XS, fill=MUTED, anchor="mm")
    return {
        "sole": (cx + 108 * s, cy + 8 * s),
        "stat": (cx + 32 * s, cy - 28 * s),
        "tank": (cx - 36 * s, cy - 20 * s),
        "hole": (holes[2][0], holes[2][1]),
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=ACCENT if active else WHITE, outline=ACCENT, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else ACCENT, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=ACCENT, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 2801).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：电熨斗怎样把褶压平", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _iron(d, 540 + dx, int(980 + (1 - show) * 16), scale=1.0, ts=time_sec, heat=0.8, steam=0.75, lift=0.05)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((70, 1560, 1010, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是越烫就越能压平", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  热和水松开，压力定住", font=FONT_L, fill=ACCENT, anchor="mm")
            d.text((540, 1660), "底板压在烫板上，裤线才出来", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2803).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：底板、蒸汽和温控", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _iron(d, 500, 860, scale=1.05, ts=time_sec, heat=0.82, steam=0.8, lift=0.0)
        if t > 0.18:
            _callout(d, parts["sole"], (min(1000, parts["sole"][0] + 10), parts["sole"][1] + 36), "电热丝", HOT, _spring(t, 0.18, 0.2))
        if t > 0.36:
            _callout(d, parts["stat"], (min(1000, parts["stat"][0] + 24), parts["stat"][1] - 20), "温控", BRASS, _spring(t, 0.36, 0.2))
        if t > 0.54:
            _callout(d, parts["hole"], (parts["hole"][0] - 160, parts["hole"][1] + 48), "蒸汽孔", WATER, _spring(t, 0.54, 0.2), anchor="rm")
        if t > 0.72:
            _callout(d, parts["tank"], (parts["tank"][0] - 140, parts["tank"][1] - 16), "水箱", WATER, _spring(t, 0.72, 0.2), anchor="rm")
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "热和水松开纤维间的小手", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "压力把新形状压在烫板上", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2807).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "褶怎样被压成新形状", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _iron(
        d,
        540,
        640,
        scale=0.92,
        ts=time_sec,
        heat=0.3 if active < 0 else 0.85,
        steam=0.05 if active < 1 else 0.85,
        lift=0.7 if active < 3 else 0.0,
    )
    steps = ["加热", "出汽", "变软", "压平"]
    tips = [
        "① 电热丝把底板加热到设定温度",
        "② 水遇热变成蒸汽，从小孔喷出",
        "③ 纤维暂时变软，原来的褶能改",
        "④ 底板贴着烫板，把新形状压住",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "只有蒸汽、没有压力，压不出裤线", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2809).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(heat=0.7, steam=0.8, lift=0.85), "为什么挂烫压不出裤线？", "几乎不施压，靠衣服自己的重量"),
        (0.32, dict(heat=1, steam=0.2, lift=0, scorch=1), "为什么温度太高布会发黄？", "热超过纤维能受的上限"),
        (0.55, dict(heat=0.15, steam=0.9, lift=0.1), "为什么有水却不出蒸汽？", "底板还没热够，水变不成汽"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _iron(d, 540, y + 230, scale=0.42, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "热和水松开纤维，压力定住新形状", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2811).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _iron(d, 540, int(640 + (1 - a) * 12), scale=1.0, ts=time_sec, heat=0.8, steam=0.7, lift=0.0)
    if t > 0.2:
        d.rounded_rectangle((70, 1160, 1010, 1380), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1220), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1285), "热和水先松开", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1350), "底板压在烫板上，褶才定住", font=FONT_L, fill=ACCENT, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1500, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1580), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1650), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
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
