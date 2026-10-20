"""电热水壶分集 · 纪录片手绘风 2D。"""

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
WATER_LT = (186, 216, 232)
STEAM = (210, 214, 218)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (236, 238, 242)
BRASS = (196, 154, 74)
SCALE_C = (176, 168, 150)
GREEN = (80, 160, 110)


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


def _point_at(pts, u):
    if len(pts) == 1:
        return pts[0]
    segs = []
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((a, b, length))
        total += length
    if total <= 0:
        return pts[-1]
    dist = _clamp01(u) * total
    for a, b, length in segs:
        if dist <= length or length == 0:
            f = 0 if length == 0 else dist / length
            return (_lerp(a[0], b[0], f), _lerp(a[1], b[1], f))
        dist -= length
    return pts[-1]


def _dots(d, pts, ts, color, n=5, speed=0.45, radius=5, limit=1.0):
    if limit <= 0.02 or not pts:
        return
    for i in range(n):
        u = (ts * speed + i / n) % 1.0
        if u > limit:
            continue
        x, y = _point_at(pts, u)
        d.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def _bimetal(d, x, y, s, tripped):
    bend = 16 * s if tripped else 3 * s
    for i, color in enumerate((BRASS, METAL_DK)):
        pts = []
        for k in range(12):
            f = k / 11
            px = x - 28 * s + f * 56 * s
            py = y + i * 5 * s + math.sin(f * math.pi) * bend
            pts.append((px, py))
        d.line(pts, fill=color, width=max(3, int(4 * s)))
    gap = 10 * s if tripped else 3 * s
    d.ellipse((x - 34 * s, y + 18 * s, x - 24 * s, y + 28 * s), fill=METAL, outline=INK, width=1)
    d.ellipse((x - 34 * s + gap + 12 * s, y + 18 * s, x - 22 * s + gap + 12 * s, y + 28 * s), fill=GREEN if tripped else HOT, outline=INK, width=1)


