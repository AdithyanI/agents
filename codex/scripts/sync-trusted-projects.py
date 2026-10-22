#!/usr/bin/env python3
"""Reconcile exact reviewed registry roots; discovery never grants trust."""
from __future__ import annotations

import argparse
import difflib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from repos.repo_registry import client_config, load_registry, resolve_path


def trusted_roots(registry: dict) -> set[Path]:
    result = set()
    for repo in registry["repos"]:
        config = client_config(registry, repo, "codex")
        trust = config.get("codex_trust", False)
        if not isinstance(trust, bool):
            raise ValueError("codex_trust must be an explicit boolean")
        path = resolve_path(repo["path"])
        if not repo["clients"]["codex"]["enabled"] or not trust or not path.is_dir():
            continue
        git = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if git.returncode == 0 and Path(git.stdout.strip()).resolve() == path:
            result.add(path)
    return result


def project_header(line: str) -> str | None:
    if not re.match(r"^\s*\[projects\.", line):
        return None
    try:
        projects = tomllib.loads(line)["projects"]
        return next(iter(projects))
    except (tomllib.TOMLDecodeError, KeyError, StopIteration):
        return None


def render(text: str, registry: dict, roots: list[Path]) -> str:
    # Validate before mutation; preserve native model, provider, plugins and user settings.
    tomllib.loads(text)
    trusted = trusted_roots(registry)
    known = {resolve_path(repo["path"]) for repo in registry["repos"]}
    known.update(resolve_path(raw) for raw in registry.get("auto_enrollment_exclusions", []))
    known.add(Path.home() / ".agents")

    def managed(raw: str) -> bool:
        path = Path(raw).expanduser().resolve()
        # Remove broad ancestor grants too: /, home and ~/GitHub would otherwise
        # make newly cloned or excluded projects trusted by inheritance.
        return path in known or any(path == root or path in root.parents or root in path.parents for root in roots)

    lines = text.splitlines(keepends=True)
    output = []
    i = 0
    while i < len(lines):
        raw = project_header(lines[i])
        if raw is None or not managed(raw):
            output.append(lines[i]); i += 1; continue
        end = i + 1
        while end < len(lines) and not re.match(r"^\s*\[", lines[end]):
            end += 1
        # Preserve non-trust project keys if there are any.
        kept = [line for line in lines[i + 1:end] if not re.match(r"^\s*trust_level\s*=", line)]
        if any(line.strip() and not line.lstrip().startswith("#") for line in kept):
            output.append(lines[i]); output.extend(kept)
        i = end
    rendered = "".join(output).rstrip() + "\n"
    existing = tomllib.loads(rendered).get("projects", {})
    for path in sorted(trusted):
        raw = str(path)
        if raw in existing:
            # Existing project metadata needs an in-section key, not a duplicate table.
            needle = next(line for line in rendered.splitlines(keepends=True) if project_header(line) == raw)
            rendered = rendered.replace(needle, needle + 'trust_level = "trusted"\n', 1)
        else:
            rendered += f'\n[projects.{json.dumps(raw)}]\ntrust_level = "trusted"\n'
    tomllib.loads(rendered)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", dest="apply", action="store_false")
    parser.add_argument("--global-only", action="store_true", help="Compatibility: global config is the only target")
    parser.add_argument("--registry", type=Path, default=ROOT / "repos/registry.json")
    parser.add_argument("--root", action="append", type=Path, default=[], help="Workspace whose stale grants are removed; never bypasses registry")
    parser.add_argument("--global-config", type=Path, default=Path.home() / ".codex/config.toml")
    args = parser.parse_args()
    target = args.global_config.expanduser().resolve()
    if args.apply and os.environ.get("CODEX_CONFIG_LOCK_HELD") != str(target):
        return subprocess.call([sys.executable, str(Path(__file__).with_name("config_lock.py")), str(target), sys.executable, str(Path(__file__)), *sys.argv[1:]])
    registry = load_registry(args.registry)
    roots = [root.expanduser().resolve() for root in (args.root or [Path.home() / "GitHub"])]
    before = target.read_text() if target.exists() else ""
    after = render(before, registry, roots)
    print(f"Exact registry trust: {len(trusted_roots(registry))} repositories")
    print("".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=str(target), tofile=str(target))), end="")
    if args.apply and before != after:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=target.parent, prefix=".trust-")
        try:
            with os.fdopen(fd, "w") as stream:
                stream.write(after)
            os.chmod(temporary, target.stat().st_mode & 0o777 if target.exists() else 0o600)
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)
        print(f"Updated: {target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
