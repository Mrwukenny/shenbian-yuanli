"""洗碗机分集 · 纪录片手绘风 2D。"""

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
DIRTY = (148, 124, 78)
SOAP = (120, 168, 196)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (226, 230, 234)
BODY_LT = (246, 247, 248)
PUMP = (62, 102, 146)


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


def _arm(d, cx, cy, length, ang, s, spray):
    dx, dy = math.cos(ang) * length, math.sin(ang) * length
    d.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=METAL, width=max(6, int(9 * s)))
    if spray > 0.15:
        norm = max(length, 1)
        for sign in (-0.72, -0.28, 0.34, 0.78):
            px, py = cx + dx * sign, cy + dy * sign
            jx, jy = -dy / norm * 26 * s, dx / norm * 26 * s
            d.line((px, py, px + jx, py + jy), fill=WATER, width=3)
            rad = 4 * s
            d.ellipse((px + jx - rad, py + jy - rad, px + jx + rad, py + jy + rad), fill=WATER_LT)
    d.ellipse((cx - 11 * s, cy - 11 * s, cx + 11 * s, cy + 11 * s), fill=METAL_DK, outline=INK, width=2)


def _washer(d, cx, cy, *, scale=1.0, ts=0.0, spray=1.0, heat=0.0, wash=0.0, drain=0.0, crowded=False):
    """斜孔喷臂自转，底部加热管，洗涤剂仓，过滤器和排水泵。"""
    s = scale
    bw, bh = 400 * s, 480 * s
    x0, y0 = cx - bw / 2, cy - bh / 2
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=18 * s, fill=BODY, outline=INK, width=3)
    _flat_round(d, (x0 + 16 * s, y0 + 14 * s, x0 + bw - 16 * s, y0 + 58 * s), 8 * s, BODY_LT, INK, 2)
    if s >= 0.7:
        label = "主洗" if wash > 0.45 else ("加热" if heat > 0.4 else "喷淋")
        d.text((x0 + 32 * s, y0 + 36 * s), label, font=FONT_XS, fill=INK, anchor="lm")
    cav = (x0 + 22 * s, y0 + 74 * s, x0 + bw - 22 * s, y0 + bh - 24 * s)
    _flat_round(d, cav, 12 * s, (236, 239, 242), INK, 2)

    det = (cav[0] + 14 * s, cav[1] + 16 * s)
    _flat_round(d, (det[0], det[1], det[0] + 64 * s, det[1] + 48 * s), 6 * s, WHITE, INK, 2)
    if wash > 0.4:
        d.polygon(
            [(det[0], det[1]), (det[0] + 64 * s, det[1]), (det[0] + 48 * s, det[1] - 22 * s)],
            fill=SOAP,
            outline=INK,
        )
        for i in range(3):
            bx = det[0] + 16 * s + i * 16 * s
            by = det[1] + 28 * s
            d.ellipse((bx, by, bx + 10 * s, by + 10 * s), fill=SOAP)

    upper_y = cav[1] + 150 * s
    lower_y = cav[1] + 300 * s
    for ry, n in ((upper_y - 28 * s, 4 if crowded else 3), (lower_y - 28 * s, 6 if crowded else 3)):
        d.line((cav[0] + 16 * s, ry + 24 * s, cav[2] - 16 * s, ry + 24 * s), fill=METAL_DK, width=3)
        for i in range(n):
            px = _lerp(cav[0] + 36 * s, cav[2] - 36 * s, (i + 0.5) / n)
            d.ellipse((px - 14 * s, ry, px + 14 * s, ry + 28 * s), fill=WHITE, outline=INK, width=2)

    ang = ts * 2.4 * max(spray, 0.05)
    _arm(d, cx, upper_y, 120 * s, ang, s, spray)
    _arm(d, cx, lower_y, 140 * s, -ang * 0.8, s, spray)

    heater_y = cav[3] - 48 * s
    if heat > 0.25:
        d.ellipse((cav[0] + 30 * s, heater_y - 16 * s, cav[2] - 70 * s, heater_y + 20 * s), fill=(*HOT_LT, int(90 * heat)))
    pts = []
    for k in range(16):
        f = k / 15
        px = _lerp(cav[0] + 36 * s, cav[2] - 90 * s, f)
        py = heater_y + math.sin(f * math.pi * 5 + ts * (4 if heat > 0.25 else 0.4)) * 4 * s
        pts.append((px, py))
    d.line(pts, fill=HOT if heat > 0.25 else METAL_DK, width=max(3, int(4 * s)))

    filt = (cav[0] + 16 * s, cav[3] - 36 * s, cav[0] + 70 * s, cav[3] - 8 * s)
    _flat_round(d, filt, 4 * s, DIRTY if wash > 0.3 else WHITE, INK, 2)
    for k in range(3):
        yy = _lerp(filt[1] + 4, filt[3] - 4, k / 2)
        d.line((filt[0] + 4, yy, filt[2] - 4, yy), fill=METAL_DK, width=1)

    pump = (cav[2] - 36 * s, cav[3] - 28 * s)
    d.ellipse((pump[0] - 18 * s, pump[1] - 18 * s, pump[0] + 18 * s, pump[1] + 18 * s), fill=PUMP, outline=INK, width=2)
    pang = ts * (7 if drain > 0.3 else 1.2)
    for k in range(3):
        a = pang + k * math.tau / 3
        d.line((pump[0], pump[1], pump[0] + math.cos(a) * 12 * s, pump[1] + math.sin(a) * 12 * s), fill=WHITE, width=2)
    if drain > 0.3:
        end = (x0 + bw + 8 * s, y0 + bh + 8 * s)
        d.line((pump[0], pump[1], end[0], end[1]), fill=DIRTY, width=5)
        d.ellipse((end[0] - 8 * s, end[1] - 8 * s, end[0] + 8 * s, end[1] + 8 * s), fill=DIRTY)

    return {
        "arm": (cx + 90 * s, lower_y),
        "heater": (cav[2] - 110 * s, heater_y),
        "soap": (det[0] + 64 * s, det[1] + 16 * s),
        "filter": (filt[2], (filt[1] + filt[3]) / 2),
        "drain": (pump[0] + 16 * s, pump[1]),
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=WATER if active else WHITE, outline=WATER, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WATER, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=WATER, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 611).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：洗碗机怎么把碗洗干净", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _washer(
            d,
            540 + dx,
            int(1020 + (1 - show) * 30),
            scale=0.92,
            ts=time_sec,
            spray=0.9 if t > 0.45 else 0.2,
            heat=0.8 if t > 0.6 else 0.0,
            wash=0.8 if t > 0.66 else 0.0,
            drain=0.4 if t > 0.75 else 0.0,
        )
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((90, 1460, 990, 1560), radius=12, fill=(255, 240, 235))
            d.text((540, 1510), "❌ 不是只靠猛水柱硬冲", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1420, 1010, 1640), radius=14, fill=(255, 245, 240))
            d.text((540, 1485), "✓  喷臂、加热、洗涤剂", font=FONT_L, fill=WATER, anchor="mm")
            d.text((540, 1565), "排水泵把脏水送走", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 613).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：洗的是哪几件事", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _washer(d, 360, 800, scale=1.0, ts=time_sec, spray=1, heat=0.8, wash=0.7, drain=0.5)
        if t > 0.18:
            _callout(d, parts["soap"], (800, 460), "洗涤剂", SOAP, _spring(t, 0.18, 0.22))
        if t > 0.32:
            _callout(d, parts["arm"], (800, 680), "斜孔喷臂", WATER, _spring(t, 0.32, 0.22))
        if t > 0.46:
            _callout(d, parts["heater"], (800, 900), "加热管", HOT, _spring(t, 0.46, 0.22))
        if t > 0.6:
            _callout(d, parts["filter"], (800, 1080), "过滤器", DIRTY, _spring(t, 0.6, 0.22))
        if t > 0.72:
            _callout(d, parts["drain"], (800, 1240), "排水泵", PUMP, _spring(t, 0.72, 0.22))
    if t > 0.8:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "斜孔让喷臂自己转，没有单独马达", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "碱拆油，酶拆蛋白和淀粉", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 617).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "一次洗涤，就这四步", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _washer(
        d,
        540,
        560,
        scale=0.82,
        ts=time_sec,
        spray=0.15 if active < 0 else 1.0,
        heat=1.0 if active >= 1 else 0.0,
        wash=1.0 if active >= 2 else 0.0,
        drain=1.0 if active >= 3 else 0.0,
    )
    steps = ["斜孔转臂", "加热管", "碱和酶", "排水泵"]
    tips = [
        "① 循环泵加压，斜孔推动喷臂转",
        "② 加热把油变软，药剂才好干活",
        "③ 碱拆油，酶拆蛋白和淀粉",
        "④ 排水泵抽走脏水，再漂洗烘干",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1080, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1240, 1010, 1360), radius=14, fill=(255, 253, 248))
        d.text((540, 1300), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1480), "不是超声，也不是一滩水冲到底", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 619).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(spray=0.7, heat=0.4, wash=0.5, drain=0.0, crowded=True), "为什么叠太密洗不净？", "水打不到背面，冲刷断了"),
        (0.32, dict(spray=0.3, heat=0.2, wash=0.9, drain=0.0, crowded=False), "为什么不用手洗剂？", "泡沫太多，也不适合循环泵"),
        (0.55, dict(spray=0.8, heat=0.45, wash=0.8, drain=0.2, crowded=False), "为什么节能档不太烫？", "酶在温热里工作，时间换温度"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 340 + (1 - a) * 40
        d.rounded_rectangle((70, y, 1010, y + 310), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _washer(d, 540, y + 210, scale=0.36, ts=time_sec, **kw)
    if t > 0.78:
        d.text((540, 1280), "喷臂冲，加热配药剂", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1360), "排水泵负责收尾", font=FONT_M, fill=WATER, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 621).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _washer(
        d,
        540,
        int(560 + (1 - a) * 24),
        scale=0.9,
        ts=time_sec,
        spray=1,
        heat=0.8,
        wash=0.75,
        drain=0.6,
    )
    if t > 0.2:
        d.rounded_rectangle((70, 1140, 1010, 1340), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1195), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1255), "斜孔转喷臂 · 加热配洗涤剂", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1320), "排水泵把脏水送走", font=FONT_L, fill=WATER, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1460, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1540), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1610), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1720),
            "评论区：电风扇，还是换个别的？",
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
