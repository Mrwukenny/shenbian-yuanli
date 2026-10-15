"""用 Pillow 按分镜绘制 2D 帧，经 FFmpeg 管道编码成竖屏片段。"""

from __future__ import annotations

import importlib
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from pipeline.utils import ROOT


def _load_drawer(module_name: str = "ac_scenes") -> Callable:
    templates = str(ROOT / "templates" / "2d")
    if templates not in sys.path:
        sys.path.insert(0, templates)
    mod = importlib.import_module(module_name)
    importlib.reload(mod)
    return mod.draw_scene


def render_scene_clip_2d(
    *,
    scene_name: str,
    duration_sec: float,
    fps: int,
    width: int,
    height: int,
    out_mp4: Path,
    ffmpeg: str = "ffmpeg",
    draw_scene: Callable | None = None,
) -> Path:
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    frames = max(int(math.ceil(duration_sec * fps)), fps)
    print(f"[2d] {scene_name} ({frames} frames, {duration_sec:.1f}s) -> {out_mp4.name}")
    drawer = draw_scene or _load_drawer()

    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-movflags",
        "+faststart",
        str(out_mp4),
    ]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    assert proc.stdin is not None
    try:
        for i in range(frames):
            t = i / max(frames - 1, 1)
            time_sec = i / fps
            try:
                img = drawer(scene_name, t, width, height, time_sec=time_sec).convert("RGB")
            except TypeError:
                img = drawer(scene_name, t, width, height).convert("RGB")
            proc.stdin.write(img.tobytes())
            if i % max(frames // 5, 1) == 0:
                print(f"  ... {scene_name} {int(100 * i / frames)}%")
    except Exception:
        proc.kill()
        raise
    finally:
        proc.stdin.close()
    _stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        err = (stderr or b"").decode("utf-8", errors="replace")
        raise RuntimeError(f"2D 编码失败: {scene_name}\n{err}")
    if not out_mp4.exists():
        raise RuntimeError(f"未产出文件: {out_mp4}")
    return out_mp4


def render_all_scenes_2d(
    episode: dict[str, Any],
    config: dict[str, Any],
    scene_audio: list[dict[str, Any]],
    renders_dir: Path,
) -> list[Path]:
    video = config.get("video", {})
    width = int(video.get("width", 1080))
    height = int(video.get("height", 1920))
    fps = int(video.get("fps", 24))
    ffmpeg = config.get("paths", {}).get("ffmpeg", "ffmpeg")
    module_name = episode.get("template_2d") or "ac_scenes"
    drawer = _load_drawer(module_name)
    print(f"[2d] 模板: {module_name}")

    outputs: list[Path] = []
    for item in scene_audio:
        out = renders_dir / f"{item['index']:02d}_{item['id']}.mp4"
        scene_name = item.get("blender_scene") or item["id"]
        render_scene_clip_2d(
            scene_name=scene_name,
            duration_sec=float(item["duration"]),
            fps=fps,
            width=width,
            height=height,
            out_mp4=out,
            ffmpeg=ffmpeg,
            draw_scene=drawer,
        )
        outputs.append(out)
    return outputs
