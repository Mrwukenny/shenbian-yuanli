"""洗衣机分集 · 纪录片手绘风 2D，强调连续动画。"""

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
WATER = (70, 140, 185)
WATER_LT = (170, 210, 235)
HOT = (195, 90, 55)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (235, 236, 238)
BODY_DK = (190, 194, 200)
CLOTH = (120, 150, 190)
CLOTH2 = (200, 120, 110)
SOAP = (140, 190, 120)
DIRT = (130, 100, 70)
GREEN = (80, 160, 110)


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
    w = int(400 * scale)
    draw.rounded_rectangle(
        (540 - w // 2, y - 36, 540 + w // 2, y + 36),
        radius=18,
        fill=(255, 253, 248, a),
        outline=ACCENT,
        width=2,
    )
    draw.text((540, y), "身边原理 · Ken", font=FONT_S, fill=(*ACCENT, a), anchor="mm")


def _bubbles(draw, cx, cy, r_area: float, time_sec: float, count: int = 12, alpha: float = 1.0):
    for i in range(count):
        phase = time_sec * 1.8 + i * 0.7
        u = (phase * 0.25 + i / count) % 1.0
        ang = i * 2.3
        px = cx + math.cos(ang + time_sec * 0.5) * r_area * (0.2 + 0.7 * u)
        py = cy - u * r_area * 1.2 + math.sin(phase) * 6
        rr = 4 + (i % 4) * 2
        a = int(160 * alpha * (1 - u * 0.5))
        draw.ellipse((px - rr, py - rr, px + rr, py + rr), outline=(*WATER_LT, a), width=2)


def _water_swirl(draw, cx, cy, R: float, time_sec: float, strength: float = 1.0):
    if strength <= 0:
        return
    for i in range(5):
        rr = R * (0.35 + i * 0.12)
        pts = []
        for k in range(24):
            a = time_sec * (2.2 + i * 0.3) + k / 24 * math.tau
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.55))
        for j in range(len(pts) - 1):
            draw.line((pts[j], pts[j + 1]), fill=WATER if i % 2 == 0 else WATER_LT, width=2)


def _cloth_piece(draw, cx, cy, ang: float, color=CLOTH, scale: float = 1.0):
    w, h = 36 * scale, 22 * scale
    pts = []
    for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h)):
        rx = dx * math.cos(ang) - dy * math.sin(ang)
        ry = dx * math.sin(ang) + dy * math.cos(ang)
        pts.append((cx + rx, cy + ry))
    draw.polygon(pts, fill=color, outline=INK)
    # 小污点
    draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=DIRT)


def _detergent_molecule(draw, cx, cy, ang: float, scale: float = 1.0):
    """一头亲水一头亲油的简化示意。"""
    L = 22 * scale
    x2 = cx + math.cos(ang) * L
    y2 = cy + math.sin(ang) * L
    _sketch_line(draw, (cx, cy), (x2, y2), SOAP, 3, int(ang * 10))
    draw.ellipse((cx - 7 * scale, cy - 7 * scale, cx + 7 * scale, cy + 7 * scale), fill=WATER, outline=INK, width=1)
    draw.ellipse((x2 - 5 * scale, y2 - 5 * scale, x2 + 5 * scale, y2 + 5 * scale), fill=HOT, outline=INK, width=1)


