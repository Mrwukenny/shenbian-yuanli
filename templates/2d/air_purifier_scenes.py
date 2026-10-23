"""空气净化器分集 · 纪录片手绘风 2D。风扇抽气，纤维拦颗粒，活性炭暂时吸附。"""

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
BODY = (226, 230, 234)
PRE = (214, 206, 190)
HEPA = (214, 224, 230)
CARBON = (86, 82, 76)
DUST = (164, 142, 104)
ODOR = (118, 146, 96)
GAS = (186, 198, 206)


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


def _fan_disc(d, cx, cy, s, ts, spin=1.0):
    r = 26 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=METAL_DK, outline=INK, width=2)
    ang = ts * 8 * max(spin, 0.05)
    for k in range(3):
        a = ang + k * math.tau / 3
        d.line((cx, cy, cx + math.cos(a) * r * 0.72, cy + math.sin(a) * r * 0.72), fill=WHITE, width=2)


def _arrow(d, p1, p2, color=INK):
    _sketch_line(d, p1, p2, color, 3, int(p1[0] + p2[1]))
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    length = 14
    bx = p2[0] - math.cos(ang) * length
    by = p2[1] - math.sin(ang) * length
    px, py = -math.sin(ang) * 6, math.cos(ang) * 6
    d.polygon([(p2[0], p2[1]), (bx + px, by + py), (bx - px, by - py)], fill=color)


def _motes(d, x0, y0, x1, y1, ts, n, color, speed=0.45):
    for i in range(n):
        u = (ts * speed + i / max(n, 1)) % 1.0
        px = _lerp(x0, x1, u)
        py = _lerp(y0, y1, (i % 4) / 3) + math.sin(ts * 3 + i) * 5
        rad = 3.2
        d.ellipse((px - rad, py - rad, px + rad, py + rad), fill=color)


