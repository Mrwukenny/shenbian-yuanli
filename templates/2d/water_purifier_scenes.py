"""净水器分集 · 纪录片手绘风 2D。"""

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
WATER_LT = (186, 216, 232)
DIRTY = (148, 124, 78)
SALT = (132, 124, 110)
CHLORINE = (86, 156, 96)
CONC = (196, 148, 64)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
HOUSING = (236, 238, 242)
PUMP = (62, 102, 146)
GREEN = (80, 160, 110)
FIBER = (214, 206, 188)


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


def _cup(d, cx, cy, s, fill):
    d.rounded_rectangle((cx - 26 * s, cy - 28 * s, cx + 26 * s, cy + 32 * s), radius=8 * s, fill=fill, outline=INK, width=2)


def _stage_art(d, box, key, ts, reached, clog, pressure):
    x0, y0, x1, y1 = box
    if key == "pp":
        d.rectangle((x0, y0, x1, y1), fill=FIBER)
        span = max(y1 - y0, 1)
        for k in range(7):
            yy = y0 + span * (k + 0.5) / 7
            d.line((x0 + 6, yy, x1 - 6, yy + math.sin(k + ts) * 2), fill=(176, 166, 146), width=2)
        grit = 5 + int(12 * clog)
        width = max(x1 - x0, 1)
        for k in range(grit):
            px = x0 + 8 + (k * 19) % max(int(width - 16), 1)
            py = y1 - 14 - (k % 5) * 9
            if py < y0 + 8:
                continue
            rad = 4 if k % 3 else 6
            d.ellipse((px, py, px + rad, py + rad), fill=DIRTY if reached else SALT)
    elif key == "carbon":
        d.rectangle((x0, y0, x1, y1), fill=(46, 43, 40))
        for k in range(16):
            gx = x0 + 8 + (k % 4) * ((x1 - x0 - 16) / 4)
            gy = y0 + 8 + (k // 4) * ((y1 - y0 - 12) / 4)
            d.ellipse((gx, gy, gx + 12, gy + 12), fill=(24, 22, 20) if k % 2 == 0 else (78, 72, 64))
        if reached:
            for k in range(4):
                gx = x0 + 16 + k * 22
                gy = y0 + 18 + (k % 2) * 18
                d.ellipse((gx, gy, gx + 8, gy + 8), fill=CHLORINE)
    elif key == "pump":
        pcx, pcy = (x0 + x1) / 2, (y0 + y1) / 2
        r = min(x1 - x0, y1 - y0) * 0.38
        d.ellipse((pcx - r, pcy - r, pcx + r, pcy + r), fill=PUMP if reached else METAL, outline=INK, width=2)
        ang = ts * (8.5 if pressure > 0.4 else 1.4)
        for k in range(3):
            a = ang + k * math.tau / 3
            d.line(
                (pcx, pcy, pcx + math.cos(a) * r * 0.72, pcy + math.sin(a) * r * 0.72),
                fill=WHITE,
                width=3,
            )
    else:
        d.rectangle((x0, y0, x1, y1), fill=(214, 226, 234))
        span = max(y1 - y0, 1)
        for k in range(8):
            yy = y0 + span * (k + 0.5) / 8
            d.line((x0 + 4, yy, x1 - 4, yy), fill=(96, 132, 162), width=2)
        if reached:
            for k in range(5):
                px = x0 + 8 + (k % 3) * 14
                py = y0 + 8 + k * 10
                d.ellipse((px, py, px + 7, py + 7), fill=CONC)
            for k in range(3):
                px = x1 - 22
                py = y0 + 12 + k * 18
                d.ellipse((px, py, px + 7, py + 7), fill=WATER)


def _purifier(
    d,
    cx,
    cy,
    *,
    scale=1.0,
    ts=0.0,
    stage=3,
    clog=0.25,
    pressure=1.0,
    waste=True,
    pure=True,
    labels=True,
):
    """四级示意：PP棉、活性炭、增压泵、反渗透，底下分净水和浓水。"""
    s = scale
    bw, bh = 360 * s, 520 * s
    x0, y0 = cx - bw / 2, cy - bh / 2
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=22 * s, fill=HOUSING, outline=INK, width=2)
    d.rectangle((cx - 11 * s, y0 - 34 * s, cx + 11 * s, y0 + 8 * s), fill=METAL_DK)
    d.ellipse((cx - 16 * s, y0 - 52 * s, cx + 16 * s, y0 - 28 * s), fill=DIRTY, outline=INK, width=2)
    if labels and s >= 0.7:
        d.text((cx + 36 * s, y0 + 26 * s), "进水", font=FONT_XS, fill=MUTED, anchor="lm")

    top = y0 + 48 * s
    slot_h = 100 * s
    gap = 12 * s
    keys = ("pp", "carbon", "pump", "membrane")
    names = ("PP棉", "活性炭", "增压泵", "反渗透")
    anchors = {"inlet": (cx, y0 - 40 * s)}
    pipe_x = x0 + 58 * s
    for i, key in enumerate(keys):
        sy = top + i * (slot_h + gap)
        reached = stage >= i
        plate = WHITE if reached else (226, 224, 218)
        d.rounded_rectangle((x0 + 24 * s, sy, x0 + bw - 22 * s, sy + slot_h), radius=12 * s, fill=plate, outline=INK, width=2)
        if i == stage:
            d.rectangle((x0 + 24 * s, sy + 10 * s, x0 + 34 * s, sy + slot_h - 10 * s), fill=ACCENT)
        art = (x0 + 86 * s, sy + 16 * s, x0 + 86 * s + 118 * s, sy + slot_h - 16 * s)
        _stage_art(d, art, key, ts, reached, clog if key == "pp" else 0.0, pressure if key == "pump" else 0.0)
        mid_y = sy + slot_h / 2
        d.line((pipe_x, mid_y, art[0], mid_y), fill=METAL, width=4)
        if labels and s >= 0.72:
            d.text((x0 + bw - 36 * s, mid_y), names[i], font=FONT_XS, fill=INK, anchor="rm")
        anchors[key] = (x0 + bw - 22 * s, mid_y)

    d.line((pipe_x, y0 + 18 * s, pipe_x, y0 + bh - 18 * s), fill=METAL, width=8)
    # 管子压在滤芯图上时，把流动的点再画一层，避免被滤芯盖住。
    pure_pt = (cx - 78 * s, y0 + bh + 86 * s)
    waste_pt = (cx + 96 * s, y0 + bh + 86 * s)
    membrane_y = anchors["membrane"][1]
    if pure:
        d.line((pipe_x, y0 + bh - 16 * s, pure_pt[0], pure_pt[1] - 34 * s), fill=WATER, width=5)
        _cup(d, pure_pt[0], pure_pt[1], s, WATER_LT)
        if labels and s >= 0.7:
            d.text((pure_pt[0], pure_pt[1] + 48 * s), "净水", font=FONT_XS, fill=WATER, anchor="mm")
    if waste:
        d.line((pipe_x, membrane_y, waste_pt[0], waste_pt[1] - 30 * s), fill=CONC, width=5)
        _cup(d, waste_pt[0], waste_pt[1], s, CONC)
        if labels and s >= 0.7:
            d.text((waste_pt[0], waste_pt[1] + 48 * s), "浓水", font=FONT_XS, fill=CONC, anchor="mm")

    inlet = (cx, y0 - 20 * s)
    pp_y = anchors["pp"][1]
    carbon_y = anchors["carbon"][1]
    pump_y = anchors["pump"][1]
    end_y = { -1: y0 + 10 * s, 0: pp_y, 1: carbon_y, 2: pump_y, 3: y0 + bh - 8 * s }.get(stage, y0 + bh - 8 * s)
    main = [inlet, (pipe_x, y0 + 24 * s), (pipe_x, end_y)]
    _dots(d, main, ts, DIRTY, n=4, speed=0.55, radius=4.5 * s, limit=0.55 if stage >= 0 else 0.3)
    if stage >= 1:
        _dots(d, [(pipe_x, pp_y), (pipe_x, carbon_y)], ts, CHLORINE, n=3, speed=0.5, radius=4 * s)
    if stage >= 3 and pure:
        _dots(d, [(pipe_x, pump_y), (pipe_x, y0 + bh - 8 * s), pure_pt], ts, WATER, n=5, speed=0.42, radius=4.5 * s)
    if stage >= 3 and waste:
        _dots(d, [(pipe_x, membrane_y), waste_pt], ts, CONC, n=4, speed=0.48, radius=4.5 * s)

    anchors["pure"] = pure_pt
    anchors["waste"] = waste_pt
    return anchors


