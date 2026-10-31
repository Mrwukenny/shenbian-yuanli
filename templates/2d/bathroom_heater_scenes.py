"""浴霸分集 · 纪录片手绘风 2D。灯暖靠红外线烤人和墙，风暖先把空气吹热。"""

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

YELLOW = (214, 164, 64)
CLOTH = (214, 206, 196)

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



def _unit(d, cx, cy, *, scale=1.0, ts=0.0, mode="lamp", blocked=0.0):
    """吸顶浴霸。mode=lamp 画红外灯泡，mode=fan 画风机和 PTC。旁边始终有换气口。"""
    s = scale
    d.line((cx - 230 * s, cy - 180 * s, cx + 250 * s, cy - 180 * s), fill=LINE, width=4)
    house = (cx - 200 * s, cy - 168 * s, cx + 160 * s, cy - 36 * s)
    d.rounded_rectangle(house, radius=14 * s, fill=BODY, outline=INK, width=3)
    bulb = (cx - 40 * s, cy - 100 * s)
    fan = (cx - 70 * s, cy - 102 * s)
    ptc = (cx + 70 * s, cy - 102 * s)
    if mode == "lamp":
        centers = []
        for i in range(3):
            bx = cx - 130 * s + i * 90 * s
            centers.append((bx, cy - 100 * s))
            d.ellipse((bx - 26 * s, cy - 138 * s, bx + 26 * s, cy - 86 * s), fill=YELLOW, outline=INK, width=2)
            for k in range(3):
                d.line((bx, cy - 84 * s, bx + (k - 1) * 18 * s, cy + 70 * s), fill=YELLOW, width=2)
        bulb = centers[1]
        if 0.65 <= s < 0.76:
            d.text((cx - 20 * s, cy + 96 * s), "空气仍凉", font=FONT_XS, fill=WATER, anchor="mm")
    else:
        d.ellipse((cx - 120 * s, cy - 146 * s, cx - 28 * s, cy - 54 * s), fill=WHITE, outline=METAL_DK, width=3)
        ang = ts * 9
        d.line(
            (cx - 74 * s, cy - 100 * s, cx - 74 * s + math.cos(ang) * 28 * s, cy - 100 * s + math.sin(ang) * 28 * s),
            fill=METAL_DK,
            width=3,
        )
        fan = (cx - 74 * s, cy - 100 * s)
        hotness = 0.25 if blocked > 0.5 else 0.9
        ptc_box = (cx - 8 * s, cy - 140 * s, cx + 78 * s, cy - 70 * s)
        d.rounded_rectangle(ptc_box, radius=6 * s, fill=_mix(METAL, HOT, hotness), outline=INK, width=2)
        ptc = (ptc_box[2], (ptc_box[1] + ptc_box[3]) / 2)
        if blocked > 0.5:
            d.rounded_rectangle((cx - 110 * s, cy - 30 * s, cx + 40 * s, cy + 6 * s), radius=4 * s, fill=CLOTH, outline=INK, width=2)
        else:
            for i in range(3):
                u = (ts * 0.9 + i / 3) % 1.0
                y = _lerp(cy - 24 * s, cy + 86 * s, u)
                x = cx - 40 * s + i * 16 * s
                d.polygon([(x, y), (x + 18 * s, y), (x + 8 * s, y + 16 * s)], fill=HOT)
    vent = (cx + 180 * s, cy - 20 * s, cx + 250 * s, cy + 64 * s)
    d.rounded_rectangle(vent, radius=8 * s, fill=WHITE, outline=WATER, width=2)
    d.line((vent[2] - 8 * s, (vent[1] + vent[3]) / 2, vent[2] + 36 * s, vent[1] - 16 * s), fill=WATER, width=3)
    if s >= 0.7:
        d.text(((vent[0] + vent[2]) / 2, vent[3] + 16 * s), "换气", font=FONT_XS, fill=WATER, anchor="mm")
    return {"bulb": bulb, "fan": fan, "ptc": ptc, "vent": (vent[0], (vent[1] + vent[3]) / 2)}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=HOT if active else WHITE, outline=HOT, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else HOT, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=HOT, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 3101).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：浴霸怎样让浴室暖和", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _unit(d, 300 + dx, int(980 + (1 - show) * 12), scale=0.72, ts=time_sec, mode="lamp")
        _unit(d, 760 + dx, int(980 + (1 - show) * 12), scale=0.72, ts=time_sec, mode="fan")
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是灯亮了空气就热", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  灯暖烤人，风暖加热空气", font=FONT_L, fill=HOT, anchor="mm")
            d.text((540, 1660), "两条路，热到达的顺序不一样", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3103).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：灯丝、PTC 和换气", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        lamp = _unit(d, 300, 860, scale=0.78, ts=time_sec, mode="lamp")
        fan = _unit(d, 760, 860, scale=0.78, ts=time_sec, mode="fan")
        if t > 0.18:
            _callout(d, lamp["bulb"], (lamp["bulb"][0] - 20, lamp["bulb"][1] - 70), "灯丝", YELLOW, _spring(t, 0.18, 0.2), anchor="mm")
        if t > 0.36:
            _callout(d, (lamp["bulb"][0], lamp["bulb"][1] + 80), (lamp["bulb"][0] - 40, lamp["bulb"][1] + 130), "红外线", ACCENT, _spring(t, 0.36, 0.2), anchor="rm")
        if t > 0.54:
            _callout(d, fan["ptc"], (min(1000, fan["ptc"][0] + 10), fan["ptc"][1] - 36), "PTC", HOT, _spring(t, 0.54, 0.2))
        if t > 0.72:
            _callout(d, fan["vent"], (min(1020, fan["vent"][0] + 16), fan["vent"][1] + 40), "换气", WATER, _spring(t, 0.72, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "红外线先被人和墙吸收", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "风暖先加热空气，换气是另一条风路", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3107).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "热怎样到你身上", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    mode = "fan" if active >= 2 else "lamp"
    _unit(d, 540, 760, scale=0.95, ts=time_sec, mode=mode, blocked=0.0)
    steps = ["选路", "灯暖", "风暖", "限温"]
    tips = [
        "① 先看开的是灯暖还是风暖",
        "② 红外线穿过空气，打到人和墙",
        "③ 风机把空气吹过发热体",
        "④ PTC 越热，电阻越大，功率下降",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "灯暖不靠烤热整屋空气", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3109).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(mode="lamp"), "为什么人暖了空气还凉？", "红外线先被皮肤和墙壁吸收"),
        (0.32, dict(mode="fan", blocked=0.0), "为什么风暖要等一会儿？", "得先加热一大团空气"),
        (0.55, dict(mode="fan", blocked=1.0), "为什么出风口不能堵住？", "热带不走，PTC 会自己降功率"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _unit(d, 540, y + 250, scale=0.4, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "灯暖烤人和墙，风暖先加热空气", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3111).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    y = int(760 + (1 - a) * 12)
    _unit(d, 300, y, scale=0.7, ts=time_sec, mode="lamp")
    _unit(d, 760, y, scale=0.7, ts=time_sec, mode="fan")
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "灯暖靠红外线", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "风暖靠热空气吹过来", font=FONT_L, fill=HOT, anchor="mm")
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
