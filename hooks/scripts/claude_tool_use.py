#!/usr/bin/env python3
"""Claude PostToolUse adapter: record touched repositories for the Stop finalizer.

Attribution is best effort and never blocks a tool call. The Stop finalizer
always includes the starting repository, so a missed registration only narrows
discovery to that repository.
"""
from __future__ import annotations

import argparse
import json
import sys

try:
    from hooks.scripts.stop import log, register_claude_tool_use
except ModuleNotFoundError:  # Direct script execution adds this directory to sys.path.
    from stop import log, register_claude_tool_use


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=["claude"], required=True)
    parser.parse_args()
    try:
        payload = json.loads(sys.stdin.read() or "null")
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict) or payload.get("hook_event_name") != "PostToolUse":
        return 0
    try:
        register_claude_tool_use(payload)
    except Exception as exc:  # noqa: BLE001 - attribution must not interrupt the tool loop.
        log("claude", f"warn tool-use-attribution tool={payload.get('tool_name')} error={exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
