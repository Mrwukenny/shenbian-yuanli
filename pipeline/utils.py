"""配置与分集加载工具。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML 根节点必须是映射: {path}")
    return data


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or (ROOT / "config.yaml")
    return load_yaml(path)


def episode_dir(episode_id: str) -> Path:
    return ROOT / "episodes" / episode_id


def load_episode(episode_id: str) -> dict[str, Any]:
    path = episode_dir(episode_id) / "episode.yaml"
    if not path.exists():
        raise FileNotFoundError(f"找不到分集配置: {path}")
    data = load_yaml(path)
    data["_dir"] = episode_dir(episode_id)
    data["_id"] = episode_id
    return data


def ensure_episode_dirs(episode: dict[str, Any]) -> dict[str, Path]:
    base = Path(episode["_dir"])
    paths = {
        "audio": base / "audio",
        "renders": base / "renders",
        "renders_3d": base / "renders_3d",
        "output": base / "output",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def render_paths_for_mode(dirs: dict[str, Path], mode: str) -> tuple[Path, str]:
    """返回 (渲染目录, 成片文件名)。"""
    if mode == "3d":
        return dirs["renders_3d"], "final_3d.mp4"
    return dirs["renders"], "final.mp4"


def split_sentences(text: str) -> list[str]:
    """按中文句末标点切句，保留标点。"""
    compact = " ".join(part.strip() for part in text.replace("\r\n", "\n").splitlines() if part.strip())
    # 去掉 YAML 多行里多余空白，保留句子
    compact = compact.replace("  ", " ")
    sentences: list[str] = []
    buf: list[str] = []
    endings = set("。？！；…")
    for ch in compact:
        buf.append(ch)
        if ch in endings:
            s = "".join(buf).strip()
            if s:
                sentences.append(s)
            buf = []
    tail = "".join(buf).strip()
    if tail:
        sentences.append(tail)
    return sentences


def scene_narration_lines(scene: dict[str, Any]) -> list[str]:
    raw = scene.get("narration") or ""
    # 优先按行（YAML 里一行一句更利于字幕）
    lines = [ln.strip() for ln in str(raw).replace("\r\n", "\n").split("\n") if ln.strip()]
    if lines:
        return lines
    return split_sentences(str(raw))
