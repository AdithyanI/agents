"""Serialize control-plane edits to the app-owned Codex configuration."""
from __future__ import annotations

import contextlib
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time


@contextlib.contextmanager
def config_lock(config: Path, timeout: float = 60):
    config.parent.mkdir(parents=True, exist_ok=True)
    with (config.parent / ".control-plane-config.lock").open("a") as stream:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Codex configuration is busy; retry the operation.")
                time.sleep(0.1)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


if __name__ == "__main__":
    config = Path(sys.argv[1])
    with config_lock(config):
        raise SystemExit(subprocess.call(sys.argv[2:], env={**os.environ, "CODEX_CONFIG_LOCK_HELD": str(config)}))
