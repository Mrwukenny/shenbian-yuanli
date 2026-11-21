#!/usr/bin/env python3
"""Build the ducked music bed, loudnorm mix, and wrapped captions for 044.

Needs numpy, ffmpeg, and assets/audio/narration.wav from generate_voice.py.
The approved narration_timings.json in this directory is the fallback clock.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "assets" / "audio"
ARTIFACTS = ROOT / "artifacts"
DURATION = 191.2
SR = 48000


def load_timings() -> dict:
    local = AUDIO / "narration_timings.json"
    return json.loads((local if local.is_file() else ROOT / "narration_timings.json").read_text(encoding="utf-8"))


def timestamp(seconds: float, ass: bool = False) -> str:
    scale = 100 if ass else 1000
    ticks = round(seconds * scale)
    sec, frac = divmod(ticks, scale)
    hour, sec = divmod(sec, 3600)
    minute, sec = divmod(sec, 60)
    if ass:
        return f"{hour}:{minute:02}:{sec:02}.{frac:02}"
    return f"{hour:02}:{minute:02}:{sec:02},{frac:03}"


def visual_width(text: str) -> float:
    return sum(0.55 if ord(char) < 128 else 1 for char in text)


def wrap(text: str) -> str:
    if visual_width(text) <= 17.5:
        return text
    cuts = []
    for index in range(2, len(text) - 2):
        left, right = text[:index], text[index:]
        cost = abs(visual_width(left) - visual_width(right))
        cost += 0 if text[index - 1] in "，。：、？；" else 14
        cost += max(0, visual_width(left) - 17.5) * 20
        cost += max(0, visual_width(right) - 17.5) * 20
        cuts.append((cost, index))
    _, index = min(cuts)
    return text[:index] + "\n" + text[index:]


def main() -> int:
    narration = AUDIO / "narration.wav"
    if not narration.is_file():
        raise SystemExit(f"缺少旁白：{narration}. 先运行 tools/generate_voice.py")
    meta = load_timings()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    samples = round(DURATION * SR)
    with wave.open(str(narration)) as handle:
        voice = np.frombuffer(handle.readframes(handle.getnframes()), np.int16).astype(np.float32) / 32768
    voice = np.pad(voice, (0, samples - len(voice)))
    clock = np.arange(samples, dtype=np.float32) / SR
    chords = [
        [146.832, 174.614, 220.0],
        [130.813, 174.614, 220.0],
        [130.813, 164.814, 195.998],
        [146.832, 195.998, 246.942],
    ]
    bed = np.zeros((samples, 2), np.float32)
    for chord_index in range(math.ceil(DURATION / 16)):
        start = max(0, chord_index * 16 - 2)
        end = min(DURATION, (chord_index + 1) * 16 + 2)
        lo, hi = int(start * SR), int(end * SR)
        local = clock[lo:hi]
        fade = np.minimum(np.clip((local - start) / 2, 0, 1), np.clip((end - local) / 2, 0, 1))
        fade = fade * fade * (3 - 2 * fade)
        for partial, frequency in enumerate(chords[chord_index % 4]):
            tone = np.sin(2 * np.pi * frequency * local + partial * 0.7) * 0.0032
            tone += np.sin(2 * np.pi * (frequency * 0.5) * local + partial * 0.5) * 0.0022
            bed[lo:hi, 0] += tone * fade * (0.9 - partial * 0.12)
            bed[lo:hi, 1] += tone * fade * (0.66 + partial * 0.12)
    edge = np.minimum(np.clip(clock / 1.4, 0, 1), np.clip((DURATION - clock) / 1.5, 0, 1))
    bed *= edge[:, None]
    block = 480
    blocks = np.abs(voice).reshape(-1, block).mean(1)
    envelope = np.interp(np.arange(samples), np.arange(len(blocks)) * block + block / 2, blocks)
    duck = 1 - 0.55 * np.clip(envelope / 0.045, 0, 1)
    mix = voice[:, None] + bed * duck[:, None]
    raw = ARTIFACTS / "mix-raw.wav"
    with wave.open(str(raw), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    measured = subprocess.run(
        ["ffmpeg", "-hide_banner", "-y", "-i", str(raw), "-af", "loudnorm=I=-16:TP=-2:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    stats = json.loads(re.findall(r"\{[^{}]*\}", measured.stderr)[-1])
    (ARTIFACTS / "loudnorm-input.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    loudnorm = (
        "loudnorm=I=-16:TP=-2:LRA=11:"
        f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
        f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
        f"offset={stats['target_offset']}:linear=true"
    )
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", loudnorm, "-ar", "48000", "-ac", "2", str(AUDIO / "mix.wav")],
        check=True,
    )
    overrides = {
        0: "我是Ken，挑战每天用3分钟\n带你了解一个身边原理。",
        36: "记住口诀：电机带泵，单向控流，\n细嘴出水，清洁靠接触。",
        37: "关注身边原理，我是Ken，\n明天继续带你了解下一个原理。",
        38: "你还想接着拆哪个家电？\n评论区告诉我。",
    }
    srt: list[str] = []
    events: list[str] = []
    for segment in meta["segments"]:
        text = overrides.get(segment["index"], wrap(segment["text"]))
        assert text.replace("\n", "") == segment["text"]
        assert max(visual_width(line) for line in text.splitlines()) <= 18
        srt.append(f"{segment['index'] + 1}\n{timestamp(segment['start'])} --> {timestamp(segment['end'])}\n{text}\n")
        events.append(
            f"Dialogue: 0,{timestamp(segment['start'], True)},{timestamp(segment['end'], True)},Ken,,0,0,0,,{text.replace(chr(10), '\\N')}"
        )
    (ROOT / "subtitles.srt").write_text("\n".join(srt), encoding="utf-8")
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Ken,Noto Sans CJK SC,52,&H00F8FAFC,&H00000000,&H0027150C,&H80000000,1,0,0,0,100,100,0,0,1,4,0,2,90,90,350,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    (ROOT / "subtitles.ass").write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    print(f"media ready {DURATION}s; {len(events)} subtitle events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
