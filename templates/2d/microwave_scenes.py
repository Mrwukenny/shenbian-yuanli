"""微波炉分集 · 纪录片手绘风 2D，强调连续动画。"""

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
WAVE = (90, 120, 185)
WAVE_LT = (170, 195, 230)
HOT = (195, 90, 55)
HOT_LT = (240, 190, 150)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (72, 76, 82)
DOOR = (55, 58, 64)
FOOD = (230, 185, 120)
WATER = (120, 175, 210)
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


def _wave_arcs(draw, cx, cy, time_sec: float, count: int = 4, spread: float = 90, alpha: float = 1.0):
    for i in range(count):
        r = 28 + i * 28 + (time_sec * 55) % 28
        a = int(140 * alpha * (1 - i / count))
        bbox = (cx - r, cy - r, cx + r, cy + r)
        draw.arc(bbox, -spread / 2, spread / 2, fill=(*WAVE, a), width=3)


def _wave_particles(draw, x0, y0, x1, y1, time_sec: float, count: int = 10):
    for i in range(count):
        u = (time_sec * 0.55 + i / count) % 1.0
        x = _lerp(x0, x1, u)
        y = _lerp(y0, y1, u) + math.sin(u * math.pi * 4 + time_sec * 6) * 12
        r = 5 + 2 * math.sin(time_sec * 8 + i)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=WAVE if i % 2 == 0 else WAVE_LT)


def _bounce_waves(draw, left, top, right, bottom, time_sec: float, count: int = 12):
    """腔体内反弹的微波粒子。"""
    for i in range(count):
        seed = i * 17.3
        sx = 0.3 + 0.4 * math.sin(seed)
        sy = 0.25 + 0.5 * math.cos(seed * 1.3)
        vx = 0.35 + 0.25 * math.sin(seed * 2)
        vy = 0.28 + 0.2 * math.cos(seed * 1.7)
        tx = (sx + time_sec * vx) % 2
        ty = (sy + time_sec * vy) % 2
        # 三角波实现反弹
        ux = tx if tx < 1 else 2 - tx
        uy = ty if ty < 1 else 2 - ty
        x = _lerp(left, right, ux)
        y = _lerp(top, bottom, uy)
        r = 6
        draw.ellipse((x - r, y - r, x + r, y + r), fill=WAVE_LT if i % 2 else WAVE)
        # 短波纹
        _sketch_line(draw, (x - 10, y), (x + 10, y + math.sin(time_sec * 10 + i) * 4), WAVE, 2, i)


def _water_molecule(draw, cx, cy, ang: float, scale: float = 1.0):
    """简化水分子：中心 O + 两个 H。"""
    o_r = 10 * scale
    h_r = 6 * scale
    draw.ellipse((cx - o_r, cy - o_r, cx + o_r, cy + o_r), fill=(220, 90, 80), outline=INK, width=1)
    for da in (-0.9, 0.9):
        a = ang + da
        hx = cx + math.cos(a) * 18 * scale
        hy = cy + math.sin(a) * 18 * scale
        _sketch_line(draw, (cx, cy), (hx, hy), INK, 2, int(a * 10))
        draw.ellipse((hx - h_r, hy - h_r, hx + h_r, hy + h_r), fill=WATER, outline=INK, width=1)


def _food_bowl(draw, cx, cy, steam: float = 0.0, time_sec: float = 0.0):
    draw.ellipse((cx - 55, cy - 18, cx + 55, cy + 28), fill=FOOD, outline=INK, width=2)
    draw.ellipse((cx - 48, cy - 28, cx + 48, cy - 8), fill=WATER, outline=INK, width=1)
    if steam > 0:
        for i in range(5):
            phase = time_sec * 2.5 + i * 0.8
            px = cx - 30 + i * 15 + math.sin(phase) * 6
            py = cy - 30 - ((phase * 0.4) % 1.0) * 50 * steam
            draw.ellipse((px - 4, py - 8, px + 4, py + 8), fill=(*MUTED, int(120 * steam)))


