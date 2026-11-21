#!/usr/bin/env python3
"""Copy pinned Three.js, GSAP, and Noto Sans SC into the 044 composition.

Run from the repository root after `npm ci --prefix production/true3d`.
Copied files stay gitignored. Nothing here downloads paid assets.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPS = ROOT / "production" / "true3d" / "node_modules"
DEST = ROOT / "episodes" / "044-water-flosser" / "true3d" / "assets"


def main() -> int:
    build = DEPS / "three" / "build"
    three = build / "three.module.js"
    core = build / "three.core.js"
    gsap = DEPS / "gsap" / "dist" / "gsap.min.js"
    fonts = DEPS / "@fontsource" / "noto-sans-sc" / "files"
    regular = fonts / "noto-sans-sc-chinese-simplified-400-normal.woff2"
    bold = fonts / "noto-sans-sc-chinese-simplified-700-normal.woff2"
    missing = [p for p in (three, core, gsap, regular, bold) if not p.is_file()]
    if missing:
        print("缺少 npm 依赖。在仓库根目录运行：", file=sys.stderr)
        print("  npm ci --prefix production/true3d", file=sys.stderr)
        for path in missing:
            print(f"  未找到 {path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    vendor = DEST / "vendor"
    font_dir = DEST / "fonts"
    audio = DEST / "audio"
    for directory in (vendor, font_dir, audio):
        directory.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(three, vendor / "three.module.js")
    shutil.copyfile(core, vendor / "three.core.js")
    shutil.copyfile(gsap, vendor / "gsap.min.js")
    shutil.copyfile(regular, font_dir / "NotoSansSC-Regular.woff2")
    shutil.copyfile(bold, font_dir / "NotoSansSC-Bold.woff2")
    print(f"已放入 {DEST.relative_to(ROOT)}")
    print("  vendor/three.module.js   three@0.181.2")
    print("  vendor/three.core.js     three@0.181.2")
    print("  vendor/gsap.min.js       gsap@3.15.1")
    print("  fonts/NotoSansSC-*.woff2 @fontsource/noto-sans-sc@5.3.1（OFL）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
