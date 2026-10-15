"""吸尘器分集 · 纪录片手绘风 2D，强调连续动画。"""

from __future__ import annotations

import math
import random
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

PAPER = (248, 245, 238)
WALL = (242, 238, 230)
FLOOR = (218, 214, 206)
INK = (38, 36, 34)
MUTED = (110, 105, 98)
ACCENT = (180, 75, 45)
AIR = (70, 130, 175)
AIR_LT = (170, 205, 230)
HOT = (195, 90, 55)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (55, 58, 64)
BODY_LT = (90, 95, 105)
DIRT = (120, 95, 70)
DIRT_LT = (160, 130, 95)
GREEN = (80, 160, 110)
FILTER = (200, 180, 120)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = (
        [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc"]
        if bold
        else [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc"]
    )
    for path in paths:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT_HERO = _font(62, bold=True)
FONT_L = _font(44, bold=True)
FONT_M = _font(34)
FONT_S = _font(28)
FONT_XS = _font(24)


def _clamp01(t: float) -> float:
    return max(0.0, min(1.0, t))


def _ease(t: float) -> float:
    t = _clamp01(t)
    return t * t * (3 - 2 * t)


def _spring(t: float, start: float = 0.0, dur: float = 0.3) -> float:
    if t < start:
        return 0.0
    p = _clamp01((t - start) / dur)
    return 1 - math.exp(-6 * p) * math.cos(p * math.pi * 2.5)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * _clamp01(t)


def _scene_t(t: float, a: float, b: float) -> float:
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    return (t - a) / (b - a)


def _pulse(time_sec: float, speed: float = 2.5, lo: float = 0.85, hi: float = 1.0) -> float:
    return lo + (hi - lo) * (0.5 + 0.5 * math.sin(time_sec * speed * math.tau))


def _wobble(x: float, y: float, seed: int, amp: float = 1.2) -> tuple[float, float]:
    return x + math.sin(seed * 1.7) * amp, y + math.cos(seed * 2.3) * amp


def _cam_drift(time_sec: float, amp_x: float = 5.0, amp_y: float = 3.0) -> tuple[float, float]:
    return math.sin(time_sec * 0.7) * amp_x, math.cos(time_sec * 0.55) * amp_y


def _paper_bg(w: int, h: int, seed: int = 7) -> Image.Image:
    img = Image.new("RGB", (w, h), PAPER)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, w, int(h * 0.62)), fill=WALL)
    draw.rectangle((0, int(h * 0.62), w, h), fill=FLOOR)
    draw.line((0, int(h * 0.62), w, int(h * 0.62)), fill=LINE, width=2)
    draw.polygon(
        [(0, 0), (int(w * 0.28), 0), (int(w * 0.22), int(h * 0.62)), (0, int(h * 0.62))],
        fill=(250, 248, 242),
    )
    rng = random.Random(seed)
    px = img.load()
    for _ in range(int(w * h * 0.008)):
        x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
        r, g, b = px[x, y]
        n = rng.randint(-5, 5)
        px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    return img


def _sketch_line(draw, p1, p2, color=INK, width=2, seed=0):
    x1, y1 = p1
    x2, y2 = p2
    steps = max(int(math.hypot(x2 - x1, y2 - y1) / 12), 2)
    pts = []
    for i in range(steps + 1):
        f = i / steps
        x, y = _lerp(x1, x2, f), _lerp(y1, y2, f)
        x, y = _wobble(x, y, seed + i, 0.8)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line((pts[i], pts[i + 1]), fill=color, width=width)


def _callout(draw, tip_xy, label_xy, text, color=INK, alpha: float = 1.0):
    if alpha <= 0.01:
        return
    tx, ty = tip_xy
    lx, ly = label_xy
    _sketch_line(draw, (tx, ty), (lx, ly), color, 2, int(tx + ty))
    draw.ellipse((tx - 5, ty - 5, tx + 5, ty + 5), fill=color)
    a = int(255 * _clamp01(alpha))
    draw.text((lx, ly), text, font=FONT_S, fill=(*color, a), anchor="lm")


