"""2D 画面的共用笔触：更粗的轮廓、简单材质明暗、坐姿人物。

渲染器在启动时调用 install()，之后各分集里的
ImageDraw.rounded_rectangle / ellipse / line / arc 会自动变厚、带阴影。
不改 episode.yaml，也不依赖 Blender。
"""

from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

_installed = False
_OrigDraw = ImageDraw.Draw


def _rgb(color) -> tuple[int, int, int] | None:
    if color is None:
        return None
    if isinstance(color, int):
        return (color, color, color)
    if isinstance(color, str):
        return None
    if len(color) >= 3:
        return (int(color[0]), int(color[1]), int(color[2]))
    return None


def _alpha(color, default: int = 255) -> int:
    if isinstance(color, tuple) and len(color) >= 4:
        return int(color[3])
    return default


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def lighten(color, t: float = 0.18) -> tuple[int, int, int]:
    rgb = _rgb(color) or (255, 255, 255)
    return _mix(rgb, (255, 255, 255), t)


def darken(color, t: float = 0.22) -> tuple[int, int, int]:
    rgb = _rgb(color) or (40, 36, 32)
    return _mix(rgb, (28, 26, 24), t)


def _box(xy) -> tuple[float, float, float, float]:
    if len(xy) == 2 and not isinstance(xy[0], (int, float)):
        (x0, y0), (x1, y1) = xy
    else:
        x0, y0, x1, y1 = xy
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    return float(x0), float(y0), float(x1), float(y1)


def _paint(image_mode: str, rgb: tuple[int, int, int], alpha: int):
    if image_mode == "RGBA":
        return (*rgb, alpha)
    return rgb


class PremiumDraw(ImageDraw.ImageDraw):
    """在原有 ImageDraw 上加轮廓和材质。_style_plain 时退回原始笔触。"""

    def _plain(self) -> bool:
        return bool(getattr(self, "_style_plain", False))

    def line(self, xy, fill=None, width=0, joint=None):
        if not self._plain():
            w = int(width or 0)
            if 0 < w < 3:
                width = w + 1
        if joint is None:
            return super().line(xy, fill=fill, width=width)
        return super().line(xy, fill=fill, width=width, joint=joint)

    def arc(self, xy, start, end, fill=None, width=1, *args, **kwargs):
        if not self._plain():
            w = int(width or 0)
            if 0 < w < 3:
                width = w + 1
        return super().arc(xy, start, end, fill=fill, width=width, *args, **kwargs)

    def rounded_rectangle(self, xy, radius=0, fill=None, outline=None, width=1, corners=None):
        if self._plain() or outline is None or _rgb(fill) is None:
            ow = width
            if not self._plain() and outline is not None:
                x0, y0, x1, y1 = _box(xy)
                if min(x1 - x0, y1 - y0) >= 18:
                    ow = max(int(width or 1), 3)
            return super().rounded_rectangle(
                xy, radius=radius, fill=fill, outline=outline, width=ow, corners=corners
            )
        x0, y0, x1, y1 = _box(xy)
        w, h = x1 - x0, y1 - y0
        if w < 56 or h < 44:
            ow = max(int(width or 1), 3)
            return super().rounded_rectangle(
                xy, radius=radius, fill=fill, outline=outline, width=ow, corners=corners
            )
        rgb = _rgb(fill)
        assert rgb is not None
        base_a = _alpha(fill)
        mode = self.im.mode if hasattr(self, "im") else "RGBA"
        lum = (rgb[0] * 3 + rgb[1] * 6 + rgb[2]) / 10
        # 浅色塑料要更重的暗部，否则白底上看不出体积
        shade_t = 0.34 if lum > 185 else 0.2
        super().rounded_rectangle(
            (x0 + 8, y0 + 12, x1 + 8, y1 + 12),
            radius=radius,
            fill=_paint(mode, (42, 36, 32), min(150, base_a)),
        )
        super().rounded_rectangle(xy, radius=radius, fill=_paint(mode, darken(rgb, shade_t), base_a))
        super().rounded_rectangle(
            (x0 + 4, y0 + 3, x1 - 9, y0 + h * 0.64),
            radius=max(4, radius * 0.75),
            fill=_paint(mode, lighten(rgb, 0.06 if lum > 210 else 0.16), base_a),
        )
        super().rounded_rectangle(
            (x0 + w * 0.12, y0 + 6, x0 + w * 0.62, y0 + max(12, h * 0.18)),
            radius=max(4, h * 0.08),
            fill=_paint(mode, (255, 255, 255), min(base_a, 230)),
        )
        stroke = _rgb(outline) or darken(rgb, 0.55)
        super().rounded_rectangle(
            xy,
            radius=radius,
            outline=_paint(mode, stroke, min(255, base_a)),
            width=max(int(width or 1), 5),
        )
        return None

    def ellipse(self, xy, fill=None, outline=None, width=1):
        if self._plain() or outline is None or _rgb(fill) is None:
            ow = width
            if not self._plain() and outline is not None:
                x0, y0, x1, y1 = _box(xy)
                if min(x1 - x0, y1 - y0) >= 16:
                    ow = max(int(width or 1), 3)
            return super().ellipse(xy, fill=fill, outline=outline, width=ow)
        x0, y0, x1, y1 = _box(xy)
        w, h = x1 - x0, y1 - y0
        if min(w, h) < 46 or max(w, h) / max(min(w, h), 1) > 2.4:
            return super().ellipse(xy, fill=fill, outline=outline, width=max(int(width or 1), 3))
        rgb = _rgb(fill)
        assert rgb is not None
        base_a = _alpha(fill)
        mode = self.im.mode if hasattr(self, "im") else "RGBA"
        lum = (rgb[0] * 3 + rgb[1] * 6 + rgb[2]) / 10
        shade_t = 0.32 if lum > 185 else 0.22
        super().ellipse((x0 + 6, y0 + 8, x1 + 6, y1 + 8), fill=_paint(mode, (42, 36, 32), min(140, base_a)))
        super().ellipse(xy, fill=_paint(mode, darken(rgb, shade_t), base_a))
        super().ellipse(
            (x0 + w * 0.08, y0 + h * 0.04, x1 - w * 0.14, y1 - h * 0.28),
            fill=_paint(mode, lighten(rgb, 0.12 if lum > 210 else 0.22), base_a),
        )
        super().ellipse(
            (x0 + w * 0.2, y0 + h * 0.1, x0 + w * 0.42, y0 + h * 0.28),
            fill=_paint(mode, (255, 255, 255), min(base_a, 210)),
        )
        stroke = _rgb(outline) or darken(rgb, 0.55)
        super().ellipse(xy, outline=_paint(mode, stroke, min(255, base_a)), width=max(int(width or 1), 5))
        return None


