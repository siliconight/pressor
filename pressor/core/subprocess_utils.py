from __future__ import annotations

import subprocess
from typing import Sequence

DEFAULT_FFPROBE_TIMEOUT = 20
DEFAULT_FFMPEG_TIMEOUT = 180


def run_external(
    cmd: Sequence[str],
    *,
    timeout: int,
    text: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(cmd),
        check=False,
        capture_output=True,
        text=text,
        timeout=timeout,
        shell=False,
    )
