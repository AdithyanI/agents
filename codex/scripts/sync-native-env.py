#!/usr/bin/env python3
"""Reconcile Codex's native credentials through the scripts-owned materializer."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import tomllib


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-dir", type=Path, default=Path(__file__).resolve().parents[1] / "config")
    parser.add_argument("--runtime-dir", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--github-root", type=Path, default=Path.home() / "GitHub")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--apply", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--dry-run", action="store_true", help="validate sources without writing (default)")
    args = parser.parse_args()

    try:
        config = tomllib.loads((args.canonical_dir / "global.config.toml").read_text())
        provider = config.get("model_provider", "openai")
        env_key = config.get("model_providers", {}).get(provider, {}).get("env_key")
        mapping = args.canonical_dir / "secrets.env.map"
        if env_key:
            keys = set()
            if mapping.is_file():
                keys = {
                    line.split("=", 1)[0].strip()
                    for line in mapping.read_text().splitlines()
                    if "=" in line and not line.lstrip().startswith("#")
                }
            if env_key not in keys:
                raise ValueError(f"provider {provider} requires {env_key}; declare it in {mapping}")
        if not mapping.is_file():
            return 0

        materializer = args.github_root / "scripts/sync/materialize_machine_env.py"
        if not materializer.is_file():
            raise ValueError(f"missing {materializer}; sync the scripts repo before applying Codex config")
        command = [
            sys.executable, str(materializer), "--secret-scope", "shared",
            "--mapping-file", str(mapping), "--output-file", str(args.runtime_dir / ".env"),
        ]
        if args.apply:
            command.append("--apply")
        elif args.check:
            command.append("--check")
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if result.returncode:
            # The materializer reports names and paths only. Never diff credential contents.
            print(result.stdout + result.stderr, end="", file=sys.stderr)
            raise ValueError(
                "native credentials are not ready. Provision the mapped secrets in this machine's "
                "DobbySecrets store, then run codex/scripts/sync-config.sh --apply. "
                "Git sync carries mappings, not secret values; sync both repos if --check is unrecognized."
            )
        print(result.stdout, end="")
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: Codex native environment: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