def install() -> None:
    """让之后的 ImageDraw.Draw 返回带材质的画笔。可重复调用。"""
    global _installed
    if _installed:
        return

    def _draw(im, mode=None):
        pen = _OrigDraw(im, mode)
        if not isinstance(pen, PremiumDraw):
            pen.__class__ = PremiumDraw
        return pen

    ImageDraw.Draw = _draw
    _installed = True


def _bands(draw: ImageDraw.ImageDraw, box, c0, c1, steps: int = 12) -> None:
    x0, y0, x1, y1 = box
    span = max(y1 - y0, 1)
    for i in range(steps):
        t = i / max(steps - 1, 1)
        ya = y0 + span * i / steps
        yb = y0 + span * (i + 1) / steps + 1
        draw.rectangle((x0, ya, x1, yb), fill=_mix(c0, c1, t))


def paper_background(
    w: int,
    h: int,
    seed: int = 7,
    paper: tuple[int, int, int] = (248, 245, 238),
    wall: tuple[int, int, int] = (242, 238, 230),
    floor: tuple[int, int, int] = (218, 214, 206),
    line: tuple[int, int, int] = (150, 142, 132),
) -> Image.Image:
    """竖向微渐变的墙和地面，加踢脚线和左侧受光。比两块纯色更有房间体积。"""
    img = Image.new("RGB", (w, h), paper)
    # 背景在安装画笔之前也可能被调用；这里用原始 Draw，避免地面色块被当成电器。
    draw = _OrigDraw(img)
    horizon = int(h * 0.62)
    _bands(draw, (0, 0, w, horizon), lighten(wall, 0.07), darken(wall, 0.05), 10)
    _bands(draw, (0, horizon, w, h), lighten(floor, 0.04), darken(floor, 0.12), 8)
    # 左侧受光墙
    draw.polygon(
        [(0, 0), (int(w * 0.3), 0), (int(w * 0.2), horizon), (0, horizon)],
        fill=lighten(wall, 0.12),
    )
    draw.rectangle((0, horizon - 10, w, horizon + 6), fill=darken(floor, 0.18))
    draw.line((0, horizon, w, horizon), fill=darken(line, 0.15), width=4)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(int(w * h * 0.004)):
        x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
        r, g, b = px[x, y]
        n = rng.randint(-6, 4)
        px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    return img


def _capsule(draw: ImageDraw.ImageDraw, a, b, fill, ink, radius: float = 15) -> None:
    """一段有体积的肢体：外圈墨线，内芯肤色或衣色，两端圆头。"""
    outer = int(radius * 2 + 8)
    inner = int(radius * 2)
    draw.line([a, b], fill=ink, width=outer, joint="curve")
    draw.line([a, b], fill=fill, width=inner, joint="curve")
    for px, py in (a, b):
        draw.ellipse((px - radius - 4, py - radius - 4, px + radius + 4, py + radius + 4), fill=ink)
        draw.ellipse((px - radius + 1, py - radius + 1, px + radius - 1, py + radius - 1), fill=fill)


