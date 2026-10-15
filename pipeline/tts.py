"""edge-tts 旁白生成。"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import edge_tts

from pipeline.cmd import run_cmd
from pipeline.utils import scene_narration_lines


async def _save_tts(text: str, voice: str, rate: str, volume: str, out_path: Path) -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    await communicate.save(str(out_path))


def synthesize_to_file(
    text: str,
    out_path: Path,
    *,
    voice: str,
    rate: str = "+0%",
    volume: str = "+0%",
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_save_tts(text, voice, rate, volume, out_path))
    return out_path


def probe_duration_sec(media_path: Path, ffprobe: str = "ffprobe") -> float:
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(media_path),
    ]
    result = run_cmd(cmd, check=False)
    if result.returncode == 0:
        try:
            return float(result.stdout.strip())
        except ValueError:
            pass

    # 无 ffprobe 时用 pydub 回退
    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(media_path)
        return len(audio) / 1000.0
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"无法读取音频时长: {media_path}") from exc


def generate_scene_audio(
    episode: dict[str, Any],
    config: dict[str, Any],
    audio_dir: Path,
) -> list[dict[str, Any]]:
    audio_cfg = config.get("audio", {})
    voice = audio_cfg.get("voice", "zh-CN-YunjianNeural")
    rate = audio_cfg.get("rate", "+0%")
    volume = audio_cfg.get("volume", "+0%")
    ffprobe = config.get("paths", {}).get("ffprobe", "ffprobe")

    results: list[dict[str, Any]] = []
    for index, scene in enumerate(episode.get("scenes", []), start=1):
        lines = scene_narration_lines(scene)
        text = "".join(lines)
        scene_id = scene.get("id", f"scene_{index:02d}")
        out_path = audio_dir / f"{index:02d}_{scene_id}.mp3"
        print(f"[tts] {scene_id} -> {out_path.name}")
        synthesize_to_file(text, out_path, voice=voice, rate=rate, volume=volume)
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


def concat_audio_files(
    scene_audio: list[dict[str, Any]],
    out_path: Path,
    *,
    ffmpeg: str = "ffmpeg",
    gap_ms: int = 280,
) -> Path:
    """用 FFmpeg 拼接各段旁白，段间插入静音。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = out_path.with_suffix(".txt")
    silence = out_path.parent / "_silence_gap.mp3"

    # 生成短静音
    gap_sec = max(gap_ms, 0) / 1000.0
    if gap_sec > 0:
        cmd_sil = [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=24000:cl=mono",
            "-t",
            f"{gap_sec:.3f}",
            "-q:a",
            "9",
            "-acodec",
            "libmp3lame",
            str(silence),
        ]
        run_cmd(cmd_sil)

    lines: list[str] = []
    for i, item in enumerate(scene_audio):
        audio_path = Path(item["audio"]).resolve().as_posix()
        lines.append(f"file '{audio_path}'")
        if gap_sec > 0 and i < len(scene_audio) - 1:
            lines.append(f"file '{silence.resolve().as_posix()}'")
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
    result = run_cmd(cmd, check=False)
    if result.returncode != 0:
        # copy 失败时重编码
        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c:a",
            "libmp3lame",
            "-q:a",
            "4",
            str(out_path),
        ]
        run_cmd(cmd)

    if silence.exists():
        silence.unlink(missing_ok=True)
    list_file.unlink(missing_ok=True)
    return out_path
