"""除湿机分集 · 纪录片手绘风 2D。冷排结水，热排留在室内；转轮式作对照。"""

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
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (214, 222, 226)
FROST = (236, 242, 246)
WHEEL = (196, 176, 132)


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


def _arrow(d, p1, p2, color=INK):
    _sketch_line(d, p1, p2, color, 3, int(abs(p1[0] + p2[1])) % 10000)
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    length = 12
    bx = p2[0] - math.cos(ang) * length
    by = p2[1] - math.sin(ang) * length
    px, py = -math.sin(ang) * 5, math.cos(ang) * 5
    d.polygon([(p2[0], p2[1]), (bx + px, by + py), (bx - px, by - py)], fill=color)


def _fins(d, box, color):
    d.rectangle(box, fill=_mix(WHITE, color, 0.25), outline=color, width=2)
    for i in range(6):
        x = _lerp(box[0] + 6, box[2] - 6, i / 5)
        d.line((x, box[1] + 4, x, box[3] - 4), fill=color, width=2)


def _dehu(d, cx, cy, *, scale=1.0, ts=0.0, kind="comp", frost=0.0, bucket=0.45, flow=1.0, drain=0.0):
    """压缩式：湿空气过冷排结水，再过热排。转轮式换成干燥剂圆轮。"""
    s = scale
    bw, bh = 420 * s, 460 * s
    x0, y0 = cx - bw / 2, cy - bh / 2
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=18 * s, fill=BODY, outline=INK, width=3)
    window = (x0 + 18 * s, y0 + 18 * s, x0 + bw - 18 * s, y0 + bh - 18 * s)
    d.rectangle(window, fill=(244, 242, 236))

    span = (26 if s < 0.62 else 70) * s
    mid_y = y0 + 150 * s
    if flow > 0.15:
        _arrow(d, (x0 - span, mid_y), (window[0] + 4 * s, mid_y), WATER)
        _arrow(d, (window[2] - 4 * s, mid_y - 10 * s), (x0 + bw + span * 0.8, mid_y - 28 * s), HOT)

    cold = (window[0] + 36 * s, window[1] + 36 * s, window[0] + 150 * s, window[1] + 230 * s)
    hot = (window[2] - 160 * s, window[1] + 36 * s, window[2] - 36 * s, window[1] + 230 * s)
    comp = ((cold[2] + hot[0]) / 2, cold[3] + 36 * s)
    wheel_c = (cx, y0 + 150 * s)

    if kind == "comp":
        _fins(d, cold, WATER)
        if frost > 0.2:
            fh = (cold[3] - cold[1]) * min(frost, 1)
            d.rectangle((cold[0], cold[1], cold[2], cold[1] + fh), fill=FROST)
        if frost < 0.55 and flow > 0.2:
            for i in range(5):
                u = (ts * 0.7 * flow + i / 5) % 1.0
                dx = _lerp(cold[0] + 10 * s, cold[2] - 10 * s, (i % 5) / 4)
                dy = _lerp(cold[3] - 8 * s, cold[3] + 36 * s, u)
                d.ellipse((dx - 3 * s, dy - 4 * s, dx + 3 * s, dy + 4 * s), fill=WATER)
        _fins(d, hot, HOT)
        d.ellipse((comp[0] - 22 * s, comp[1] - 22 * s, comp[0] + 22 * s, comp[1] + 22 * s), fill=METAL_DK, outline=INK, width=2)
        d.line((cold[2], cold[3] - 10 * s, comp[0], comp[1]), fill=METAL, width=3)
        d.line((comp[0], comp[1], hot[0], hot[3] - 10 * s), fill=HOT, width=3)
    else:
        rad = 70 * s
        d.ellipse((wheel_c[0] - rad, wheel_c[1] - rad, wheel_c[0] + rad, wheel_c[1] + rad), fill=WHEEL, outline=INK, width=2)
        d.ellipse((wheel_c[0] - 16 * s, wheel_c[1] - 16 * s, wheel_c[0] + 16 * s, wheel_c[1] + 16 * s), fill=WHITE, outline=INK, width=2)
        for k in range(6):
            a = ts * 0.8 + k * math.tau / 6
            d.line(
                (wheel_c[0], wheel_c[1], wheel_c[0] + math.cos(a) * rad * 0.85, wheel_c[1] + math.sin(a) * rad * 0.85),
                fill=INK,
                width=2,
            )
        heat = (wheel_c[0] - 30 * s, wheel_c[1] + rad + 8 * s, wheel_c[0] + 30 * s, wheel_c[1] + rad + 28 * s)
        d.rectangle(heat, fill=HOT_LT, outline=HOT, width=2)
        comp = (wheel_c[0], heat[3])

    buck = (window[0] + 28 * s, window[3] - 100 * s, window[2] - 28 * s, window[3] - 16 * s)
    d.rectangle(buck, fill=WHITE, outline=INK, width=2)
    level = _lerp(buck[3] - 6 * s, buck[1] + 8 * s, _clamp01(bucket))
    d.rectangle((buck[0] + 4 * s, level, buck[2] - 4 * s, buck[3] - 4 * s), fill=WATER_LT)
    d.ellipse((buck[2] - 28 * s, level - 8 * s, buck[2] - 12 * s, level + 8 * s), fill=ACCENT if bucket > 0.9 else WHITE, outline=INK, width=2)
    if drain > 0.3:
        end = (x0 + bw + 8 * s, y0 + bh + 10 * s)
        d.line(((buck[2], (buck[1] + buck[3]) / 2), end), fill=WATER, width=4)

    if s >= 0.72:
        tag = "压缩式" if kind == "comp" else "转轮式"
        d.text((cx, y0 + bh + 18 * s), tag, font=FONT_XS, fill=MUTED, anchor="mm")
    return {
        "cold": (cold[2], (cold[1] + cold[3]) / 2) if kind == "comp" else (wheel_c[0] + 70 * s, wheel_c[1]),
        "hot": (hot[0], (hot[1] + hot[3]) / 2) if kind == "comp" else (wheel_c[0], wheel_c[1] + 90 * s),
        "comp": comp,
        "bucket": (buck[2], (buck[1] + buck[3]) / 2),
        "inlet": (x0, mid_y),
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=WATER if active else WHITE, outline=WATER, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WATER, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=WATER, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 2101).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：除湿机靠什么把水取出", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _dehu(d, 540 + dx, int(1040 + (1 - show) * 24), scale=0.9, ts=time_sec, kind="comp", bucket=0.4, flow=0.9)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((70, 1540, 1010, 1640), radius=12, fill=(255, 240, 235))
            d.text((540, 1590), "❌ 不是海绵吸湿，也不降温", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1500, 1010, 1700), radius=14, fill=(255, 245, 240))
            d.text((540, 1560), "✓  冷排结水，热排留在屋里", font=FONT_L, fill=WATER, anchor="mm")
            d.text((540, 1640), "所以房间往往会更暖一点", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2103).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：水在冷排上变成水", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _dehu(d, 500, 860, scale=1.0, ts=time_sec, bucket=0.5, flow=1)
        if t > 0.2:
            _callout(d, parts["cold"], (parts["cold"][0] + 30, parts["cold"][1] - 80), "冷排", WATER, _spring(t, 0.2, 0.22))
        if t > 0.38:
            _callout(d, parts["hot"], (min(990, parts["hot"][0] + 80), parts["hot"][1] - 40), "热排", HOT, _spring(t, 0.38, 0.22))
        if t > 0.54:
            _callout(d, parts["comp"], (parts["comp"][0] + 150, parts["comp"][1]), "压缩机", METAL_DK, _spring(t, 0.54, 0.22))
        if t > 0.7:
            _callout(d, parts["bucket"], (min(990, parts["bucket"][0] + 40), parts["bucket"][1] + 46), "水箱", WATER, _spring(t, 0.7, 0.22))
    if t > 0.8:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "冷排要低于露点，水蒸气才结水", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "热排在室内，空调才把热排到室外", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2107).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "水离开空气，就这四步", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _dehu(
        d,
        540,
        620,
        scale=0.78,
        ts=time_sec,
        kind="wheel" if active >= 3 else "comp",
        frost=0.0,
        bucket=0.25 if active < 1 else 0.6,
        flow=0.3 if active < 0 else 1.0,
    )
    steps = ["湿气进", "冷排结", "热送回", "转轮式"]
    tips = [
        "① 风扇把湿空气抽过冷排",
        "② 低于露点，水蒸气凝成水",
        "③ 干空气过热排，热回房间",
        "④ 转轮式靠干燥剂，冷天更稳",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1180, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1340, 1010, 1460), radius=14, fill=(255, 253, 248))
        d.text((540, 1400), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1560), "它除湿，不负责把房间吹凉", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2109).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(kind="comp", flow=1, bucket=0.4), "为什么吹出来的是热风？", "热排在屋里，结水的热也回来"),
        (0.32, dict(kind="comp", flow=0.35, frost=0.9, bucket=0.15), "为什么天冷几乎不出水？", "冷排结霜，能凝的水变少"),
        (0.55, dict(kind="comp", flow=0.2, bucket=0.96, drain=1), "为什么水箱一满就停？", "浮子断开，排水多半靠重力"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 340 + (1 - a) * 40
        d.rounded_rectangle((70, y, 1010, y + 310), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _dehu(d, 540, y + 214, scale=0.30, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1300), "冷排结水，热排留在屋里", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2111).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _dehu(d, 360, int(640 + (1 - a) * 16), scale=0.72, ts=time_sec, kind="comp", bucket=0.55, flow=1)
    _dehu(d, 760, int(640 + (1 - a) * 16), scale=0.72, ts=time_sec, kind="wheel", bucket=0.4, flow=0.8)
    if t > 0.2:
        d.rounded_rectangle((70, 1140, 1010, 1360), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1195), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1255), "冷排把水蒸气变成水", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1320), "热留在房间里", font=FONT_L, fill=HOT, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1480, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1560), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1630), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1740),
            "评论区：破壁机，还是换个别的？",
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
