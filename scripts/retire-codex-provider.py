#!/usr/bin/env python3
"""Remove the retired managed Azure selector without changing native Codex state."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codex/scripts"))
from config_lock import config_lock

IDENTIFIER = "io.adithyan.codex-provider"
CATALOGS = ("model-catalogs/azure-astra.json", "model-catalogs/azure-gpt6.json")


def atomic_write(path: Path, content: str) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=".provider-retirement-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def clean_config(text: str, managed_selection: bool) -> str:
    data = tomllib.loads(text)
    provider = data.get("model_provider")
    keys = set()
    if provider == "azure" or (managed_selection and provider == "openai"):
        keys.add("model_provider")
    if data.get("profile") == "azure-astra":
        keys.add("profile")
    if (managed_selection or provider == "azure") and data.get("forced_login_method") == "chatgpt":
        keys.add("forced_login_method")
    if data.get("model_catalog_json") in CATALOGS:
        keys.add("model_catalog_json")
    if managed_selection or provider == "azure" or "model_catalog_json" in keys:
        for key, value in (("model_context_window", 400000), ("model_auto_compact_token_limit", 350000)):
            if data.get(key) == value:
                keys.add(key)
    lines = []
    section = ""
    for line in text.splitlines(keepends=True):
        header = re.match(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$", line.rstrip())
        if header:
            section = header[1]
        elif line.lstrip().startswith("[["):
            section = "__array__"
        if section == "model_providers.azure" or section.startswith("model_providers.azure."):
            continue
        if section == "profiles.azure-astra" or section.startswith("profiles.azure-astra."):
            continue
        assignment = re.match(r"^\s*([A-Za-z_][A-Za-z_0-9]*)\s*=", line)
        if assignment:
            if not section and assignment[1] in keys:
                continue
            if section == "features" and assignment[1] == "standalone_web_search" and (managed_selection or provider == "azure"):
                continue
        lines.append(line)
    result = "".join(lines)
    tomllib.loads(result)
    return result


def plan(home: Path) -> tuple[list[tuple[Path, str]], list[Path], Path | None]:
    config = home / ".codex/config.toml"
    state = home / ".local/state/codex-control-plane/provider"
    updates = []
    removals = []
    managed_selection = state.is_file() and state.read_text().strip() in {"azure", "subscription"}
    for path in (config, home / ".codex/.env"):
        if path.is_symlink():
            raise ValueError(f"refusing to edit a symlink: {path}")
        if not path.is_file():
            continue
        before = path.read_text()
        if path == config:
            after = clean_config(before, managed_selection)
        else:
            after = "".join(line for line in before.splitlines(keepends=True)
                            if not re.match(r"^\s*(?:export\s+)?AZURE_OPENAI_API_KEY\s*=", line))
        if before != after:
            updates.append((path, after))
    for relative in (".codex/azure-astra.config.toml", *(".codex/" + item for item in CATALOGS),
                     ".local/state/codex-control-plane/log/provider-menu.out.log",
                     ".local/state/codex-control-plane/log/provider-menu.err.log"):
        path = home / relative
        if path.exists() or path.is_symlink():
            if path.is_dir() and not path.is_symlink():
                raise ValueError(f"unexpected directory at owned artifact: {path}")
            removals.append(path)
    if managed_selection:
        removals.append(state)
    for name, target in (("codex-provider", home / "GitHub/agents/scripts/codex-provider.py"),
                         ("codex-azure", home / "GitHub/scripts/bin/codex-azure")):
        path = home / "bin" / name
        if path.is_symlink() and path.resolve() == target.resolve():
            removals.append(path)
    app = home / "Applications/Codex Provider.app"
    plist = home / "Library/LaunchAgents" / f"{IDENTIFIER}.plist"
    executable = app / "Contents/MacOS/CodexProvider"
    if app.exists():
        if app.is_symlink() or plistlib.loads((app / "Contents/Info.plist").read_bytes()).get("CFBundleIdentifier") != IDENTIFIER:
            raise ValueError(f"unrelated application: {app}")
        removals.append(app)
    if plist.exists():
        value = plistlib.loads(plist.read_bytes())
        if plist.is_symlink() or value.get("Label") != IDENTIFIER or value.get("ProgramArguments") != [str(executable)]:
            raise ValueError(f"unrelated launch agent: {plist}")
        removals.append(plist)
    return updates, removals, executable if app.exists() or plist.exists() else None


def retire(home: Path, apply: bool) -> dict:
    updates, removals, executable = plan(home)
    changed = [str(path) for path, _ in updates] + [str(path) for path in removals]
    if apply:
        config = home / ".codex/config.toml"
        with config_lock(config):
            # Re-evaluate under the same lock used by shared sync and the old selector.
            updates, removals, executable = plan(home)
            changed = [str(path) for path, _ in updates] + [str(path) for path in removals]
            if executable and sys.platform == "darwin":
                subprocess.run(["/bin/launchctl", "bootout", f"gui/{os.getuid()}/{IDENTIFIER}"], capture_output=True, timeout=10)
                processes = subprocess.run(["/bin/ps", "-axo", "pid=,comm="], capture_output=True, text=True, check=True, timeout=10)
                for row in processes.stdout.splitlines():
                    fields = row.strip().split(maxsplit=1)
                    if len(fields) == 2 and fields[1] == str(executable):
                        try:
                            os.kill(int(fields[0]), 15)
                        except ProcessLookupError:
                            pass
            for path, after in updates:
                if path == config:
                    backup = home / ".local/state/codex-control-plane/backups/retired-provider/config.toml"
                    backup.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    if not backup.exists():
                        backup.write_bytes(path.read_bytes())
                        backup.chmod(0o600)
                atomic_write(path, after)
            for path in removals:
                if path.is_dir() and not path.is_symlink():
                    shutil.rmtree(path)
                else:
                    path.unlink(missing_ok=True)
    return {"applied": apply, "changed_paths": changed, "restart_required": bool(changed)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-input", action="store_true", help="Never prompts")
    args = parser.parse_args()
    try:
        result = retire(Path.home(), args.apply)
        print(json.dumps({"status": "ok", "data": result}))
        return 0
    except (OSError, ValueError, TimeoutError, subprocess.SubprocessError, plistlib.InvalidFileException) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
