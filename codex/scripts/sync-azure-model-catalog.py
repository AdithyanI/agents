#!/usr/bin/env python3
"""Materialize the Azure profile's catalog without changing Codex's source cache."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import tomllib
from pathlib import Path


MODEL = "gpt-6-astra"
CATALOG = Path("model-catalogs/azure-astra.json")


def read_models(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    models = data.get("models") if isinstance(data, dict) else None
    if not isinstance(models, list) or not models:
        raise ValueError(f"{path}: expected a non-empty models array")
    slugs = [item.get("slug") if isinstance(item, dict) else None for item in models]
    if any(not isinstance(slug, str) or not slug for slug in slugs):
        raise ValueError(f"{path}: each model must have a non-empty slug")
    if len(set(slugs)) != len(slugs) or slugs.count(MODEL) != 1:
        raise ValueError(f"{path}: expected unique models including {MODEL}")
    return models


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=".azure-astra-", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--canonical-dir", type=Path, default=Path(__file__).resolve().parents[1] / "config"
    )
    parser.add_argument("--runtime-dir", type=Path, default=Path.home() / ".codex")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--apply", action="store_true", help="refresh the local derived catalog")
    modes.add_argument("--check", action="store_true", help="validate the saved catalog without refreshing")
    modes.add_argument("--dry-run", action="store_true", help="inspect the planned refresh (default)")
    args = parser.parse_args()

    try:
        profile = args.canonical_dir / "azure-astra.config.toml"
        if not profile.is_file():
            return 0
        config = tomllib.loads(profile.read_text(encoding="utf-8"))
        if config.get("model_catalog_json") != CATALOG.as_posix():
            return 0
        if config.get("model_provider") != "azure" or config.get("model") != MODEL:
            raise ValueError("the Azure catalog must be scoped to the Azure Astra profile")

        target = args.runtime_dir / CATALOG
        if args.check:
            models = read_models(target)
            model = next(item for item in models if item["slug"] == MODEL)
            if model.get("use_responses_lite") is not False:
                raise ValueError(f"{target}: {MODEL} must use standard Responses")
            print(f"Azure model catalog valid: {target} ({len(models)} models)")
            return 0

        source = args.runtime_dir / "models_cache.json"
        if not source.is_file():
            raise ValueError(
                f"missing source catalog {source}; start codex-openai to populate Codex's "
                "normal model catalog, then rerun codex/scripts/sync-config.sh --apply"
            )
        models = read_models(source)
        model = next(item for item in models if item["slug"] == MODEL)
        if not isinstance(model.get("use_responses_lite"), bool):
            raise ValueError(f"{source}: {MODEL} no longer declares use_responses_lite; review the workaround")
        model["use_responses_lite"] = False
        rendered = json.dumps({"models": models}, indent=2, ensure_ascii=False) + "\n"
        if target.is_file() and target.read_text(encoding="utf-8") == rendered:
            print(f"Azure model catalog unchanged: {target}")
        elif args.apply:
            atomic_write(target, rendered)
            print(f"Azure model catalog refreshed: {target} ({len(models)} models; only {MODEL} modified)")
        else:
            print(f"Would refresh Azure model catalog: {target} from {source}; only {MODEL} modified")
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: Azure model catalog: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
