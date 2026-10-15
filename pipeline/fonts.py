"""跨平台中文字体：微软雅黑 → Noto CJK → DejaVu。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

# Windows 雅黑优先，其次各发行版常见的 Noto CJK，最后 DejaVu（无汉字，仅兜底）。
_YAHEI_REGULAR = (
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\msyh.ttf"),
)
_YAHEI_BOLD = (
    Path(r"C:\Windows\Fonts\msyhbd.ttc"),
    Path(r"C:\Windows\Fonts\msyhbd.ttf"),
)
_NOTO_REGULAR_NAMES = (
    "NotoSansCJK-Regular.ttc",
    "NotoSansCJKsc-Regular.otf",
    "NotoSansSC-Regular.otf",
)
_NOTO_BOLD_NAMES = (
    "NotoSansCJK-Bold.ttc",
    "NotoSansCJKsc-Bold.otf",
    "NotoSansSC-Bold.otf",
)
_NOTO_DIRS = (
    Path("/usr/share/fonts/opentype/noto"),
    Path("/usr/share/fonts/noto-cjk"),
    Path("/usr/share/fonts/truetype/noto"),
    Path("/usr/share/fonts/google-noto-cjk"),
    Path("/usr/local/share/fonts"),
    Path.home() / ".local/share/fonts",
    Path.home() / ".fonts",
)
_DEJAVU_REGULAR = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path(r"C:\Windows\Fonts\DejaVuSans.ttf"),
)
_DEJAVU_BOLD = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path(r"C:\Windows\Fonts\DejaVuSans-Bold.ttf"),
)

_warned_fallback = False


@dataclass(frozen=True)
class FontSpec:
    path: Path
    index: int
    family: str


def _noto_paths(names: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for directory in _NOTO_DIRS:
        if not directory.is_dir():
            continue
        for name in names:
            candidate = directory / name
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            found.append(candidate)
    if found:
        return found
    roots = (
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        Path.home() / ".local/share/fonts",
    )
    for root in roots:
        if not root.is_dir():
            continue
        for name in names:
            for candidate in root.rglob(name):
                if not candidate.is_file():
                    continue
                resolved = candidate.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                found.append(candidate)
                if len(found) >= 4:
                    return found
    return found


def _existing(paths: tuple[Path, ...] | list[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if not path.is_file():
            continue
        try:
            key = path.resolve()
        except OSError:
            key = path
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def _candidate_files(bold: bool) -> list[Path]:
    if bold:
        groups = (
            _existing(_YAHEI_BOLD),
            _existing(_YAHEI_REGULAR),
            _noto_paths(_NOTO_BOLD_NAMES),
            _noto_paths(_NOTO_REGULAR_NAMES),
            _existing(_DEJAVU_BOLD),
            _existing(_DEJAVU_REGULAR),
        )
    else:
        groups = (
            _existing(_YAHEI_REGULAR),
            _existing(_YAHEI_BOLD),
            _noto_paths(_NOTO_REGULAR_NAMES),
            _noto_paths(_NOTO_BOLD_NAMES),
            _existing(_DEJAVU_REGULAR),
            _existing(_DEJAVU_BOLD),
        )
    ordered: list[Path] = []
    seen: set[Path] = set()
    for group in groups:
        for path in group:
            try:
                key = path.resolve()
            except OSError:
                key = path
            if key in seen:
                continue
            seen.add(key)
            ordered.append(path)
    return ordered


def _face_rank(family: str) -> int:
    """简体非等宽优先。雅黑 / DejaVu 只有一个实用面，同分时保留更小的 index。"""
    name = family.casefold()
    rank = 0
    if "mono" in name:
        rank -= 20
    if "cjk sc" in name or name.endswith(" sc"):
        rank += 50
    elif "cjk" in name or "yahei" in name or "微软雅黑" in family:
        rank += 10
    return rank


def _best_face(path: Path) -> tuple[int, str] | None:
    best: tuple[int, int, str] | None = None
    for index in range(32):
        try:
            font = ImageFont.truetype(str(path), size=32, index=index)
        except OSError:
            break
        family, _style = font.getname()
        rank = _face_rank(family)
        if best is None or rank > best[0]:
            best = (rank, index, family)
    if best is None:
        return None
    return best[1], best[2]


@lru_cache(maxsize=4)
def resolve_cjk_font(bold: bool = False) -> FontSpec | None:
    for path in _candidate_files(bold):
        face = _best_face(path)
        if face is None:
            continue
        index, family = face
        return FontSpec(path=path, index=index, family=family)
    return None


def load_cjk_font(size: int, bold: bool = False):
    """加载中文字体。找不到雅黑和 Noto 时退回 DejaVu，再不行用 Pillow 默认位图字体。"""
    global _warned_fallback
    spec = resolve_cjk_font(bold)
    if spec is None:
        if not _warned_fallback:
            print(
                "警告: 未找到中文字体（微软雅黑 / Noto CJK / DejaVu），画面中文可能无法显示。",
                file=sys.stderr,
            )
            _warned_fallback = True
        return ImageFont.load_default()
    if "dejavu" in spec.family.casefold() and not _warned_fallback:
        print(
            "警告: 未找到微软雅黑或 Noto CJK，已退回 DejaVu，中文会显示为方框。"
            "请安装 fonts-noto-cjk，或在 Windows 上使用微软雅黑。",
            file=sys.stderr,
        )
        _warned_fallback = True
    return ImageFont.truetype(str(spec.path), size=size, index=spec.index)


def cjk_font_dir() -> Path | None:
    spec = resolve_cjk_font(False)
    if spec is None:
        return None
    return spec.path.parent


def _fontconfig_has_family(name: str) -> bool:
    fc = shutil.which("fc-list")
    if not fc or not name.strip():
        return False
    result = subprocess.run(
        [fc, name, "family"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return False
    target = name.casefold()
    for line in result.stdout.splitlines():
        families = line.split(":", 1)[1] if ":" in line else line
        # fc-list 可能附带 style=，只比较族名本身
        families = families.split(":style=", 1)[0]
        for family in families.split(","):
            if family.strip().casefold() == target:
                return True
    return False


def resolve_ass_font_name(preferred: str | None = None) -> str:
    """ASS Fontname：配置的字体已安装则沿用，否则改用本机解析到的中文字体族名。"""
    name = (preferred or "Microsoft YaHei").strip() or "Microsoft YaHei"
    if _fontconfig_has_family(name):
        return name
    spec = resolve_cjk_font(False)
    if spec is None:
        return name
    if name.casefold() in {"microsoft yahei", "微软雅黑"} and "yahei" in spec.family.casefold():
        return "Microsoft YaHei"
    return spec.family
