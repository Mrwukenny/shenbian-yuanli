"""咖啡机分集 · 纪录片手绘风 2D。家用滴滤为主，半自动只点到泵和细粉。"""

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
WATER_LT = (186, 216, 232)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (226, 230, 234)
GROUND = (78, 52, 36)
BREW = (112, 72, 44)
BREW_LT = (176, 132, 88)
SCALE_C = (186, 176, 150)
PAPER_F = (228, 220, 200)


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
    _sketch_line(d, p1, p2, color, 3, int(p1[0] + p2[1]))
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    length = 12
    bx = p2[0] - math.cos(ang) * length
    by = p2[1] - math.sin(ang) * length
    px, py = -math.sin(ang) * 5, math.cos(ang) * 5
    d.polygon([(p2[0], p2[1]), (bx + px, by + py), (bx - px, by - py)], fill=color)


def _drip(d, cx, cy, *, scale=1.0, ts=0.0, heat=0.6, flow=1.0, grind="mid", limescale=0.0):
    """滴滤：水箱、加热管、花洒、纸滤和壶。粗细改变水滴快慢。"""
    s = scale
    spec = {
        "coarse": (7, 5.2, 1.15, 0.25),
        "mid": (12, 3.2, 0.72, 0.55),
        "fine": (18, 1.8, 0.32, 0.82),
    }
    count, grain, speed, dark = spec.get(grind, spec["mid"])
    w, h = 420 * s, 500 * s
    left, top = cx - w / 2, cy - h / 2
    d.rounded_rectangle((left, top + h - 36 * s, left + w, top + h), radius=12 * s, fill=BODY, outline=INK, width=3)

    tank = (left + 16 * s, top + 18 * s, left + 158 * s, top + 230 * s)
    _flat_round(d, tank, 12 * s, WHITE, INK, 2)
    d.rectangle((tank[0] + 10 * s, tank[1] + 70 * s, tank[2] - 10 * s, tank[3] - 12 * s), fill=WATER_LT)

    shower = (left + 280 * s, top + 86 * s)
    tube_x = (tank[0] + tank[2]) / 2
    tube_y = tank[3] - 8 * s
    col = HOT if heat > 0.4 else METAL
    d.line([(tube_x, tube_y), (tube_x, tube_y + 34 * s), (shower[0], tube_y + 34 * s), shower], fill=col, width=max(4, int(7 * s)))
    if limescale > 0.15:
        for i in range(4):
            bx = _lerp(tube_x + 10 * s, shower[0] - 8 * s, i / 3)
            by = tube_y + 34 * s
            rad = (4 + 5 * limescale) * s
            d.ellipse((bx - rad, by - rad * 0.65, bx + rad, by + rad * 0.65), fill=SCALE_C, outline=INK, width=1)

    _flat_round(d, (left + 190 * s, top + 24 * s, left + w - 22 * s, top + 100 * s), 10 * s, BODY, INK, 2)
    for i in range(4):
        hx = _lerp(shower[0] - 36 * s, shower[0] + 36 * s, i / 3)
        d.ellipse((hx - 3 * s, shower[1] - 3 * s, hx + 3 * s, shower[1] + 3 * s), fill=METAL_DK)

    basket = (left + 198 * s, top + 148 * s, left + w - 28 * s, top + 292 * s)
    rim = [
        (basket[0], basket[1]),
        (basket[2], basket[1]),
        (basket[2] - 16 * s, basket[3]),
        (basket[0] + 16 * s, basket[3]),
    ]
    d.polygon(rim, fill=WHITE)
    d.line(rim + [rim[0]], fill=INK, width=2)
    d.arc(
        (basket[0] + 18 * s, basket[1] + 16 * s, basket[2] - 18 * s, basket[3] + 16 * s),
        15,
        165,
        fill=PAPER_F,
        width=3,
    )
    for i in range(count):
        gx = _lerp(basket[0] + 28 * s, basket[2] - 28 * s, (i * 0.37) % 1)
        gy = _lerp(basket[1] + 28 * s, basket[3] - 14 * s, (i * 0.23) % 1)
        rad = grain * s
        d.ellipse((gx - rad, gy - rad, gx + rad, gy + rad), fill=GROUND)

    if flow > 0.15:
        drops = 4 if grind != "fine" else 3
        for i in range(drops):
            u = (ts * speed * max(flow, 0.2) + i / drops) % 1.0
            dx = shower[0] + math.sin(i * 1.7) * 16 * s
            dy = _lerp(shower[1] + 8 * s, basket[3] + 6 * s, u)
            d.ellipse((dx - 3 * s, dy - 5 * s, dx + 3 * s, dy + 5 * s), fill=BREW)

    carafe = (left + 214 * s, top + 310 * s, left + w - 46 * s, top + h - 46 * s)
    d.rectangle(carafe, fill=(236, 240, 242), outline=INK, width=2)
    level = _lerp(carafe[3] - 8 * s, carafe[1] + 18 * s, 0.22 + 0.45 * _clamp01(flow))
    d.rectangle((carafe[0] + 5 * s, level, carafe[2] - 5 * s, carafe[3] - 5 * s), fill=_mix(BREW_LT, BREW, dark))

    if s >= 0.7:
        d.text((cx, top + h + 16 * s), "滴滤", font=FONT_XS, fill=MUTED, anchor="mm")
    return {
        "tank": (tank[2], (tank[1] + tank[3]) / 2),
        "tube": ((tube_x + shower[0]) / 2, tube_y + 34 * s),
        "shower": (shower[0] + 20 * s, shower[1]),
        "paper": (basket[2] - 8 * s, (basket[1] + basket[3]) / 2),
    }


