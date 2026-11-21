#!/usr/bin/env python3
"""Mux a HyperFrames visual render with the mix and burn ASS captions.

Writes gitignored MP4s under true3d/renders/. The compat file is H.264
Constrained Baseline, yuv420p, no B-frames, AAC, faststart.
Does not publish anywhere.
"""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDERS = ROOT / "renders"
FONT_DIRS = (
    Path("/usr/share/fonts/opentype/noto"),
    Path("/usr/share/fonts/noto-cjk"),
    Path("/usr/share/fonts/truetype/noto"),
)


def fonts_dir() -> Path:
    for path in FONT_DIRS:
        if path.is_dir():
            return path
    raise SystemExit("烧字幕需要 Noto CJK。安装：sudo apt install fonts-noto-cjk")


def run(cmd: list[str], log: Path) -> None:
    with log.open("w") as handle:
        subprocess.run(cmd, check=True, stdout=handle, stderr=subprocess.STDOUT)


def atoms(path: Path) -> list[dict]:
    found = []
    with path.open("rb") as handle:
        while handle.tell() < path.stat().st_size:
            offset = handle.tell()
            data = handle.read(8)
            if len(data) < 8:
                break
            size, kind = struct.unpack(">I4s", data)
            if size == 1:
                size = struct.unpack(">Q", handle.read(8))[0]
            if not size:
                break
            found.append({"type": kind.decode("ascii"), "offset": offset, "size": size})
            handle.seek(offset + size)
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual", type=Path, required=True, help="HyperFrames picture-only mp4")
    args = parser.parse_args()
    visual = args.visual.resolve()
    mix = ROOT / "assets" / "audio" / "mix.wav"
    ass = ROOT / "subtitles.ass"
    if not visual.is_file() or not mix.is_file() or not ass.is_file():
        raise SystemExit("需要 --visual、assets/audio/mix.wav 和 subtitles.ass")
    RENDERS.mkdir(parents=True, exist_ok=True)
    logs = ROOT / "artifacts"
    logs.mkdir(parents=True, exist_ok=True)
    font = fonts_dir()
    jobs = [
        ("master", "high", "18", "192k", []),
        ("compat", "baseline", "20", "160k", ["-bf", "0", "-level:v", "4.0", "-x264-params", "cabac=0:bframes=0:8x8dct=0"]),
    ]
    for kind, profile, crf, bitrate, extra in jobs:
        out = RENDERS / f"044-water-flosser-3d-{kind}.mp4"
        run(
            [
                "ffmpeg", "-y", "-i", str(visual), "-i", str(mix),
                "-map", "0:v:0", "-map", "1:a:0",
                "-vf", f"ass={ass}:fontsdir={font}",
                "-c:v", "libx264", "-profile:v", profile, "-preset", "medium", "-crf", crf,
                "-pix_fmt", "yuv420p", *extra,
                "-c:a", "aac", "-b:a", bitrate, "-ar", "48000", "-ac", "2",
                "-t", "191.2", "-movflags", "+faststart", str(out),
            ],
            logs / f"encode-{kind}.log",
        )
        probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(out)]))
        video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
        audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
        assert video["width"] == 1080 and video["height"] == 1920 and video["pix_fmt"] == "yuv420p"
        assert abs(float(probe["format"]["duration"]) - 191.2) < 0.1
        if kind == "compat":
            assert video["profile"] == "Constrained Baseline" and video["has_b_frames"] == 0
        layout = atoms(out)
        assert next(item["offset"] for item in layout if item["type"] == "moov") < next(item["offset"] for item in layout if item["type"] == "mdat")
        run(["ffmpeg", "-v", "error", "-xerror", "-err_detect", "explode", "-i", str(out), "-f", "null", "-"], logs / f"decode-{kind}.log")
        print(kind, video["profile"], probe["format"]["duration"], out.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
