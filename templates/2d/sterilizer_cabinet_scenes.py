"""消毒柜分集 · 纪录片手绘风 2D。高温、臭氧和紫外线都只处理碰得到的表面。"""

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
WATER_LT = (186, 214, 232)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (214, 216, 220)

BOWL = (236, 236, 232)
UV = (120, 96, 196)
OZONE = (96, 168, 120)
SOIL = (150, 110, 72)

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



def _bowls(d, cx, shelf_y, s, stacked):
    if stacked > 0.5:
        d.arc((cx - 36 * s, shelf_y - 34 * s, cx + 24 * s, shelf_y - 2 * s), 200, 340, fill=BOWL, width=max(2, int(3 * s)))
        d.arc((cx - 8 * s, shelf_y - 62 * s, cx + 52 * s, shelf_y - 28 * s), 200, 340, fill=BOWL, width=max(2, int(3 * s)))
        d.ellipse((cx + 8 * s, shelf_y - 48 * s, cx + 28 * s, shelf_y - 34 * s), fill=SOIL)
    else:
        d.arc((cx - 92 * s, shelf_y - 46 * s, cx - 16 * s, shelf_y - 4 * s), 200, 340, fill=BOWL, width=max(2, int(3 * s)))
        d.arc((cx + 20 * s, shelf_y - 46 * s, cx + 96 * s, shelf_y - 4 * s), 200, 340, fill=BOWL, width=max(2, int(3 * s)))


