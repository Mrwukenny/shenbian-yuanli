"""安全调用外部命令（兼容 Windows 控制台编码）。"""

from __future__ import annotations

import subprocess
from typing import Sequence


def run_cmd(cmd: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(cmd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            "命令失败:\n"
            + " ".join(cmd)
            + "\nstdout:\n"
            + (result.stdout or "")
            + "\nstderr:\n"
            + (result.stderr or "")
        )
    return result
