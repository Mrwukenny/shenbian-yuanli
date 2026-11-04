"""路由器分集 · 纪录片手绘风 2D。外面的网从光猫进来，路由器看小包要去哪，再用无线电轮流送。"""

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
BOARD = (196, 168, 132)
SIGNAL = (36, 122, 96)


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


def _router(d, cx, cy, *, scale=1.0, ts=0.0, signal=0.9, wan=1.0, crowd=0.0, packet=0.0):
    """光猫、路由器和手机。满格只表示无线电近，不表示外网是通的。"""
    s = scale
    modem_box = (cx - 310 * s, cy - 8 * s, cx - 196 * s, cy + 80 * s)
    d.rounded_rectangle(modem_box, radius=8 * s, fill=WHITE, outline=INK, width=2)
    led = (80, 168, 96) if wan > 0.5 else ACCENT
    d.ellipse((cx - 292 * s, cy + 18 * s, cx - 274 * s, cy + 36 * s), fill=led, outline=INK, width=1)
    modem = ((modem_box[0] + modem_box[2]) / 2, modem_box[1] + 8 * s)
    if wan < 0.5:
        d.line((modem_box[0] + 12 * s, modem_box[1] + 16 * s, modem_box[2] - 12 * s, modem_box[3] - 12 * s), fill=ACCENT, width=3)
    d.line((cx - 196 * s, cy + 50 * s, cx - 124 * s, cy + 50 * s), fill=METAL_DK, width=max(2, int(4 * s)))
    d.rounded_rectangle((cx - 128 * s, cy - 4 * s, cx + 136 * s, cy + 90 * s), radius=14 * s, fill=BODY, outline=INK, width=3)
    d.line((cx - 78 * s, cy - 4 * s, cx - 104 * s, cy - 112 * s), fill=INK, width=max(3, int(5 * s)))
    d.line((cx + 86 * s, cy - 4 * s, cx + 116 * s, cy - 112 * s), fill=INK, width=max(3, int(5 * s)))
    ant = (cx + 116 * s, cy - 118 * s)
    d.ellipse((ant[0] - 8 * s, ant[1] - 8 * s, ant[0] + 8 * s, ant[1] + 8 * s), fill=METAL_DK)
    d.ellipse((cx - 112 * s, cy - 122 * s, cx - 96 * s, cy - 106 * s), fill=METAL_DK)
    blink = ACCENT if math.sin(ts * 6) > 0 else (80, 168, 96)
    d.ellipse((cx - 100 * s, cy + 28 * s, cx - 82 * s, cy + 46 * s), fill=blink)
    body = (cx + 20 * s, cy + 40 * s)
    phone_x = cx + 268 * s
    d.rounded_rectangle((phone_x - 32 * s, cy - 84 * s, phone_x + 32 * s, cy + 62 * s), radius=8 * s, fill=WHITE, outline=INK, width=2)
    bars = 1 if signal < 0.4 else (2 if signal < 0.75 else 3)
    for i in range(3):
        h = (14 + i * 12) * s
        col = SIGNAL if i < bars else LINE
        d.rectangle((phone_x - 20 * s + i * 14 * s, cy + 10 * s - h, phone_x - 10 * s + i * 14 * s, cy + 10 * s), fill=col)
    phone = (phone_x, cy - 84 * s)
    if signal > 0.15:
        for i in range(bars):
            r = (28 + i * 18) * s
            d.arc((ant[0] - r, ant[1] - r, ant[0] + r, ant[1] + r), 300, 50, fill=SIGNAL, width=2)
    if signal < 0.45:
        d.rectangle((cx + 160 * s, cy - 130 * s, cx + 188 * s, cy + 110 * s), fill=BOARD, outline=INK, width=2)
    if crowd > 0.5:
        for dx in (-48, 0, 48):
            px = phone_x + dx * s
            py = cy + 100 * s
            d.rounded_rectangle((px - 16 * s, py, px + 16 * s, py + 52 * s), radius=4 * s, fill=WHITE, outline=INK, width=2)
    if packet > 0.5:
        u = (ts * 0.45) % 1.0
        if u < 0.5:
            x = _lerp(phone_x, cx, u / 0.5)
            y = cy + 8 * s
        else:
            x = _lerp(cx, cx - 250 * s, (u - 0.5) / 0.5)
            y = cy + 42 * s
        d.ellipse((x - 7 * s, y - 7 * s, x + 7 * s, y + 7 * s), fill=ACCENT, outline=INK, width=1)
    if s >= 0.7 and wan < 0.5:
        d.text((cx - 252 * s, cy + 108 * s), "外网断了", font=FONT_XS, fill=ACCENT, anchor="mm")
    return {"modem": modem, "antenna": ant, "phone": phone, "body": body}


