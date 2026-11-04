"""榨汁机分集 · 纪录片手绘风 2D。汁穿过网，过不了孔的纤维留下，靠甩或者靠挤。"""

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
BODY = (214, 216, 220)
JUICE = (196, 96, 36)
PULP = (186, 146, 86)
LEAF = (72, 128, 62)
RIND = (214, 164, 64)


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


def _glass(d, gx, gy, s, level, settle):
    top = gy - 16 * s
    bot = gy + 92 * s
    d.line([(gx, top), (gx + 8 * s, bot), (gx + 52 * s, bot), (gx + 60 * s, top)], fill=INK, width=max(2, int(3 * s)))
    if level <= 0.04:
        return
    y = _lerp(bot - 8 * s, top + 18 * s, level)
    d.polygon([(gx + 6 * s, y), (gx + 54 * s, y), (gx + 48 * s, bot - 4 * s), (gx + 12 * s, bot - 4 * s)], fill=JUICE)
    if settle > 0.5:
        mid = _lerp(y, bot - 4 * s, 0.55)
        d.polygon([(gx + 8 * s, mid), (gx + 52 * s, mid), (gx + 48 * s, bot - 4 * s), (gx + 12 * s, bot - 4 * s)], fill=PULP)
        d.line((gx + 8 * s, mid, gx + 52 * s, mid), fill=INK, width=max(1, int(2 * s)))