def _kettle(d, cx, cy, *, scale=1.0, ts=0.0, power=1.0, boil=0.0, tripped=False, limescale=0.0, lid_open=False):
    """壶底电阻发热，蒸汽沿手柄走到双金属片；过热保护贴在底板上。"""
    s = scale
    bw, bh = 250 * s, 300 * s
    x0, y0 = cx - bw / 2, cy - bh / 2 + 10 * s
    x1, y1 = x0 + bw, y0 + bh
    # 把手和蒸汽通道在壶身右侧
    handle_x = x1 + 18 * s
    d.rounded_rectangle((handle_x, y0 + 28 * s, handle_x + 36 * s, y1 - 10 * s), radius=16 * s, fill=BODY, outline=INK, width=2)
    d.line((x1 - 4 * s, y0 + 36 * s, handle_x, y0 + 48 * s), fill=METAL_DK, width=max(4, int(6 * s)))
    d.line((x1 - 4 * s, y1 - 36 * s, handle_x, y1 - 48 * s), fill=METAL_DK, width=max(4, int(6 * s)))

    d.rounded_rectangle((x0, y0, x1, y1), radius=28 * s, fill=WHITE, outline=INK, width=3)
    water_top = _lerp(y1 - 28 * s, y0 + 70 * s, 0.55)
    _flat_round(d, (x0 + 16 * s, water_top, x1 - 16 * s, y1 - 16 * s), 16 * s, _mix(WATER, WATER_LT, boil * 0.35), None, 0)
    if boil > 0.15:
        for i in range(5):
            bx = x0 + 40 * s + (i * 37 * s) % (bw - 70 * s)
            by = _lerp(y1 - 30 * s, water_top + 10 * s, (ts * 0.5 + i / 5) % 1)
            rad = (3 + i % 3) * s
            d.ellipse((bx, by, bx + rad, by + rad), fill=WHITE)
    if limescale > 0.05:
        d.rectangle((x0 + 28 * s, y1 - 28 * s, x1 - 28 * s, y1 - 14 * s), fill=(*SCALE_C, int(180 + 60 * limescale)))

    spout = (x0 - 36 * s, y0 + 78 * s, x0 + 8 * s, y0 + 118 * s)
    d.polygon([(x0 + 6 * s, y0 + 70 * s), (x0 - 40 * s, y0 + 86 * s), (x0 - 40 * s, y0 + 112 * s), (x0 + 6 * s, y0 + 124 * s)], fill=WHITE, outline=INK)
    lid_y = y0 - (28 * s if lid_open else 8 * s)
    d.rounded_rectangle((x0 + 28 * s, lid_y, x1 - 28 * s, y0 + 16 * s), radius=8 * s, fill=METAL, outline=INK, width=2)
    d.ellipse((cx - 8 * s, lid_y - 16 * s, cx + 8 * s, lid_y), fill=METAL_DK, outline=INK, width=1)

    plate = (x0 + 18 * s, y1 - 8 * s, x1 - 18 * s, y1 + 28 * s)
    plate_fill = HOT if power > 0.4 and not tripped else METAL_DK
    _flat_round(d, plate, 8 * s, plate_fill, INK, 2)
    if power > 0.4 and not tripped and s >= 0.7:
        pts = []
        for k in range(10):
            f = k / 9
            pts.append((_lerp(plate[0] + 16 * s, plate[2] - 16 * s, f), (plate[1] + plate[3]) / 2 + math.sin(f * 8 + ts * 6) * 3 * s))
        d.line(pts, fill=HOT_LT, width=3)
    base = (x0 - 10 * s, y1 + 36 * s, x1 + 46 * s, y1 + 78 * s)
    d.rounded_rectangle(base, radius=10 * s, fill=METAL_DK, outline=INK, width=2)
    d.ellipse((x0 + 16 * s, y1 + 50 * s, x0 + 30 * s, y1 + 64 * s), fill=BRASS)
    d.ellipse((x0 + 40 * s, y1 + 50 * s, x0 + 54 * s, y1 + 64 * s), fill=BRASS)

    switch = (handle_x - 8 * s, y1 - 86 * s)
    _flat_round(d, (switch[0], switch[1], switch[0] + 62 * s, switch[1] + 70 * s), 8 * s, WHITE, INK, 2)
    _bimetal(d, switch[0] + 30 * s, switch[1] + 22 * s, s, tripped)
    cutout = (plate[2] - 16 * s, plate[1] + 8 * s)
    d.ellipse((cutout[0] - 9 * s, cutout[1] - 9 * s, cutout[0] + 9 * s, cutout[1] + 9 * s), fill=ACCENT if limescale > 0.4 else BRASS, outline=INK, width=2)

    steam_limit = 0.15 if lid_open else boil
    path = [
        (cx, water_top + 8 * s),
        (cx, y0 + 8 * s),
        (handle_x + 16 * s, y0 + 40 * s),
        (handle_x + 16 * s, switch[1] + 8 * s),
    ]
    if not lid_open:
        _dots(d, path, ts, STEAM, n=5, speed=0.55, radius=4.5 * s, limit=steam_limit if boil < 0.85 else 1.0)
    else:
        _dots(d, [(cx, y0), (cx, y0 - 70 * s)], ts, STEAM, n=4, speed=0.6, radius=5 * s, limit=0.9)

    return {
        "plate": (cx, (plate[1] + plate[3]) / 2),
        "steam": (handle_x + 16 * s, y0 + 120 * s),
        "bimetal": (switch[0] + 54 * s, switch[1] + 28 * s),
        "cutout": cutout,
        "lid": (cx, lid_y),
        "base": ((base[0] + base[2]) / 2, (base[1] + base[3]) / 2),
        "spout": spout,
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=HOT if active else WHITE, outline=HOT, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else HOT, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=HOT, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 511).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：电热水壶怎么知道水开了", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _kettle(
            d,
            500 + dx,
            int(980 + (1 - show) * 40),
            scale=1.15,
            ts=time_sec,
            power=0.2 if t > 0.7 else 0.95,
            boil=0.95 if t > 0.55 else 0.2,
            tripped=t > 0.7,
        )
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((90, 1480, 990, 1580), radius=12, fill=(255, 240, 235))
            d.text((540, 1530), "❌ 不是读到一百度才关机", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1460, 1010, 1660), radius=14, fill=(255, 245, 240))
            d.text((540, 1520), "✓  蒸汽推动双金属片", font=FONT_L, fill=HOT, anchor="mm")
            d.text((540, 1600), "咔哒断开。干烧另有过热保护", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 513).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：谁在烧，谁在跳", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _kettle(d, 380, 800, scale=1.15, ts=time_sec, power=0.95, boil=0.85, tripped=False)
        if t > 0.18:
            _callout(d, parts["steam"], (860, 480), "蒸汽通道", MUTED, _spring(t, 0.18, 0.22))
        if t > 0.34:
            _callout(d, parts["bimetal"], (860, 700), "双金属片", BRASS, _spring(t, 0.34, 0.22))
        if t > 0.5:
            _callout(d, parts["plate"], (860, 960), "电热盘", HOT, _spring(t, 0.5, 0.22))
        if t > 0.66:
            _callout(d, parts["cutout"], (860, 1160), "过热保护", ACCENT, _spring(t, 0.66, 0.22))
    if t > 0.8:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "电阻发热，蒸汽走到双金属片", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "干烧保护贴在底板，不靠蒸汽", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 517).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "水开跳闸，就这四步", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _kettle(
        d,
        500,
        620,
        scale=1.05,
        ts=time_sec,
        power=0.15 if active >= 3 else 1.0,
        boil=0.15 if active <= 0 else (0.45 if active == 1 else 0.95),
        tripped=active >= 3,
    )
    steps = ["电阻烧水", "底板冒泡", "蒸汽到位", "金属片跳开"]
    tips = [
        "① 电阻发热，底板把热传给水",
        "② 先冒小泡，金属片还没弯够",
        "③ 沸腾后蒸汽冲进手柄通道",
        "④ 双金属片弯曲，顶开触点",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1140, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1300, 1010, 1420), radius=14, fill=(255, 253, 248))
        d.text((540, 1360), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1540), "等的是蒸汽。高山上不到一百度也会跳", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 519).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(power=1.0, boil=0.7, tripped=False, limescale=0.0, lid_open=False), "为什么最后不放慢？", "没跳闸前一直是满功率"),
        (0.32, dict(power=0.3, boil=0.25, tripped=True, limescale=0.85, lid_open=False), "为什么水垢多了会早跳？", "底板先过热，过热保护先动"),
        (0.55, dict(power=1.0, boil=0.8, tripped=False, limescale=0.0, lid_open=True), "为什么大开盖子不跳？", "蒸汽没进通道，金属片收不到热"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 340 + (1 - a) * 40
        d.rounded_rectangle((70, y, 1010, y + 310), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _kettle(d, 520, y + 210, scale=0.48, ts=time_sec, **kw)
    if t > 0.78:
        d.text((540, 1280), "电阻发热，蒸汽推开金属片", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1360), "干烧是另一道保护", font=FONT_M, fill=ACCENT, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 521).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _kettle(
        d,
        500,
        int(560 + (1 - a) * 30),
        scale=1.15,
        ts=time_sec,
        power=0.15 if t > 0.55 else 0.95,
        boil=0.95,
        tripped=t > 0.55,
    )
    if t > 0.2:
        d.rounded_rectangle((70, 1120, 1010, 1320), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1175), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1235), "电阻发热 · 蒸汽找金属片", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1300), "咔哒一声就断电", font=FONT_L, fill=HOT, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1440, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1520), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1590), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1700),
            "评论区：洗碗机，还是换个别的？",
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
