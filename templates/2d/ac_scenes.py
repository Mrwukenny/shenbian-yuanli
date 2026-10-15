"""空调首集 · 纪录片手绘风 2D，强调连续动画与节奏感。"""

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
COLD = (65, 125, 165)
COLD_LT = (180, 210, 230)
HOT = (195, 90, 55)
HOT_LT = (240, 190, 150)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
COPPER = (175, 115, 65)
SKIN = (235, 200, 170)
SHIRT = (140, 155, 175)
SOFA = (175, 178, 182)
GREEN = (80, 160, 110)


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


def _ease_out(t: float) -> float:
    t = _clamp01(t)
    return 1 - (1 - t) ** 3


def _spring(t: float, start: float = 0.0, dur: float = 0.3) -> float:
    """带回弹的入场。"""
    if t < start:
        return 0.0
    p = _clamp01((t - start) / dur)
    return 1 - math.exp(-6 * p) * math.cos(p * math.pi * 2.5)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * _clamp01(t)


def _pop(t: float, start: float = 0.0, dur: float = 0.22) -> float:
    if t < start:
        return 0.0
    return _ease((t - start) / dur)


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


def _cam_drift(time_sec: float, amp_x: float = 6.0, amp_y: float = 4.0) -> tuple[float, float]:
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
    draw.line((int(w * 0.22), 0, int(w * 0.22), int(h * 0.62)), fill=LINE, width=1)
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
    w = int(400 * scale)
    draw.rounded_rectangle((540 - w // 2, y - 36, 540 + w // 2, y + 36), radius=18, fill=(255, 253, 248, a), outline=ACCENT, width=2)
    draw.text((540, y), "身边原理 · Ken", font=FONT_S, fill=(*ACCENT, a), anchor="mm")


def _cold_stream(draw, x0, y0, w, h, time_sec: float, strength: float = 1.0):
    """冷气粒子流：多段下落 + 摆荡。"""
    if strength <= 0:
        return
    n = 10
    for i in range(n):
        phase = time_sec * 2.8 + i * 0.55
        px = x0 + (i + 0.5) * w / n + math.sin(phase * 1.3) * 8
        prog = (phase * 0.45 + i * 0.1) % 1.0
        py = y0 + prog * h
        r = 4 + 3 * (1 - prog)
        col = COLD_LT if i % 2 else COLD
        draw.ellipse((px - r, py - r, px + r, py + r), fill=(*col, int(180 * strength)))
        _sketch_line(draw, (px, py - 8), (px + math.sin(phase * 2) * 5, py + 14), col, 2, i)


def _heat_stream(draw, x0, y0, time_sec: float, strength: float = 1.0, count: int = 6):
    if strength <= 0:
        return
    for i in range(count):
        phase = time_sec * 3.2 + i * 0.7
        py = y0 - (phase * 0.35 + i * 0.15) % 1.0 * 90
        px = x0 + math.sin(phase * 2.1) * 18 + i * 8
        wob = 8 + 6 * math.sin(phase * 3)
        _sketch_line(draw, (px, py + 20), (px + wob, py - 10), HOT, 3, i)
        draw.ellipse((px - 3, py - 12, px + 3, py - 6), fill=HOT_LT)


def _flow_along_path(draw, path, time_sec: float, count: int, speed: float, hot_until: int):
    """沿折线流动的多个粒子（含拖尾）。"""
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
        u = (time_sec * speed * 0.15 + i / count) % 1.0
        x, y, si = pos_at(u)
        hot = si < hot_until
        col = HOT if hot else COLD
        r = 8 if hot else 7
        draw.ellipse((x - r, y - r, x + r, y + r), fill=col)
        # 拖尾
        x2, y2, _ = pos_at(u - 0.02)
        _sketch_line(draw, (x2, y2), (x, y), col, 3, i)


def _draw_fan(draw, cx, cy, R: float, time_sec: float, rpm: float = 3.5, blades: int = 3):
    ang = time_sec * rpm * math.tau
    draw.ellipse((cx - R, cy - R, cx + R, cy + R), outline=METAL_DK, width=2, fill=WHITE)
    for k in range(blades):
        a = ang + k * (math.tau / blades)
        x2 = cx + math.cos(a) * (R - 8)
        y2 = cy + math.sin(a) * (R - 8)
        draw.line((cx, cy, x2, y2), fill=METAL_DK, width=5)
    draw.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=METAL_DK)


def _sofa_person(draw, cx: int, cy: int, time_sec: float = 0.0):
    bob = math.sin(time_sec * 2.2) * 3
    sw, sh = 320, 110
    x0, y0 = cx - sw // 2, cy - sh // 2 + bob
    draw.rounded_rectangle((x0 + 3, y0 + 5, x0 + sw + 3, y0 + sh + 5), radius=12, fill=(160, 163, 168))
    draw.rounded_rectangle((x0, y0, x0 + sw, y0 + sh), radius=12, fill=SOFA, outline=METAL_DK, width=2)
    draw.rounded_rectangle((x0 + 8, y0 - 28, x0 + sw - 8, y0 + 8), radius=8, fill=SOFA, outline=METAL_DK, width=1)
    px = cx - 30
    draw.ellipse((px - 22, y0 - 70, px + 22, y0 - 26), fill=SKIN, outline=INK, width=1)
    draw.rounded_rectangle((px - 28, y0 - 30, px + 28, y0 + 20), radius=8, fill=SHIRT, outline=INK, width=1)
    # 扇动
    ang = math.sin(time_sec * 8) * 0.55
    fx = px + 42 + math.cos(ang) * 22
    fy = y0 - 8 + math.sin(ang) * 14
    _sketch_line(draw, (px + 36, y0 - 6), (fx, fy), MUTED, 3, 1)
    # 舒服表情：眼睛弯
    draw.arc((px - 12, y0 - 58, px - 4, y0 - 50), 0, 180, fill=INK, width=2)
    draw.arc((px + 4, y0 - 58, px + 12, y0 - 50), 0, 180, fill=INK, width=2)


def _indoor(draw, cx, cy, w=440, h=130, time_sec=0.0, blow=0.0, cut=False, label=False, label_alpha=1.0):
    pulse = _pulse(time_sec, 3.0, 0.98, 1.02)
    cx, cy = cx, cy
    w, h = w * pulse, h
    x0, y0 = cx - w / 2, cy - h / 2
    draw.rounded_rectangle((x0 + 4, y0 + 6, x0 + w + 4, y0 + h + 6), radius=14, fill=(210, 206, 200))
    draw.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=14, fill=WHITE, outline=METAL_DK, width=2)
    for i in range(6):
        draw.line((x0 + 36, y0 + 12 + i * 5, x0 + w - 36, y0 + 12 + i * 5), fill=LINE, width=1)
    draw.rounded_rectangle((x0 + 22, y0 + 48, x0 + w - 22, y0 + h - 14), radius=8, fill=(245, 243, 238), outline=LINE, width=1)
    for i in range(3):
        yy = y0 + 58 + i * 12
        draw.line((x0 + 50, yy, x0 + w - 50, yy), fill=METAL_DK, width=2)
    draw.ellipse((x0 + w - 44, y0 + 62, x0 + w - 30, y0 + 76), fill=GREEN)
    if cut:
        glow = int(120 + 80 * _pulse(time_sec, 4))
        draw.rounded_rectangle((x0 + 50, y0 + 18, x0 + w - 50, y0 + 62), radius=6, outline=COLD, width=2)
        for i in range(5):
            xx = x0 + 80 + i * 58
            draw.arc((xx - 12, y0 + 26, xx + 12, y0 + 54), 0, 360, fill=COPPER, width=2)
    if blow > 0:
        _cold_stream(draw, x0 + 40, y0 + h - 4, w - 80, 120 + 40 * blow, time_sec, blow)
    if label:
        _callout(draw, (cx, y0 - 8), (cx - 180, y0 - 60), "室内机", COLD, label_alpha)


