#!/usr/bin/env python3
"""Synthesize the approved 044 script with edge-tts. No paid speech API.

Writes gitignored audio under true3d/assets/audio/. Does not overwrite the
approved narration_timings.json unless --update-timings is passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "assets" / "audio"
SR = 48000
GAP = 0.28


def edge_argv() -> list[str]:
    found = shutil.which("edge-tts")
    if found:
        return [found]
    return [sys.executable, "-m", "edge_tts"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-timings", action="store_true")
    args = parser.parse_args()
    lines = [line.strip() for line in (ROOT / "script.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    AUDIO.mkdir(parents=True, exist_ok=True)
    raws: list[bytes] = []
    segments = []
    cursor = 0
    for index, text in enumerate(lines):
        digest = hashlib.sha256(text.encode()).hexdigest()[:12]
        mp3 = AUDIO / f"voice_{digest}.mp3"
        wav = AUDIO / f"voice_{digest}.wav"
        if not mp3.exists():
            subprocess.run(
                [*edge_argv(), "-t", text, "-v", "zh-CN-YunjianNeural", "--rate=+0%", "--write-media", str(mp3)],
                check=True,
            )
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-ar", str(SR), "-ac", "1", str(wav)], check=True)
        with wave.open(str(wav)) as handle:
            data = handle.readframes(handle.getnframes())
            frames = handle.getnframes()
        start = cursor / SR
        cursor += frames
        end = cursor / SR
        raws.append(data)
        segments.append(
            {
                "index": index,
                "id": f"sent_{index:03d}",
                "text": text,
                "start": round(start, 6),
                "end": round(end, 6),
                "duration": round(frames / SR, 6),
            }
        )
        if index < len(lines) - 1:
            raws.append(b"\x00\x00" * int(SR * GAP))
            cursor += int(SR * GAP)
        print(index, round(start, 3), round(end, 3), text, flush=True)
    with wave.open(str(AUDIO / "narration.wav"), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(b"".join(raws))
    meta = {
        "voice": "zh-CN-YunjianNeural",
        "rate": "+0%",
        "gap_ms": 280,
        "sample_rate": SR,
        "duration": cursor / SR,
        "segments": segments,
    }
    (AUDIO / "narration_timings.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.update_timings:
        (ROOT / "narration_timings.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DURATION", cursor / SR, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
