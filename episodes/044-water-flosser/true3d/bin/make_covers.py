#!/usr/bin/env python3
"""Rebuild the 3:4 and 4:3 covers from a transparent device render.

The approved JPGs already live in covers/. This script writes there only with
--force, after tools/qa_frame.mjs has saved artifacts/cover-device.png.
Pillow needs a Noto CJK Bold TTC (apt install fonts-noto-cjk). The woff2 files
used by the HTML page are a different install and are not used here.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT_CANDIDATES = (
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"),
    Path("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc"),
)


def find_font() -> Path:
    for path in FONT_CANDIDATES:
        if path.is_file():
            return path
    raise SystemExit("未找到 Noto CJK Bold。安装：sudo apt install fonts-noto-cjk")


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    index = 2 if path.suffix == ".ttc" else 0
    return ImageFont.truetype(str(path), size, index=index)


def text(draw: ImageDraw.ImageDraw, face: Path, xy, content: str, size: int, fill: str = "#f3f7fc") -> None:
    draw.text(xy, content, font=font(face, size), fill=fill)


def background(width: int, height: int) -> Image.Image:
    yy, xx = np.mgrid[0:height, 0:width]
    left = np.exp(-(((xx - width * 0.2) / (width * 0.65)) ** 2 + ((yy - height * 0.4) / (height * 0.8)) ** 2) * 3)
    right = np.exp(-(((xx - width * 0.85) / (width * 0.6)) ** 2 + ((yy - height * 0.7) / (height * 0.6)) ** 2) * 3)
    arr = np.zeros((height, width, 3), np.float32) + [10, 19, 37]
    arr += left[:, :, None] * [23, 6, 36]
    arr += right[:, :, None] * [0, 25, 30]
    return Image.fromarray(np.uint8(np.clip(arr, 0, 255)), "RGB").convert("RGBA")


def diagram(draw, face, x, y, scale=1.0) -> None:
    names = [("电机", "#f5a85d"), ("水泵", "#b59afa"), ("喷嘴", "#67e8f9")]
    for index, (name, color) in enumerate(names):
        xx = x + index * 170 * scale
        draw.rounded_rectangle([xx, y, xx + 134 * scale, y + 75 * scale], radius=15 * scale, outline=color, width=3)
        text(draw, face, (xx + 25 * scale, y + 13 * scale), name, int(34 * scale), color)
        if index < 2:
            yy = y + 37 * scale
            draw.line([xx + 142 * scale, yy, xx + 162 * scale, yy], fill="#8fd4e5", width=3)
            draw.polygon(
                [(xx + 164 * scale, yy), (xx + 154 * scale, yy - 7 * scale), (xx + 154 * scale, yy + 7 * scale)],
                fill="#8fd4e5",
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="overwrite the approved covers")
    args = parser.parse_args()
    asset_path = ROOT / "artifacts" / "cover-device.png"
    if not asset_path.is_file():
        raise SystemExit(f"缺少 {asset_path}. 先跑 node production/true3d/qa_frame.mjs")
    face = find_font()
    out = ROOT / "covers"
    out.mkdir(parents=True, exist_ok=True)
    asset = Image.open(asset_path).convert("RGBA")
    asset = asset.crop(asset.getbbox())
    for name, width, height in (("cover_3x4.jpg", 1080, 1440), ("cover_4x3.jpg", 1440, 1080)):
        dest = out / name
        if dest.exists() and not args.force:
            print(f"保留已批准封面 {dest.name}（加 --force 才覆盖）")
            continue
        image = background(width, height)
        draw = ImageDraw.Draw(image)
        if width < height:
            text(draw, face, (88, 64), "身边原理 / 044", 30, "#bba6f8")
            text(draw, face, (86, 120), "Ken带你拆", 74)
            text(draw, face, (78, 213), "冲牙器", 158, "#82e9f7")
            drawn_h = 910
            drawn_w = round(asset.width * drawn_h / asset.height)
            x, y = 620 - drawn_w // 2 + 90, 425
            glow = Image.new("RGBA", (width, height))
            ImageDraw.Draw(glow).ellipse((x - 90, y + 110, x + drawn_w + 130, y + drawn_h + 80), fill=(42, 181, 207, 33))
            image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(55)))
            image.alpha_composite(asset.resize((drawn_w, drawn_h), Image.Resampling.LANCZOS), (x, y))
            draw = ImageDraw.Draw(image)
            text(draw, face, (88, 535), "一股水", 56)
            text(draw, face, (88, 611), "为什么能", 48, "#c4b5fd")
            text(draw, face, (88, 677), "冲走碎屑？", 48, "#c4b5fd")
            for index, line in enumerate(("电机怎样带动泵", "阀门怎样管方向", "脉冲怎样到喷嘴")):
                yy = 890 + index * 86
                draw.line((88, yy, 380, yy), fill=("#edb16c", "#ad8af3", "#67dce8")[index], width=3)
                text(draw, face, (88, yy + 10), line, 28, "#c7d4e4")
            draw.line((88, 1355, 990, 1355), fill="#2f6578", width=2)
            text(draw, face, (88, 1370), "看懂结构，不迷信大水压", 27, "#9bb2c8")
        else:
            text(draw, face, (96, 67), "身边原理 / 044", 31, "#c4b5fd")
            text(draw, face, (92, 175), "Ken带你拆", 92)
            text(draw, face, (81, 292), "冲牙器", 180, "#82e9f7")
            text(draw, face, (98, 535), "水流为什么会脉冲？", 49, "#dbe9f4")
            diagram(draw, face, 100, 695, 1.05)
            text(draw, face, (99, 842), "从电机到喷嘴，拆开这条水路", 34, "#b7c5da")
            drawn_h = 870
            drawn_w = round(asset.width * drawn_h / asset.height)
            x, y = 1065 - drawn_w // 2, 85
            glow = Image.new("RGBA", (width, height))
            ImageDraw.Draw(glow).ellipse((x - 100, y + 170, x + drawn_w + 90, y + drawn_h), fill=(33, 166, 192, 38))
            image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(65)))
            image.alpha_composite(asset.resize((drawn_w, drawn_h), Image.Resampling.LANCZOS), (x, y))
            draw = ImageDraw.Draw(image)
            draw.line((100, 985, 1340, 985), fill="#326075", width=2)
            text(draw, face, (100, 1000), "电机带泵 · 单向控流 · 清洁靠接触", 28, "#97aeca")
        image.convert("RGB").save(dest, quality=96, subsampling=0, dpi=(144, 144))
        print(dest.name, image.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