def _fade_text(draw, xy, text, font, color, alpha: float, anchor="mm", dy: float = 0.0):
    if alpha <= 0.01:
        return
    a = int(255 * _clamp01(alpha))
    x, y = xy
    draw.text((x, y + dy), text, font=font, fill=(*color, a), anchor=anchor)


def _ken_badge(draw, y: int, alpha: float = 1.0, scale: float = 1.0):
    if alpha <= 0:
        return
    a = int(255 * _clamp01(alpha))
    bw = int(400 * scale)
    draw.rounded_rectangle(
        (540 - bw // 2, y - 36, 540 + bw // 2, y + 36),
        radius=18,
        fill=(255, 253, 248, a),
        outline=ACCENT,
        width=2,
    )
    draw.text((540, y), "身边原理 · Ken", font=FONT_S, fill=(*ACCENT, a), anchor="mm")


def _safe_ellipse(draw, box, **kwargs):
    x0, y0, x1, y1 = box
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    draw.ellipse((x0, y0, x1, y1), **kwargs)


def _air_particles(draw, path, time_sec: float, count: int = 10, dirty: bool = True, speed: float = 1.2):
    if len(path) < 2:
        return
    segs = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
    lengths = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
    total = sum(lengths) or 1.0

    def pos_at(u: float):
        d = (u % 1.0) * total
        for idx, ((a, b), ln) in enumerate(zip(segs, lengths)):
            if d <= ln:
                f = d / ln if ln else 0
                return _lerp(a[0], b[0], f), _lerp(a[1], b[1], f), idx
            d -= ln
        return path[-1][0], path[-1][1], len(segs) - 1

    for i in range(count):
        u = (time_sec * speed * 0.18 + i / count) % 1.0
        x, y, si = pos_at(u)
        if dirty and si < max(1, len(segs) // 2):
            col = DIRT if i % 2 == 0 else DIRT_LT
            r = 5
        else:
            col = AIR if i % 2 == 0 else AIR_LT
            r = 4
        draw.ellipse((x - r, y - r, x + r, y + r), fill=col)


def _fan(draw, cx, cy, R: float, time_sec: float, rpm: float = 8.0):
    ang = time_sec * rpm * math.tau
    _safe_ellipse(draw, (cx - R, cy - R, cx + R, cy + R), outline=METAL_DK, width=2, fill=BODY_LT)
    for k in range(4):
        a = ang + k * math.tau / 4
        x2 = cx + math.cos(a) * (R - 6)
        y2 = cy + math.sin(a) * (R - 6)
        draw.line((cx, cy, x2, y2), fill=METAL, width=max(2, int(R / 8)))
    _safe_ellipse(draw, (cx - R * 0.2, cy - R * 0.2, cx + R * 0.2, cy + R * 0.2), fill=METAL_DK)


def _dust_pile(draw, x, y, amount: float = 1.0):
    for i in range(int(4 + 6 * amount)):
        px = x + (i - 3) * 8
        py = y - (i % 3) * 4
        r = 4 + (i % 3)
        draw.ellipse((px - r, py - r, px + r, py + r), fill=DIRT if i % 2 else DIRT_LT)


def _vacuum_body(
    draw,
    cx,
    cy,
    *,
    scale: float = 1.0,
    time_sec: float = 0.0,
    suction: float = 1.0,
    show_cutaway: bool = False,
    bin_full: float = 0.35,
    blocked: bool = False,
):
    """立式/卧式简化：机身 + 软管 + 地刷。"""
    s = scale
    # 机身
    bw, bh = 200 * s, 260 * s
    x0, y0 = cx - bw / 2, cy - bh / 2
    draw.rounded_rectangle((x0 + 4, y0 + 6, x0 + bw + 4, y0 + bh + 6), radius=18 * s, fill=(180, 176, 170))
    draw.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=18 * s, fill=BODY, outline=INK, width=2)

    # 尘杯区
    cup = (x0 + bw * 0.12, y0 + bh * 0.12, x0 + bw * 0.88, y0 + bh * 0.48)
    draw.rounded_rectangle(cup, radius=10 * s, fill=(40, 44, 50), outline=METAL, width=2)
    fill_top = _lerp(cup[3], cup[1], _clamp01(bin_full))
    if cup[3] - fill_top > 4:
        draw.rounded_rectangle((cup[0] + 4, fill_top, cup[2] - 4, cup[3] - 4), radius=6 * s, fill=DIRT)
        _dust_pile(draw, (cup[0] + cup[2]) / 2, cup[3] - 18 * s, bin_full)

    # 电机风扇区
    fx, fy = cx, y0 + bh * 0.68
    fr = 28 * s
    if show_cutaway:
        draw.rounded_rectangle((x0 + bw * 0.2, y0 + bh * 0.52, x0 + bw * 0.8, y0 + bh * 0.88), radius=8 * s, fill=BODY_LT, outline=METAL_DK, width=1)
        _fan(draw, fx, fy, fr, time_sec, rpm=10 * suction)
        # 滤芯
        draw.rounded_rectangle((x0 + bw * 0.25, y0 + bh * 0.52, x0 + bw * 0.75, y0 + bh * 0.58), radius=3, fill=FILTER, outline=INK, width=1)
    else:
        draw.ellipse((fx - 12 * s, fy - 8 * s, fx + 12 * s, fy + 8 * s), fill=GREEN)
        draw.text((cx, y0 + bh * 0.92), "ON", font=FONT_XS, fill=GREEN, anchor="mm")

    # 软管
    hose_x0 = x0 + bw * 0.08
    hose_y = y0 + bh * 0.28
    hx1, hy1 = hose_x0 - 80 * s, hose_y + 40 * s
    hx2, hy2 = hose_x0 - 160 * s, cy + bh * 0.35
    _sketch_line(draw, (hose_x0, hose_y), (hx1, hy1), METAL_DK, max(4, int(8 * s)), 1)
    _sketch_line(draw, (hx1, hy1), (hx2, hy2), METAL_DK, max(4, int(8 * s)), 2)

    # 地刷
    brush_w, brush_h = 120 * s, 36 * s
    bx0, by0 = hx2 - brush_w / 2, hy2 - brush_h / 2
    draw.rounded_rectangle((bx0, by0, bx0 + brush_w, by0 + brush_h), radius=8 * s, fill=BODY_LT, outline=INK, width=2)
    # 滚刷
    roll_y = by0 + brush_h * 0.55
    ang = time_sec * 10 * suction
    for i in range(6):
        px = bx0 + brush_w * 0.15 + i * brush_w * 0.12
        dy = math.sin(ang + i) * 4 * s
        draw.line((px, roll_y - 6 * s + dy, px, roll_y + 6 * s + dy), fill=METAL, width=2)

    # 地面灰尘被吸入
    if suction > 0.2 and not blocked:
        path = [
            (bx0 + brush_w * 0.5, by0 + brush_h + 8),
            (hx2, hy2),
            (hx1, hy1),
            (hose_x0, hose_y),
            (cx, (cup[1] + cup[3]) / 2),
        ]
        if show_cutaway:
            path.append((fx, fy - fr))
            path.append((cx + bw * 0.55, fy))
        _air_particles(draw, path, time_sec, count=12, dirty=True, speed=1.4 * suction)
    elif blocked:
        # 堵死：粒子在吸嘴处打转
        for i in range(6):
            a = time_sec * 6 + i
            px = bx0 + brush_w / 2 + math.cos(a) * 20
            py = by0 + brush_h + 10 + math.sin(a) * 8
            draw.ellipse((px - 4, py - 4, px + 4, py + 4), fill=DIRT)

    return {
        "cup": cup,
        "fan": (fx, fy),
        "brush": (bx0 + brush_w / 2, by0 + brush_h / 2),
        "body": (x0, y0, x0 + bw, y0 + bh),
    }


def _pressure_gauge(draw, cx, cy, low: bool, time_sec: float):
    _safe_ellipse(draw, (cx - 50, cy - 50, cx + 50, cy + 50), fill=WHITE, outline=INK, width=2)
    label = "低压" if low else "常压"
    col = AIR if low else MUTED
    pulse = _pulse(time_sec, 4, 0.9, 1.0) if low else 1.0
    draw.text((cx, cy - 8), label, font=FONT_S, fill=col, anchor="mm")
    draw.text((cx, cy + 22), f"{'↓' if low else '='}", font=FONT_M, fill=col, anchor="mm")
    if low:
        r = 40 * pulse
        draw.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=AIR, width=3)