def _cab(d, cx, cy, *, scale=1.0, ts=0.0, mode="heat", stacked=0.0, soil=0.0):
    """双层柜。高温、臭氧陶瓷片、紫外灯都画出来，mode 决定哪一条在工作。"""
    s = scale
    box = (cx - 168 * s, cy - 230 * s, cx + 168 * s, cy + 220 * s)
    d.rounded_rectangle(box, radius=16 * s, fill=BODY, outline=INK, width=3)
    mid = cy + 10 * s
    d.line((box[0] + 16 * s, mid, box[2] - 16 * s, mid), fill=METAL, width=3)
    d.line((box[0] + 16 * s, box[3] - 36 * s, box[2] - 16 * s, box[3] - 36 * s), fill=METAL, width=3)
    _bowls(d, cx, mid - 6 * s, s, stacked if mode == "uv" else 0.0)
    if soil > 0.4 and stacked < 0.5:
        d.ellipse((cx - 70 * s, mid - 28 * s, cx - 48 * s, mid - 16 * s), fill=SOIL)
    _bowls(d, cx, box[3] - 40 * s, s, 0.0)

    heat_on = mode in ("heat", "all")
    ozone_on = mode in ("ozone", "all")
    uv_on = mode in ("uv", "all")
    d.rectangle((box[0] + 28 * s, box[3] - 24 * s, box[2] - 28 * s, box[3] - 10 * s), fill=HOT if heat_on else METAL_DK)
    if heat_on:
        for i in range(3):
            d.arc((box[0] + 36 * s + i * 70 * s, mid + 16 * s, box[0] + 90 * s + i * 70 * s, mid + 48 * s), 200, 340, fill=HOT, width=2)
    plate = (cx - 22 * s, box[1] + 70 * s, cx + 22 * s, box[1] + 96 * s)
    d.rounded_rectangle(plate, radius=3 * s, fill=OZONE if ozone_on else WHITE, outline=INK, width=2)
    if ozone_on:
        for i in range(8):
            u = (ts * 0.35 + i / 8) % 1.0
            ox = _lerp(box[0] + 30 * s, box[2] - 36 * s, (i * 0.17) % 1)
            oy = _lerp(box[3] - 30 * s, box[1] + 36 * s, u)
            d.ellipse((ox, oy, ox + 8 * s, oy + 8 * s), fill=OZONE)
    lamp = (cx - 10 * s, box[1] + 18 * s, cx + 10 * s, box[1] + 52 * s)
    d.rectangle(lamp, fill=UV if uv_on else METAL)
    if uv_on:
        reach = mid - 8 * s if stacked > 0.5 else box[3] - 56 * s
        for k in range(-2, 3):
            d.line((cx, lamp[3], cx + k * 34 * s, reach), fill=UV, width=2)
    if 0.65 <= s < 0.9:
        name = {"heat": "高温", "ozone": "臭氧", "uv": "紫外线", "all": "三条路"}.get(mode, "")
        d.text((cx, box[3] + 16 * s), name, font=FONT_XS, fill=MUTED, anchor="mm")
    return {
        "shelf": (cx + 80 * s, mid - 16 * s),
        "heat": (box[2] - 24 * s, box[3] - 16 * s),
        "plate": (plate[2], (plate[1] + plate[3]) / 2),
        "lamp": (lamp[2] + 4 * s, (lamp[1] + lamp[3]) / 2),
    }


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=UV if active else WHITE, outline=UV, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else UV, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=UV, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 3201).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：消毒柜怎样处理餐具", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _cab(d, 540 + dx, int(1040 + (1 - show) * 12), scale=0.85, ts=time_sec, mode="all", stacked=0, soil=0)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是门一关就都干净", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  先洗净，再让热或光照到", font=FONT_L, fill=UV, anchor="mm")
            d.text((540, 1660), "叠紧和残渣，都会挡住", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3203).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：高温、臭氧和紫外线", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _cab(d, 500, 900, scale=0.95, ts=time_sec, mode="all", stacked=0.0)
        if t > 0.18:
            _callout(d, parts["shelf"], (min(1000, parts["shelf"][0] + 10), parts["shelf"][1] - 20), "层架", INK, _spring(t, 0.18, 0.2))
        if t > 0.36:
            _callout(d, parts["heat"], (min(1000, parts["heat"][0] + 36), parts["heat"][1] - 28), "加热管", HOT, _spring(t, 0.36, 0.2))
        if t > 0.54:
            _callout(d, parts["plate"], (parts["plate"][0] - 150, parts["plate"][1] - 10), "陶瓷片", OZONE, _spring(t, 0.54, 0.2), anchor="rm")
        if t > 0.72:
            _callout(d, parts["lamp"], (min(1000, parts["lamp"][0] + 16), parts["lamp"][1] - 10), "紫外灯", UV, _spring(t, 0.72, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "热要停够时间，臭氧能进缝", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "紫外线只照到光打到的那一面", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3207).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "表面怎样被处理到", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _cab(
        d,
        540,
        700,
        scale=0.72,
        ts=time_sec,
        mode="heat" if active < 2 else "all",
        stacked=1.0 if active == 0 else 0.0,
        soil=0.8 if active == 0 else 0.0,
    )
    steps = ["洗净", "摊开", "作用", "计时"]
    tips = [
        "① 残渣会挡住热、气体和光",
        "② 碗盘分开，别叠成一摞",
        "③ 高温、臭氧或紫外线碰上表面",
        "④ 没到时间就开门，这一轮停了",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "它不是把整柜都变成无菌", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3209).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(mode="uv", stacked=1.0), "为什么叠紧了不放心？", "紫外线过不去碗和碗之间"),
        (0.32, dict(mode="heat", stacked=0.0), "为什么塑料不进高温层？", "那一层靠持续的热，塑料会变形"),
        (0.55, dict(mode="ozone", stacked=0.0), "为什么结束时有气味？", "臭氧还没散完，之后变回氧气"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _cab(d, 540, y + 255, scale=0.34, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "先洗净再摊开，热或光才碰得到", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3211).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _cab(d, 540, int(700 + (1 - a) * 12), scale=0.78, ts=time_sec, mode="all")
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "先洗净，再摊开", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "热、臭氧或光，才碰得到", font=FONT_L, fill=UV, anchor="mm")
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
