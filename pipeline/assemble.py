"""FFmpeg：拼接画面、叠字幕、混音、导出成片。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.cmd import run_cmd
from pipeline.fonts import cjk_font_dir, resolve_ass_font_name


def _filter_path(path: Path) -> str:
    """FFmpeg 滤镜参数里的路径：正斜杠，并转义盘符冒号。"""
    return path.resolve().as_posix().replace(":", r"\:").replace("'", r"\'")


def concat_videos(clips: list[Path], out_path: Path, *, ffmpeg: str = "ffmpeg") -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = out_path.with_suffix(".txt")
    lines = [f"file '{p.resolve().as_posix()}'" for p in clips]
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c",
        "copy",
        str(out_path),
    ]
    try:
        run_cmd(cmd)
    except RuntimeError:
        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "24",
            str(out_path),
        ]
        run_cmd(cmd)
    list_file.unlink(missing_ok=True)
    return out_path


def mux_audio_subtitles(
    *,
    video_path: Path,
    audio_path: Path,
    srt_path: Path,
    out_path: Path,
    config: dict[str, Any],
    ass_path: Path | None = None,
) -> Path:
    ffmpeg = config.get("paths", {}).get("ffmpeg", "ffmpeg")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 优先烧 ASS（含正确 PlayRes）；否则回退 SRT
    if ass_path and ass_path.exists():
        vf = f"ass='{_filter_path(ass_path)}'"
        font_dir = cjk_font_dir()
        if font_dir is not None:
            vf += f":fontsdir='{_filter_path(font_dir)}'"
    else:
        sub = config.get("subtitle", {})
        font_name = resolve_ass_font_name(str(sub.get("font_name", "Microsoft YaHei")))
        font_size = int(sub.get("font_size", 36))
        # SRT 默认 PlayRes 约 384x288，MarginV 只能用小数值
        margin_v = 36
        margin_l = 18
        margin_r = 18
        primary = sub.get("primary_color", "&H00FFFFFF")
        outline_c = sub.get("outline_color", "&H00000000")
        outline = int(sub.get("outline", 2))
        shadow = int(sub.get("shadow", 0))
        border_style = int(sub.get("border_style", 1))
        srt_escaped = _filter_path(srt_path)
        force_style = (
            f"FontName={font_name},FontSize={font_size},PrimaryColour={primary},"
            f"OutlineColour={outline_c},Outline={outline},Shadow={shadow},"
            f"MarginV={margin_v},MarginL={margin_l},MarginR={margin_r},"
            f"Alignment=2,BorderStyle={border_style},WrapStyle=2"
        )
        vf = f"subtitles='{srt_escaped}':force_style='{force_style}'"
        font_dir = cjk_font_dir()
        if font_dir is not None:
            vf += f":fontsdir='{_filter_path(font_dir)}'"

    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-vf",
        vf,
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(out_path),
    ]
    run_cmd(cmd)
    return out_path


def write_douyin_copy(episode: dict[str, Any], out_path: Path) -> Path:
    douyin = episode.get("douyin") or {}
    title = douyin.get("title") or episode.get("title") or ""
    description = (douyin.get("description") or "").rstrip()
    tags = episode.get("tags") or []
    tag_line = " ".join(f"#{t}" for t in tags)
    text = (
        f"标题：{title}\n\n"
        f"简介：\n{description}\n\n"
        f"封面大字：{episode.get('cover_text', '')}\n\n"
        f"标签：{tag_line}\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    return out_path
