"""扫地机器人分集 · 纪录片手绘风 2D。激光或陀螺仪认路，边刷滚刷尘盒扫地。"""

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
DUST = (164, 142, 104)
LIDAR = (180, 75, 45)


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
    r = 18 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=METAL_DK, outline=INK, width=2)
    ang = ts * 8 * max(spin, 0.05)
    for k in range(3):
        a = ang + k * math.tau / 3
        d.line((cx, cy, cx + math.cos(a) * r * 0.7, cy + math.sin(a) * r * 0.7), fill=WHITE, width=2)


def _ray_end(cx, cy, ang, box, reach):
    dx, dy = math.cos(ang), math.sin(ang)
    x, y = cx, cy
    for i in range(1, 48):
        nx = cx + dx * reach * i / 48
        ny = cy + dy * reach * i / 48
        if nx <= box[0] or nx >= box[2] or ny <= box[1] or ny >= box[3]:
            return nx, ny
        x, y = nx, ny
    return x, y


def _robot_top(d, cx, cy, s, ts, *, lidar=1.0, sweep=1.0, full=0.0, room=None):
    radius = 72 * s
    d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=BODY, outline=INK, width=3)
    d.ellipse(
        (cx - radius * 0.78, cy - radius * 0.78, cx + radius * 0.78, cy + radius * 0.78),
        outline=METAL,
        width=2,
    )
    cap = 26 * s
    d.ellipse((cx - cap, cy - cap, cx + cap, cy + cap), fill=WHITE, outline=INK, width=2)
    if lidar > 0.2:
        ang = ts * 1.8
        reach = 220 * s
        box = room or (cx - reach, cy - reach, cx + reach, cy + reach)
        x2, y2 = _ray_end(cx, cy, ang, box, reach)
        d.line((cx, cy, x2, y2), fill=LIDAR, width=3)
        x3, y3 = _ray_end(cx, cy, ang - 0.35, box, reach * 0.75)
        d.line((cx, cy, x3, y3), fill=(*LIDAR, 140), width=2)
    heading = -math.pi / 2
    bx = cx + math.cos(heading + 0.85) * radius * 0.95
    by = cy + math.sin(heading + 0.85) * radius * 0.95
    br = 16 * s
    d.ellipse((bx - br, by - br, bx + br, by + br), fill=METAL, outline=INK, width=2)
    spin = ts * 8 * max(sweep, 0.05)
    for k in range(3):
        a = spin + k * math.tau / 3
        d.line((bx, by, bx + math.cos(a) * br * 1.6, by + math.sin(a) * br * 1.6), fill=INK, width=2)
    bin_w, bin_h = 28 * s, 18 * s
    d.rectangle(
        (cx - bin_w / 2, cy + 8 * s, cx + bin_w / 2, cy + 8 * s + bin_h),
        fill=_mix(WHITE, DUST, 0.2 + 0.75 * full),
        outline=INK,
        width=2,
    )
    return {
        "lidar": (cx + cap, cy - cap),
        "brush": (bx + br, by),
        "bin": (cx + bin_w / 2, cy + 8 * s),
        "body": (cx + radius, cy),
    }


