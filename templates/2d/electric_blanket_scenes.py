"""电热毯分集 · 纪录片手绘风 2D。一根电热丝铺开发热，低挡是少通一会儿。"""

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
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
HOT = (198, 92, 52)
WARM = (232, 176, 64)
CLOTH = (236, 214, 196)
BED = (186, 150, 118)
SENSE = (64, 122, 150)


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


def _rr(d, box, radius, **kw):
    x0, y0, x1, y1 = box
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    rad = min(float(radius), max(0.0, (x1 - x0) / 2 - 0.8), max(0.0, (y1 - y0) / 2 - 0.8))
    if rad < 1 or (x1 - x0) < 2 or (y1 - y0) < 2:
        d.rectangle((x0, y0, x1, y1), **kw)
        return
    d.rounded_rectangle((x0, y0, x1, y1), radius=rad, **kw)


def _powered(ts, duty, plugged):
    if plugged < 0.5:
        return False
    frac = 0.22 + 0.7 * _clamp01(duty)
    return ((ts * 0.55) % 1.0) < frac


def _blanket(d, cx, cy, *, scale=1.0, ts=0.0, mode="flat", duty=0.85, plugged=1.0, residual=0.0, sense=1.0, caption=""):
    """一根丝在毯子里走整片。控制器改的是通电时间。"""
    s = scale
    on = _powered(ts, duty, plugged)
    cloth = _mix(CLOTH, HOT, 0.28 * residual + (0.18 if on else 0))
    _rr(d, (cx - 210 * s, cy + 36 * s, cx + 230 * s, cy + 150 * s), 10 * s, fill=BED, outline=INK, width=2)
    _rr(d, (cx - 190 * s, cy - 78 * s, cx + 170 * s, cy + 78 * s), 12 * s, fill=cloth, outline=INK, width=3)
    wire = (cx - 40 * s, cy)
    sense_pt = (cx + 20 * s, cy + 20 * s)
    if mode == "folded":
        for i in range(3):
            y = cy - 28 * s + i * 26 * s
            _rr(d, (cx - 150 * s, y - 10 * s, cx + 130 * s, y + 16 * s), 4 * s, fill=_mix(CLOTH, HOT, 0.45), outline=INK, width=2)
            d.line((cx - 130 * s, y, cx + 110 * s, y), fill=HOT, width=max(3, int(5 * s)))
            if sense > 0.5:
                d.line((cx - 130 * s, y + 7 * s, cx + 110 * s, y + 7 * s), fill=SENSE, width=2)
        wire = (cx, cy - 4 * s)
        sense_pt = (cx + 40 * s, cy + 30 * s)
    else:
        col = HOT if on else METAL_DK
        pts = []
        for i in range(5):
            y = cy - 52 * s + i * 22 * s
            x0, x1 = cx - 150 * s, cx + 130 * s
            if i % 2:
                x0, x1 = x1, x0
            pts.append((x0, y))
            pts.append((x1, y))
        d.line(pts, fill=col, width=max(3, int(5 * s)), joint="curve")
        if sense > 0.5:
            sense_pts = [(x + 8 * s, y + 8 * s) for x, y in pts]
            d.line(sense_pts, fill=SENSE, width=2, joint="curve")
        wire = pts[2]
        sense_pt = (pts[4][0], pts[4][1] + 10 * s)
    ctrl = (cx + 214 * s, cy + 8 * s)
    _rr(d, (ctrl[0] - 36 * s, ctrl[1] - 28 * s, ctrl[0] + 36 * s, ctrl[1] + 34 * s), 6 * s, fill=WHITE, outline=INK, width=2)
    dot = HOT if on else LINE
    d.ellipse((ctrl[0] - 8 * s, ctrl[1] - 12 * s, ctrl[0] + 8 * s, ctrl[1] + 4 * s), fill=dot, outline=INK, width=1)
    if plugged < 0.5:
        d.line((ctrl[0] - 70 * s, ctrl[1] + 40 * s, ctrl[0] - 28 * s, ctrl[1] + 18 * s), fill=METAL_DK, width=3)
        d.line((ctrl[0] - 8 * s, ctrl[1] + 22 * s, ctrl[0] + 8 * s, ctrl[1] + 40 * s), fill=ACCENT, width=3)
    else:
        d.line((cx + 150 * s, cy + 8 * s, ctrl[0] - 36 * s, ctrl[1]), fill=METAL_DK, width=max(2, int(3 * s)))
    if caption and s >= 0.42:
        d.text((cx, cy + 208 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
    return {"wire": wire, "control": ctrl, "sense": sense_pt, "cloth": (cx - 150 * s, cy - 70 * s)}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=HOT if active else WHITE, outline=HOT, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else HOT, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=HOT, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 4001).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：电热毯怎样发热又怎样停", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        y = int(980 + (1 - show) * 12)
        _blanket(d, 300 + dx, y, scale=0.48, ts=time_sec, duty=0.9, caption="铺开")
        _blanket(d, 790 + dx, y, scale=0.48, ts=time_sec, mode="folded", duty=0.9, caption="叠着")
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是低挡换了一根凉丝", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  同一根丝，通电久才更热", font=FONT_L, fill=HOT, anchor="mm")
            d.text((540, 1660), "铺开用。叠着，热会堆在一处", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4003).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：电热丝和控制器", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _blanket(d, 460, 900, scale=0.78, ts=time_sec, duty=0.85, sense=1)
        if t > 0.18:
            _callout(d, parts["wire"], (parts["wire"][0] - 40, parts["wire"][1] - 70), "电热丝", HOT, _spring(t, 0.18, 0.2), anchor="rm")
        if t > 0.36:
            _callout(d, parts["sense"], (parts["sense"][0] - 30, parts["sense"][1] + 56), "感温线", SENSE, _spring(t, 0.36, 0.2), anchor="rm")
        if t > 0.54:
            _callout(d, parts["control"], (min(1020, parts["control"][0] + 10), parts["control"][1] - 50), "控制器", INK, _spring(t, 0.54, 0.2))
        if t > 0.72:
            _callout(d, parts["cloth"], (parts["cloth"][0] - 20, parts["cloth"][1] - 24), "布", MUTED, _spring(t, 0.72, 0.2), anchor="rm")
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "低挡是少通一会儿，不是另一根丝", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "感温线是为了断电，不是为了叠着开", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4007).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "热怎样铺开，又怎样停", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    duty = 0.95 if active < 3 else 0.28
    _blanket(
        d,
        500,
        760,
        scale=0.7,
        ts=time_sec if active != 3 else time_sec * 0.35,
        duty=duty,
        mode="flat",
        residual=0.15 if active >= 2 else 0,
    )
    steps = ["通电", "铺开", "传热", "暂停"]
    tips = [
        "① 电流挤过电热丝，丝就发热",
        "② 丝弯过整张毯，热铺开",
        "③ 布把热传到床上",
        "④ 控制器暂停，低挡停得更久",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "同一根丝，差别在通电多久", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4009).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(duty=0.25, plugged=1, residual=0), "为什么低挡没那么热？", "还是那根丝，通电更短"),
        (0.32, dict(duty=0, plugged=0, residual=0.7), "为什么拔掉以后还暖？", "丝已断电，布和床还存着热"),
        (0.55, dict(mode="folded", duty=0.9, plugged=1), "为什么不能叠着通电？", "几段丝叠在一起，热散不走"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _blanket(d, 520, y + 230, scale=0.38, ts=time_sec, sense=0, **kw)
    if t > 0.82:
        d.text((540, 1480), "同一根丝铺开，通电久才更热", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 4011).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _blanket(d, 500, int(720 + (1 - a) * 12), scale=0.62, ts=time_sec, duty=0.8)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "电热丝铺开才发热", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "低挡是少通一会儿", font=FONT_L, fill=HOT, anchor="mm")
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