def _step_ring(draw, x, y, num: int, name: str, active: bool, time_sec: float):
    base_r = 34 if active else 26
    r = base_r * (_pulse(time_sec, 5, 0.92, 1.08) if active else 1.0)
    col = AIR if active else MUTED
    if active:
        glow = r + 8 + 3 * math.sin(time_sec * 6)
        draw.ellipse((x - glow, y - glow, x + glow, y + glow), outline=(*AIR, 70), width=3)
    draw.ellipse((x - r, y - r, x + r, y + r), fill=AIR if active else WHITE, outline=AIR, width=3)
    draw.text((x, y), str(num), font=FONT_M, fill=WHITE if active else AIR, anchor="mm")
    if active:
        bounce = math.sin(time_sec * 4) * 3
        draw.text((x, y + r + 26 + bounce), name, font=FONT_S, fill=col, anchor="mm")


# ── 分镜 ──


def draw_hook(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, seed=71).convert("RGBA")
    draw = ImageDraw.Draw(img)

    intro = _spring(t, 0.0, 0.3)
    if intro > 0:
        _ken_badge(draw, 170, intro, scale=0.85 + 0.15 * intro)
        slide = (1 - intro) * 36
        _fade_text(draw, (540 + dx, 300), "我是 Ken", FONT_HERO, INK, intro, dy=slide)
        _fade_text(draw, (540, 390), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28), dy=(1 - _spring(t, 0.05, 0.28)) * 28)
        _fade_text(draw, (540, 460), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(draw, (540, 550), "今天：吸尘器怎么吸起灰尘", FONT_L, ACCENT, _spring(t, 0.16, 0.3))

    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        y = 880 + (1 - show) * 50
        _vacuum_body(draw, 560 + dx, int(y), scale=1.05, time_sec=time_sec, suction=0.9 if t > 0.5 else 0.4, show_cutaway=t > 0.55)

    if t > 0.5:
        wrong = _ease(_scene_t(t, 0.5, 0.64))
        right = _spring(t, 0.66, 0.28)
        if wrong > 0 and right < 0.35:
            shake = math.sin(time_sec * 12) * 3 * wrong
            draw.rounded_rectangle((140 + shake, 1280, 940 + shake, 1380), radius=12, fill=(255, 240, 235))
            draw.text((540, 1330), "❌ 不是凭空产生「魔法吸力」", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            draw.rounded_rectangle((100, 1260, 980, 1440), radius=14, fill=(235, 245, 252))
            draw.text((540, 1320), "✓  造低压，大气压把灰「推」进来", font=FONT_L, fill=AIR, anchor="mm")
            draw.text((540, 1395), "机内低压  ←  外面常压", font=FONT_S, fill=MUTED, anchor="mm")

    return img.convert("RGB")


def draw_cutaway(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    dx, _ = _cam_drift(time_sec, 4, 2)
    img = _paper_bg(w, h, seed=73).convert("RGBA")
    draw = ImageDraw.Draw(img)
    title = _spring(t, 0.0, 0.2)
    _fade_text(draw, (540, 95), "拆开看：气流走哪条路", FONT_L, INK, title, dy=(1 - title) * 18)

    show_body = _spring(t, 0.05, 0.28)
    show_fan = _spring(t, 0.22, 0.25)
    show_filter = _spring(t, 0.4, 0.25)
    show_brush = _spring(t, 0.55, 0.28)

    if show_body > 0:
        parts = _vacuum_body(
            draw,
            500 + dx,
            int(560 + (1 - show_body) * -30),
            scale=1.15,
            time_sec=time_sec,
            suction=0.85,
            show_cutaway=show_fan > 0.3,
            bin_full=0.4,
        )
        if show_fan > 0.4:
            _callout(draw, parts["fan"], (720, 480), "风扇抽气", AIR, show_fan)
            _callout(draw, ((parts["cup"][0] + parts["cup"][2]) / 2, parts["cup"][1]), (720, 360), "尘杯拦灰", DIRT, show_fan)
        if show_filter > 0.4:
            _callout(draw, (500, 620), (720, 620), "滤芯拦细尘", FILTER, show_filter)
        if show_brush > 0.3:
            _callout(draw, parts["brush"], (120, 780), "滚刷拍打", MUTED, show_brush)

    if show_brush > 0.4:
        draw.rounded_rectangle((100, 1050, 980, 1280), radius=14, fill=(255, 253, 248))
        draw.text((540, 1110), "密封也很关键", font=FONT_M, fill=INK, anchor="mm")
        draw.text((540, 1185), "哪里漏风，吸力就在哪里打折", font=FONT_S, fill=MUTED, anchor="mm")
        # 漏风示意
        for i in range(4):
            x = 280 + i * 140
            wob = math.sin(time_sec * 8 + i) * 5
            _sketch_line(draw, (x, 1235), (x + 20 + wob, 1235 - 25), AIR_LT, 2, i)

    return img.convert("RGB")


def draw_cycle(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    img = _paper_bg(w, h, seed=77).convert("RGBA")
    draw = ImageDraw.Draw(img)
    draw.text((540, 90), "气压差四步走", font=FONT_L, fill=INK, anchor="mm")

    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))

    # 中部示意：机内低压 vs 外面常压
    draw.rounded_rectangle((80, 200, 500, 560), radius=16, fill=WHITE, outline=LINE, width=2)
    draw.rounded_rectangle((580, 200, 1000, 560), radius=16, fill=WHITE, outline=LINE, width=2)
    draw.text((290, 240), "机内", font=FONT_S, fill=MUTED, anchor="mm")
    draw.text((790, 240), "外面", font=FONT_S, fill=MUTED, anchor="mm")
    _pressure_gauge(draw, 290, 380, low=active >= 0, time_sec=time_sec)
    _pressure_gauge(draw, 790, 380, low=False, time_sec=time_sec)

    # 箭头：外面推入
    if active >= 1:
        for i in range(5):
            y = 300 + i * 40
            phase = (time_sec * 1.5 + i * 0.15) % 1.0
            x = _lerp(620, 460, phase)
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=DIRT if i % 2 else AIR)
        draw.text((540, 520), "大气压把空气 + 灰尘推入 →", font=FONT_S, fill=AIR, anchor="mm")

    # 下方吸尘器动画
    _vacuum_body(
        draw,
        540,
        780,
        scale=0.85,
        time_sec=time_sec,
        suction=0.3 if active < 0 else 1.0,
        show_cutaway=True,
        bin_full=0.2 + 0.15 * max(0, active),
    )

    steps = ["抽气", "涌入", "分离", "过滤"]
    for i, name in enumerate(steps):
        x = 180 + i * 240
        _step_ring(draw, x, 1080, i + 1, name, i == active, time_sec)

    tips = [
        "① 风扇甩出空气 → 腔内气压下降",
        "② 外面气压更高 → 气流从吸嘴涌入",
        "③ 尘杯离心/滤网 → 大颗粒留下来",
        "④ 滤芯拦住细尘 → 干净空气排出",
    ]
    if active >= 0:
        draw.rounded_rectangle((80, 1200, 1000, 1320), radius=14, fill=(255, 253, 248))
        draw.text((540, 1260), tips[active], font=FONT_M, fill=INK, anchor="mm")

    if t > 0.82:
        draw.text((540, 1450), "吸的是气压差，不是真空魔法", font=FONT_S, fill=MUTED, anchor="mm")

    return img.convert("RGB")


def draw_analogy(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    img = _paper_bg(w, h, seed=79).convert("RGBA")
    draw = ImageDraw.Draw(img)
    draw.text((540, 95), "几个常见现象，一次说清", font=FONT_L, fill=INK, anchor="mm")

    cards = [
        (0.08, "尘满了为什么变弱？", "通道堵了，气压差维持不住"),
        (0.32, "滤芯为什么要清/换？", "堵住排气口，电机白转还易过热"),
        (0.55, "吸嘴贴死为什么吸不动？", "没进气 = 没气流 = 灰带不走"),
    ]
    y0 = 250
    for idx, (start, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = y0 + idx * 310 + (1 - a) * 40
        draw.rounded_rectangle((90, y, 990, y + 270), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        draw.text((540, y + 40), title, font=FONT_M, fill=INK, anchor="mm")
        draw.text((540, y + 95), sub, font=FONT_S, fill=MUTED, anchor="mm")

        if idx == 0:
            _vacuum_body(draw, 320, y + 185, scale=0.55, time_sec=time_sec, suction=0.25, bin_full=0.92, show_cutaway=True)
            draw.text((320, y + 250), "尘满 ✗", font=FONT_XS, fill=HOT, anchor="mm")
            _vacuum_body(draw, 760, y + 185, scale=0.55, time_sec=time_sec, suction=1.0, bin_full=0.2, show_cutaway=True)
            draw.text((760, y + 250), "畅通 ✓", font=FONT_XS, fill=GREEN, anchor="mm")
        elif idx == 1:
            # 滤芯堵塞示意
            draw.rounded_rectangle((300, y + 140, 480, y + 230), radius=8, fill=FILTER, outline=INK, width=2)
            for i in range(8):
                draw.line((320 + i * 18, y + 150, 320 + i * 18, y + 220), fill=DIRT, width=3)
            draw.text((390, y + 250), "滤芯堵", font=FONT_XS, fill=HOT, anchor="mm")
            _fan(draw, 720, y + 185, 40, time_sec, rpm=12)
            draw.text((720, y + 250), "电机空转发热", font=FONT_XS, fill=ACCENT, anchor="mm")
        else:
            _vacuum_body(draw, 540, y + 185, scale=0.55, time_sec=time_sec, suction=0.8, blocked=True, show_cutaway=True)
            draw.text((540, y + 250), "进气口被堵死", font=FONT_XS, fill=HOT, anchor="mm")

    if t > 0.78:
        draw.text((540, 1240), "气流才是搬运工", font=FONT_L, fill=INK, anchor="mm")
        draw.text((540, 1310), "气压差才是动力", font=FONT_M, fill=AIR, anchor="mm")

    return img.convert("RGB")


def draw_outro(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    img = _paper_bg(w, h, seed=83).convert("RGBA")
    draw = ImageDraw.Draw(img)

    assemble = _spring(t, 0.0, 0.35)
    _vacuum_body(
        draw,
        540,
        int(480 + (1 - assemble) * 35),
        scale=1.1,
        time_sec=time_sec,
        suction=0.9,
        show_cutaway=True,
        bin_full=0.3,
    )

    if t > 0.2:
        draw.rounded_rectangle((80, 820, 1000, 1040), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        draw.text((540, 870), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        draw.text((540, 940), "风扇抽气造低压", font=FONT_L, fill=INK, anchor="mm")
        draw.text((540, 1000), "大气压推进来 · 滤芯层层拦", font=FONT_L, fill=AIR, anchor="mm")

    if t > 0.5:
        badge = _spring(t, 0.5, 0.25)
        _ken_badge(draw, 1140, badge, scale=0.9 + 0.1 * badge)
        _fade_text(draw, (540, 1230), "关注身边原理 · 我是 Ken", FONT_L, INK, badge, dy=(1 - badge) * 22)
        _fade_text(draw, (540, 1300), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))

    if t > 0.75:
        blink = 0.6 + 0.4 * _pulse(time_sec, 2)
        draw.text(
            (540, 1480),
            "评论区：冰箱 / 吹风机 / 抽油烟机？",
            font=FONT_S,
            fill=(*MUTED, int(255 * blink)),
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


def draw_scene(
    scene_name: str,
    t: float,
    width: int = 1080,
    height: int = 1920,
    *,
    time_sec: float | None = None,
) -> Image.Image:
    ts = time_sec if time_sec is not None else t * 120.0
    return SCENE_DRAWERS.get(scene_name, draw_hook)(_clamp01(t), width, height, ts)