def _juicer(d, cx, cy, *, scale=1.0, ts=0.0, mode="fast", leaf=0.0, settle=0.0, chunks=0.0, juice=0.7, caption=""):
    """fast 是离心网篮，slow 是螺杆慢磨，blend 是没有留渣网的杯子。"""
    s = scale
    if mode == "blend":
        d.rounded_rectangle((cx - 78 * s, cy - 100 * s, cx + 78 * s, cy + 130 * s), radius=18 * s, fill=WHITE, outline=INK, width=3)
        d.rectangle((cx - 62 * s, cy - 10 * s, cx + 62 * s, cy + 108 * s), fill=PULP)
        d.ellipse((cx - 28 * s, cy + 16 * s, cx + 4 * s, cy + 42 * s), fill=LEAF, outline=INK, width=1)
        d.ellipse((cx + 8 * s, cy + 48 * s, cx + 36 * s, cy + 70 * s), fill=RIND, outline=INK, width=1)
        ang = ts * 8
        d.line((cx - math.cos(ang) * 36 * s, cy + 78 * s, cx + math.cos(ang) * 36 * s, cy + 78 * s), fill=METAL_DK, width=3)
        if caption and s >= 0.55:
            d.text((cx, cy + 160 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
        return {
            "mesh": (cx + 70 * s, cy + 20 * s),
            "motor": (cx, cy + 110 * s),
            "pulp": (cx, cy + 40 * s),
            "spout": (cx + 70 * s, cy),
            "auger": (cx, cy + 20 * s),
        }

    if mode == "slow":
        d.rounded_rectangle((cx - 214 * s, cy - 34 * s, cx - 156 * s, cy + 42 * s), radius=8 * s, fill=METAL_DK, outline=INK, width=2)
        motor = (cx - 186 * s, cy + 4 * s)
        d.rounded_rectangle((cx - 160 * s, cy - 50 * s, cx + 108 * s, cy + 54 * s), radius=22 * s, fill=BODY, outline=INK, width=3)
        d.rounded_rectangle((cx - 142 * s, cy - 28 * s, cx + 86 * s, cy + 30 * s), radius=12 * s, fill=WHITE, outline=LINE, width=2)
        shift = (ts * 28) % 32
        for i in range(6):
            x = cx - 130 * s + i * 36 * s + shift * s
            if x > cx + 64 * s:
                continue
            d.arc((x, cy - 22 * s, x + 28 * s, cy + 22 * s), 200, 30, fill=METAL_DK, width=max(2, int(3 * s)))
        auger = (cx - 8 * s, cy)
        d.line((cx - 120 * s, cy + 22 * s, cx + 70 * s, cy + 22 * s), fill=METAL, width=2)
        mesh = (cx + 16 * s, cy + 28 * s)
        if juice > 0.15:
            d.polygon([(cx - 18 * s, cy + 50 * s), (cx + 20 * s, cy + 50 * s), (cx + 2 * s, cy + 96 * s)], fill=JUICE)
        spout = (cx, cy + 84 * s)
        d.ellipse((cx + 102 * s, cy - 18 * s, cx + 154 * s, cy + 26 * s), fill=PULP, outline=INK, width=2)
        pulp = (cx + 128 * s, cy + 4 * s)
        if leaf > 0.5:
            d.ellipse((cx - 126 * s, cy - 108 * s, cx - 78 * s, cy - 64 * s), fill=LEAF, outline=INK, width=2)
        if chunks > 0.5:
            d.ellipse((cx - 70 * s, cy - 108 * s, cx - 36 * s, cy - 76 * s), fill=RIND, outline=INK, width=2)
        if caption and s >= 0.55:
            d.text((cx, cy + 128 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
        return {"mesh": mesh, "motor": motor, "pulp": pulp, "spout": spout, "auger": auger}

    motor = (cx - 36 * s, cy + 128 * s)
    d.rounded_rectangle((cx - 118 * s, cy + 90 * s, cx + 46 * s, cy + 166 * s), radius=12 * s, fill=METAL_DK, outline=INK, width=2)
    ang = ts * (4 if chunks > 0.45 else 12)
    d.line((motor[0], motor[1], motor[0] + math.cos(ang) * 16 * s, motor[1] + math.sin(ang) * 16 * s), fill=ACCENT, width=3)
    d.polygon(
        [(cx - 100 * s, cy - 112 * s), (cx + 58 * s, cy - 86 * s), (cx + 42 * s, cy + 86 * s), (cx - 82 * s, cy + 86 * s)],
        fill=WHITE,
        outline=INK,
    )
    for i in range(6):
        y = cy - 80 * s + i * 26 * s
        d.line((cx - 84 * s, y, cx + 36 * s, y + 6 * s), fill=METAL, width=2)
    mesh = (cx + 50 * s, cy)
    if chunks > 0.45:
        for i, col in enumerate((RIND, LEAF if leaf > 0.5 else RIND, PULP)):
            x = cx - 70 * s + i * 32 * s
            d.ellipse((x, cy - 156 * s, x + 26 * s, cy - 136 * s), fill=col, outline=INK, width=1)
    else:
        for i in range(5):
            a = ts * 8 + i
            x = cx - 20 * s + math.cos(a) * 28 * s
            y = cy + math.sin(a) * 24 * s
            col = LEAF if leaf > 0.5 and i % 2 == 0 else PULP
            d.ellipse((x, y, x + 10 * s, y + 10 * s), fill=col)
    if juice > 0.12:
        d.polygon([(cx + 36 * s, cy + 8 * s), (cx + 96 * s, cy + 30 * s), (cx + 96 * s, cy + 46 * s), (cx + 36 * s, cy + 30 * s)], fill=JUICE)
    spout = (cx + 96 * s, cy + 38 * s)
    shown = 0.22 if leaf > 0.5 else juice
    _glass(d, cx + 112 * s, cy - 6 * s, s, shown, settle)
    if leaf > 0.5:
        lw, lh = max(22, 48 * s), max(16, 36 * s)
        d.ellipse((cx - 78 * s, cy - 150 * s - lh, cx - 78 * s + lw, cy - 150 * s), fill=LEAF, outline=INK, width=2)
    if caption and s >= 0.55:
        d.text((cx, cy + 196 * s), caption, font=FONT_S, fill=MUTED, anchor="mm")
    return {"mesh": mesh, "motor": motor, "pulp": (cx - 16 * s, cy + 24 * s), "spout": spout, "auger": mesh}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=JUICE if active else WHITE, outline=JUICE, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else JUICE, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=JUICE, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 3701).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：榨汁机怎样把汁和渣分开", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        y = int(1040 + (1 - show) * 12)
        _juicer(d, 280 + dx, y, scale=0.58, ts=time_sec, mode="fast", juice=0.75, caption="快转")
        _juicer(d, 800 + dx, y, scale=0.58, ts=time_sec, mode="slow", juice=0.7, caption="慢挤")
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是把水果打成糊", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  汁过网，渣被留下来", font=FONT_L, fill=JUICE, anchor="mm")
            d.text((540, 1660), "靠甩，或者靠挤", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3703).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：网、篮子和螺杆", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        fast = _juicer(d, 280, 980, scale=0.62, ts=time_sec, mode="fast", juice=0.7, caption="快转")
        slow = _juicer(d, 800, 980, scale=0.62, ts=time_sec, mode="slow", juice=0.7, caption="慢挤")
        if t > 0.18:
            _callout(d, fast["mesh"], (fast["mesh"][0] - 130, fast["mesh"][1] - 20), "网篮", INK, _spring(t, 0.18, 0.2), anchor="rm")
        if t > 0.36:
            _callout(d, fast["motor"], (fast["motor"][0] - 120, fast["motor"][1] + 6), "电机", METAL_DK, _spring(t, 0.36, 0.2), anchor="rm")
        if t > 0.54:
            _callout(d, slow["auger"], (min(1020, slow["auger"][0] + 30), slow["auger"][1] - 70), "螺杆", ACCENT, _spring(t, 0.54, 0.2))
        if t > 0.72:
            _callout(d, slow["pulp"], (min(1040, slow["pulp"][0] + 8), slow["pulp"][1] + 36), "出渣", PULP, _spring(t, 0.72, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "孔让汁过去，比孔粗的是渣", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "破壁机没有这层留渣的网", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3707).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "汁和渣怎样分开", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    chunks = 0.85 if active <= 0 else (0.4 if active == 1 else 0.0)
    juice = 0.08 if active <= 0 else (0.28 if active == 1 else (0.62 if active == 2 else 0.9))
    mode = "slow" if active == 2 else "fast"
    _juicer(d, 520, 680, scale=0.7, ts=time_sec, mode=mode, chunks=chunks, juice=juice)
    steps = ["切开", "上网", "分离", "留渣"]
    tips = [
        "① 刀盘或螺杆先把果肉切开",
        "② 碎果肉贴到网上",
        "③ 汁被甩出，或从缝里挤出",
        "④ 过不了孔的纤维留下来",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "没有这张网，出来的就是带渣的糊", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3709).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(mode="fast", settle=1, juice=0.85, chunks=0), "为什么放一会儿会分层？", "细纤维跟着汁穿过了网"),
        (0.32, dict(mode="fast", leaf=1, juice=0.25, chunks=0.2), "为什么叶子用快的出汁少？", "叶子轻，汁还没甩出就走了"),
        (0.55, dict(mode="blend"), "为什么破壁机打出来是糊？", "没有留渣的网，渣也留杯里"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _juicer(d, 540, y + 230, scale=0.4, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "汁过网，渣留下，靠甩或者靠挤", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3711).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    y = int(700 + (1 - a) * 12)
    _juicer(d, 300, y, scale=0.55, ts=time_sec, mode="fast", juice=0.8, caption="快转")
    _juicer(d, 780, y, scale=0.55, ts=time_sec, mode="slow", juice=0.75, caption="慢挤")
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "网让汁过去", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "过不了孔的，就是渣", font=FONT_L, fill=JUICE, anchor="mm")
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
