"""燃气灶分集 · 纪录片手绘风 2D。一次空气预混，二次空气烧完外焰。热电偶只负责熄火关阀。"""

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
BRASS = (196, 154, 74)
BLUE = (78, 146, 214)
BLUE_LT = (186, 214, 236)
YELLOW = (214, 164, 64)
POT = (96, 108, 118)


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


def _arrow(d, p1, p2, color=INK):
    _sketch_line(d, p1, p2, color, 3, int(abs(p1[0] + p2[1])) % 10000)
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    length = 12
    bx = p2[0] - math.cos(ang) * length
    by = p2[1] - math.sin(ang) * length
    px, py = -math.sin(ang) * 5, math.cos(ang) * 5
    d.polygon([(p2[0], p2[1]), (bx + px, by + py), (bx - px, by - py)], fill=color)


def _stove(d, cx, cy, *, scale=1.0, ts=0.0, air=0.75, lit=1.0, pot=1.0, lick=0.0, spark=0.4):
    """喷嘴、风门、火孔、蓝火或黄火、热电偶。lick 越大，火苗越往锅壁上窜。"""
    s = scale
    deck_y = cy + 10 * s
    d.rounded_rectangle((cx - 210 * s, deck_y, cx + 210 * s, deck_y + 22 * s), radius=4 * s, fill=METAL_DK, outline=INK, width=2)
    d.ellipse((cx - 78 * s, deck_y - 26 * s, cx + 78 * s, deck_y + 10 * s), fill=METAL, outline=INK, width=2)
    d.ellipse((cx - 24 * s, deck_y - 14 * s, cx + 24 * s, deck_y + 4 * s), fill=METAL_DK, outline=INK, width=1)

    flame_color = _mix(BLUE, YELLOW, 1 - _clamp01(air))
    inner = BLUE_LT if air > 0.45 else YELLOW
    if lit > 0.35:
        tall = (26 + lick * 48) * s
        for i in range(9):
            a = -math.pi * 0.85 + i * (math.pi * 1.7 / 8)
            fx = cx + math.cos(a) * 70 * s
            fy = deck_y - 6 * s + math.sin(a) * 8 * s
            hgt = tall * (0.75 + 0.25 * math.sin(ts * 7 + i))
            if air > 0.92:
                fy -= 10 * s
                hgt *= 0.7
            d.polygon([(fx - 6 * s, fy), (fx + 6 * s, fy), (fx + math.sin(ts * 5 + i) * 3 * s, fy - hgt)], fill=flame_color)
        if air > 0.4 and lick < 0.4:
            d.arc((cx - 46 * s, deck_y - 34 * s, cx + 46 * s, deck_y - 2 * s), 200, 340, fill=inner, width=2)

    pot_bottom = deck_y - 48 * s - lick * 8 * s
    if pot > 0.2:
        d.rounded_rectangle((cx - 92 * s, pot_bottom - 70 * s, cx + 92 * s, pot_bottom), radius=8 * s, fill=POT, outline=INK, width=2)
        d.ellipse((cx - 92 * s, pot_bottom - 86 * s, cx + 92 * s, pot_bottom - 52 * s), fill=_mix(POT, WHITE, 0.25), outline=INK, width=2)

    d.rectangle((cx - 7 * s, deck_y + 22 * s, cx + 7 * s, deck_y + 78 * s), fill=METAL)
    nozzle = (cx - 12 * s, deck_y + 78 * s, cx + 12 * s, deck_y + 98 * s)
    d.polygon(
        [(cx - 12 * s, nozzle[1]), (cx + 12 * s, nozzle[1]), (cx + 4 * s, nozzle[3]), (cx - 4 * s, nozzle[3])],
        fill=BRASS,
        outline=INK,
    )
    gap = (6 + _clamp01(air) * 22) * s
    shutter = (cx + 18 * s, deck_y + 80 * s, cx + 18 * s + gap, deck_y + 98 * s)
    d.rectangle(shutter, outline=WATER, width=2)
    if s >= 0.45:
        _arrow(d, (shutter[2] + 16 * s, (shutter[1] + shutter[3]) / 2), (shutter[2], (shutter[1] + shutter[3]) / 2), WATER)

    couple_hot = lit > 0.55
    d.line((cx + 58 * s, deck_y + 8 * s, cx + 58 * s, deck_y - 24 * s), fill=BRASS, width=max(2, int(3 * s)))
    d.ellipse((cx + 51 * s, deck_y - 34 * s, cx + 65 * s, deck_y - 20 * s), fill=HOT if couple_hot else METAL, outline=INK, width=1)

    if spark > 0.2 and (ts % 1.4) < 0.18:
        d.line((cx - 62 * s, deck_y - 8 * s, cx - 48 * s, deck_y + 6 * s), fill=BLUE, width=2)
    else:
        d.line((cx - 64 * s, deck_y + 4 * s, cx - 64 * s, deck_y - 16 * s), fill=METAL_DK, width=2)
    if lit < 0.3 and s >= 0.35:
        d.text((cx, deck_y + 112 * s), "火已灭", font=FONT_XS, fill=MUTED, anchor="mm")

    return {
        "nozzle": (nozzle[2], (nozzle[1] + nozzle[3]) / 2),
        "air": (shutter[2], (shutter[1] + shutter[3]) / 2),
        "port": (cx + 70 * s, deck_y - 8 * s),
        "couple": (cx + 66 * s, deck_y - 28 * s),
        "flame": (cx + 20 * s, deck_y - 36 * s),
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=BLUE if active else WHITE, outline=BLUE, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else BLUE, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=BLUE, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 2701).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：燃气灶怎样把火稳住", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _stove(d, 540 + dx, int(980 + (1 - show) * 16), scale=1.0, ts=time_sec, air=0.78, lit=1, spark=0.5)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((70, 1560, 1010, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是火越大就热得越快", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  先混空气，再点燃", font=FONT_L, fill=BLUE, anchor="mm")
            d.text((540, 1660), "蓝火对着锅底，热才进锅", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2703).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：混气、火孔和热电偶", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _stove(d, 500, 820, scale=1.05, ts=time_sec, air=0.8, lit=1, spark=0.8)
        if t > 0.18:
            _callout(d, parts["nozzle"], (parts["nozzle"][0] - 150, parts["nozzle"][1] + 20), "喷嘴", BRASS, _spring(t, 0.18, 0.2), anchor="rm")
        if t > 0.36:
            _callout(d, parts["air"], (min(1000, parts["air"][0] + 30), parts["air"][1] + 36), "风门", WATER, _spring(t, 0.36, 0.2))
        if t > 0.54:
            _callout(d, parts["port"], (min(1000, parts["port"][0] + 20), parts["port"][1] - 30), "火孔", INK, _spring(t, 0.54, 0.2))
        if t > 0.72:
            _callout(d, parts["couple"], (min(1000, parts["couple"][0] + 24), parts["couple"][1] - 16), "热电偶", HOT, _spring(t, 0.72, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "一次空气在喷嘴处混入", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "二次空气在火孔外，帮外焰烧完", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2707).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "火怎样稳住，又把锅烧热", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _stove(
        d,
        540,
        600,
        scale=0.92,
        ts=time_sec,
        air=0.78,
        lit=0.15 if active < 2 else 1,
        lick=0.05,
        spark=1 if active == 2 else 0.15,
    )
    steps = ["混气", "出孔", "点燃", "传热"]
    tips = [
        "① 燃气从喷嘴喷出，卷进一次空气",
        "② 混合气从火孔均匀冒出",
        "③ 电火花点燃，火焰连成一圈",
        "④ 外焰对着锅底，把热量传进去",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "空气不够，火焰发黄，锅底也容易黑", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2709).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(air=0.18, lit=1, lick=0.05), "为什么发黄不是更旺？", "空气不够，燃烧不充分"),
        (0.32, dict(air=0.8, lit=1, lick=1), "为什么火最大不一定更快？", "窜出锅壁的热，没有进菜里"),
        (0.55, dict(air=0.75, lit=0.0, lick=0, spark=0), "为什么溢汤以后火会灭？", "热电偶一凉，气阀就关上"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _stove(d, 540, y + 230, scale=0.42, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "先混好空气，再在外焰把热交给锅", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2711).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _stove(d, 540, int(620 + (1 - a) * 12), scale=1.0, ts=time_sec, air=0.8, lit=1, lick=0.05)
    if t > 0.2:
        d.rounded_rectangle((70, 1160, 1010, 1380), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1220), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1285), "先混空气，再点燃", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1350), "蓝火对着锅底，热才进锅", font=FONT_L, fill=BLUE, anchor="mm")
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