def _washer_body(
    draw,
    cx,
    cy,
    *,
    w: float = 360,
    h: float = 420,
    time_sec: float = 0.0,
    lid_open: float = 0.0,
    water_level: float = 0.55,
    swirl: float = 1.0,
    spin: float = 0.0,
    show_pulsator: bool = True,
    show_motor: bool = False,
    shake: float = 0.0,
):
    sx = math.sin(time_sec * 18) * 6 * shake
    x0, y0 = cx - w / 2 + sx, cy - h / 2
    # 阴影
    draw.rounded_rectangle((x0 + 6, y0 + 10, x0 + w + 6, y0 + h + 10), radius=22, fill=(200, 196, 190))
    draw.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=22, fill=BODY, outline=INK, width=2)
    # 控制面板（按比例，避免小尺寸时坐标倒置）
    panel_top = y0 + h * 0.04
    panel_bot = y0 + h * 0.16
    draw.rounded_rectangle((x0 + w * 0.08, panel_top, x0 + w * 0.92, panel_bot), radius=6, fill=BODY_DK, outline=METAL_DK, width=1)
    kn = min(18, w * 0.08)
    draw.ellipse((x0 + w * 0.78, panel_top + 4, x0 + w * 0.78 + kn, panel_top + 4 + kn), fill=GREEN, outline=INK, width=1)

    # 内筒开口
    pad_x = w * 0.11
    drum = (x0 + pad_x, y0 + h * 0.2, x0 + w - pad_x, y0 + h * 0.86)
    if drum[3] - drum[1] < 20:
        drum = (x0 + pad_x, y0 + h * 0.22, x0 + w - pad_x, y0 + h * 0.88)
    draw.ellipse(drum, fill=(55, 60, 68), outline=METAL_DK, width=2)
    dcx = (drum[0] + drum[2]) / 2
    dcy = (drum[1] + drum[3]) / 2
    drum_rx = (drum[2] - drum[0]) / 2
    drum_ry = (drum[3] - drum[1]) / 2

    # 水位
    if water_level > 0.02:
        mid_y = _lerp(drum[3] - 4, drum[1] + 4, _clamp01(water_level))
        if mid_y < drum[3] - 6:
            draw.ellipse((drum[0] + 6, mid_y, drum[2] - 6, drum[3] - 4), fill=(*WATER, 140))
            _water_swirl(draw, dcx, (mid_y + drum[3]) / 2, drum_rx * 0.55, time_sec, swirl)
            _bubbles(draw, dcx, mid_y + 8, max(20, drum_rx * 0.45), time_sec, count=max(4, int(8 * w / 360)), alpha=0.7 * swirl)

    # 衣物翻滚
    rpm = 1.2 + spin * 8
    cloth_n = 5 if w >= 220 else 3
    for i in range(cloth_n):
        a = time_sec * rpm + i * 1.25
        r = drum_rx * (0.35 + (i % 3) * 0.12)
        px = dcx + math.cos(a) * r
        py = dcy + math.sin(a) * r * (0.45 if spin < 0.5 else 0.75)
        _cloth_piece(draw, px, py, a + i, CLOTH if i % 2 == 0 else CLOTH2, scale=max(0.4, 0.85 * w / 360))

    # 波轮
    if show_pulsator:
        pcx, pcy = dcx, drum[3] - drum_ry * 0.35
        pr = max(12, drum_rx * 0.38)
        ang = time_sec * (3.5 if swirl > 0.3 else 0.4) * (1 if int(time_sec * 2) % 2 == 0 else -1)
        draw.ellipse((pcx - pr, pcy - pr * 0.35, pcx + pr, pcy + pr * 0.35), fill=METAL, outline=METAL_DK, width=2)
        for k in range(4):
            a = ang + k * math.pi / 2
            _sketch_line(draw, (pcx, pcy), (pcx + math.cos(a) * pr * 0.85, pcy + math.sin(a) * pr * 0.25), METAL_DK, 2, k)

    # 小孔示意
    hole_n = 10 if w >= 220 else 6
    for i in range(hole_n):
        a = i / hole_n * math.tau
        hx = dcx + math.cos(a) * (drum_rx - max(6, w * 0.04))
        hy = dcy + math.sin(a) * (drum_ry - max(8, h * 0.05))
        hr = max(2, w * 0.008)
        draw.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=METAL)

    # 盖子
    if lid_open < 0.85:
        lid_h = max(4, h * 0.12 * (1 - lid_open))
        lid_top = y0 + h * 0.175
        draw.rounded_rectangle((x0 + w * 0.14, lid_top, x0 + w * 0.86, lid_top + lid_h), radius=4, fill=BODY_DK, outline=INK, width=1)

    # 底座电机
    if show_motor:
        mx, my = cx + sx, y0 + h + 10
        draw.rounded_rectangle((mx - 50, my, mx + 50, my + 55), radius=8, fill=METAL_DK, outline=INK, width=2)
        draw.ellipse((mx - 18, my + 12, mx + 18, my + 48), fill=METAL)
        ang = time_sec * 10
        _sketch_line(draw, (mx, my + 30), (mx + math.cos(ang) * 14, my + 30 + math.sin(ang) * 14), INK, 3, 1)
        _callout(draw, (mx + 50, my + 20), (mx + 90, my - 10), "电机", MUTED)


def _step_ring(draw, x, y, num: int, name: str, active: bool, time_sec: float):
    base_r = 34 if active else 26
    r = base_r * (_pulse(time_sec, 5, 0.92, 1.08) if active else 1.0)
    col = WATER if active else MUTED
    if active:
        glow = r + 8 + 3 * math.sin(time_sec * 6)
        draw.ellipse((x - glow, y - glow, x + glow, y + glow), outline=(*WATER, 70), width=3)
    draw.ellipse((x - r, y - r, x + r, y + r), fill=WATER if active else WHITE, outline=WATER, width=3)
    draw.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WATER, anchor="mm")
    if active:
        bounce = math.sin(time_sec * 4) * 3
        draw.text((x, y + r + 26 + bounce), name, font=FONT_S, fill=col, anchor="mm")


