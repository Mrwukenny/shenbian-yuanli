"""干衣机分集 · 纪录片手绘风 2D。暖风蒸发，冷凝或排气把水带走；热泵顺带回收热量。"""

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
BODY = (214, 220, 226)
CLOTH = ((186, 168, 148), (120, 146, 168), (168, 150, 130))


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


def _fins(d, box, color):
    d.rectangle(box, fill=_mix(WHITE, color, 0.22), outline=color, width=2)
    span = box[2] - box[0]
    if span < 8:
        return
    for i in range(5):
        x = _lerp(box[0] + 4, box[2] - 4, i / 4)
        d.line((x, box[1] + 3, x, box[3] - 3), fill=color, width=2)


def _dryer(d, cx, cy, *, scale=1.0, ts=0.0, mode="loop", bucket=0.4, lint=0.15, flow=1.0, hot=0.75):
    """滚筒、冷热盘管、水盒和滤网。mode=vent 时湿气直接离开。"""
    s = scale
    bw, bh = 440 * s, 390 * s
    x0, y0 = cx - bw / 2, cy - bh / 2
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=18 * s, fill=BODY, outline=INK, width=3)
    drum = (x0 + 155 * s, y0 + 150 * s)
    rad = 108 * s
    d.ellipse((drum[0] - rad, drum[1] - rad, drum[0] + rad, drum[1] + rad), fill=(236, 238, 242), outline=INK, width=3)
    d.ellipse(
        (drum[0] - rad * 0.7, drum[1] - rad * 0.7, drum[0] + rad * 0.7, drum[1] + rad * 0.7),
        outline=LINE,
        width=2,
    )
    n_cloth = 3 if lint > 0.75 else 5
    for i in range(n_cloth):
        ang = ts * 1.3 * max(flow, 0.15) + i * 1.25
        px = drum[0] + math.cos(ang) * rad * 0.38
        py = drum[1] + math.sin(ang) * rad * 0.32
        cw, ch = 22 * s, 14 * s
        d.rounded_rectangle((px - cw, py - ch, px + cw, py + ch), radius=3 * s, fill=CLOTH[i % 3], outline=INK, width=1)

    cold = (x0 + bw - 130 * s, y0 + 36 * s, x0 + bw - 48 * s, y0 + 140 * s)
    hotb = (x0 + bw - 130 * s, y0 + 168 * s, x0 + bw - 48 * s, y0 + 268 * s)
    if mode == "loop":
        _fins(d, cold, WATER)
        _fins(d, hotb, HOT if hot > 0.35 else METAL)
        if flow > 0.2:
            _arrow(d, (drum[0] + rad * 0.75, drum[1] - 16 * s), (cold[0] - 2 * s, (cold[1] + cold[3]) / 2), WATER)
            _arrow(d, (hotb[0] - 2 * s, (hotb[1] + hotb[3]) / 2), (drum[0] + rad * 0.55, drum[1] + 24 * s), HOT)
        if flow > 0.25 and lint < 0.85:
            for i in range(4):
                u = (ts * 0.7 * flow + i / 4) % 1.0
                dx = _lerp(cold[0] + 6 * s, cold[2] - 6 * s, (i % 3) / 2)
                dy = _lerp(cold[3] - 2 * s, cold[3] + 22 * s, u)
                d.ellipse((dx - 3 * s, dy - 4 * s, dx + 3 * s, dy + 4 * s), fill=WATER)
    else:
        d.rectangle(cold, outline=LINE, width=2)
        d.rectangle(hotb, outline=LINE, width=2)
        _arrow(d, (drum[0] + rad * 0.8, drum[1]), (x0 + bw + 28 * s, drum[1] - 10 * s), MUTED)

    tank = (x0 + 28 * s, y0 + bh - 78 * s, x0 + 180 * s, y0 + bh - 18 * s)
    d.rectangle(tank, fill=WHITE, outline=INK, width=2)
    level = _lerp(tank[3] - 4 * s, tank[1] + 6 * s, _clamp01(bucket))
    if bucket > 0.05:
        d.rectangle((tank[0] + 3 * s, level, tank[2] - 3 * s, tank[3] - 3 * s), fill=WATER_LT)
    filt = (x0 + 200 * s, y0 + bh - 78 * s, x0 + 270 * s, y0 + bh - 18 * s)
    d.rectangle(filt, fill=_mix(WHITE, MUTED, _clamp01(lint)), outline=INK, width=2)
    if s >= 0.7:
        d.text((cx, y0 + bh + 16 * s), "排气" if mode == "vent" else "热泵 / 冷凝", font=FONT_XS, fill=MUTED, anchor="mm")
    return {
        "drum": (drum[0] + rad * 0.2, drum[1] - rad * 0.2),
        "cold": (cold[2], (cold[1] + cold[3]) / 2),
        "hot": (hotb[2], (hotb[1] + hotb[3]) / 2),
        "tank": ((tank[0] + tank[2]) / 2, tank[1]),
        "filter": ((filt[0] + filt[2]) / 2, filt[1]),
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=WATER if active else WHITE, outline=WATER, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WATER, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=WATER, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 2401).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：干衣机怎样把水拿走", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _dryer(d, 540 + dx, int(1020 + (1 - show) * 16), scale=0.95, ts=time_sec, bucket=0.35, flow=1, hot=0.8)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((90, 1560, 990, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 水不是被热风变没了", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  水变成气，再被带走", font=FONT_L, fill=WATER, anchor="mm")
            d.text((540, 1660), "冷凝成水，或者排出室外", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2403).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：滚筒、冷热和水盒", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _dryer(d, 500, 860, scale=1.05, ts=time_sec, bucket=0.45, lint=0.2, hot=0.85)
        if t > 0.2:
            _callout(d, parts["drum"], (parts["drum"][0] - 180, parts["drum"][1] - 80), "滚筒", INK, _spring(t, 0.2, 0.22), anchor="rm")
        if t > 0.38:
            _callout(d, parts["cold"], (min(990, parts["cold"][0] + 20), parts["cold"][1] - 30), "冷盘管", WATER, _spring(t, 0.38, 0.22))
        if t > 0.54:
            _callout(d, parts["hot"], (min(990, parts["hot"][0] + 20), parts["hot"][1] + 10), "热盘管", HOT, _spring(t, 0.54, 0.22))
        if t > 0.7:
            _callout(d, parts["tank"], (parts["tank"][0] - 40, parts["tank"][1] + 70), "水盒", WATER, _spring(t, 0.7, 0.22), anchor="rm")
    if t > 0.8:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "热泵把冷端的热搬回滚筒", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "滤网拦住线屑，风路才走得通", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2407).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "水离开衣服，就这四步", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _dryer(
        d,
        540,
        620,
        scale=0.85,
        ts=time_sec,
        mode="vent" if active == 2 else "loop",
        bucket=0.2 if active < 2 else 0.55,
        flow=0.4 if active < 1 else 1,
        hot=0.2 if active < 1 else 0.8,
    )
    steps = ["翻开", "蒸发", "带走", "送回"]
    tips = [
        "① 滚筒翻动，褶皱里的水见到风",
        "② 暖空气把纤维里的水变成气",
        "③ 冷表面结成水，排气式则送出室外",
        "④ 干空气再加热，送回滚筒",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1180, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1340, 1010, 1460), radius=14, fill=(255, 253, 248))
        d.text((540, 1400), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1560), "衣服干了，是水被拿出筒外", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2409).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(bucket=0.96, lint=0.1, hot=0.7), "为什么水盒满了烘不干？", "冷凝水没处去，湿气降不下来"),
        (0.32, dict(bucket=0.2, lint=0.92, flow=0.25, hot=0.8), "为什么滤网一堵就变慢？", "风量小了，水蒸气带不走"),
        (0.55, dict(bucket=0.35, lint=0.1, hot=0.35, flow=1), "为什么不是越烫越好？", "热泵用更低的温度多循环"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _dryer(d, 540, y + 250, scale=0.48, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "暖风把水变成气，冷面再把它变成水", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2411).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _dryer(d, 360, int(640 + (1 - a) * 12), scale=0.62, ts=time_sec, mode="loop", bucket=0.5, hot=0.7)
    _dryer(d, 760, int(640 + (1 - a) * 12), scale=0.62, ts=time_sec, mode="vent", bucket=0.1, hot=0.9)
    if t > 0.2:
        d.rounded_rectangle((70, 1140, 1010, 1360), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1195), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1255), "暖风带走水蒸气", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1320), "冷凝或排气，把水拿出筒外", font=FONT_L, fill=WATER, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1500, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1580), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1650), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1760),
            "评论区：挂烫机，还是换个别的？",
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