def _step_ring(d, x, y, num, name, active, ts):
    r = (34 if active else 26) * (_pulse(ts, 5, 0.92, 1.08) if active else 1)
    d.ellipse((x - r, y - r, x + r, y + r), fill=SIGNAL if active else WHITE, outline=SIGNAL, width=3)
    d.text((x, y), str(num), font=FONT_M, fill=WHITE if active else SIGNAL, anchor="mm")
    if active:
        d.text((x, y + r + 28), name, font=FONT_S, fill=SIGNAL, anchor="mm")


def draw_hook(t, w, h, time_sec=0.0):
    dx, _ = _cam_drift(time_sec)
    img = _paper_bg(w, h, 3601).convert("RGBA")
    d = ImageDraw.Draw(img)
    intro = _spring(t, 0, 0.3)
    if intro > 0:
        _ken_badge(d, 150, intro, 0.85 + 0.15 * intro)
        _fade_text(d, (540 + dx, 250), "我是 Ken", FONT_HERO, INK, intro, dy=(1 - intro) * 36)
        _fade_text(d, (540, 330), "挑战每天用 3 分钟", FONT_L, INK, _spring(t, 0.05, 0.28))
        _fade_text(d, (540, 400), "带你了解一个身边原理", FONT_M, MUTED, _spring(t, 0.1, 0.28))
        _fade_text(d, (540, 490), "今天：路由器怎样让手机上网", FONT_L, ACCENT, _spring(t, 0.16, 0.3))
    show = _ease(_scene_t(t, 0.28, 0.45))
    if show > 0:
        _router(d, 520 + dx, int(1040 + (1 - show) * 12), scale=0.72, ts=time_sec, signal=0.95, packet=0.8)
    if t > 0.5:
        right = _spring(t, 0.66, 0.28)
        if right < 0.35:
            d.rounded_rectangle((80, 1560, 1000, 1660), radius=12, fill=(255, 240, 235))
            d.text((540, 1610), "❌ 不是路由器在生产网", font=FONT_M, fill=ACCENT, anchor="mm")
        if right > 0:
            d.rounded_rectangle((70, 1520, 1010, 1720), radius=14, fill=(255, 245, 240))
            d.text((540, 1580), "✓  它是路口，负责转发", font=FONT_L, fill=SIGNAL, anchor="mm")
            d.text((540, 1660), "满格不等于外面的网是通的", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3603).convert("RGBA")
    d = ImageDraw.Draw(img)
    _fade_text(d, (540, 90), "拆开看：光猫、天线和手机", FONT_L, INK, _spring(t, 0, 0.2))
    show = _spring(t, 0.05, 0.28)
    if show > 0:
        parts = _router(d, 500, 980, scale=0.78, ts=time_sec, signal=0.95, packet=1)
        if t > 0.18:
            _callout(d, parts["modem"], (parts["modem"][0], parts["modem"][1] - 36), "光猫", INK, _spring(t, 0.18, 0.2), anchor="mm")
        if t > 0.36:
            _callout(d, parts["antenna"], (min(1020, parts["antenna"][0] + 16), parts["antenna"][1] - 16), "天线", SIGNAL, _spring(t, 0.36, 0.2))
        if t > 0.54:
            _callout(d, parts["body"], (parts["body"][0], parts["body"][1] + 70), "转发", ACCENT, _spring(t, 0.54, 0.2), anchor="mm")
        if t > 0.72:
            _callout(d, parts["phone"], (min(1040, parts["phone"][0] + 10), parts["phone"][1] - 28), "手机", INK, _spring(t, 0.72, 0.2))
    if t > 0.82:
        d.rounded_rectangle((70, 1560, 1010, 1760), radius=14, fill=(255, 253, 248))
        d.text((540, 1620), "无线电只负责家里这一段", font=FONT_M, fill=INK, anchor="mm")
        d.text((540, 1695), "同一个信道里，大家要轮流说话", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_cycle(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3607).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "一次上网，小包怎么走", font=FONT_L, fill=INK, anchor="mm")
    active = -1 if t < 0.06 else min(3, int((t - 0.06) / 0.2))
    _router(
        d,
        520,
        720,
        scale=0.7,
        ts=time_sec,
        signal=0.35 if active <= 0 else 0.95,
        wan=1,
        packet=1 if active >= 2 else 0,
    )
    steps = ["进门", "加入", "发包", "送回"]
    tips = [
        "① 外面的网从光猫送进来",
        "② 手机对上名字，加入这段对话",
        "③ 请求装进小包，用无线电发出",
        "④ 路由器转发，再把回包送回",
    ]
    for i, name in enumerate(steps):
        _step_ring(d, 160 + i * 250, 1220, i + 1, name, i == active, time_sec)
    if active >= 0:
        d.rounded_rectangle((60, 1380, 1020, 1500), radius=14, fill=(255, 253, 248))
        d.text((540, 1440), tips[active], font=FONT_M, fill=INK, anchor="mm")
    if t > 0.84:
        d.text((540, 1600), "满格只说明这一小段无线电很近", font=FONT_S, fill=MUTED, anchor="mm")
    return img.convert("RGB")


