#!/usr/bin/env python3
"""Select the Codex provider on this Mac. Existing sessions require reopening."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codex/scripts"))
import provider_selection as provider


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def main() -> int:
    start = time.monotonic()
    command = "codex-provider"
    result = {"schema_version": "1.0", "command": command, "status": "ok", "data": None,
              "error": None, "meta": {"request_id": str(uuid.uuid4()),
              "timestamp_utc": datetime.now(timezone.utc).isoformat()}}
    exit_code = 0
    try:
        parser = Parser(description=__doc__, epilog="Examples: codex-provider status --plain; codex-provider subscription --apply")
        parser.add_argument("action", nargs="?", choices=["status", "azure", "subscription"], default="status")
        modes = parser.add_mutually_exclusive_group()
        modes.add_argument("--apply", action="store_true", help="save this Mac's selection and update its config")
        modes.add_argument("--dry-run", action="store_true", help="validate without writes (default)")
        output = parser.add_mutually_exclusive_group()
        output.add_argument("--plain", action="store_true")
        output.add_argument("--json", action="store_true")
        parser.add_argument("--no-input", action="store_true", help="never prompt (always honored)")
        parser.add_argument("--timeout", type=float, default=60, help="configuration lock timeout in seconds (default 60)")
        args = parser.parse_args()
        if not 0 < args.timeout <= 300:
            raise ValueError("--timeout must be greater than zero and at most 300 seconds")
        result["command"] = f"codex-provider {args.action}"
        config, canonical = Path.home() / ".codex/config.toml", ROOT / "codex/config"
        result["data"] = provider.status(config, canonical) if args.action == "status" else provider.switch(
            config, canonical, args.action, args.apply, args.timeout)
    except (OSError, ValueError, TimeoutError, KeyboardInterrupt) as exc:
        exit_code, code = (5, "E_TIMEOUT") if isinstance(exc, (TimeoutError, KeyboardInterrupt)) else (3, "E_AUTH") if isinstance(exc, PermissionError) else (4, "E_NOT_READY") if isinstance(exc, OSError) else (2, "E_VALIDATION")
        result.update(status="error", error={"code": code, "message": str(exc) or "Interrupted", "retryable": exit_code in (4, 5),
                      "hint": "Run codex-provider status --plain; check the named dependency, then retry."})
    result["meta"]["duration_ms"] = round((time.monotonic() - start) * 1000)
    if "--plain" in sys.argv:
        if result["error"]:
            print(result["error"]["message"], file=sys.stderr)
        else:
            data = result["data"]
            print(f"This Mac: {data['selected']} (config: {data['effective_provider']}; in sync: {data['config_in_sync']})")
            if data.get("requested"):
                print(f"Would select: {data['requested']}. Use --apply to save.")
            print("Applies to new terminal sessions. Reopen Codex and start a new task for the desktop app.")
    else:
        print(json.dumps(result))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