def _purifier(d, cx, cy, *, scale=1.0, ts=0.0, flow=1.0, dust=0.7, clog=0.0, carbon=0.3, leak=0.0, gas=0.0, odor_in=0.0, odor_out=0.0):
    """塔式剖视：底进风，粗网、折叠纤维、活性炭，风扇把空气送回顶部。"""
    s = scale
    bw, bh = 280 * s, 500 * s
    x0, y0 = cx - bw / 2, cy - bh / 2
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=26 * s, fill=BODY, outline=INK, width=3)
    _flat_round(d, (x0 + 28 * s, y0 + 16 * s, x0 + bw - 28 * s, y0 + 52 * s), 8 * s, WHITE, INK, 2)
    for i in range(5):
        yy = y0 + 24 * s + i * 6 * s
        d.line((x0 + 48 * s, yy, x0 + bw - 48 * s, yy), fill=METAL, width=2)

    stack_top = y0 + 78 * s
    stack_bot = y0 + bh - 118 * s
    left, right = x0 + 36 * s, x0 + bw - 36 * s
    span = stack_bot - stack_top
    carbon_box = (left, stack_top, right, stack_top + span * 0.22)
    hepa_box = (left, carbon_box[3] + 10 * s, right, carbon_box[3] + 10 * s + span * 0.46)
    pre_box = (left, hepa_box[3] + 10 * s, right, stack_bot)

    sat = _clamp01(carbon)
    d.rectangle(carbon_box, fill=_mix((120, 114, 104), CARBON, 0.35 + 0.65 * sat), outline=INK, width=2)
    for k in range(6):
        px = _lerp(carbon_box[0] + 16 * s, carbon_box[2] - 16 * s, (k % 3) / 2)
        py = _lerp(carbon_box[1] + 10 * s, carbon_box[3] - 10 * s, (k // 3))
        d.ellipse((px - 5 * s, py - 4 * s, px + 5 * s, py + 4 * s), outline=WHITE, width=1)

    pleat = _mix(HEPA, DUST, clog * 0.75)
    d.rectangle(hepa_box, fill=pleat, outline=INK, width=2)
    folds = 7
    for i in range(folds):
        x = _lerp(hepa_box[0] + 8 * s, hepa_box[2] - 8 * s, i / (folds - 1))
        d.line((x, hepa_box[1] + 4 * s, x, hepa_box[3] - 4 * s), fill=METAL_DK, width=2)
    stuck = int((4 + 8 * dust) * (0.4 + clog))
    for i in range(stuck):
        sx = _lerp(hepa_box[0] + 10 * s, hepa_box[2] - 10 * s, (i * 0.37) % 1)
        sy = _lerp(hepa_box[1] + 8 * s, hepa_box[3] - 8 * s, (i * 0.53) % 1)
        d.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=DUST)

    d.rectangle(pre_box, fill=PRE, outline=INK, width=2)
    gy = pre_box[1] + 8 * s
    while gy < pre_box[3] - 4 * s:
        d.line((pre_box[0] + 4 * s, gy, pre_box[2] - 4 * s, gy), fill=INK, width=1)
        gy += max(8 * s, 7)
    gx = pre_box[0] + 10 * s
    while gx < pre_box[2] - 4 * s:
        d.line((gx, pre_box[1] + 4 * s, gx, pre_box[3] - 4 * s), fill=INK, width=1)
        gx += max(16 * s, 12)

    fan = (cx, y0 + bh - 58 * s)
    _fan_disc(d, fan[0], fan[1], s * 1.15, ts, 0.25 + flow)

    inlet_y = (pre_box[1] + pre_box[3]) / 2
    in_span = (36 if s < 0.62 else 78) * s
    out_span = (22 if s < 0.62 else 62) * s
    if flow > 0.15:
        _arrow(d, (x0 - in_span, inlet_y), (x0 + 4 * s, inlet_y), DUST if dust > 0.2 else WATER)
        _arrow(d, (cx, y0 + 6 * s), (cx, y0 - out_span), GAS if gas > 0.2 else WATER)
    if dust > 0.05 and flow > 0.1:
        _motes(d, x0 - in_span, inlet_y - 14 * s, pre_box[0], inlet_y + 14 * s, ts, int(3 + 5 * dust), DUST, 0.35 + 0.4 * flow)
    if gas > 0.2:
        _motes(d, cx - 8 * s, y0 + 4 * s, cx + 10 * s, y0 - out_span, ts, 4, GAS, 0.5)
    if odor_in > 0.2:
        for i in range(3):
            u = (ts * 0.45 + i / 3) % 1.0
            ox = _lerp(x0 - 10 * s, carbon_box[0] + 20 * s, u)
            oy = (carbon_box[1] + carbon_box[3]) / 2 + math.sin(i + ts) * 6 * s
            d.arc((ox, oy, ox + 16 * s, oy + 12 * s), 200, 20, fill=ODOR, width=2)
    if odor_out > 0.2:
        for i in range(3):
            ox = cx + 20 * s + i * 12 * s
            oy = y0 - 8 * s - (ts * 28 * odor_out + i * 16) % (40 * s + 20)
            d.arc((ox, oy, ox + 16 * s, oy + 12 * s), 200, 20, fill=ODOR, width=2)
    if leak > 0.2:
        reach = (28 if s < 0.62 else 80) * s
        _motes(d, x0 + bw + 6 * s, cy - 16 * s, x0 + bw + reach, cy + 28 * s, ts, 6, DUST, 0.25)

    if s >= 0.72:
        d.text((cx, y0 + bh + 22 * s), "剖视", font=FONT_XS, fill=MUTED, anchor="mm")
    return {
        "pre": (pre_box[2], (pre_box[1] + pre_box[3]) / 2),
        "hepa": (hepa_box[2], (hepa_box[1] + hepa_box[3]) / 2),
        "carbon": (carbon_box[2], (carbon_box[1] + carbon_box[3]) / 2),
        "fan": (x0 + bw - 8 * s, fan[1]),
        "outlet": (cx, y0),
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=WATER if active else WHITE, outline=WATER, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WATER, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=WATER, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 1801).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：空气净化器靠什么变干净", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _purifier(
            d,
            540 + dx,
            int(1040 + (1 - show) * 30),
            scale=0.92,
            ts=time_sec,
            flow=0.9 if t > 0.45 else 0.2,
            dust=0.85,
            carbon=0.25,
        )
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((90, 1540, 990, 1640), radius=12, fill=(255, 240, 235))
            d.text((540, 1590), "❌ 不是造氧气，也不是负离子", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1500, 1010, 1700), radius=14, fill=(255, 245, 240))
            d.text((540, 1560), "✓  风扇抽气，纤维把灰拦住", font=FONT_L, fill=WATER, anchor="mm")
            d.text((540, 1640), "气味暂时吸在活性炭上", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 1803).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：空气穿过哪几层", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    parts = None
    if show > 0:
        parts = _purifier(d, 400, 900, scale=1.0, ts=time_sec, flow=1, dust=0.8, carbon=0.35)
        if t > 0.22:
            _callout(d, parts["pre"], (parts["pre"][0] + 180, parts["pre"][1]), "粗网", (132, 104, 72), _spring(t, 0.22, 0.22))
        if t > 0.38:
            _callout(d, parts["hepa"], (parts["hepa"][0] + 180, parts["hepa"][1] - 10), "细纤维", WATER, _spring(t, 0.38, 0.22))
        if t > 0.54:
            _callout(d, parts["carbon"], (parts["carbon"][0] + 180, parts["carbon"][1]), "活性炭", CARBON, _spring(t, 0.54, 0.22))
        if t > 0.7:
            _callout(d, parts["fan"], (parts["fan"][0] + 150, parts["fan"][1] + 36), "风扇", METAL_DK, _spring(t, 0.7, 0.22))
    if t > 0.8:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "零点三微米附近最难拦", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "快慢大致是风量乘过滤效率", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 1807).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "脏空气变少，就这四步", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _purifier(
        d,
        540,
        620,
        scale=0.78,
        ts=time_sec,
        flow=0.2 if active < 0 else 1.0,
        dust=0.9 if active < 2 else 0.45,
        clog=0.15,
        carbon=0.85 if active >= 3 else 0.2,
        gas=0.15 if active == 2 else 0.0,
        odor_in=1.0 if active >= 3 else 0.0,
        odor_out=0.35 if active >= 3 else 0.0,
    )
    steps = ["抽进来", "拦住灰", "送回去", "炭吸附"]
    tips = [
        "① 风扇把房间空气抽进来",
        "② 粗网挡毛，细纤维抓住颗粒",
        "③ 空气送回，颗粒被一遍遍稀释",
        "④ 炭吸气味，饱和后会再漏出",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1180, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1340, 1010, 1460), radius=14, fill=(255, 253, 248))
        d.text((540, 1400), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1560), "循环过滤，不是一次把房间抽干", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 1809).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(flow=0.25, dust=0.35, clog=0.9, carbon=0.7), "为什么滤网旧了还在转？", "风量掉了，拦住的灰变少"),
        (0.32, dict(flow=0.85, dust=0.9, clog=0.1, carbon=0.2, leak=1.0), "为什么开窗数值不降？", "新的脏空气一直进来"),
        (0.55, dict(flow=1, dust=0.55, clog=0.05, carbon=0.4, gas=1), "为什么降不了二氧化碳？", "纤维和普通炭都不抓它"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 340 + (1 - a) * 40
        d.rounded_rectangle((70, y, 1010, y + 310), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _purifier(d, 540, y + 214, scale=0.30, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1300), "风扇送风，纤维拦灰，炭只是暂时吸附", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 1811).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _purifier(d, 540, int(620 + (1 - a) * 24), scale=0.9, ts=time_sec, flow=1, dust=0.7, carbon=0.3)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1380), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1235), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1295), "风扇送风 · 纤维拦颗粒", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1360), "活性炭只是暂时吸附", font=FONT_L, fill=WATER, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1500, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1580), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1650), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1760),
            "评论区：咖啡机，还是换个别的？",
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
