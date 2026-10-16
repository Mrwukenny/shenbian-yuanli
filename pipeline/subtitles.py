"""根据旁白句与音频时长生成 ASS/SRT（竖屏 PlayRes 正确，避免字幕飞顶裁切）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.fonts import resolve_ass_font_name


def _format_ts_srt(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    ms_total = int(round(seconds * 1000))
    hours, rem = divmod(ms_total, 3600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def _format_ts_ass(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    cs_total = int(round(seconds * 100))
    hours, rem = divmod(cs_total, 3600_00)
    minutes, rem = divmod(rem, 60_00)
    secs, cs = divmod(rem, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def wrap_chinese_text(text: str, max_chars: int = 14) -> str:
    """按字数折行，避免竖屏字幕横向溢出。最多两行。"""
    s = text.strip()
    if not s:
        return s
    if len(s) <= max_chars:
        return s
    break_chars = set("，、；： ")
    best = -1
    lo = max(6, max_chars - 4)
    hi = min(len(s) - 1, max_chars + 2)
    for i in range(lo, hi + 1):
        if s[i - 1] in break_chars:
            best = i
    if best < 0:
        best = max_chars
    first = s[:best].rstrip("，、；： ")
    second = s[best:].lstrip("，、；： ")
    if len(second) > max_chars:
        second = second[: max_chars - 1] + "…"
    return f"{first}\n{second}"


def _allocate_line_durations(lines: list[str], total: float) -> list[float]:
    weights = [max(len(line), 1) for line in lines]
    weight_sum = float(sum(weights))
    raw = [total * (w / weight_sum) for w in weights]
    min_dur = min(0.55, total / max(len(lines) * 2, 1))
    adjusted = [max(d, min_dur) for d in raw]
    scale = total / sum(adjusted)
    return [d * scale for d in adjusted]


def _iter_cues(
    scene_audio: list[dict[str, Any]],
    *,
    gap_ms: int,
    max_chars_per_line: int,
):
    gap = max(gap_ms, 0) / 1000.0
    cursor = 0.0
    for i, scene in enumerate(scene_audio):
        lines: list[str] = scene.get("lines") or [scene.get("text", "")]
        duration = float(scene["duration"])
        line_durs = _allocate_line_durations(lines, duration)
        local_t = 0.0
        for line, dur in zip(lines, line_durs):
            start = cursor + local_t
            end = cursor + min(local_t + dur, duration)
            if end <= start:
                end = start + 0.2
            wrapped = wrap_chinese_text(line.strip(), max_chars=max_chars_per_line)
            yield start, end, wrapped
            local_t += dur
        cursor += duration
        if i < len(scene_audio) - 1:
            cursor += gap


def build_srt_from_scenes(
    scene_audio: list[dict[str, Any]],
    *,
    gap_ms: int = 280,
    max_chars_per_line: int = 14,
) -> str:
    blocks: list[str] = []
    for idx, (start, end, wrapped) in enumerate(
        _iter_cues(scene_audio, gap_ms=gap_ms, max_chars_per_line=max_chars_per_line),
        start=1,
    ):
        blocks.append(
            f"{idx}\n{_format_ts_srt(start)} --> {_format_ts_srt(end)}\n{wrapped}\n"
        )
    return "\n".join(blocks).rstrip() + "\n"


def build_ass_from_scenes(
    scene_audio: list[dict[str, Any]],
    *,
    gap_ms: int = 280,
    max_chars_per_line: int = 14,
    config: dict[str, Any] | None = None,
) -> str:
    """生成带正确竖屏 PlayRes 的 ASS，避免 MarginV 按 288 高度误算。"""
    sub = (config or {}).get("subtitle", {})
    video = (config or {}).get("video", {})
    width = int(video.get("width", 1080))
    height = int(video.get("height", 1920))
    preferred_font = sub.get("font_name", "Microsoft YaHei")
    font_name = resolve_ass_font_name(str(preferred_font))
    if font_name != preferred_font:
        print(f"[subtitles] 系统没有字体 {preferred_font}，ASS 改用 {font_name}")
    font_size = int(sub.get("font_size", 36))
    margin_v = int(sub.get("margin_v", 260))
    margin_l = int(sub.get("margin_l", 72))
    margin_r = int(sub.get("margin_r", 72))
    primary = sub.get("primary_color", "&H00FFFFFF")
    outline_c = sub.get("outline_color", "&H00000000")
    outline = float(sub.get("outline", 2))
    shadow = float(sub.get("shadow", 0))
    border_style = int(sub.get("border_style", 1))

    header = f"""[Script Info]
ScriptType: v4.00+
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary},&H000000FF,{outline_c},&H80000000,0,0,0,0,100,100,0,0,{border_style},{outline},{shadow},2,{margin_l},{margin_r},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events: list[str] = []
    for start, end, wrapped in _iter_cues(
        scene_audio, gap_ms=gap_ms, max_chars_per_line=max_chars_per_line
    ):
        text = wrapped.replace("\n", r"\N")
        events.append(
            f"Dialogue: 0,{_format_ts_ass(start)},{_format_ts_ass(end)},Default,,0,0,0,,{text}"
        )
    return header + "\n".join(events) + "\n"


def write_srt(
    scene_audio: list[dict[str, Any]],
    out_path: Path,
    *,
    gap_ms: int = 280,
    max_chars_per_line: int = 14,
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = build_srt_from_scenes(
        scene_audio,
        gap_ms=gap_ms,
        max_chars_per_line=max_chars_per_line,
    )
    out_path.write_text(content, encoding="utf-8")
    return out_path


def write_ass(
    scene_audio: list[dict[str, Any]],
    out_path: Path,
    *,
    gap_ms: int = 280,
    max_chars_per_line: int = 14,
    config: dict[str, Any] | None = None,
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = build_ass_from_scenes(
        scene_audio,
        gap_ms=gap_ms,
        max_chars_per_line=max_chars_per_line,
        config=config,
    )
    out_path.write_text(content, encoding="utf-8-sig")
    return out_path
