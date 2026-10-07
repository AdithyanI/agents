#!/usr/bin/env python3
"""Reconcile Codex's native credentials through the scripts-owned materializer."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tomllib


def validate_mapping_sources(materializer: Path, mapping: Path) -> None:
    """Use the scripts-owned grammar and name contract without reading values."""
    spec = importlib.util.spec_from_file_location("codex_native_mapping_contract", materializer)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load mapping validator from {materializer}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    mappings = module._parse_mapping_file(mapping)
    store = importlib.import_module("local_secret_store")
    for item in mappings:
        # secret_path only validates components and constructs a path. Neither
        # it nor the mapping parser opens the canonical store or generated env.
        try:
            store.secret_path(root=materializer.parent, scope_name="shared", secret_name=item.secret_name)
        except store.LocalSecretStoreError as exc:
            raise ValueError(str(exc)) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-dir", type=Path, default=Path(__file__).resolve().parents[1] / "config")
    parser.add_argument("--runtime-dir", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--github-root", type=Path, default=Path.home() / "GitHub")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--apply", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--dry-run", action="store_true", help="validate canonical credential readiness without writing (default)")
    modes.add_argument("--check-sources", action="store_true", help="validate provider mappings only; do not read live credential values or generated .env")
    args = parser.parse_args()

    try:
        config = tomllib.loads((args.canonical_dir / "global.config.toml").read_text())
        # Shared profiles remain usable regardless of this machine's default.
        providers = {config.get("model_provider", "openai")}
        for profile in args.canonical_dir.glob("*.config.toml"):
            providers.add(tomllib.loads(profile.read_text()).get("model_provider", "openai"))
        mapping = args.canonical_dir / "secrets.env.map"
        for provider in providers:
            env_key = config.get("model_providers", {}).get(provider, {}).get("env_key")
            if not env_key:
                continue
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
            if args.check_sources:
                print("Codex native environment source validation passed; live credentials not checked (no native mapping).")
            return 0

        materializer = args.github_root / "scripts/sync/materialize_machine_env.py"
        if not materializer.is_file():
            raise ValueError(f"missing {materializer}; sync the scripts repo before applying Codex config")
        if args.check_sources:
            validate_mapping_sources(materializer, mapping)
            print("Codex native environment source validation passed; live credentials not checked.")
            return 0
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
                "~/.local/share/dobby-secrets store, then run codex/scripts/sync-config.sh --apply. "
                "Git sync carries mappings, not secret values; sync both repos if --check is unrecognized."
            )
        print(result.stdout, end="")
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: Codex native environment: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
