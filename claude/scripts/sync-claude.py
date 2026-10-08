#!/usr/bin/env python3
"""Render or check the optional Claude Code control plane."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from claude.control_plane import main

if __name__ == "__main__":
    raise SystemExit(main())