def draw_seated_host(
    draw: ImageDraw.ImageDraw,
    cx: float,
    seat_y: float,
    time_sec: float = 0.0,
    *,
    skin: tuple[int, int, int] = (232, 196, 166),
    shirt: tuple[int, int, int] = (72, 96, 128),
    ink: tuple[int, int, int] = (38, 36, 34),
    hair: tuple[int, int, int] = (58, 44, 36),
) -> None:
    """坐姿讲解人：头身有脖子和肩膀，四肢是粗轮廓，脸上有五官。

    seat_y 是坐垫上沿。画的时候关掉自动材质，避免头变成高光气球。
    """
    bob = math.sin(time_sec * 2.1) * 2.2
    seat_y = seat_y + bob
    hx = cx - 28
    was_plain = bool(getattr(draw, "_style_plain", False))
    draw._style_plain = True
    try:
        shoulder_y = seat_y - 124
        hip_y = seat_y + 8
        pants = darken(shirt, 0.18)
        # 大腿
        _capsule(draw, (hx - 8, hip_y), (hx + 54, hip_y + 16), pants, ink, radius=16)
        _capsule(draw, (hx + 20, hip_y + 6), (hx + 78, hip_y + 36), pants, ink, radius=14)
        # 躯干
        torso = [
            (hx - 52, shoulder_y + 10),
            (hx + 50, shoulder_y + 4),
            (hx + 40, hip_y),
            (hx - 42, hip_y + 6),
        ]
        draw.polygon(torso, fill=darken(shirt, 0.2))
        draw.line(torso + [torso[0]], fill=ink, width=6, joint="curve")
        draw.polygon(
            [
                (hx - 36, shoulder_y + 18),
                (hx + 24, shoulder_y + 14),
                (hx + 16, hip_y - 16),
                (hx - 28, hip_y - 8),
            ],
            fill=lighten(shirt, 0.2),
        )
        draw.polygon(
            [(hx - 14, shoulder_y + 12), (hx + 16, shoulder_y + 8), (hx + 2, shoulder_y + 36)],
            fill=darken(shirt, 0.35),
        )
        # 肩膀圆头，让手臂从身体里长出来
        draw.ellipse((hx - 62, shoulder_y - 4, hx - 28, shoulder_y + 32), fill=shirt, outline=ink, width=5)
        draw.ellipse((hx + 26, shoulder_y - 6, hx + 62, shoulder_y + 30), fill=shirt, outline=ink, width=5)
        ang = math.sin(time_sec * 7.5) * 0.5
        _capsule(draw, (hx - 46, shoulder_y + 16), (hx - 78, shoulder_y + 62), skin, ink, radius=13)
        _capsule(draw, (hx - 78, shoulder_y + 62), (hx - 36, hip_y + 10), skin, ink, radius=12)
        elbow = (hx + 78, shoulder_y + 48)
        hand = (hx + 108 + math.cos(ang) * 16, shoulder_y + 24 + math.sin(ang) * 22)
        _capsule(draw, (hx + 46, shoulder_y + 14), elbow, skin, ink, radius=13)
        _capsule(draw, elbow, hand, skin, ink, radius=12)
        draw.ellipse((hand[0] - 12, hand[1] - 10, hand[0] + 12, hand[1] + 14), fill=skin, outline=ink, width=4)
        # 脖子和头
        draw.rounded_rectangle(
            (hx - 14, shoulder_y - 22, hx + 14, shoulder_y + 18),
            radius=8,
            fill=darken(skin, 0.08),
            outline=ink,
            width=4,
        )
        head = (hx + 2, shoulder_y - 72)
        draw.ellipse((head[0] - 46, head[1] - 58, head[0] + 42, head[1] + 6), fill=hair, outline=ink, width=5)
        draw.ellipse((head[0] - 38, head[1] - 36, head[0] + 38, head[1] + 44), fill=lighten(skin, 0.06), outline=ink, width=5)
        draw.ellipse((head[0] - 40, head[1] + 8, head[0] - 16, head[1] + 36), fill=darken(skin, 0.1), outline=ink, width=4)
        draw.ellipse((head[0] + 28, head[1] + 6, head[0] + 46, head[1] + 34), fill=darken(skin, 0.1), outline=ink, width=4)
        draw.pieslice((head[0] - 38, head[1] - 48, head[0] + 38, head[1] + 8), 200, 340, fill=hair, outline=ink, width=4)
        # 下颌阴影
        draw.arc((head[0] - 28, head[1] + 8, head[0] + 28, head[1] + 40), 20, 160, fill=darken(skin, 0.18), width=6)
        eye_y = head[1] - 2
        for ex, brow in ((head[0] - 16, head[0] - 24), (head[0] + 12, head[0] + 6)):
            draw.line([(brow, eye_y - 16), (brow + 16, eye_y - 18)], fill=ink, width=4)
            draw.ellipse((ex - 8, eye_y - 6, ex + 8, eye_y + 8), fill=(252, 250, 246), outline=ink, width=3)
            draw.ellipse((ex - 3, eye_y - 1, ex + 4, eye_y + 6), fill=ink)
            draw.ellipse((ex, eye_y, ex + 2, eye_y + 2), fill=(255, 255, 255))
        draw.polygon(
            [(head[0] - 2, head[1] + 6), (head[0] + 6, head[1] + 6), (head[0] + 2, head[1] + 16)],
            fill=darken(skin, 0.22),
        )
        draw.arc((head[0] - 16, head[1] + 16, head[0] + 18, head[1] + 36), 15, 165, fill=ink, width=4)
    finally:
        draw._style_plain = was_plain


install()
