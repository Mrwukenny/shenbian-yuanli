"""破壁机分集 · 纪录片手绘风 2D。高速刀片加旋涡，渣汁同留；加热可选。"""

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
WATER = (70, 130, 175)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (86, 96, 104)
SLURRY = (176, 142, 72)
CHUNK = (120, 86, 48)
JUICE = (214, 170, 78)
PULP = (122, 78, 42)


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


def _flat_round(d, box, radius, fill, outline=INK, width=2):
    d.rounded_rectangle(box, radius=radius, fill=fill)
    if outline is not None:
        d.rounded_rectangle(box, radius=radius, outline=outline, width=width)


def _jar(d, cx, cy, *, scale=1.0, ts=0.0, vortex=1.0, heat=0.0, liquid=1.0, chunks=0.6, bubbles=0.0):
    """杯底刀片、杯壁凸筋、旋涡。液体不够时碎块贴壁。"""
    s = scale
    bw = 220 * s
    jar_h = 280 * s
    base_h = 78 * s
    left = cx - bw / 2
    base_top = cy + jar_h * 0.28
    d.rounded_rectangle((left - 16 * s, base_top, left + bw + 16 * s, base_top + base_h), radius=16 * s, fill=BODY, outline=INK, width=3)
    tooth = (cx, base_top + 18 * s)
    d.polygon(
        [
            (tooth[0] - 10 * s, tooth[1] + 8 * s),
            (tooth[0] + 10 * s, tooth[1] + 8 * s),
            (tooth[0] + 4 * s, tooth[1] - 10 * s),
            (tooth[0] - 4 * s, tooth[1] - 10 * s),
        ],
        fill=METAL,
    )

    jar = (left, base_top - jar_h, left + bw, base_top + 8 * s)
    d.rounded_rectangle(jar, radius=18 * s, fill=(248, 250, 252))
    d.rounded_rectangle(jar, radius=18 * s, outline=INK, width=3)
    if heat > 0.25:
        d.rectangle((jar[0] + 8 * s, jar[3] - 28 * s, jar[2] - 8 * s, jar[3] - 8 * s), fill=HOT_LT)

    liq = _clamp01(liquid)
    if liq > 0.08:
        lh = (jar_h - 36 * s) * (0.25 + 0.6 * liq)
        wet = (jar[0] + 12 * s, jar[3] - 14 * s - lh, jar[2] - 12 * s, jar[3] - 14 * s)
        d.rectangle(wet, fill=SLURRY)
        if vortex > 0.25 and liq > 0.35:
            vw = (16 + 28 * vortex) * s
            d.ellipse((cx - vw, wet[1] + 8 * s, cx + vw, wet[3] - 4 * s), outline=WHITE, width=2)
            d.line((cx, wet[1] + 10 * s, cx, wet[3] - 8 * s), fill=WHITE, width=2)
        if bubbles > 0.2:
            for i in range(5):
                bx = _lerp(wet[0] + 8 * s, wet[2] - 8 * s, (i * 0.37) % 1)
                by = _lerp(wet[1] + 8 * s, wet[3] - 8 * s, (ts * 0.2 + i / 5) % 1)
                rad = 4 * s
                d.ellipse((bx - rad, by - rad, bx + rad, by + rad), outline=WHITE, width=1)

    n = int(3 + 6 * chunks)
    for i in range(n):
        if liq < 0.35 or vortex < 0.3:
            px = jar[0] + 18 * s if i % 2 == 0 else jar[2] - 18 * s
            py = _lerp(jar[1] + 40 * s, jar[3] - 36 * s, (i % 5) / 4)
        else:
            ang = ts * 3 * max(vortex, 0.2) + i
            px = cx + math.cos(ang) * (30 + (i % 3) * 12) * s
            py = jar[3] - 40 * s - (jar_h * 0.25) + math.sin(ang) * 16 * s
        rad = (7 if chunks > 0.5 else 4) * s
        d.ellipse((px - rad, py - rad * 0.7, px + rad, py + rad * 0.7), fill=CHUNK)

    bang = ts * (10 if vortex > 0.2 else 2)
    by = jar[3] - 22 * s
    for k in range(4):
        a = bang + k * math.pi / 2
        d.line((cx, by, cx + math.cos(a) * 48 * s, by + math.sin(a) * 12 * s), fill=METAL, width=3)
    d.ellipse((cx - 7 * s, by - 7 * s, cx + 7 * s, by + 7 * s), fill=METAL_DK, outline=INK, width=1)

    for side in (-1, 1):
        x = cx + side * (bw / 2 - 18 * s)
        d.line((x, jar[1] + 48 * s, x, jar[3] - 48 * s), fill=LINE, width=4)

    lid = (jar[0] + 8 * s, jar[1] - 16 * s, jar[2] - 8 * s, jar[1] + 18 * s)
    _flat_round(d, lid, 8 * s, WHITE, INK, 2)
    vent = (cx - 10 * s, lid[1] + 4 * s, cx + 10 * s, lid[3] - 4 * s)
    d.ellipse(vent, fill=HOT_LT if heat > 0.3 else WHITE, outline=INK, width=2)
    if heat > 0.3:
        for i in range(2):
            sx = cx + (i - 0.5) * 16 * s
            sy = lid[1] - 10 * s - ((ts * 24 + i * 14) % 28)
            d.arc((sx, sy, sx + 14 * s, sy + 12 * s), 200, 340, fill=MUTED, width=2)

    return {
        "blade": (cx + 48 * s, by),
        "rib": (cx + bw / 2 - 18 * s, (jar[1] + jar[3]) / 2),
        "vent": (cx + 12 * s, lid[1]),
        "heat": (jar[2] - 8 * s, jar[3] - 18 * s),
        "base": (left + bw + 16 * s, base_top + 24 * s),
    }


