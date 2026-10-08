"""Narrow Claude renderer; only previously recorded paths/keys may be replaced.

Plan every output before mutating anything. The manifest is ownership evidence,
not a discovery heuristic: handwritten files and unrecorded symlinks are never
adopted. JSON documents retain unknown settings, servers, and hook groups.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from typing import Any

from hooks.control_plane import load_hooks_registry, render_runtime_hooks
from mcp.control_plane import load_mcp_catalog
from repos.repo_registry import client_config, load_registry, resolve_path

ROOT = Path(__file__).resolve().parents[1]
STATE = Path(".local/state/agents-control-plane/claude")
RESERVED_SKILLS = {"synced", "anthropic-skills"}


class ClaudeSyncError(ValueError):
    """An actionable input, ownership, or runtime capability failure."""


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ClaudeSyncError(f"Expected a JSON object: {path}")
    return value


def json_text(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def probe_client(policy: dict[str, Any]) -> str | None:
    executable = shutil.which("claude")
    if not executable:
        if policy.get("required", False):
            raise ClaudeSyncError("Required Claude Code CLI is missing; install Claude Code and rerun bootstrap.")
        return None
    result = subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=15, check=False)
    match = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", result.stdout)
    minimum = policy.get("minimum_version", "2.1.281")
    if not isinstance(minimum, str) or not re.fullmatch(r"\d+\.\d+\.\d+", minimum):
        raise ClaudeSyncError("Claude policy minimum_version must be a three-part version")
    if result.returncode or not match:
        raise ClaudeSyncError("Cannot identify Claude Code version; repair `claude --version` and rerun.")
    if tuple(map(int, match.groups())) < tuple(map(int, minimum.split("."))):
        raise ClaudeSyncError(f"Claude Code {match.group()} is below required {minimum}; upgrade Claude Code for native AGENTS.md support.")
    return match.group()


def safe_parent(path: Path, anchor: Path) -> None:
    """Reject linked output parents instead of following them into other state."""
    try:
        relative = path.relative_to(anchor)
    except ValueError as exc:
        raise ClaudeSyncError(f"Output escapes its owner: {path}") from exc
    cursor = anchor
    for part in relative.parts[:-1]:
        cursor /= part
        if cursor.is_symlink():
            raise ClaudeSyncError(f"Refusing symlink output ancestor: {cursor}")
        if cursor.exists() and not cursor.is_dir():
            raise ClaudeSyncError(f"Output ancestor is not a directory: {cursor}")


def snapshot(path: Path) -> dict[str, Any] | None:
    if path.is_symlink():
        return {"kind": "link", "value": os.readlink(path)}
    if not path.exists():
        return None
    if not path.is_file():
        raise ClaudeSyncError(f"Refusing non-file output: {path}")
    return {"kind": "file", "value": path.read_text(encoding="utf-8")}


def file_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def mapped_repo(raw: str, home: Path, github_root: Path | None) -> Path:
    if github_root is not None and raw.startswith("~/GitHub/"):
        return (github_root / raw[len("~/GitHub/"):]).resolve()
    return resolve_path(raw, home)


def desired_outputs(root: Path, home: Path, github_root: Path | None, selected: set[Path]) -> tuple[dict[str, Any], set[str]]:
    registry = load_registry(root / "repos/registry.json", home=home)
    repos = {mapped_repo(repo["path"], home, github_root): repo for repo in registry["repos"]}
    unknown = selected - repos.keys()
    if unknown:
        raise ClaudeSyncError("Unknown exact repository path: " + ", ".join(map(str, sorted(unknown))))
    configured = {path: repo for path, repo in repos.items() if repo["clients"]["claude"]["enabled"]}
    for repo in configured.values():
        if client_config(registry, repo, "claude"):
            raise ClaudeSyncError(f"Unsupported Claude config for {repo['id']}; the pilot owns guidance, skills, MCPs, and registry hooks only.")
    existing = {}
    missing = {str(path) for path in repos if not path.is_dir()}
    for path, repo in repos.items():
        if not path.is_dir():
            continue
        result = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False, timeout=10)
        if result.returncode or Path(result.stdout.strip()).resolve() != path:
            missing.add(str(path))
            if not selected or path in selected:
                print(f"SKIP existing non-Git repository root: {path}")
            continue
        existing[path] = repo
    enabled = {path: repo for path, repo in existing.items() if repo["clients"]["claude"]["enabled"]}
    active = {path: repo for path, repo in enabled.items() if not selected or path in selected}
    for path in sorted(str(path) for path in repos if not path.is_dir()):
        if not selected or Path(path) in selected:
            print(f"SKIP missing repository: {path}")
    hooks = load_hooks_registry(root / "hooks/registry.json")
    catalog = load_mcp_catalog(root / "mcp/config/presets.json", registry["repos"])
    desired: dict[str, Any] = {}

    def add(path: Path, scope: str, kind: str, value: Any) -> None:
        if str(path) in desired:
            raise ClaudeSyncError(f"Duplicate Claude output: {path}")
        desired[str(path)] = {"scope": scope, "kind": kind, "value": value}

    if configured:
        guidance = (root / "config/global.agents.md").read_text(encoding="utf-8").rstrip()
        overlay = (root / "claude/config/guidance.md").read_text(encoding="utf-8").strip()
        add(home / ".claude/CLAUDE.md", "global", "text", guidance + "\n\n" + overlay + "\n")
        global_hooks = render_runtime_hooks(hooks, "claude")["hooks"]
        if global_hooks:
            add(home / ".claude/settings.json", "global", "hooks", global_hooks)
    for path, repo in active.items():
        values = {}
        for name, definition in catalog.presets_for(repo["path"]):
            if "cwd" in definition:
                raise ClaudeSyncError(f"MCP {name} declares cwd, which Claude project MCP cannot represent; use a portable command wrapper.")
            values[name] = {"type": definition["transport"], **{k: v for k, v in definition.items() if k != "transport"}}
        if values:
            add(path / ".mcp.json", str(path), "mcp", values)
        repo_hooks = render_runtime_hooks(hooks, "claude", repo_name=path.name)["hooks"]
        if repo_hooks:
            add(path / ".claude/settings.json", str(path), "hooks", repo_hooks)

    skills = read_object(root / "skills/registry.json")
    for skill in skills.get("managed_skills", []):
        clients = skill.get("clients", ["codex"])
        if not isinstance(clients, list) or not clients or any(not isinstance(c, str) or c not in {"codex", "claude"} for c in clients) or len(clients) != len(set(clients)):
            raise ClaudeSyncError(f"Invalid clients for skill {skill.get('skill')}")
        if "claude" not in clients or skill["scope"] == "dormant":
            continue
        name = skill["skill"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name) or name in RESERVED_SKILLS:
            raise ClaudeSyncError(f"Unsafe or reserved Claude skill name: {name}")
        source = (root / skill["source_path"]).resolve()
        if not (source / "SKILL.md").is_file():
            raise ClaudeSyncError(f"Missing skill source: {source}/SKILL.md")
        if skill["scope"] == "global" and configured:
            add(home / ".claude/skills" / name, "global", "link", str(source))
        elif skill["scope"] == "repo":
            targets = skill.get("repos", [])
            for path, repo in active.items():
                assigned = any(target == repo["id"] or ("/" not in target and target == path.name) or mapped_repo(target, home, github_root) == path for target in targets)
                if assigned:
                    add(path / ".claude/skills" / name, str(path), "link", str(source))
    # Native plugin skills deliberately have no translation into Claude.
    return desired, missing


def validate_output(path: Path, entry: dict[str, Any], home: Path) -> None:
    scope, kind = entry.get("scope"), entry.get("kind")
    anchor = home if scope == "global" else Path(scope or "")
    if not anchor.is_absolute() or not path.is_absolute():
        raise ClaudeSyncError(f"Invalid output ownership: {path}")
    base = anchor / ".claude"
    valid = (kind == "text" and scope == "global" and path == base / "CLAUDE.md") or (kind == "hooks" and path == base / "settings.json") or (kind == "mcp" and scope != "global" and path == anchor / ".mcp.json") or (kind == "link" and path.parent == base / "skills" and path.name not in RESERVED_SKILLS)
    if not valid:
        raise ClaudeSyncError(f"Invalid managed output path/kind: {path}")
    safe_parent(path, anchor)


def merge_json(path: Path, current: dict[str, Any] | None, old: dict[str, Any] | None, new: dict[str, Any] | None) -> dict[str, Any] | None:
    kind = (new or old)["kind"]
    if current and current["kind"] != "file":
        raise ClaudeSyncError(f"Refusing linked JSON output: {path}")
    obj = json.loads(current["value"]) if current else {}
    if not isinstance(obj, dict):
        raise ClaudeSyncError(f"Expected JSON object: {path}")
    original = copy.deepcopy(obj)
    key = "mcpServers" if kind == "mcp" else "hooks"
    table = obj.setdefault(key, {})
    if not isinstance(table, dict):
        raise ClaudeSyncError(f"Expected {key} object: {path}")
    before, after = (old or {}).get("value", {}), (new or {}).get("value", {})
    for name, value in before.items():
        if kind == "mcp":
            if name in table and table[name] != value:
                raise ClaudeSyncError(f"Managed MCP was edited: {path} ({name}); reconcile it before syncing.")
            table.pop(name, None)
        else:
            groups = table.get(name, [])
            if not isinstance(groups, list):
                raise ClaudeSyncError(f"Expected hook group array: {path} ({name})")
            groups = groups.copy()
            for group in value:
                if group in groups:
                    groups.remove(group)
                elif groups:
                    raise ClaudeSyncError(f"Managed hook was edited: {path} ({name}); reconcile it before syncing.")
            if groups:
                table[name] = groups
            else:
                table.pop(name, None)
    for name, value in after.items():
        if kind == "mcp":
            if name in table:
                raise ClaudeSyncError(f"Unmanaged MCP name conflicts: {path} ({name})")
            table[name] = value
        else:
            groups = table.setdefault(name, [])
            if not isinstance(groups, list):
                raise ClaudeSyncError(f"Expected hook group array: {path} ({name})")
            known_commands = {h.get("command") for g in groups if isinstance(g, dict) for h in g.get("hooks", []) if isinstance(h, dict)}
            if any(h.get("command") in known_commands for g in value for h in g.get("hooks", [])):
                raise ClaudeSyncError(f"Unmanaged hook command conflicts: {path} ({name})")
            groups.extend(value)
    if not table:
        obj.pop(key, None)
    if current and obj == original:
        return current
    if not obj and old and old.get("created", False) and not new:
        return None
    return {"kind": "file", "value": json_text(obj)}


def build_plan(root: Path, home: Path, github_root: Path | None = None, selected: set[Path] | None = None, *, machine_enabled: bool = True) -> tuple[list[dict[str, Any]], dict[str, Any], Path]:
    selected = selected or set()
    manifest_path = home / STATE / "manifest.json"
    safe_parent(manifest_path, home)
    if manifest_path.is_symlink():
        raise ClaudeSyncError(f"Refusing linked ownership manifest: {manifest_path}")
    manifest = read_object(manifest_path) if manifest_path.exists() else {"version": 1, "outputs": {}}
    if manifest.get("version") != 1 or not isinstance(manifest.get("outputs"), dict):
        raise ClaudeSyncError(f"Invalid Claude ownership manifest: {manifest_path}")
    desired, missing = desired_outputs(root, home, github_root, selected) if machine_enabled else ({}, set())
    previous = manifest["outputs"]
    retained = copy.deepcopy(previous)
    plan = []
    for name in sorted(previous.keys() | desired.keys()):
        path = Path(name)
        old, new = previous.get(name), desired.get(name)
        entry = new or old
        scope = entry.get("scope")
        if scope != "global" and ((selected and Path(scope) not in selected) or scope in missing or not Path(scope).is_dir()):
            continue
        validate_output(path, entry, home)
        if old:
            validate_output(path, old, home)
            if new and (old["scope"], old["kind"]) != (new["scope"], new["kind"]):
                raise ClaudeSyncError(f"Output ownership changed unexpectedly: {path}")
        current = snapshot(path)
        kind = entry["kind"]
        if kind in {"mcp", "hooks"}:
            target = merge_json(path, current, old, new)
        else:
            if current:
                if not old:
                    raise ClaudeSyncError(f"Unmanaged file conflicts: {path}; move it aside or reconcile explicitly before syncing.")
                intact = current["kind"] == "link" and current["value"] == old["value"] if kind == "link" else current["kind"] == "file" and file_hash(current["value"]) == old["sha256"]
                if not intact:
                    raise ClaudeSyncError(f"Managed output was edited: {path}; reconcile it before syncing.")
            target = ({"kind": "link" if kind == "link" else "file", "value": new["value"]} if new else None)
        if current != target:
            plan.append({"path": path, "before": current, "after": target})
        if new:
            record = copy.deepcopy(new)
            if kind == "text":
                record["sha256"] = file_hash(record.pop("value"))
            if kind in {"mcp", "hooks"}:
                record["created"] = old.get("created", False) if old else current is None
            retained[name] = record
        else:
            retained.pop(name, None)
    return plan, {"version": 1, "outputs": retained}, manifest_path


def atomic_write(path: Path, target: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".agents-", dir=path.parent)
    tmp = Path(temporary)
    try:
        if target["kind"] == "link":
            os.close(descriptor)
            tmp.unlink()
            tmp.symlink_to(target["value"])
        else:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(target["value"])
                stream.flush()
                os.fsync(stream.fileno())
            if path.is_file() and not path.is_symlink():
                tmp.chmod(path.stat().st_mode & 0o777)
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def recover_pending(home: Path) -> None:
    """Restore a fully preflighted interrupted transaction before a new apply."""
    pending = home / STATE / "pending.json"
    if not pending.exists():
        return
    safe_parent(pending, home)
    if pending.is_symlink():
        raise ClaudeSyncError(f"Refusing linked recovery journal: {pending}")
    journal = read_object(pending)
    if journal.get("version") != 1 or not isinstance(journal.get("changes"), list):
        raise ClaudeSyncError(f"Invalid recovery journal: {pending}")
    for item in journal["changes"]:
        path = Path(item["path"])
        if path in {home / STATE / "manifest.json", home / STATE / "enabled.json"}:
            safe_parent(path, home)
        else:
            validate_output(path, item["owner"], home)
        current = snapshot(path)
        if current != item["before"] and current != item["after"]:
            raise ClaudeSyncError(f"Interrupted sync output was edited: {path}; reconcile it with {pending} before retrying.")
    for item in reversed(journal["changes"]):
        path = Path(item["path"])
        if snapshot(path) == item["before"]:
            continue
        if item["before"] is None:
            path.unlink(missing_ok=True)
        else:
            atomic_write(path, item["before"])
    pending.unlink()


def _sync_installed(root: Path, home: Path, *, version: str, mode: str, github_root: Path | None, selected: set[Path] | None, machine_enabled: bool, update_enablement: bool) -> int:
    pending = home / STATE / "pending.json"
    safe_parent(pending, home)
    if pending.is_symlink():
        raise ClaudeSyncError(f"Refusing linked recovery journal: {pending}")
    if pending.exists():
        if mode != "apply":
            raise ClaudeSyncError("Interrupted Claude sync needs recovery; rerun with --apply.")
        recover_pending(home)
    plan, manifest, manifest_path = build_plan(root, home, github_root, selected, machine_enabled=machine_enabled)
    target_manifest = {"kind": "file", "value": json_text(manifest)}
    current_manifest = snapshot(manifest_path)
    manifest_changed = current_manifest != target_manifest and (bool(manifest["outputs"]) or current_manifest is not None)
    enablement_path = home / STATE / "enabled.json"
    current_enablement = snapshot(enablement_path)
    target_enablement = {"kind": "file", "value": json_text({"enabled": machine_enabled})}
    enablement_changed = update_enablement and current_enablement != target_enablement
    for item in plan:
        print(f"{'REMOVE' if item['after'] is None else 'WRITE'} {item['path']}")
    if mode == "check":
        if plan or manifest_changed:
            print("ERROR Claude outputs differ; run claude/scripts/sync-claude.py --apply.", file=sys.stderr)
            return 1
        print(f"Claude Code {version}: control plane is current.")
        return 0
    if mode == "apply" and (plan or manifest_changed or enablement_changed):
        backup_dir = home / STATE / "backups" / uuid.uuid4().hex
        safe_parent(backup_dir / "index.json", home)
        # Catch changes since planning before making any output mutation.
        for item in plan:
            if snapshot(item["path"]) != item["before"]:
                raise ClaudeSyncError(f"Output changed during sync: {item['path']}; rerun.")
        if snapshot(manifest_path) != current_manifest:
            raise ClaudeSyncError("Ownership manifest changed during sync; rerun.")
        if snapshot(enablement_path) != current_enablement:
            raise ClaudeSyncError("Machine enablement changed during sync; rerun.")
        backup = [{"path": str(item["path"]), "before": item["before"]} for item in plan if item["before"]]
        if current_manifest:
            backup.append({"path": str(manifest_path), "before": current_manifest})
        if enablement_changed and current_enablement:
            backup.append({"path": str(enablement_path), "before": current_enablement})
        if backup:
            atomic_write(backup_dir / "index.json", {"kind": "file", "value": json_text(backup)})
        previous = json.loads(current_manifest["value"])["outputs"] if current_manifest else {}
        changes = [{**item, "path": str(item["path"]), "owner": manifest["outputs"].get(str(item["path"]), previous.get(str(item["path"])))} for item in plan]
        changes.append({"path": str(manifest_path), "before": current_manifest, "after": target_manifest})
        if enablement_changed:
            changes.append({"path": str(enablement_path), "before": current_enablement, "after": target_enablement})
        atomic_write(pending, {"kind": "file", "value": json_text({"version": 1, "changes": changes})})
        try:
            for item in changes:
                path = Path(item["path"])
                if item["after"] is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write(path, item["after"])
        except BaseException:
            recover_pending(home)
            raise
        pending.unlink()
    print(f"Claude {mode}: {len(plan)} output changes.")
    return 0


def sync(root: Path, home: Path, *, mode: str = "dry-run", github_root: Path | None = None, selected: set[Path] | None = None, enable: bool = False, disable: bool = False) -> int:
    root, home = root.resolve(), home.resolve()
    selected = {path.resolve() for path in selected or set()}
    if (enable or disable) and mode != "apply":
        raise ClaudeSyncError("--enable and --disable require --apply.")
    if enable and disable:
        raise ClaudeSyncError("Choose only one of --enable and --disable.")
    if disable and selected:
        raise ClaudeSyncError("--disable affects this entire machine; omit --repo to remove all owned outputs.")
    enablement = home / STATE / "enabled.json"
    safe_parent(enablement, home)
    if enablement.is_symlink():
        raise ClaudeSyncError(f"Refusing linked machine enablement: {enablement}")
    settings = read_object(enablement) if enablement.exists() else {"enabled": False}
    if set(settings) != {"enabled"} or not isinstance(settings["enabled"], bool):
        raise ClaudeSyncError(f"Invalid Claude machine enablement: {enablement}")
    machine_enabled = (settings["enabled"] or enable) and not disable
    if not machine_enabled and not disable:
        print("SKIP Claude Code is disabled on this machine; opt in with --apply --enable.")
        return 0
    version = "disabled" if disable else probe_client(read_object(root / "claude/config/policy.json"))
    if version is None:
        print("SKIP Claude Code is not installed (optional client).")
        return 0
    if mode != "apply":
        return _sync_installed(root, home, version=version, mode=mode, github_root=github_root, selected=selected, machine_enabled=machine_enabled, update_enablement=False)
    lock = home / STATE / "sync.lock"
    safe_parent(lock, home)
    if lock.is_symlink():
        raise ClaudeSyncError(f"Refusing linked sync lock: {lock}")
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        recover_pending(home)
        # A preceding sync may have disabled this machine while we waited.
        settings = read_object(enablement) if enablement.exists() else {"enabled": False}
        if set(settings) != {"enabled"} or not isinstance(settings["enabled"], bool):
            raise ClaudeSyncError(f"Invalid Claude machine enablement: {enablement}")
        machine_enabled = (settings["enabled"] or enable) and not disable
        if not machine_enabled and not disable:
            print("SKIP Claude Code is disabled on this machine; opt in with --apply --enable.")
            return 0
        return _sync_installed(root, home, version=version, mode=mode, github_root=github_root, selected=selected, machine_enabled=machine_enabled, update_enablement=enable or disable)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--apply", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--dry-run", action="store_true")
    enablement = parser.add_mutually_exclusive_group()
    enablement.add_argument("--enable", action="store_true", help="Opt this machine into Claude management (requires --apply)")
    enablement.add_argument("--disable", action="store_true", help="Disable this machine and remove its owned outputs (requires --apply; no --repo)")
    parser.add_argument("--repo", action="append", default=[], help="Exact registered repository root; repeat to select several")
    parser.add_argument("--home", type=Path, default=Path.home(), help="Runtime home (isolated fixture support)")
    parser.add_argument("--github-root", type=Path, help="Map registered ~/GitHub repositories to this root")
    parser.add_argument("--root", type=Path, default=ROOT, help="Canonical control-plane source root")
    args = parser.parse_args(argv)
    home = args.home.expanduser().resolve()
    github_root = args.github_root.expanduser().resolve() if args.github_root else None
    try:
        return sync(args.root.resolve(), home, mode="apply" if args.apply else "check" if args.check else "dry-run", github_root=github_root, selected={mapped_repo(raw, home, github_root) for raw in args.repo}, enable=args.enable, disable=args.disable)
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