def draw_analogy(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3609).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((540, 86), "几个现象，一次说清", font=FONT_L, fill=INK, anchor="mm")
    cards = [
        (0.08, dict(signal=1, wan=0), "为什么满格却打不开网页？", "满格只说明离路由器很近"),
        (0.32, dict(signal=1, wan=1, crowd=1), "为什么人一多就变慢？", "同一条信道里要轮流说话"),
        (0.55, dict(signal=0.25, wan=1), "为什么隔墙格数会掉？", "墙会挡住和吸收无线电"),
    ]
    for idx, (start, kw, title, sub) in enumerate(cards):
        a = _spring(t, start, 0.25)
        if a <= 0:
            continue
        y = 160 + idx * 420 + (1 - a) * 30
        d.rounded_rectangle((70, y, 1010, y + 390), radius=16, fill=(255, 253, 248), outline=LINE, width=2)
        d.text((540, y + 36), title, font=FONT_M, fill=INK, anchor="mm")
        d.text((540, y + 84), sub, font=FONT_S, fill=MUTED, anchor="mm")
        _router(d, 540, y + 230, scale=0.32, ts=time_sec, **kw)
    if t > 0.82:
        d.text((540, 1480), "路由器转发小包，Wi-Fi 只是那段无线电", font=FONT_M, fill=INK, anchor="mm")
    return img.convert("RGB")


def draw_outro(t, w, h, time_sec=0.0):
    img = _paper_bg(w, h, 3611).convert("RGBA")
    d = ImageDraw.Draw(img)
    a = _spring(t, 0, 0.35)
    _router(d, 520, int(700 + (1 - a) * 12), scale=0.68, ts=time_sec, signal=0.95, packet=1)
    if t > 0.2:
        d.rounded_rectangle((70, 1180, 1010, 1400), radius=16, fill=(255, 253, 248), outline=ACCENT, width=2)
        d.text((540, 1240), "口诀记住", font=FONT_S, fill=MUTED, anchor="mm")
        d.text((540, 1305), "外面的网从光猫进来", font=FONT_L, fill=INK, anchor="mm")
        d.text((540, 1368), "无线电轮流把包送过去", font=FONT_L, fill=SIGNAL, anchor="mm")
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