def _semi(d, cx, cy, s, ts):
    """家用半自动只画泵、细粉饼和杯子，不展开商业意式。"""
    w, h = 210 * s, 240 * s
    left, top = cx - w / 2, cy - h / 2
    _flat_round(d, (left, top, left + w, top + 64 * s), 8 * s, BODY, INK, 2)
    if s >= 0.45:
        d.text((cx, top + 32 * s), "泵", font=FONT_S, fill=INK, anchor="mm")
    puck = (left + 48 * s, top + 88 * s, left + w - 48 * s, top + 122 * s)
    d.rectangle(puck, fill=GROUND, outline=INK, width=2)
    _arrow(d, (cx, top + 64 * s), (cx, puck[1] - 2 * s), WATER)
    cup = (left + 58 * s, top + 146 * s, left + w - 58 * s, top + h - 16 * s)
    d.rectangle(cup, outline=INK, width=2)
    d.rectangle((cup[0] + 4 * s, cup[1] + 18 * s, cup[2] - 4 * s, cup[3] - 4 * s), fill=BREW)
    if s >= 0.45:
        d.text((cx, top + h + 8 * s), "半自动", font=FONT_XS, fill=MUTED, anchor="mm")
    return {"pump": (left + w, top + 32 * s), "puck": (puck[2], (puck[1] + puck[3]) / 2)}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=WATER if active else WHITE, outline=WATER, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WATER, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=WATER, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 1901).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：家用咖啡机怎么出味道", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _drip(d, 540 + dx, int(1040 + (1 - show) * 24), scale=0.86, ts=time_sec, heat=0.85, flow=0.75, grind="mid")
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((90, 1540, 990, 1640), radius=12, fill=(255, 240, 235))
            d.text((540, 1590), "❌ 不是在机器里把豆烤香", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1500, 1010, 1700), radius=14, fill=(255, 245, 240))
            d.text((540, 1560), "✓  热水把味道从粉里溶出", font=FONT_L, fill=WATER, anchor="mm")
            d.text((540, 1640), "半自动只是把水压过更细的粉", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 1903).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：热水怎么淋到粉上", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _drip(d, 360, 760, scale=0.92, ts=time_sec, heat=1, flow=0.8, grind="mid")
        if t > 0.2:
            _callout(d, parts["tank"], (parts["tank"][0] + 40, parts["tank"][1] - 80), "冷水", WATER, _spring(t, 0.2, 0.22))
        if t > 0.36:
            _callout(d, parts["tube"], (parts["tube"][0], parts["tube"][1] + 70), "加热管", HOT, _spring(t, 0.36, 0.22))
        if t > 0.52:
            _callout(d, parts["shower"], (min(980, parts["shower"][0] + 120), parts["shower"][1] - 20), "花洒", INK, _spring(t, 0.52, 0.22))
        if t > 0.66:
            _callout(d, parts["paper"], (min(980, parts["paper"][0] + 80), parts["paper"][1] + 30), "纸滤", GROUND, _spring(t, 0.66, 0.22))
    if t > 0.62:
        a = _spring(t, 0.62, 0.25)
        if a > 0:
            _semi(d, 860, int(1280 + (1 - a) * 20), 0.7, time_sec)
    if t > 0.8:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "纸滤拦的是细粉，不是咖啡因", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "半自动不另开一轮烘焙", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 1907).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "味道进杯子，就这四步", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    grind = "fine" if active >= 3 else "mid"
    _drip(
        d,
        540,
        620,
        scale=0.78,
        ts=time_sec,
        heat=1 if active >= 0 else 0.2,
        flow=0.25 if active <= 0 else (0.4 if active >= 3 else 0.9),
        grind=grind,
    )
    steps = ["烧热水", "淋到粉", "纸滤渣", "看粗细"]
    tips = [
        "① 冷水进加热管，烧成热水",
        "② 花洒淋开，味道溶进水里",
        "③ 纸滤拦住细粉，液滴进壶",
        "④ 太细易苦，太粗易淡偏酸",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1180, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1340, 1010, 1460), radius=14, fill=(255, 253, 248))
        d.text((540, 1400), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1560), "浓淡常常是时间和粗细，不是旋钮在烤豆", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 1909).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(heat=0.7, flow=0.35, grind="fine"), "为什么同一袋豆味道飘？", "常常是粗细和停留时间"),
        (0.32, dict(heat=0.55, flow=0.4, grind="mid", limescale=0.95), "为什么要定期除垢？", "水垢让水量和温度一起飘"),
        (0.55, dict(heat=0.8, flow=0.9, grind="mid"), "为什么纸滤留不住咖啡因？", "咖啡因溶于水，跟着液体走"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 340 + (1 - a) * 40
        d.rounded_rectangle((70, y, 1010, y + 310), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _drip(d, 540, y + 214, scale=0.30, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1300), "热水溶解，纸滤拦渣，粗细决定快慢", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 1911).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _drip(d, 540, int(640 + (1 - a) * 20), scale=0.84, ts=time_sec, heat=0.9, flow=0.8, grind="mid")
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1380), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1235), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1295), "热水把味道溶出来", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1360), "粗细决定水走多快", font=FONT_L, fill=WATER, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1500, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1580), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1650), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1760),
            "评论区：扫地机，还是换个别的？",
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
