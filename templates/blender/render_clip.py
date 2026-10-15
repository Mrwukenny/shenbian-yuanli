"""
Blender headless 入口：
  blender --background --python render_clip.py -- --scene hook --frames 72 ...
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _parse_args(argv: list[str]) -> argparse.Namespace:
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True)
    parser.add_argument("--frames", type=int, required=True)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--engine", default="BLENDER_EEVEE_NEXT")
    parser.add_argument("--output", required=True)
    parser.add_argument("--episode", default="001-air-conditioner")
    parser.add_argument("--templates-dir", required=True)
    return parser.parse_args(argv)


def _resolve_produced(out: Path, frames: int) -> Path | None:
    """Blender FFMPEG 常写出 stem0001-00NN.mp4。"""
    candidates = [
        out,
        out.with_suffix(".mp4"),
        Path(str(out.with_suffix("")) + ".mp4"),
        out.parent / f"{out.stem}0001-{frames:04d}.mp4",
        out.parent / f"{out.with_suffix('').name}0001-{frames:04d}.mp4",
    ]
    for c in candidates:
        if c.exists() and c.stat().st_size > 0:
            return c
    # 模糊匹配最近生成的相关 mp4
    stem = out.with_suffix("").name
    matches = sorted(
        out.parent.glob(f"{stem}*.mp4"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def main() -> int:
    args = _parse_args(sys.argv)
    templates_dir = Path(args.templates_dir)
    sys.path.insert(0, str(templates_dir))

    import bpy  # noqa: WPS433 - Blender runtime

    from ac_system import build_scene  # type: ignore  # noqa: WPS433
    from common import configure_render  # type: ignore  # noqa: WPS433

    build_scene(args.scene, args.frames)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    # 使用带扩展名的路径，减少命名歧义；仍可能写出 frame range 后缀
    configure_render(
        width=args.width,
        height=args.height,
        fps=args.fps,
        frames=args.frames,
        engine=args.engine,
        output_path=str(out.with_suffix("")),
    )
    bpy.ops.render.render(animation=True)

    produced = _resolve_produced(out, args.frames)
    if produced is None:
        raise FileNotFoundError(f"Blender 未产出视频: {out}")
    if produced.resolve() != out.resolve():
        if out.exists():
            out.unlink()
        produced.replace(out)

    print(f"[render_clip] done -> {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
