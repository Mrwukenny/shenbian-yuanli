"""挂烫机分集 · 纪录片手绘风 2D。常压蒸汽放热凝结，纤维暂时变软，重力拉直。不讲杀菌。"""

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
BODY = (236, 232, 226)
CLOTH = (214, 206, 196)
SCALE_C = (150, 146, 140)


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


def _shirt(d, cx, top, s, smooth):
    d.line((cx, top - 28 * s, cx, top), fill=METAL_DK, width=2)
    d.arc((cx - 18 * s, top - 36 * s, cx + 18 * s, top - 8 * s), 200, 340, fill=METAL, width=3)
    d.polygon(
        [
            (cx, top + 8 * s),
            (cx + 78 * s, top + 36 * s),
            (cx + 52 * s, top + 58 * s),
            (cx + 52 * s, top + 168 * s),
            (cx - 52 * s, top + 168 * s),
            (cx - 52 * s, top + 58 * s),
            (cx - 78 * s, top + 36 * s),
        ],
        fill=CLOTH,
        outline=INK,
    )
    amp = (1 - _clamp01(smooth)) * 12 * s
    for i in range(4):
        y = top + 78 * s + i * 18 * s
        pts = []
        for k in range(7):
            x = cx - 36 * s + k * 12 * s
            yy = y + math.sin(k * 1.3 + i) * amp
            pts.append((x, yy))
        if len(pts) >= 2:
            d.line(pts, fill=INK, width=2)
    return (cx, top + 90 * s)


def _iron(d, cx, cy, s):
    d.polygon(
        [(cx - 40 * s, cy), (cx + 46 * s, cy - 8 * s), (cx + 46 * s, cy + 16 * s), (cx - 28 * s, cy + 22 * s)],
        fill=METAL,
        outline=INK,
    )
    d.rectangle((cx - 10 * s, cy - 36 * s, cx + 10 * s, cy), fill=METAL_DK, outline=INK, width=1)
    if s >= 0.4:
        d.text((cx, cy + 36 * s), "熨斗", font=FONT_XS, fill=MUTED, anchor="mm")