def _microwave_body(
    draw,
    cx,
    cy,
    *,
    w: float = 420,
    h: float = 280,
    open_door: float = 0.0,
    time_sec: float = 0.0,
    show_waves: bool = False,
    show_magnetron: bool = False,
    plate_spin: float = 0.0,
    cutaway: bool = False,
):
    x0, y0 = cx - w / 2, cy - h / 2
    # 机身阴影
    draw.rounded_rectangle((x0 + 5, y0 + 8, x0 + w + 5, y0 + h + 8), radius=16, fill=(200, 196, 190))
    draw.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=16, fill=BODY, outline=INK, width=2)
    # 控制面板
    panel_x = x0 + w - 70
    draw.rounded_rectangle((panel_x, y0 + 20, x0 + w - 16, y0 + h - 20), radius=8, fill=METAL_DK)
    for i in range(3):
        by = y0 + 50 + i * 36
        draw.ellipse((panel_x + 18, by, panel_x + 38, by + 20), fill=GREEN if i == 0 else METAL)
    # 腔体
    cavity = (x0 + 28, y0 + 28, panel_x - 18, y0 + h - 28)
    draw.rounded_rectangle(cavity, radius=8, fill=(40, 42, 48), outline=METAL, width=2)
    # 转盘
    pcx = (cavity[0] + cavity[2]) / 2
    pcy = cavity[3] - 42
    draw.ellipse((pcx - 70, pcy - 18, pcx + 70, pcy + 18), fill=METAL, outline=METAL_DK, width=1)
    ang = plate_spin
    for k in range(3):
        a = ang + k * 2.094
        draw.line((pcx, pcy, pcx + math.cos(a) * 55, pcy + math.sin(a) * 12), fill=METAL_DK, width=2)
    _food_bowl(draw, pcx, pcy - 8, steam=0.5 if show_waves else 0.0, time_sec=time_sec)

    if show_waves:
        _bounce_waves(draw, cavity[0] + 20, cavity[1] + 20, cavity[2] - 20, cavity[3] - 50, time_sec, count=14)

    if show_magnetron:
        mx, my = x0 - 20, y0 + 40
        draw.rounded_rectangle((mx - 50, my, mx + 10, my + 90), radius=8, fill=METAL_DK, outline=INK, width=2)
        draw.ellipse((mx - 20, my + 30, mx + 10, my + 60), fill=ACCENT)
        _wave_particles(draw, mx + 10, my + 45, cavity[0] + 10, (cavity[1] + cavity[3]) / 2, time_sec, count=8)
        _callout(draw, (mx - 20, my + 20), (mx - 160, my - 20), "磁控管", ACCENT)

    # 门（可半开）
    door_w = (cavity[2] - cavity[0]) * (1 - 0.55 * open_door)
    door_box = (cavity[0], cavity[1], cavity[0] + door_w, cavity[3])
    if open_door < 0.95:
        draw.rounded_rectangle(door_box, radius=6, fill=DOOR, outline=INK, width=2)
        # 金属网
        step = 14
        for i in range(int((door_box[2] - door_box[0]) / step)):
            for j in range(int((door_box[3] - door_box[1]) / step)):
                px = door_box[0] + 10 + i * step
                py = door_box[1] + 12 + j * step
                if px < door_box[2] - 8 and py < door_box[3] - 8:
                    draw.rectangle((px, py, px + 6, py + 6), outline=METAL, width=1)

    if cutaway:
        # 剖开示意：右侧露出波导
        draw.polygon(
            [
                (panel_x - 40, y0 + 40),
                (panel_x - 10, y0 + 40),
                (panel_x - 10, y0 + h - 40),
                (panel_x - 40, y0 + h - 60),
            ],
            fill=WAVE_LT,
            outline=WAVE,
        )


def _oven_compare(draw, cx, cy, label: str, heat_outside: bool, time_sec: float):
    draw.rounded_rectangle((cx - 90, cy - 70, cx + 90, cy + 70), radius=10, fill=WHITE, outline=INK, width=2)
    draw.text((cx, cy - 90), label, font=FONT_S, fill=MUTED, anchor="mm")
    # 食物块
    draw.rounded_rectangle((cx - 35, cy - 25, cx + 35, cy + 35), radius=6, fill=FOOD, outline=INK, width=1)
    if heat_outside:
        for i in range(6):
            a = time_sec * 2 + i * 1.05
            x = cx + math.cos(a) * 55
            y = cy + math.sin(a) * 40
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=HOT)
        draw.text((cx, cy + 55), "从外往里烤", font=FONT_XS, fill=HOT, anchor="mm")
    else:
        for i in range(5):
            ox = cx - 20 + i * 10
            oy = cy + math.sin(time_sec * 8 + i) * 4
            _water_molecule(draw, ox, oy, time_sec * 10 + i, scale=0.55)
        draw.text((cx, cy + 55), "水分子自己晃", font=FONT_XS, fill=WAVE, anchor="mm")