def _centrifuge_arrows(draw, cx, cy, time_sec: float, strength: float = 1.0):
    for i in range(8):
        a = i / 8 * math.tau + time_sec * 0.5
        x1 = cx + math.cos(a) * 40
        y1 = cy + math.sin(a) * 40
        x2 = cx + math.cos(a) * (70 + 20 * strength)
        y2 = cy + math.sin(a) * (70 + 20 * strength)
        _sketch_line(draw, (x1, y1), (x2, y2), WATER, 3, i)
        # 水滴
        draw.ellipse((x2 - 5, y2 - 5, x2 + 5, y2 + 5), fill=WATER_LT)


# ── 分镜 ──


def draw_hook(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, seed=51).convert("RGBA")
    draw = ImageDraw.Draw(img)

    intro = _spring(t, 0.0, 0.3)
    if intro > 0:
        _ken_badge(draw, 170, intro, scale=0.85 + 0.15 * intro)
        slide = (1 - intro) * 36
        _fade_text(draw, (540 + dx, 300), "我是 Ken", FONT_HERO, INK, intro, dy=slide)
        _fade_text(draw, (540, 390), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28), dy=(1 - _spring(t, 0.05, 0.28)) * 28)
        _fade_text(draw, (540, 460), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(draw, (540, 550), "今天：洗衣机怎么洗干净衣服", FONT_L, ACCENT, _spring(t, 0.16, 0.3))

    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        y = 900 + (1 - show) * 50
        _washer_body(
            draw,
            540 + dx,
            int(y),
            w=340,
            h=400,
            time_sec=time_sec,
            lid_open=0.55,
            swirl=0.8 if t > 0.5 else 0.3,
            water_level=0.5,
        )

    if t > 0.5:
        wrong = _ease(_scene_t(t, 0.5, 0.64))
        right = _spring(t, 0.66, 0.28)
        if wrong > 0 and right < 0.35:
            shake = math.sin(time_sec * 12) * 3 * wrong
            draw.rounded_rectangle((140 + shake, 1280, 940 + shake, 1380), radius=12, fill=(255, 240, 235))
            draw.text((540, 1330), "❌ 不只是大桶搅水泡一泡", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            draw.rounded_rectangle((100, 1260, 980, 1440), radius=14, fill=(235, 245, 252))
            draw.text((540, 1320), "✓  水流冲 + 衣物搓 + 洗涤剂撬污", font=FONT_L, fill=WATER, anchor="mm")
            labels = ["冲刷", "摩擦", "撬污"]
            for i, lab in enumerate(labels):
                x = 220 + i * 220
                draw.ellipse((x - 36, 1385, x + 36, 1455), fill=WHITE, outline=WATER, width=2)
                draw.text((x, 1420), lab, font=FONT_S, fill=WATER, anchor="mm")

    return img.convert("RGB")


def draw_cutaway(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    dx, _ = _cam_drift(time_sec, 4, 2)
    img = _paper_bg(w, h, seed=53).convert("RGBA")
    draw = ImageDraw.Draw(img)
    title = _spring(t, 0.0, 0.2)
    _fade_text(draw, (540, 95), "拆开看：洗衣机里有谁", FONT_L, INK, title, dy=(1 - title) * 18)

    show_body = _spring(t, 0.05, 0.28)
    show_pulsator = _spring(t, 0.22, 0.25)
    show_motor = _spring(t, 0.4, 0.25)
    show_flow = _spring(t, 0.58, 0.28)

    if show_body > 0:
        _washer_body(
            draw,
            540 + dx,
            int(560 + (1 - show_body) * -30),
            w=380,
            h=440,
            time_sec=time_sec,
            lid_open=0.7,
            swirl=0.6 * show_pulsator,
            show_pulsator=True,
            show_motor=show_motor > 0.3,
            water_level=0.45,
        )

    if show_pulsator > 0.4:
        _callout(draw, (540, 620), (780, 520), "内筒小孔", MUTED, show_pulsator)
        _callout(draw, (540, 720), (780, 700), "波轮搅水", WATER, show_pulsator)

    if show_motor > 0.4:
        _callout(draw, (540, 920), (120, 980), "排水泵抽脏水", MUTED, show_motor)

    if show_flow > 0.3:
        draw.rounded_rectangle((100, 1100, 980, 1380), radius=14, fill=(255, 253, 248))
        draw.text((540, 1150), "程序流水线", font=FONT_M, fill=INK, anchor="mm")
        steps = ["进水", "洗涤", "排水", "漂洗", "甩干"]
        for i, name in enumerate(steps):
            x = 160 + i * 170
            on = int((time_sec * 1.2) % 5) == i
            draw.rounded_rectangle((x - 55, 1220, x + 55, 1300), radius=10, fill=WATER if on else WHITE, outline=WATER, width=2)
            draw.text((x, 1260), name, font=FONT_S, fill=WHITE if on else WATER, anchor="mm")
            if i < 4:
                _sketch_line(draw, (x + 58, 1260), (x + 112, 1260), LINE, 2, i)

    return img.convert("RGB")


def draw_cycle(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    img = _paper_bg(w, h, seed=57).convert("RGBA")
    draw = ImageDraw.Draw(img)
    draw.text((540, 90), "去污四步 + 甩干", font=FONT_L, fill=INK, anchor="mm")

    active = -1 if t < 0.06 else min(4, int((t - 0.06) / 0.16))
    # 0润湿 1摩擦 2洗涤剂 3漂洗 4甩干

    # 左侧洗衣机状态随步骤变化
    swirl = 0.3 if active < 1 else (1.0 if active < 4 else 0.2)
    spin = 1.0 if active >= 4 else 0.0
    water = 0.15 if active >= 4 else 0.55
    _washer_body(
        draw,
        280,
        520,
        w=300,
        h=360,
        time_sec=time_sec,
        lid_open=0.4,
        swirl=swirl,
        spin=spin,
        water_level=water,
        shake=0.4 if active >= 4 else 0.0,
    )

    # 右侧特写
    draw.rounded_rectangle((480, 240, 1000, 760), radius=16, fill=WHITE, outline=LINE, width=2)
    if active <= 0:
        draw.text((740, 290), "① 润湿纤维", font=FONT_M, fill=WATER, anchor="mm")
        for i in range(6):
            x = 580 + i * 55
            y = 480 + math.sin(time_sec * 3 + i) * 8
            draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=WATER_LT)
            _sketch_line(draw, (x, y - 40), (x, y - 10), WATER, 2, i)
        draw.text((740, 650), "降低表面张力，水钻进缝隙", font=FONT_S, fill=MUTED, anchor="mm")
    elif active == 1:
        draw.text((740, 290), "② 翻滚摩擦", font=FONT_M, fill=WATER, anchor="mm")
        for i in range(4):
            a = time_sec * 4 + i * 1.5
            _cloth_piece(draw, 740 + math.cos(a) * 80, 480 + math.sin(a) * 50, a, CLOTH if i % 2 else CLOTH2)
        draw.text((740, 650), "泥沙被机械力蹭下来", font=FONT_S, fill=MUTED, anchor="mm")
    elif active == 2:
        draw.text((740, 290), "③ 洗涤剂撬污", font=FONT_M, fill=SOAP, anchor="mm")
        # 油污团
        draw.ellipse((700, 430, 780, 510), fill=DIRT, outline=INK, width=2)
        for i in range(8):
            a = time_sec * 2 + i * 0.8
            _detergent_molecule(draw, 740 + math.cos(a) * 70, 470 + math.sin(a) * 55, a + math.pi, scale=1.0)
        draw.text((740, 620), "一头亲水 · 一头亲油", font=FONT_S, fill=MUTED, anchor="mm")
        draw.text((740, 680), "把油污拽进水里", font=FONT_S, fill=SOAP, anchor="mm")
    elif active == 3:
        draw.text((740, 290), "④ 排水 + 漂洗", font=FONT_M, fill=WATER, anchor="mm")
        for i in range(10):
            u = (time_sec * 0.8 + i / 10) % 1.0
            x = 560 + i * 40
            y = 350 + u * 280
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=WATER if i % 2 else WATER_LT)
        draw.text((740, 680), "脏水走，清水冲残留", font=FONT_S, fill=MUTED, anchor="mm")
    else:
        draw.text((740, 290), "⑤ 离心甩干", font=FONT_M, fill=ACCENT, anchor="mm")
        _centrifuge_arrows(draw, 740, 480, time_sec, 1.0)
        draw.text((740, 650), "水被甩出小孔，衣服变半干", font=FONT_S, fill=MUTED, anchor="mm")

    steps = ["润湿", "摩擦", "撬污", "漂洗", "甩干"]
    for i, name in enumerate(steps):
        x = 140 + i * 200
        _step_ring(draw, x, 980, i + 1, name, i == active, time_sec)

    tips = [
        "清水 + 洗涤剂先润湿纤维",
        "波轮/滚筒让衣物互相摩擦",
        "洗涤剂分子专撬油污",
        "排水后再用清水漂净",
        "高速旋转：离心力甩出水",
    ]
    if active >= 0:
        draw.rounded_rectangle((80, 1120, 1000, 1240), radius=14, fill=(255, 253, 248))
        draw.text((540, 1180), tips[active], font=FONT_M, fill=INK, anchor="mm")

    return img.convert("RGB")


def draw_analogy(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    img = _paper_bg(w, h, seed=59).convert("RGBA")
    draw = ImageDraw.Draw(img)
    draw.text((540, 95), "几个日常现象，一次说清", font=FONT_L, fill=INK, anchor="mm")

    cards = [
        (0.08, "为什么不能塞太满？", "转不动、摩擦不够，还伤电机"),
        (0.32, "洗涤剂为什么不能倒太多？", "泡沫过多难漂净，残留刺激皮肤"),
        (0.55, "甩干时为什么会「走路」？", "衣物偏心 → 离心力一边大一边小"),
    ]
    y0 = 260
    for idx, (start, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = y0 + idx * 300 + (1 - a) * 40
        draw.rounded_rectangle((90, y, 990, y + 260), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        draw.text((540, y + 40), title, font=FONT_M, fill=INK, anchor="mm")
        draw.text((540, y + 95), sub, font=FONT_S, fill=MUTED, anchor="mm")

        if idx == 0:
            # 过满 vs 合适
            _washer_body(draw, 300, y + 180, w=140, h=160, time_sec=time_sec, lid_open=0.3, swirl=0.2, water_level=0.7)
            for i in range(8):
                _cloth_piece(draw, 300 + (i - 4) * 8, y + 160, 0.2 * i, CLOTH, 0.45)
            draw.text((300, y + 240), "太满 ✗", font=FONT_XS, fill=HOT, anchor="mm")
            _washer_body(draw, 780, y + 180, w=140, h=160, time_sec=time_sec, lid_open=0.3, swirl=0.9, water_level=0.45)
            draw.text((780, y + 240), "留空 ✓", font=FONT_XS, fill=SOAP, anchor="mm")
        elif idx == 1:
            for i in range(14):
                _bubbles(draw, 540, y + 180, 120, time_sec + i * 0.1, count=1, alpha=0.9)
            draw.ellipse((480, y + 150, 600, y + 220), outline=SOAP, width=3)
            draw.text((540, y + 185), "泡沫墙", font=FONT_S, fill=SOAP, anchor="mm")
        else:
            # 偏心晃动
            _washer_body(
                draw,
                540 + math.sin(time_sec * 10) * 18,
                y + 175,
                w=160,
                h=180,
                time_sec=time_sec,
                swirl=0.1,
                spin=1.0,
                water_level=0.1,
                shake=1.0,
            )
            draw.text((540, y + 245), "偏心 → 机身乱晃", font=FONT_XS, fill=ACCENT, anchor="mm")

    if t > 0.78:
        draw.text((540, 1220), "力学 + 化学联手去污", font=FONT_L, fill=INK, anchor="mm")
        draw.text((540, 1290), "不是魔法，也不是单纯泡水", font=FONT_M, fill=ACCENT, anchor="mm")

    return img.convert("RGB")


def draw_outro(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    img = _paper_bg(w, h, seed=61).convert("RGBA")
    draw = ImageDraw.Draw(img)

    assemble = _spring(t, 0.0, 0.35)
    _washer_body(
        draw,
        540,
        int(480 + (1 - assemble) * 35),
        w=360,
        h=420,
        time_sec=time_sec,
        lid_open=0.35,
        swirl=0.85,
        water_level=0.5,
        show_motor=True,
    )

    if t > 0.2:
        card = _spring(t, 0.2, 0.28)
        draw.rounded_rectangle((90, 820, 990, 1040), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        draw.text((540, 870), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        draw.text((540, 940), "水流冲 · 衣物搓 · 洗涤剂撬污", font=FONT_L, fill=INK, anchor="mm")
        draw.text((540, 1000), "离心力甩干", font=FONT_L, fill=WATER, anchor="mm")

    if t > 0.5:
        badge = _spring(t, 0.5, 0.25)
        _ken_badge(draw, 1140, badge, scale=0.9 + 0.1 * badge)
        _fade_text(draw, (540, 1230), "关注身边原理 · 我是 Ken", FONT_L, INK, badge, dy=(1 - badge) * 22)
        _fade_text(draw, (540, 1300), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))

    if t > 0.75:
        blink = 0.6 + 0.4 * _pulse(time_sec, 2)
        draw.text(
            (540, 1480),
            "评论区：冰箱 / 吸尘器 / 抽油烟机？",
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