def _outdoor(draw, cx, cy, w=250, h=310, time_sec=0.0, cut=False, heat=0.0, label=False, label_alpha=1.0):
    shake = math.sin(time_sec * 14) * 2 * heat if heat > 0.3 else 0
    cx += shake
    x0, y0 = cx - w / 2, cy - h / 2
    draw.rounded_rectangle((x0 + 3, y0 + 5, x0 + w + 3, y0 + h + 5), radius=10, fill=(200, 196, 190))
    draw.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=10, fill=METAL, outline=METAL_DK, width=2)
    fx, fy = cx, y0 + h * 0.36
    _draw_fan(draw, fx, fy, 58, time_sec, rpm=5.5)
    for i in range(14):
        shimmer = int(2 * math.sin(time_sec * 5 + i * 0.4))
        draw.line((x0 + 10 + i * 3.5, y0 + 18, x0 + 10 + i * 3.5 + shimmer, y0 + h - 72), fill=COPPER, width=2)
    if cut:
        cx2, cy2 = cx - 20, y0 + h * 0.78
        pz = math.sin(time_sec * 6) * 6
        draw.ellipse((cx2 - 34, cy2 - 34 + pz, cx2 + 34, cy2 + 34 + pz), fill=(80, 84, 90), outline=INK, width=2)
        draw.rectangle((cx2 - 18, cy2 - 50 + pz, cx2 + 18, cy2 - 30 + pz), fill=(80, 84, 90), outline=INK, width=1)
    if heat > 0:
        _heat_stream(draw, x0 + w + 8, y0 + h * 0.25, time_sec, heat, count=7)
    if label:
        _callout(draw, (cx, y0 + h + 8), (cx + 160, y0 + h + 50), "室外机", HOT, label_alpha)