def _robot_cut(d, cx, cy, s, ts, *, spin=1.0, full=0.3, lidar=1.0):
    """侧剖：边刷、滚刷、尘盒、激光和轮上的码盘。"""
    w, h = 480 * s, 300 * s
    left, top = cx - w / 2, cy - h / 2
    d.rounded_rectangle((left + 70 * s, top + 78 * s, left + w - 24 * s, top + h - 28 * s), radius=40 * s, fill=BODY, outline=INK, width=3)
    lx, ly = left + w * 0.62, top + 48 * s
    d.ellipse((lx - 32 * s, ly - 26 * s, lx + 32 * s, ly + 26 * s), fill=WHITE, outline=INK, width=2)
    if lidar > 0.2:
        ang = ts * 2.2
        d.line((lx, ly, lx + math.cos(ang) * 70 * s, ly + math.sin(ang) * 16 * s), fill=LIDAR, width=3)
    bx, by = left + 36 * s, top + h - 48 * s
    br = 24 * s
    d.ellipse((bx - br, by - br, bx + br, by + br), fill=METAL, outline=INK, width=2)
    ang = ts * 7 * max(spin, 0.1)
    for k in range(3):
        a = ang + k * math.tau / 3
        d.line((bx, by, bx + math.cos(a) * br * 1.45, by + math.sin(a) * br * 0.7), fill=INK, width=2)
    roller = (left + 100 * s, top + h - 70 * s, left + 250 * s, top + h - 34 * s)
    _flat_round(d, roller, 12 * s, METAL_DK, INK, 2)
    for i in range(4):
        x = _lerp(roller[0] + 10 * s, roller[2] - 10 * s, i / 3)
        d.line((x, roller[1] + 4 * s, x, roller[3] - 4 * s), fill=WHITE, width=2)
    binb = (left + 270 * s, top + 120 * s, left + w - 48 * s, top + 210 * s)
    d.rectangle(binb, fill=_mix(WHITE, DUST, 0.2 + 0.7 * full), outline=INK, width=2)
    _fan_disc(d, (binb[0] + binb[2]) / 2, binb[1] - 22 * s, s, ts, spin)
    wheel = (left + 190 * s, top + h - 8 * s)
    d.ellipse((wheel[0] - 18 * s, wheel[1] - 18 * s, wheel[0] + 18 * s, wheel[1] + 18 * s), fill=INK)
    tick = ts * 4
    d.line(
        (wheel[0], wheel[1], wheel[0] + math.cos(tick) * 12 * s, wheel[1] + math.sin(tick) * 12 * s),
        fill=WHITE,
        width=2,
    )
    d.line((left + 86 * s, top + h - 20 * s, left + 86 * s, top + h + 18 * s), fill=ACCENT, width=2)
    return {
        "brush": (bx + br, by - 8 * s),
        "roller": (roller[2], (roller[1] + roller[3]) / 2),
        "bin": (binb[2], (binb[1] + binb[3]) / 2),
        "lidar": (lx + 28 * s, ly),
        "wheel": (wheel[0] + 20 * s, wheel[1]),
    }


def _room(d, box):
    d.rectangle(box, outline=INK, width=3)
    d.line((box[0], box[1], box[2], box[1]), fill=INK, width=4)


