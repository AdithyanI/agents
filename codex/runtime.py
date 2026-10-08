"""Resolve the optional local Codex runtime for shared machine orchestration."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hooks.scripts.stop_feedback_turn import FeedbackTurnError, resolve_codex_executable


def available_codex_executable() -> str | None:
    """Use an explicit override or the existing desktop-aware executable resolver.

    Overrides are authoritative, including a missing executable: do not silently
    switch to a different installation. An absent client is optional only in the
    shared orchestrators; direct Codex commands keep their own error behavior.
    """
    override = os.environ.get("CODEX_BIN", "").strip()
    if override:
        return shutil.which(override)
    try:
        executable = resolve_codex_executable()
    except FeedbackTurnError:
        return None
    return shutil.which(executable)


if __name__ == "__main__":
    # Empty output is an absent runtime, not a failed machine bootstrap.
    print(available_codex_executable() or "")