def _pipe(draw, x1, y1, x2, y2, time_sec: float = 0.0):
    _sketch_line(draw, (x1, y1 - 6), (x2, y2 - 6), COPPER, 8, 1)
    _sketch_line(draw, (x1, y1 + 8), (x2, y2 + 8), (140, 88, 48), 5, 2)
    path = [(x1, y1 - 6), (x2, y2 - 6)]
    _flow_along_path(draw, path, time_sec, count=6, speed=1.2, hot_until=1)


def _step_ring(draw, x, y, num: int, name: str, active: bool, hot: bool, time_sec: float):
    base_r = 38 if active else 28
    r = base_r * (_pulse(time_sec, 5, 0.92, 1.08) if active else 1.0)
    col = HOT if hot else COLD
    if active:
        glow_r = r + 8 + 4 * math.sin(time_sec * 6)
        draw.ellipse((x - glow_r, y - glow_r, x + glow_r, y + glow_r), outline=(*col, 80), width=3)
    draw.ellipse((x - r, y - r, x + r, y + r), fill=col if active else WHITE, outline=col, width=3)
    draw.text((x, y), str(num), font=FONT_M, fill=WHITE if active else col, anchor="mm")
    if active:
        bounce = math.sin(time_sec * 4) * 4
        draw.text((x, y + r + 28 + bounce), name, font=FONT_S, fill=col, anchor="mm")


def _heat_arrow(draw, x1, y1, x2, y2, alpha: float, time_sec: float = 0.0):
    if alpha <= 0:
        return
    # 流动虚线箭头
    ang = math.atan2(y2 - y1, x2 - x1)
    dist = math.hypot(x2 - x1, y2 - y1)
    dash = 5
    for i in range(int(dist / 14)):
        f0 = ((i * 14 + time_sec * 80) % dist) / dist
        f1 = min(f0 + 0.08, 1.0)
        ax = _lerp(x1, x2, f0)
        ay = _lerp(y1, y2, f0)
        bx = _lerp(x1, x2, f1)
        by = _lerp(y1, y2, f1)
        _sketch_line(draw, (ax, ay), (bx, by), HOT, 4, i)
    s = 16
    for da in (2.6, -2.6):
        ax = x2 - s * math.cos(ang - da)
        ay = y2 - s * math.sin(ang - da)
        _sketch_line(draw, (x2, y2), (ax, ay), HOT, 3, int(da * 10))


