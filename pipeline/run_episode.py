"""一键跑通单集：TTS → 字幕 → 2D/3D 画面 → 合成。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pipeline.assemble import concat_videos, mux_audio_subtitles, write_douyin_copy
from pipeline.render_2d import render_all_scenes_2d
from pipeline.render_3d import render_all_scenes
from pipeline.subtitles import write_ass, write_srt
from pipeline.tts import concat_audio_files, generate_scene_audio, probe_duration_sec
from pipeline.utils import ROOT, ensure_episode_dirs, load_config, load_episode, render_paths_for_mode, scene_narration_lines


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="科普视频单集流水线")
    parser.add_argument("--id", required=True, help="分集目录名，如 001-air-conditioner")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config.yaml",
        help="全局配置路径",
    )
    parser.add_argument(
        "--skip-render",
        action="store_true",
        help="跳过画面渲染（需 renders 下已有片段）",
    )
    parser.add_argument(
        "--tts-only",
        action="store_true",
        help="只生成旁白与字幕，不渲染不合成",
    )
    parser.add_argument(
        "--reuse-audio",
        action="store_true",
        help="复用 episodes/*/audio 已有旁白，跳过 TTS（更快重出画面）",
    )
    parser.add_argument(
        "--mode",
        choices=["2d", "3d", "placeholder"],
        default=None,
        help="画面模式，默认读 config.video.render_mode",
    )
    parser.add_argument(
        "--placeholder-video",
        action="store_true",
        help="用纯色占位视频合成（兼容旧参数）",
    )
    return parser.parse_args(argv)


def _make_placeholder_clips(
    scene_audio: list[dict],
    renders_dir: Path,
    config: dict,
) -> list[Path]:
    from pipeline.cmd import run_cmd

    ffmpeg = config.get("paths", {}).get("ffmpeg", "ffmpeg")
    width = int(config.get("video", {}).get("width", 1080))
    height = int(config.get("video", {}).get("height", 1920))
    fps = int(config.get("video", {}).get("fps", 24))
    colors = ["0x1B3A4B", "0x245C6E", "0x2F6F5E", "0x3D5A80", "0x1F2A44"]
    clips: list[Path] = []
    for i, item in enumerate(scene_audio):
        out = renders_dir / f"{item['index']:02d}_{item['id']}.mp4"
        color = colors[i % len(colors)]
        dur = float(item["duration"])
        label = item["id"].replace(":", " ")
        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s={width}x{height}:d={dur:.3f}:r={fps}",
            "-vf",
            f"drawtext=text='{label}':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(out),
        ]
        result = run_cmd(cmd, check=False)
        if result.returncode != 0:
            cmd = [
                ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s={width}x{height}:d={dur:.3f}:r={fps}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(out),
            ]
            run_cmd(cmd)
        clips.append(out)
    return clips


def _load_existing_scene_audio(episode: dict, audio_dir: Path, config: dict) -> list[dict]:
    ffprobe = config.get("paths", {}).get("ffprobe", "ffprobe")
    results: list[dict] = []
    for index, scene in enumerate(episode.get("scenes", []), start=1):
        scene_id = scene.get("id", f"scene_{index:02d}")
        out_path = audio_dir / f"{index:02d}_{scene_id}.mp3"
        if not out_path.exists():
            raise FileNotFoundError(f"--reuse-audio 缺少旁白: {out_path}")
        lines = scene_narration_lines(scene)
        text = "".join(lines)
        duration = probe_duration_sec(out_path, ffprobe=ffprobe)
        results.append(
            {
                "index": index,
                "id": scene_id,
                "blender_scene": scene.get("blender_scene", scene_id),
                "text": text,
                "lines": lines,
                "audio": out_path,
                "duration": duration,
            }
        )
    return results


def run(
    episode_id: str,
    config_path: Path,
    *,
    skip_render: bool,
    tts_only: bool,
    reuse_audio: bool,
    mode: str | None,
    placeholder_video: bool,
) -> Path | None:
    config = load_config(config_path)
    episode = load_episode(episode_id)
    dirs = ensure_episode_dirs(episode)

    render_mode = mode or config.get("video", {}).get("render_mode", "2d")
    if placeholder_video:
        render_mode = "placeholder"

    print(f"==> 分集: {episode.get('title', episode_id)} | 画面模式: {render_mode}")
    if reuse_audio:
        scene_audio = _load_existing_scene_audio(episode, dirs["audio"], config)
        print("[tts] 复用已有旁白")
    else:
        scene_audio = generate_scene_audio(episode, config, dirs["audio"])

    ffmpeg = config.get("paths", {}).get("ffmpeg", "ffmpeg")
    gap_ms = int(config.get("audio", {}).get("gap_ms", 280))
    full_audio = dirs["audio"] / "full_narration.mp3"
    if reuse_audio and full_audio.exists():
        print(f"[tts] 复用整轨 {full_audio.name}")
    else:
        concat_audio_files(scene_audio, full_audio, ffmpeg=ffmpeg, gap_ms=gap_ms)
    full_dur = probe_duration_sec(full_audio, ffprobe=config.get("paths", {}).get("ffprobe", "ffprobe"))
    print(f"[tts] 整轨时长 {full_dur:.1f}s -> {full_audio}")

    srt_path = dirs["output"] / "subtitles.srt"
    ass_path = dirs["output"] / "subtitles.ass"
    max_chars = int(config.get("subtitle", {}).get("max_chars_per_line", 14))
    write_srt(scene_audio, srt_path, gap_ms=gap_ms, max_chars_per_line=max_chars)
    write_ass(
        scene_audio,
        ass_path,
        gap_ms=gap_ms,
        max_chars_per_line=max_chars,
        config=config,
    )
    print(f"[subtitles] {srt_path}")
    print(f"[subtitles] {ass_path}")

    meta = {
        "episode_id": episode_id,
        "title": episode.get("title"),
        "audio_duration_sec": full_dur,
        "render_mode": render_mode,
        "scenes": [
            {
                "id": s["id"],
                "duration": s["duration"],
                "blender_scene": s["blender_scene"],
                "audio": str(s["audio"]),
            }
            for s in scene_audio
        ],
    }
    meta_path = dirs["output"] / "build_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    write_douyin_copy(episode, dirs["output"] / "douyin_copy.txt")

    if tts_only:
        print("TTS/字幕完成（--tts-only）")
        return None

    renders_dir, final_name = render_paths_for_mode(dirs, render_mode)

    if skip_render:
        clips = []
        for item in scene_audio:
            clip = renders_dir / f"{item['index']:02d}_{item['id']}.mp4"
            if not clip.exists():
                raise FileNotFoundError(f"--skip-render 但缺少片段: {clip}")
            clips.append(clip)
    elif render_mode == "placeholder":
        clips = _make_placeholder_clips(scene_audio, renders_dir, config)
    elif render_mode == "3d":
        clips = render_all_scenes(episode, config, scene_audio, renders_dir)
    else:
        clips = render_all_scenes_2d(episode, config, scene_audio, renders_dir)

    silent_video = renders_dir / "_concat_silent.mp4"
    concat_videos(clips, silent_video, ffmpeg=ffmpeg)

    final_path = dirs["output"] / final_name
    mux_audio_subtitles(
        video_path=silent_video,
        audio_path=full_audio,
        srt_path=srt_path,
        ass_path=ass_path,
        out_path=final_path,
        config=config,
    )
    print(f"==> 成片: {final_path}")
    return final_path


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    try:
        run(
            args.id,
            args.config,
            skip_render=args.skip_render,
            tts_only=args.tts_only,
            reuse_audio=args.reuse_audio,
            mode=args.mode,
            placeholder_video=args.placeholder_video,
        )
    except Exception as exc:  # noqa: BLE001 - CLI 入口统一报错
        print(f"错误: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