def _spark(draw, x, y, time_sec: float, strength: float = 1.0):
    if strength <= 0:
        return
    for i in range(6):
        a = time_sec * 14 + i * 1.05
        L = 12 + 10 * _pulse(time_sec + i, 8, 0.5, 1.0) * strength
        _sketch_line(draw, (x, y), (x + math.cos(a) * L, y + math.sin(a) * L), HOT, 2, i)


def _step_ring(draw, x, y, num: int, name: str, active: bool, time_sec: float):
    base_r = 36 if active else 26
    r = base_r * (_pulse(time_sec, 5, 0.92, 1.08) if active else 1.0)
    col = WAVE if active else MUTED
    if active:
        glow = r + 8 + 3 * math.sin(time_sec * 6)
        draw.ellipse((x - glow, y - glow, x + glow, y + glow), outline=(*WAVE, 70), width=3)
    draw.ellipse((x - r, y - r, x + r, y + r), fill=WAVE if active else WHITE, outline=WAVE, width=3)
    draw.text((x, y), str(num), font=FONT_M, fill=WHITE if active else WAVE, anchor="mm")
    if active:
        bounce = math.sin(time_sec * 4) * 3
        draw.text((x, y + r + 26 + bounce), name, font=FONT_S, fill=col, anchor="mm")


# ── 分镜 ──