def _bow(box, u, slip=0.0, ts=0.0):
    rows = 4
    total = (u % 1.0) * rows
    row = min(int(total), rows - 1)
    frac = total - row
    if row % 2:
        frac = 1 - frac
    x = _lerp(box[0] + 70, box[2] - 70, frac)
    y = _lerp(box[1] + 70, box[3] - 70, (row + 0.5) / rows)
    if slip > 0.2:
        x += math.sin(ts * 2.4 + row) * 36 * slip
        y += math.cos(ts * 1.7) * 18 * slip
    return x, y


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=WATER if active else WHITE, outline=WATER, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WATER, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=WATER, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 2001).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：扫地机怎么知道扫到哪", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    room = (180, 700, 900, 1280)
    if show > 0:
        _room(d, room)
        _robot_top(d, 540 + dx * 0.2, 980, 1.35, time_sec, lidar=1, sweep=1, full=0.25, room=room)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((90, 1500, 990, 1600), radius=12, fill=(255, 240, 235))
            d.text((540, 1550), "❌ 屋里不靠卫星认路", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1460, 1010, 1680), radius=14, fill=(255, 245, 240))
            d.text((540, 1525), "✓  激光测距，或陀螺仪认路", font=FONT_L, fill=WATER, anchor="mm")
            d.text((540, 1605), "边刷滚刷把灰送进尘盒", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2003).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：认路和扫地是两套", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _robot_cut(d, 420, 860, 1.15, time_sec, spin=1, full=0.45, lidar=1)
        if t > 0.18:
            _callout(d, parts["lidar"], (min(980, parts["lidar"][0] + 140), parts["lidar"][1] - 20), "激光", LIDAR, _spring(t, 0.18, 0.2))
        if t > 0.34:
            _callout(d, parts["brush"], (160, parts["brush"][1]), "边刷", METAL_DK, _spring(t, 0.34, 0.2), anchor="rm")
        if t > 0.5:
            _callout(d, parts["roller"], (min(980, parts["roller"][0] + 160), parts["roller"][1] + 40), "滚刷", INK, _spring(t, 0.5, 0.2))
        if t > 0.64:
            _callout(d, parts["bin"], (min(980, parts["bin"][0] + 80), parts["bin"][1] - 30), "尘盒", DUST, _spring(t, 0.64, 0.2))
        if t > 0.76:
            _callout(d, parts["wheel"], (parts["wheel"][0] + 120, parts["wheel"][1] + 36), "码盘", INK, _spring(t, 0.76, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "吸力和手持、桶式是同一类", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "这集的差别在认路，不在魔法吸力", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2007).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "房间怎么走完", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    room = (200, 200, 880, 980)
    _room(d, room)
    for i in range(6):
        px, py = _bow(room, i / 6, 0, time_sec)
        d.ellipse((px - 4, py - 4, px + 4, py + 4), fill=LINE)
    pose = _bow(room, time_sec * 0.08, 0.0, time_sec)
    _robot_top(
        d,
        pose[0],
        pose[1],
        1.05,
        time_sec,
        lidar=1 if active != 0 else 0.3,
        sweep=1 if active >= 2 else 0.3,
        full=0.85 if active >= 3 else 0.2,
        room=room,
    )
    if active == 0:
        d.text((540, 1040), "激光量到墙", font=FONT_S, fill=LIDAR, anchor="mm")
    steps = ["激光量", "对上图", "来回走", "灰入盒"]
    tips = [
        "① 激光转一圈，量到墙和家具",
        "② 和已经扫到的轮廓对上",
        "③ 来回走，边刷把灰拨向滚刷",
        "④ 滚刷扬灰，风机送进尘盒",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1240, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((70, 1400, 1010, 1520), radius=14, fill=(255, 253, 248))
        d.text((540, 1460), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "没有激光就靠陀螺仪，轮子打滑路线会漂", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2009).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, "legs", "为什么绕着椅子腿打转？", "激光看见的是腿，不是椅子"),
        (0.32, "full", "为什么尘满了还在跑？", "认路还在，吸力已经差了"),
        (0.55, "gap", "为什么矮缝里还是有灰？", "边刷够不到比机身更矮的缝"),
    ]
    for idx, (start, kind, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 340 + (1 - a) * 40
        d.rounded_rectangle((70, y, 1010, y + 310), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        room = (360, y + 120, 720, y + 290)
        d.rectangle(room, outline=LINE, width=2)
        if kind == "legs":
            for i in range(4):
                lx = 500 + (i % 2) * 36
                ly = y + 150 + (i // 2) * 36
                d.ellipse((lx, ly, lx + 14, ly + 14), fill=INK)
            _robot_top(d, 560, y + 230, 0.55, time_sec, room=room, full=0.2)
        elif kind == "full":
            _robot_top(d, 540, y + 210, 0.7, time_sec, room=room, full=0.95, sweep=0.4)
        else:
            d.rectangle((room[2] - 70, room[1] + 16, room[2] - 16, room[1] + 48), fill=METAL_DK)
            _robot_top(d, room[0] + 80, y + 210, 0.62, time_sec, room=room, full=0.3)
    if t > 0.82:
        d.text((540, 1300), "激光或陀螺仪认路，边刷滚刷送进尘盒", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 2011).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    room = (160, 280, 920, 1000)
    _room(d, room)
    _robot_top(d, 540, int(640 + (1 - a) * 16), 1.4, time_sec, lidar=1, sweep=1, full=0.4, room=room)
    if t > 0.2:
        d.rounded_rectangle((70, 1140, 1010, 1360), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1195), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1255), "激光或陀螺仪认路", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1320), "边刷 · 滚刷 · 尘盒", font=FONT_L, fill=WATER, anchor="mm")
    if t > 0.48:
        b = _spring(t, 0.48, 0.25)
        _ken_badge(d, 1480, b, 0.9 + 0.1 * b)
        _fade_text(d, (540, 1560), "关注身边原理 · 我是 Ken", FONT_L, INK, b)
        _fade_text(d, (540, 1630), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))
    if t > 0.72:
        d.text(
            (540, 1740),
            "评论区：除湿机，还是换个别的？",
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