def _thermometer(draw, x, y, level: float, time_sec: float):
    wobble = math.sin(time_sec * 3) * 2
    draw.rounded_rectangle((x - 14 + wobble, y - 80, x + 14 + wobble, y + 40), radius=8, fill=WHITE, outline=INK, width=2)
    draw.ellipse((x - 22 + wobble, y + 28, x + 22 + wobble, y + 72), fill=WHITE, outline=INK, width=2)
    h = int(100 * _clamp01(level))
    draw.rectangle((x - 8 + wobble, y + 40 - h, x + 8 + wobble, y + 40), fill=HOT)
    draw.ellipse((x - 16 + wobble, y + 34, x + 16 + wobble, y + 66), fill=HOT)
    draw.text((x + 36, y - 20), f"{int(40 + 40 * level)}°C", font=FONT_S, fill=HOT, anchor="lm")


def _piston_anim(draw, cx, cy, time_sec: float):
    dz = math.sin(time_sec * 8) * 14
    draw.ellipse((cx - 55, cy - 55, cx + 55, cy + 55), fill=(80, 84, 90), outline=INK, width=2)
    draw.rectangle((cx - 28, cy - 75 + dz, cx + 28, cy - 52 + dz), fill=(80, 84, 90), outline=INK, width=1)
    draw.ellipse((cx - 38, cy - 20 + dz, cx + 38, cy + 20 + dz), fill=METAL, outline=INK, width=2)


# ── 分镜 ──