def draw_hook(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    dx, dy = _cam_drift(time_sec)
    img = _paper_bg(w, h, seed=31).convert("RGBA")
    draw = ImageDraw.Draw(img)

    intro = _spring(t, 0.0, 0.3)
    if intro > 0:
        _ken_badge(draw, 170, intro, scale=0.85 + 0.15 * intro)
        slide = (1 - intro) * 36
        _fade_text(draw, (540 + dx, 300), "我是 Ken", FONT_HERO, INK, intro, dy=slide)
        _fade_text(draw, (540, 390), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28), dy=(1 - _spring(t, 0.05, 0.28)) * 28)
        _fade_text(draw, (540, 460), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(draw, (540, 550), "今天：微波炉怎么加热食物", FONT_L, ACCENT, _spring(t, 0.16, 0.3))

    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        y = 820 + (1 - show) * 60
        _microwave_body(
            draw,
            540 + dx,
            int(y),
            open_door=0.35,
            time_sec=time_sec,
            show_waves=t > 0.55,
            plate_spin=time_sec * 1.2,
        )

    if t > 0.48:
        wrong = _ease(_scene_t(t, 0.48, 0.62))
        right = _spring(t, 0.64, 0.28)
        if wrong > 0 and right < 0.35:
            shake = math.sin(time_sec * 12) * 3 * wrong
            draw.rounded_rectangle((150 + shake, 1180, 930 + shake, 1280), radius=12, fill=(255, 240, 235))
            draw.text((540, 1230), "❌ 不是小烤箱在烤空气", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            draw.rounded_rectangle((120, 1160, 960, 1320), radius=14, fill=(235, 242, 252))
            draw.text((540, 1210), "✓  让水分子自己「跳舞」发热", font=FONT_L, fill=WAVE, anchor="mm")
            for i in range(4):
                _water_molecule(
                    draw,
                    300 + i * 120,
                    1420,
                    time_sec * 9 + i * 1.2,
                    scale=0.9 + 0.1 * math.sin(time_sec * 6 + i),
                )

    return img.convert("RGB")


def draw_cutaway(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    dx, _ = _cam_drift(time_sec, 4, 2)
    img = _paper_bg(w, h, seed=33).convert("RGBA")
    draw = ImageDraw.Draw(img)
    title = _spring(t, 0.0, 0.2)
    _fade_text(draw, (540, 95), "拆开看：微波从哪来、去哪", FONT_L, INK, title, dy=(1 - title) * 18)

    show_body = _spring(t, 0.05, 0.28)
    show_mag = _spring(t, 0.22, 0.25)
    show_cavity = _spring(t, 0.4, 0.25)
    show_door = _spring(t, 0.58, 0.28)

    if show_body > 0:
        _microwave_body(
            draw,
            540 + dx,
            int(520 + (1 - show_body) * -40),
            w=460,
            h=300,
            open_door=0.15 + 0.5 * show_door,
            time_sec=time_sec,
            show_waves=show_cavity > 0.4,
            show_magnetron=show_mag > 0.3,
            plate_spin=time_sec * 1.5,
            cutaway=show_mag > 0.5,
        )

    if show_mag > 0.4:
        _callout(draw, (280, 480), (80, 380), "波导管送波", WAVE, show_mag)

    if show_cavity > 0.4:
        _callout(draw, (540, 620), (760, 700), "金属壁反弹", METAL_DK, show_cavity)
        _callout(draw, (540, 660), (760, 780), "转盘匀热", MUTED, show_cavity)

    if show_door > 0.3:
        draw.rounded_rectangle((140, 980, 940, 1180), radius=14, fill=(255, 253, 248))
        draw.text((540, 1030), "门上的金属网", font=FONT_M, fill=INK, anchor="mm")
        draw.text((540, 1095), "网眼比波长小 → 微波出不去，光能进来", font=FONT_S, fill=MUTED, anchor="mm")
        # 网示意
        for i in range(8):
            for j in range(3):
                px = 360 + i * 28
                py = 1135 + j * 14
                draw.rectangle((px, py, px + 10, py + 8), outline=METAL_DK, width=1)

    return img.convert("RGB")


def draw_cycle(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    img = _paper_bg(w, h, seed=37).convert("RGBA")
    draw = ImageDraw.Draw(img)
    draw.text((540, 90), "水分子怎么被加热？", font=FONT_L, fill=INK, anchor="mm")

    # 左侧微波炉小图
    _microwave_body(
        draw,
        270,
        420,
        w=280,
        h=190,
        open_door=0.6,
        time_sec=time_sec,
        show_waves=True,
        plate_spin=time_sec * 2,
    )

    # 右侧放大水分子
    draw.rounded_rectangle((520, 260, 980, 620), radius=16, fill=WHITE, outline=LINE, width=2)
    draw.text((750, 295), "极性水分子跟着电场翻转", font=FONT_S, fill=MUTED, anchor="mm")
    for i in range(3):
        for j in range(2):
            cx = 600 + i * 110
            cy = 400 + j * 110
            ang = time_sec * 12 + i + j * 2
            _water_molecule(draw, cx, cy, ang, scale=1.1)
            # 电场箭头示意
            ay = cy - 40 + math.sin(time_sec * 10) * 8
            _sketch_line(draw, (cx - 30, ay), (cx + 30, ay), WAVE, 2, i + j)

    steps = ["产波", "入腔", "翻转", "升温"]
    pos = [(180, 760), (400, 760), (640, 760), (880, 760)]
    active = -1 if t < 0.08 else min(3, int((t - 0.08) / 0.18))
    for i, (name, (x, y)) in enumerate(zip(steps, pos)):
        _step_ring(draw, x, y, i + 1, name, i == active, time_sec)

    tips = [
        "① 磁控管发出约 2.45GHz 微波",
        "② 波导管把波送进腔体来回反弹",
        "③ 水分子随电场每秒翻转数十亿次",
        "④ 分子摩擦碰撞 → 宏观温度上升",
    ]
    if active >= 0:
        draw.rounded_rectangle((80, 980, 1000, 1100), radius=14, fill=(255, 253, 248))
        draw.text((540, 1040), tips[active], font=FONT_M, fill=INK, anchor="mm")

    if t > 0.7:
        alpha = _ease(_scene_t(t, 0.7, 0.88))
        draw.text((540, 1220), "含水量越高，通常热得越快", font=FONT_S, fill=(*MUTED, int(255 * alpha)), anchor="mm")
        draw.text((540, 1280), "穿透几厘米：内外一起晃，不是只烤表面", font=FONT_S, fill=(*WAVE, int(255 * alpha)), anchor="mm")

    # 频率数字脉冲
    if t > 0.15:
        freq_pulse = _pulse(time_sec, 3, 0.9, 1.0)
        draw.text((540, 1450), f"≈ 24.5 亿次 / 秒 × {freq_pulse:.2f}", font=FONT_XS, fill=ACCENT, anchor="mm")

    return img.convert("RGB")


def draw_analogy(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    img = _paper_bg(w, h, seed=41).convert("RGBA")
    draw = ImageDraw.Draw(img)
    draw.text((540, 95), "几个常见现象，一次说清", font=FONT_L, fill=INK, anchor="mm")

    # 三卡片依次出现
    cards = [
        (0.08, "金属为什么危险？", "反射微波，还可能打火"),
        (0.32, "冰块为什么热得慢？", "水分子被冻住，不好跟着翻"),
        (0.55, "为什么有时热得不均？", "水分分布 + 驻波叠加"),
    ]
    y0 = 280
    for idx, (start, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = y0 + idx * 280 + (1 - a) * 40
        draw.rounded_rectangle((100, y, 980, y + 230), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        draw.text((540, y + 40), title, font=FONT_M, fill=INK, anchor="mm")
        draw.text((540, y + 95), sub, font=FONT_S, fill=MUTED, anchor="mm")

        if idx == 0:
            # 叉子 + 火花
            fx, fy = 300, y + 160
            _sketch_line(draw, (fx, fy - 30), (fx, fy + 40), METAL_DK, 4, 1)
            for prong in (-12, 0, 12):
                _sketch_line(draw, (fx + prong, fy - 30), (fx + prong, fy - 55), METAL_DK, 3, 2)
            _spark(draw, fx, fy - 60, time_sec, a)
            draw.text((700, y + 160), "别放金属！", font=FONT_S, fill=HOT, anchor="mm")
        elif idx == 1:
            # 冰块 vs 液态水
            draw.rounded_rectangle((260, y + 130, 360, y + 200), radius=6, fill=(200, 225, 245), outline=WAVE, width=2)
            draw.text((310, y + 165), "冰", font=FONT_S, fill=WAVE, anchor="mm")
            for i in range(3):
                _water_molecule(draw, 620 + i * 70, y + 165, 0.2 * i, scale=0.7)
            draw.text((760, y + 200), "液态水更活", font=FONT_XS, fill=MUTED, anchor="mm")
        else:
            # 不均匀加热示意
            for i in range(5):
                hotness = 0.3 + 0.7 * abs(math.sin(i * 0.9 + time_sec))
                col = (
                    int(_lerp(FOOD[0], HOT[0], hotness)),
                    int(_lerp(FOOD[1], HOT[1], hotness)),
                    int(_lerp(FOOD[2], HOT[2], hotness)),
                )
                x = 280 + i * 100
                draw.ellipse((x - 28, y + 145, x + 28, y + 195), fill=col, outline=INK, width=1)

    if t > 0.78:
        draw.text((540, 1200), "加热的是能跟着电场晃的分子", font=FONT_M, fill=INK, anchor="mm")
        draw.text((540, 1270), "不是均匀地「烤空气」", font=FONT_L, fill=ACCENT, anchor="mm")

    return img.convert("RGB")


def draw_outro(t: float, w: int, h: int, time_sec: float = 0.0) -> Image.Image:
    img = _paper_bg(w, h, seed=43).convert("RGBA")
    draw = ImageDraw.Draw(img)

    assemble = _spring(t, 0.0, 0.35)
    _microwave_body(
        draw,
        540,
        int(480 + (1 - assemble) * 40),
        w=440,
        h=290,
        open_door=0.25,
        time_sec=time_sec,
        show_waves=True,
        show_magnetron=True,
        plate_spin=time_sec * 1.4,
    )

    if t > 0.2:
        card = _spring(t, 0.2, 0.28)
        draw.rounded_rectangle((100, 780, 980, 1000), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        draw.text((540, 830), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        draw.text((540, 900), "磁控管产波 · 腔体反弹", font=FONT_L, fill=INK, anchor="mm")
        draw.text((540, 960), "水分子跳舞 · 食物就热了", font=FONT_L, fill=WAVE, anchor="mm")

    if t > 0.5:
        badge = _spring(t, 0.5, 0.25)
        _ken_badge(draw, 1120, badge, scale=0.9 + 0.1 * badge)
        _fade_text(draw, (540, 1210), "关注身边原理 · 我是 Ken", FONT_L, INK, badge, dy=(1 - badge) * 22)
        _fade_text(draw, (540, 1280), "明天继续 3 分钟了解下一个原理", FONT_M, ACCENT, _spring(t, 0.56, 0.25))

    if t > 0.75:
        blink = 0.6 + 0.4 * _pulse(time_sec, 2)
        draw.text(
            (540, 1450),
            "评论区：冰箱 / 电磁炉 / 空气炸锅？",
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