def _mini(d, cx, cy, mode, ts):
    """类比卡片里的小滤芯排，不画整台机器。"""
    names = ("PP", "炭", "膜")
    fills = (FIBER, (46, 43, 40), (214, 226, 234))
    for i, name in enumerate(names):
        x = cx - 210 + i * 92
        d.rounded_rectangle((x, cy - 48, x + 72, cy + 58), radius=10, fill=WHITE, outline=INK, width=2)
        d.rectangle((x + 14, cy - 24, x + 58, cy + 36), fill=fills[i])
        d.text((x + 36, cy + 6), name, font=FONT_XS, fill=INK if i != 1 else WHITE, anchor="mm")
        if i < 2:
            d.line((x + 72, cy, x + 92, cy), fill=METAL_DK, width=4)
    if mode == "clog":
        d.rectangle((cx - 188, cy + 8, cx - 150, cy + 34), fill=DIRTY)
        d.text((cx + 70, cy), "堵住 / 吸满", font=FONT_S, fill=ACCENT, anchor="lm")
    elif mode == "tds":
        d.rounded_rectangle((cx + 62, cy - 46, cx + 250, cy + 50), radius=12, fill=(28, 36, 34), outline=INK, width=2)
        d.text((cx + 156, cy - 10), "TDS 15", font=FONT_M, fill=GREEN, anchor="mm")
        d.text((cx + 156, cy + 26), "≠ 安全", font=FONT_XS, fill=(255, 196, 160), anchor="mm")
    else:
        d.line((cx + 46, cy + 20, cx - 10, cy + 78), fill=WATER, width=5)
        d.line((cx + 46, cy + 20, cx + 130, cy + 78), fill=CONC, width=5)
        _dots(d, [(cx + 46, cy + 20), (cx - 10, cy + 78)], ts, WATER, n=3, speed=0.8, radius=4)
        _dots(d, [(cx + 46, cy + 20), (cx + 130, cy + 78)], ts, CONC, n=3, speed=0.7, radius=4)
        d.text((cx - 10, cy + 100), "净水", font=FONT_XS, fill=WATER, anchor="mm")
        d.text((cx + 130, cy + 100), "浓水", font=FONT_XS, fill=CONC, anchor="mm")


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=WATER if active else WHITE, outline=WATER, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WATER, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=WATER, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 311).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：净水器怎么处理自来水", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _purifier(
            d,
            540 + dx,
            int(980 + (1 - show) * 40),
            scale=0.72,
            ts=time_sec,
            stage=3 if t > 0.55 else 0,
            clog=0.35,
            pressure=0.95 if t > 0.55 else 0.2,
            waste=t > 0.62,
            pure=t > 0.55,
            labels=True,
        )
    if t > 0.5:
        wrong = _ease(_scene_t(t, 0.5, 0.64))
        right = _spring(t, 0.66, 0.28)
        if wrong > 0 and right < 0.35:
            d.rounded_rectangle((90, 1480, 990, 1580), radius=12, fill=(255, 240, 235))
            d.text((540, 1530), "❌ TDS越低，并不等于越安全", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1460, 1010, 1660), radius=14, fill=(255, 245, 240))
            d.text((540, 1520), "✓  分级拦截，再用压力过膜", font=FONT_L, fill=WATER, anchor="mm")
            d.text((540, 1600), "TDS只是导电粗测，不是安全证明", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 313).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：水经过哪几级", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    parts = None
    if show > 0:
        parts = _purifier(
            d,
            430,
            760,
            scale=0.98,
            ts=time_sec,
            stage=3,
            clog=0.4,
            pressure=1.0,
            waste=True,
            pure=True,
            labels=False,
        )
        if t > 0.2:
            _callout(d, parts["pp"], (760, parts["pp"][1]), "PP棉", INK, _spring(t, 0.2, 0.22))
        if t > 0.34:
            _callout(d, parts["carbon"], (760, parts["carbon"][1]), "活性炭", INK, _spring(t, 0.34, 0.22))
        if t > 0.48:
            _callout(d, parts["pump"], (760, parts["pump"][1]), "增压泵", PUMP, _spring(t, 0.48, 0.22))
        if t > 0.6:
            _callout(d, parts["membrane"], (760, parts["membrane"][1]), "反渗透膜", WATER, _spring(t, 0.6, 0.22))
        if t > 0.72:
            _callout(d, parts["waste"], (860, parts["waste"][1]), "浓水", CONC, _spring(t, 0.72, 0.22))
    if t > 0.8:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "PP棉拦渣，活性炭先去掉余氯", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "泵加压过膜，浓水把盐冲走", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 317).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "水分开，就这四步", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _purifier(
        d,
        540,
        560,
        scale=0.7,
        ts=time_sec,
        stage=active,
        clog=0.85 if active == 0 else 0.3,
        pressure=1.0 if active >= 2 else 0.15,
        waste=active >= 3,
        pure=active >= 3,
        labels=True,
    )
    steps = ["PP棉拦渣", "炭去余氯", "泵压过膜", "浓水冲盐"]
    tips = [
        "① 泥沙锈渣卡在PP棉纤维里",
        "② 活性炭去余氯，坐满就漏",
        "③ 压力更高，水才走向淡的一侧",
        "④ 净水出去，浓水把盐冲走",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1120, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1280, 1010, 1400), radius=14, fill=(255, 253, 248))
        d.text((540, 1340), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1500), "超滤孔更大，盐过得去，TDS几乎不变", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 319).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, "clog", "为什么滤芯要换？", "堵住、吸满，或者膜被余氯伤到"),
        (0.32, "tds", "为什么TDS低不等于安全？", "它只看溶解离子，不是安全分"),
        (0.55, "waste", "为什么要排浓水？", "在冲膜，比例不是安全分数"),
    ]
    for idx, (start, mode, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 340 + (1 - a) * 40
        d.rounded_rectangle((70, y, 1010, y + 310), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _mini(d, 520, y + 190, mode, time_sec)
    if t > 0.78:
        d.text((540, 1280), "口感变淡，是矿物质少了", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1360), "不是伤身证明，也不是健康分数", font=FONT_M, fill=ACCENT, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 321).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _purifier(
        d,
        540,
        int(520 + (1 - a) * 30),
        scale=0.78,
        ts=time_sec,
        stage=3,
        clog=0.3,
        pressure=1.0,
        waste=True,
        pure=True,
        labels=True,
    )
    if t > 0.2:
        d.rounded_rectangle((70, 1080, 1010, 1320), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1130), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1195), "PP棉拦渣 · 活性炭去氯", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1265), "泵压过膜 · 浓水冲盐", font=FONT_L, fill=WATER, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1420, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1500), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1570), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text((540, 1660), "TDS不是安全成绩单", font=FONT_S, fill=MUTED, anchor="mm")
        d.text(
            (540, 1740),
            "评论区：电烤箱，还是换个别的？",
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