def draw_hook(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    dx, dy = _cam_drift(time_sec, 5, 3)
    img = _paper_bg(w, h, seed=11).convert("RGBA")
    draw = ImageDraw.Draw(img)

    intro = _spring(t, 0.0, 0.32)
    if intro > 0:
        _ken_badge(draw, 180, intro, scale=0.85 + 0.15 * intro)
        slide = (1 - intro) * 40
        _fade_text(draw, (540 + dx, 320), "我是 Ken", FONT_HERO, INK, intro, dy=slide)
        _fade_text(draw, (540, 410), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28), dy=(1 - _spring(t, 0.05, 0.28)) * 30)
        _fade_text(draw, (540, 480), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28), dy=(1 - _spring(t, 0.1, 0.28)) * 25)
        _fade_text(draw, (540, 580), "今天：空调怎么让房间变凉", FONT_L, ACCENT, _spring(t, 0.16, 0.3), dy=(1 - _spring(t, 0.16, 0.3)) * 35)

    room = _ease(_scene_t(t, 0.3, 0.46))
    if room > 0:
        slide_room = (1 - room) * 80
        _sofa_person(draw, 420 + dx, int(1180 + slide_room), time_sec)
        blow = _ease(_scene_t(t, 0.4, 0.78))
        _indoor(draw, 540 + dx, int(720 + slide_room * 0.3), w=460, h=135, time_sec=time_sec, blow=blow * room, label=room > 0.5, label_alpha=room)
        heat = 0.35 if t > 0.52 else 0.0
        _outdoor(draw, 820, int(1380 + slide_room * 0.2), w=200, h=250, time_sec=time_sec, heat=heat)

    if t > 0.52:
        wrong = _ease(_scene_t(t, 0.52, 0.65))
        right = _spring(t, 0.66, 0.25)
        if wrong > 0 and right < 0.4:
            shake = math.sin(time_sec * 12) * 3 * wrong
            draw.rounded_rectangle((180 + shake, 1480, 900 + shake, 1580), radius=12, fill=(255, 240, 235))
            draw.text((540, 1530), "❌ 不是在「制造冷气」", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            draw.rounded_rectangle((140, 1460, 940, 1620), radius=14, fill=(240, 248, 252))
            draw.text((540, 1510), "✓  把房间里的热搬到室外", font=FONT_L, fill=COLD, anchor="mm")
            _heat_arrow(draw, 540, 1280, 820, 1380, right, time_sec)
            _heat_stream(draw, 760, 1320, time_sec, right * 0.8, count=4)

    return img.convert("RGB")


def draw_cutaway(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    dx, dy = _cam_drift(time_sec, 4, 3)
    img = _paper_bg(w, h, seed=13).convert("RGBA")
    draw = ImageDraw.Draw(img)
    title_in = _spring(t, 0.0, 0.2)
    _fade_text(draw, (540, 100), "拆开看：两台机器怎么配合", FONT_L, INK, title_in, dy=(1 - title_in) * 20)

    show_in = _spring(t, 0.05, 0.28)
    show_pipe = _spring(t, 0.18, 0.25)
    show_out = _spring(t, 0.32, 0.28)
    show_comp = _spring(t, 0.52, 0.28)

    if show_in > 0:
        y_in = 320 + (1 - show_in) * -60
        _indoor(draw, 540 + dx, int(y_in), w=500, h=140, time_sec=time_sec, cut=show_in > 0.5, blow=0.45 * show_in, label=True, label_alpha=show_in)
        if show_in > 0.45:
            _callout(draw, (380, y_in), (160, y_in + 70), "蒸发器吸热", COLD, show_in)
            _cold_stream(draw, 300, y_in + 80, 200, 60, time_sec, 0.5 * show_in)

    if show_pipe > 0:
        _pipe(draw, 540, 420, 540, 560, time_sec)
        draw.text((720, 490), "铜管 · 制冷剂", font=FONT_S, fill=MUTED, anchor="mm")

    if show_out > 0:
        y_out = 820 + (1 - show_out) * 70
        _outdoor(draw, 540, int(y_out), w=290, h=350, time_sec=time_sec, cut=show_out > 0.5, heat=0.5 if t > 0.55 else 0.15, label=True, label_alpha=show_out)
        if show_out > 0.5:
            _callout(draw, (680, y_out - 40), (860, y_out - 100), "冷凝器放热", HOT, show_out)

    if show_comp > 0:
        cy = 1080 + (1 - show_comp) * 50
        _piston_anim(draw, 540, int(cy), time_sec)
        _callout(draw, (540, cy), (200, cy + 70), "压缩机：推动循环", INK, show_comp)
        draw.text((540, 1280), "制冷剂 = 专职搬运工", font=FONT_M, fill=MUTED, anchor="mm")

    return img.convert("RGB")


def draw_cycle(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    img = _paper_bg(w, h, seed=17).convert("RGBA")
    draw = ImageDraw.Draw(img)
    draw.text((540, 95), "四步循环 · 记住顺序", font=FONT_L, fill=INK, anchor="mm")

    _indoor(draw, 180, 420, w=260, h=85, time_sec=time_sec, cut=True, blow=0.55)
    _outdoor(draw, 900, 460, w=190, h=240, time_sec=time_sec, cut=True, heat=0.55)

    path = [(540, 260), (760, 420), (540, 620), (320, 780), (540, 940), (540, 260)]
    for i in range(len(path) - 1):
        _sketch_line(draw, path[i], path[i + 1], LINE, 5, i)
        _sketch_line(draw, path[i], path[i + 1], COPPER, 2, i + 10)

    steps = ["压缩", "冷凝", "节流", "蒸发"]
    pos = [(760, 420), (540, 620), (320, 780), (180, 420)]
    hot_flags = [True, True, False, False]
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.17))

    for i, (name, (x, y), hot) in enumerate(zip(steps, pos, hot_flags)):
        _step_ring(draw, x, y, i + 1, name, i == active, hot, time_sec)

    _flow_along_path(draw, path, time_sec, count=8, speed=1.8, hot_until=2)

    tips = [
        "① 压缩机把气体压紧 → 变热高压",
        "② 室外冷凝器：风扇散热，气体变液体",
        "③ 节流阀降压 → 液体变冷",
        "④ 室内蒸发器吸热 → 房间变凉",
    ]
    if active >= 0:
        tip_in = _pulse(time_sec, 3, 0.0, 1.0) * 0.15 + 0.85
        draw.rounded_rectangle((80, 1080, 1000, 1180), radius=14, fill=(255, 253, 248))
        draw.text((540, 1130), tips[active], font=FONT_M, fill=INK, anchor="mm")

    if t > 0.72:
        alpha = _ease(_scene_t(t, 0.72, 0.88))
        draw.text((540, 1320), "一圈一圈，热就被搬走了", font=FONT_S, fill=(*MUTED, int(255 * alpha)), anchor="mm")

    return img.convert("RGB")


def draw_analogy(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    dx, _ = _cam_drift(time_sec, 8, 0)
    img = _paper_bg(w, h, seed=19).convert("RGBA")
    draw = ImageDraw.Draw(img)
    draw.text((540, 100), "摸摸室外机：为什么烫？", font=FONT_L, fill=INK, anchor="mm")

    heat = _ease(min(t / 0.32, 1))
    zoom = 1.0 + heat * 0.06
    _outdoor(draw, 540 + dx, 720, w=340 * zoom, h=420 * zoom, time_sec=time_sec, cut=True, heat=max(heat, 0.25))

    if t > 0.2:
        box_in = _spring(t, 0.2, 0.25)
        draw.rounded_rectangle((200, 980, 880, 1080), radius=12, fill=(*HOT_LT, int(255 * box_in)))
        draw.text((540, 1030), "不是坏了 —— 是热量的出口", font=FONT_M, fill=HOT, anchor="mm")

    if t > 0.4:
        _heat_arrow(draw, 540, 920, 540, 760, _ease(_scene_t(t, 0.4, 0.58)), time_sec)
        _thermometer(draw, 720, 780, _clamp01(t * 1.1), time_sec)

    if t > 0.58:
        scale_in = _spring(t, 0.58, 0.3)
        draw.text((540, 1200), "空调不造冷，只搬家", font=FONT_HERO, fill=INK, anchor="mm")
        draw.text((540, 1290), "室内凉 ↓  室外热 ↑", font=FONT_M, fill=MUTED, anchor="mm")
        _cold_stream(draw, 200, 1240, 200, 80, time_sec, 0.4 * scale_in)
        _heat_stream(draw, 820, 1240, time_sec, 0.5 * scale_in, count=5)

    if t > 0.78:
        draw.text((540, 1420), "整栋楼夏天都在往外扔热量", font=FONT_S, fill=MUTED, anchor="mm")

    return img.convert("RGB")


def draw_outro(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    img = _paper_bg(w, h, seed=23).convert("RGBA")
    draw = ImageDraw.Draw(img)

    assemble = _spring(t, 0.0, 0.35)
    _indoor(draw, 280, int(480 + (1 - assemble) * -40), w=360, h=105, time_sec=time_sec, blow=0.65, label=True, label_alpha=assemble)
    _pipe(draw, 480, 490, 620, 510, time_sec)
    _outdoor(draw, 820, int(530 + (1 - assemble) * 40), w=230, h=290, time_sec=time_sec, heat=0.5, label=True, label_alpha=assemble)

    if t > 0.12:
        draw.text((540, 780), "室内吸热  →  室外放热", font=FONT_M, fill=MUTED, anchor="mm")
        for i in range(6):
            yy = 650 + i * 10 + math.sin(time_sec * 4 + i) * 2
            _sketch_line(draw, (620, yy), (740, yy), COPPER, 3, i)

    if t > 0.32:
        card = _spring(t, 0.32, 0.28)
        draw.rounded_rectangle((120, 900, 960, 1040), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        draw.text((540, 950), "热量搬运队", font=FONT_L, fill=INK, anchor="mm")
        draw.text((540, 1010), "制冷剂 = 队员  ·  压缩机 = 队长", font=FONT_S, fill=MUTED, anchor="mm")
        path = [(300, 520), (820, 560)]
        _flow_along_path(draw, path, time_sec, count=5, speed=1.0, hot_until=0)

    if t > 0.52:
        badge = _spring(t, 0.52, 0.25)
        _ken_badge(draw, 1160, badge, scale=0.9 + 0.1 * badge)
        _fade_text(draw, (540, 1240), "关注身边原理 · 我是 Ken", FONT_L, INK, badge, dy=(1 - badge) * 25)
        _fade_text(draw, (540, 1310), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.58, 0.25))

    if t > 0.75:
        blink = 0.6 + 0.4 * _pulse(time_sec, 2)
        draw.text((540, 1460), "评论区：冰箱 / 洗衣机 / 无线充？", font=FONT_S, fill=(*MUTED, int(255 * blink)), anchor="mm")

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
