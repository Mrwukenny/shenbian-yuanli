"""调用 Blender headless 渲染各分镜。"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

from pipeline.cmd import run_cmd
from pipeline.utils import ROOT


def _blender_bin(config: dict[str, Any]) -> str:
    return config.get("paths", {}).get("blender", "blender")


def render_scene_clip(
    *,
    blender: str,
    scene_name: str,
    duration_sec: float,
    fps: int,
    width: int,
    height: int,
    engine: str,
    out_mp4: Path,
    episode_id: str,
) -> Path:
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    frames = max(int(math.ceil(duration_sec * fps)), fps)  # 至少 1 秒

    runner = ROOT / "templates" / "blender" / "render_clip.py"
    cmd = [
        blender,
        "--background",
        "--python",
        str(runner),
        "--",
        "--scene",
        scene_name,
        "--frames",
        str(frames),
        "--fps",
        str(fps),
        "--width",
        str(width),
        "--height",
        str(height),
        "--engine",
        engine,
        "--output",
        str(out_mp4.resolve()),
        "--episode",
        episode_id,
        "--templates-dir",
        str((ROOT / "templates" / "blender").resolve()),
    ]
    print(f"[blender] {scene_name} ({frames} frames) -> {out_mp4.name}")
    result = run_cmd(cmd, check=False)
    if result.returncode != 0:
        sys.stderr.write((result.stdout or "") + "\n" + (result.stderr or "") + "\n")
        raise RuntimeError(f"Blender 渲染失败: {scene_name} (exit {result.returncode})")
    if not out_mp4.exists():
        raise RuntimeError(f"Blender 未产出文件: {out_mp4}")
    return out_mp4


def render_all_scenes(
    episode: dict[str, Any],
    config: dict[str, Any],
    scene_audio: list[dict[str, Any]],
    renders_dir: Path,
) -> list[Path]:
    video = config.get("video", {})
    width = int(video.get("width", 1080))
    height = int(video.get("height", 1920))
    fps = int(video.get("fps", 24))
    engine = video.get("blender_engine", "BLENDER_EEVEE_NEXT")
    blender = _blender_bin(config)
    episode_id = episode.get("_id") or episode.get("id") or "episode"

    outputs: list[Path] = []
    for item in scene_audio:
        out = renders_dir / f"{item['index']:02d}_{item['id']}.mp4"
        render_scene_clip(
            blender=blender,
            scene_name=item["blender_scene"],
            duration_sec=float(item["duration"]),
            fps=fps,
            width=width,
            height=height,
            engine=engine,
            out_mp4=out,
            episode_id=str(episode_id),
        )
        outputs.append(out)
    return outputs