def _steamer(d, cx, cy, *, scale=1.0, ts=0.0, steam=0.8, smooth=0.45, reach=1.0, scale_amt=0.0):
    """水箱、加热腔、软管、喷头，旁边是挂着的衣服。"""
    s = scale
    base = (cx - 150 * s, cy + 20 * s, cx - 28 * s, cy + 150 * s)
    d.rounded_rectangle(base, radius=12 * s, fill=BODY, outline=INK, width=3)
    water_top = _lerp(base[3] - 16 * s, base[1] + 28 * s, 0.55)
    d.rectangle((base[0] + 8 * s, water_top, base[2] - 8 * s, base[3] - 10 * s), fill=WATER_LT)
    boiler = (base[0] + 10 * s, base[1] + 8 * s, base[2] - 10 * s, base[1] + 28 * s)
    d.rectangle(boiler, fill=HOT if steam > 0.3 else METAL_DK)
    if scale_amt > 0.2:
        for i in range(3):
            sx = base[0] + 18 * s + i * 22 * s
            d.ellipse((sx, boiler[3] + 6 * s, sx + 12 * s, boiler[3] + 14 * s), fill=SCALE_C, outline=INK, width=1)

    head = (cx + 70 * s, cy - 20 * s)
    if reach < 0.45:
        head = (cx + 36 * s, cy - 80 * s)
    hose = [
        ((base[0] + base[2]) / 2, base[1]),
        (cx - 10 * s, cy - 80 * s),
        (head[0] - 20 * s, head[1] + 10 * s),
    ]
    d.line(hose, fill=METAL_DK, width=max(2, int(6 * s)))
    d.rounded_rectangle(
        (head[0] - 16 * s, head[1] - 28 * s, head[0] + 22 * s, head[1] + 36 * s),
        radius=8 * s,
        fill=WHITE,
        outline=INK,
        width=2,
    )
    for i in range(3):
        by = head[1] - 8 * s + i * 10 * s
        d.line((head[0] + 22 * s, by, head[0] + 34 * s, by - 4 * s), fill=INK, width=2)

    shirt_top = cy - 120 * s
    cloth = _shirt(d, cx + 150 * s, shirt_top, s, smooth if reach > 0.5 else 0.05)
    if steam > 0.25 and reach > 0.5:
        for i in range(4):
            u = (ts * 0.6 + i / 4) % 1.0
            sx = _lerp(head[0] + 24 * s, cloth[0] - 20 * s, u)
            sy = head[1] - 6 * s + math.sin(ts * 3 + i) * 6 * s
            d.arc((sx, sy, sx + 16 * s, sy + 12 * s), 200, 340, fill=MUTED, width=2)
    elif steam > 0.25:
        for i in range(3):
            u = (ts * 0.5 + i / 3) % 1.0
            sx = head[0] + 10 * s
            sy = head[1] - 20 * s - u * 30 * s
            d.arc((sx, sy, sx + 14 * s, sy + 10 * s), 200, 340, fill=MUTED, width=2)
    return {
        "boiler": ((boiler[0] + boiler[2]) / 2, boiler[1]),
        "hose": (cx - 10 * s, cy - 80 * s),
        "head": (head[0] + 22 * s, head[1]),
        "cloth": cloth,
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=HOT if active else WHITE, outline=HOT, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else HOT, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=HOT, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 2501).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：挂烫机怎样松开褶皱", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _steamer(d, 470 + dx, int(980 + (1 - show) * 16), scale=1.0, ts=time_sec, steam=0.9, smooth=0.55)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是立起来死压的熨斗", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  蒸汽松开纤维", font=FONT_L, fill=HOT, anchor="mm")
            d.text((540, 1660), "衣服挂着，重力帮它拉直", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2503).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：蒸汽、纤维和小手", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _steamer(d, 420, 860, scale=1.05, ts=time_sec, steam=1, smooth=0.35)
        if t > 0.2:
            _callout(d, parts["boiler"], (parts["boiler"][0] - 30, parts["boiler"][1] + 80), "加热腔", HOT, _spring(t, 0.2, 0.22), anchor="rm")
        if t > 0.38:
            _callout(d, parts["hose"], (parts["hose"][0] - 40, parts["hose"][1] - 40), "软管", METAL_DK, _spring(t, 0.38, 0.22), anchor="rm")
        if t > 0.54:
            _callout(d, parts["head"], (min(980, parts["head"][0] + 20), parts["head"][1] - 50), "喷头", INK, _spring(t, 0.54, 0.22))
        if t > 0.7:
            _callout(d, parts["cloth"], (min(1000, parts["cloth"][0] + 40), parts["cloth"][1]), "纤维", ACCENT, _spring(t, 0.7, 0.22))
    if t > 0.8:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "氢键像纤维之间暂时牵住的小手", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "热和水一到，小手松开，干了再牵上", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2507).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "褶皱怎样被松开", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    smooth = 0.1 if active < 2 else (0.45 if active == 2 else 0.9)
    _steamer(
        d,
        500,
        620,
        scale=0.85,
        ts=time_sec,
        steam=0.2 if active < 0 else 0.9,
        smooth=smooth,
        reach=0.2 if active < 1 else 1,
    )
    steps = ["烧开", "送汽", "凝结", "拉直"]
    tips = [
        "① 加热腔把水烧成大约一百度的蒸汽",
        "② 蒸汽沿软管到达喷头",
        "③ 蒸汽在衣服上放热，并凝成水",
        "④ 衣服挂直，重力把纤维拉平",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1380, 1010, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "贴近布面就好，不必死死压住", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2509).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, "far", "为什么挥两下，褶还在？", "蒸汽没在布上停留够久"),
        (0.32, "iron", "为什么压不出锋利裤线？", "裤线要靠底板和烫板的压力"),
        (0.55, "scale", "为什么蒸汽会变小？", "水垢窄了加热腔里的水路"),
    ]
    for idx, (start, kind, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        if kind == "iron":
            _steamer(d, 390, y + 250, scale=0.42, ts=time_sec, steam=0.8, smooth=0.7)
            _iron(d, 760, y + 250, 1.1)
        elif kind == "scale":
            _steamer(d, 500, y + 250, scale=0.48, ts=time_sec, steam=0.25, smooth=0.2, scale_amt=1)
        else:
            _steamer(d, 500, y + 250, scale=0.48, ts=time_sec, steam=0.8, smooth=0.05, reach=0.2)
    if t > 0.82:
        d.text((540, 1480), "蒸汽送去热和水，重力把衣服拉直", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2511).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _steamer(d, 470, int(640 + (1 - a) * 12), scale=0.95, ts=time_sec, steam=0.85, smooth=0.85)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "蒸汽松开纤维", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1370), "挂着的衣服，靠重力拉直", font=FONT_L, fill=HOT, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1520, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1600), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1670), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1780),
            "评论区：电动牙刷，还是换个别的？",
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