def _juicer(d, cx, cy, s, ts):
    """榨汁机把渣分到旁边，杯子里主要是汁。"""
    w, h = 180 * s, 230 * s
    left, top = cx - w / 2, cy - h / 2
    d.polygon(
        [(cx, top), (left + w, top + 70 * s), (left, top + 70 * s)],
        fill=WHITE,
        outline=INK,
    )
    d.rectangle((left + 20 * s, top + 70 * s, left + w - 20 * s, top + 150 * s), fill=METAL, outline=INK, width=2)
    ang = ts * 6
    d.line((cx, top + 110 * s, cx + math.cos(ang) * 24 * s, top + 110 * s + math.sin(ang) * 10 * s), fill=WHITE, width=2)
    pulp = (left + w - 10 * s, top + 80 * s, left + w + 48 * s, top + 150 * s)
    d.rectangle(pulp, fill=PULP, outline=INK, width=2)
    cup = (left + 40 * s, top + 160 * s, left + w - 50 * s, top + h)
    d.rectangle(cup, outline=INK, width=2)
    d.rectangle((cup[0] + 4 * s, cup[1] + 16 * s, cup[2] - 4 * s, cup[3] - 4 * s), fill=JUICE)
    if s >= 0.45:
        d.text((cx, top + h + 14 * s), "榨汁机", font=FONT_XS, fill=MUTED, anchor="mm")
    return {"pulp": (pulp[2], (pulp[1] + pulp[3]) / 2), "juice": (cup[2], (cup[1] + cup[3]) / 2)}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=WATER if active else WHITE, outline=WATER, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WATER, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=WATER, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 2201).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：破壁机为什么打得成浆", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _jar(d, 540 + dx, int(1020 + (1 - show) * 20), scale=1.0, ts=time_sec, vortex=0.9, heat=0.15, liquid=0.85, chunks=0.45)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((90, 1540, 990, 1640), radius=12, fill=(255, 240, 235))
            d.text((540, 1590), "❌ 不是转速更高的榨汁机", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1500, 1010, 1700), radius=14, fill=(255, 245, 240))
            d.text((540, 1560), "✓  渣和汁都留在杯子里", font=FONT_L, fill=WATER, anchor="mm")
            d.text((540, 1640), "刀片切碎，旋涡再送回刀上", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2203).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：刀、筋、盖和加热", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _jar(d, 420, 900, scale=1.15, ts=time_sec, vortex=1, heat=0.7, liquid=0.8, chunks=0.35)
        if t > 0.2:
            _callout(d, parts["blade"], (min(980, parts["blade"][0] + 80), parts["blade"][1] + 20), "刀片", METAL_DK, _spring(t, 0.2, 0.22))
        if t > 0.38:
            _callout(d, parts["rib"], (min(980, parts["rib"][0] + 70), parts["rib"][1] - 40), "凸筋", INK, _spring(t, 0.38, 0.22))
        if t > 0.54:
            _callout(d, parts["vent"], (parts["vent"][0] + 160, parts["vent"][1] - 10), "排气盖", HOT, _spring(t, 0.54, 0.22))
        if t > 0.7:
            _callout(d, parts["heat"], (min(980, parts["heat"][0] + 60), parts["heat"][1] + 30), "加热盘", HOT, _spring(t, 0.7, 0.22))
    if t > 0.8:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "没有出渣口，纤维还在杯里", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "不加热时，它就是高速搅拌机", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2207).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "块怎么变成细浆", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _jar(
        d,
        540,
        640,
        scale=0.95,
        ts=time_sec,
        vortex=0.2 if active < 1 else 1.0,
        heat=1.0 if active >= 3 else 0.0,
        liquid=0.85,
        chunks=0.85 if active < 2 else 0.2,
    )
    steps = ["刀片转", "旋涡起", "越打越细", "可选加热"]
    tips = [
        "① 电机带动杯底刀片快转",
        "② 液体旋涡，中间下四周上",
        "③ 颗粒一次次回到刀上变细",
        "④ 要加热时，底部边搅边煮",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1180, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1340, 1010, 1460), radius=14, fill=(255, 253, 248))
        d.text((540, 1400), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1560), "液体太少，刀会空转，块还贴在杯壁", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2209).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, "dry", "为什么干果打不动？", "没有液体把它们送回刀上"),
        (0.32, "air", "为什么营养不会自动翻倍？", "细胞切开了，也更接触空气"),
        (0.55, "juice", "为什么它不是榨汁机？", "渣和汁都留在杯子里"),
    ]
    for idx, (start, kind, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 340 + (1 - a) * 40
        d.rounded_rectangle((70, y, 1010, y + 310), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        if kind == "dry":
            _jar(d, 540, y + 214, scale=0.32, ts=time_sec, vortex=0.1, liquid=0.12, chunks=0.95)
        elif kind == "air":
            _jar(d, 540, y + 214, scale=0.32, ts=time_sec, vortex=0.8, liquid=0.8, chunks=0.15, bubbles=1)
        else:
            _jar(d, 390, y + 220, scale=0.26, ts=time_sec, vortex=0.8, liquid=0.75, chunks=0.2)
            _juicer(d, 700, y + 214, 0.42, time_sec)
    if t > 0.82:
        d.text((540, 1300), "高速刀切碎，旋涡送料，渣和汁都留下", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2211).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _jar(d, 540, int(640 + (1 - a) * 16), scale=1.0, ts=time_sec, vortex=1, heat=0.45, liquid=0.8, chunks=0.2)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1380), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1235), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1295), "高速刀片切碎，旋涡送料", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1360), "渣和汁都留在杯里", font=FONT_L, fill=WATER, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1500, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1580), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1650), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1760),
            "评论区：干衣机，还是换个别的？",
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
