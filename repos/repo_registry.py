"""Client-neutral repository identity and explicit client configuration."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY = Path(__file__).resolve().parent / "registry.json"
CLIENTS = ("codex", "claude")
ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]*\Z")


def resolve_path(raw: str, home: Path | None = None) -> Path:
    home = home or Path.home()
    if raw == "~":
        return home.resolve()
    if raw.startswith("~/"):
        return (home / raw[2:]).resolve()
    return Path(raw).resolve()


def validate_registry(data: Any, *, home: Path | None = None) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("repository registry must be an object")
    if type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("repository registry version must be 1")
    unknown = set(data) - {"version", "defaults", "repos", "auto_enrollment_exclusions"}
    if unknown:
        raise ValueError(f"unsupported repository registry keys: {', '.join(sorted(unknown))}")
    defaults = data.get("defaults", {})
    if not isinstance(defaults, dict) or set(defaults) - set(CLIENTS):
        raise ValueError("defaults must be an object keyed by supported clients")
    for client, config in defaults.items():
        if not isinstance(config, dict):
            raise ValueError(f"defaults.{client} must be an object")
    repos = data.get("repos")
    if not isinstance(repos, list):
        raise ValueError("repos must be an array")
    seen_ids: set[str] = set()
    seen_paths: set[Path] = set()
    for index, repo in enumerate(repos):
        scope = f"repos[{index}]"
        if not isinstance(repo, dict):
            raise ValueError(f"{scope} must be an object")
        unknown = set(repo) - {"id", "path", "clients"}
        if unknown:
            raise ValueError(f"{scope} unsupported keys: {', '.join(sorted(unknown))}")
        repo_id = repo.get("id")
        if not isinstance(repo_id, str) or not ID_PATTERN.fullmatch(repo_id):
            raise ValueError(f"{scope}.id must be a stable lowercase repository ID")
        if repo_id in seen_ids:
            raise ValueError(f"duplicate repo id: {repo_id}")
        seen_ids.add(repo_id)
        raw_path = repo.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError(f"{scope}.path must be a non-empty string")
        if raw_path != raw_path.strip() or not (raw_path.startswith("~/") or Path(raw_path).is_absolute()):
            raise ValueError(f"{scope}.path must be an absolute or ~/ path")
        path = resolve_path(raw_path, home)
        if path in seen_paths:
            raise ValueError(f"duplicate repo path: {raw_path}")
        seen_paths.add(path)
        clients = repo.get("clients")
        if not isinstance(clients, dict) or set(clients) != set(CLIENTS):
            raise ValueError(f"{scope}.clients must explicitly declare codex and claude")
        for client, settings in clients.items():
            where = f"{scope}.clients.{client}"
            if not isinstance(settings, dict) or set(settings) - {"enabled", "config"}:
                raise ValueError(f"{where} supports only enabled and config")
            if not isinstance(settings.get("enabled"), bool):
                raise ValueError(f"{where}.enabled must be a boolean")
            config = settings.get("config", {})
            if not isinstance(config, dict):
                raise ValueError(f"{where}.config must be an object")
            if set(config) & {"id", "path", "clients", "enabled"}:
                raise ValueError(f"{where}.config cannot redefine repository identity or client enablement")
    exclusions = data.get("auto_enrollment_exclusions", [])
    if not isinstance(exclusions, list):
        raise ValueError("auto_enrollment_exclusions must be an array")
    for index, raw_path in enumerate(exclusions):
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError(f"auto_enrollment_exclusions[{index}] must be a non-empty path")
        if not (raw_path.startswith("~/") or Path(raw_path).is_absolute()):
            raise ValueError(f"auto_enrollment_exclusions[{index}] must be an absolute or ~/ path")
    return data


def load_registry(path: Path = DEFAULT_REGISTRY, *, home: Path | None = None) -> dict[str, Any]:
    return validate_registry(json.loads(Path(path).read_text(encoding="utf-8")), home=home)


def enabled_repositories(registry: dict[str, Any], client: str | None = None) -> list[dict[str, Any]]:
    """Return native entries for one client, or any enabled client for shared work."""
    if client is not None and client not in CLIENTS:
        raise ValueError(f"unsupported client: {client}")
    clients = (client,) if client else CLIENTS
    return [repo for repo in registry["repos"] if any(repo["clients"][name]["enabled"] for name in clients)]


def client_config(registry: dict[str, Any], repo: dict[str, Any], client: str) -> dict[str, Any]:
    """Merge defaults and repo config; one-level config tables merge by key."""
    if client not in CLIENTS:
        raise ValueError(f"unsupported client: {client}")
    result = copy.deepcopy(registry.get("defaults", {}).get(client, {}))
    for key, value in repo["clients"][client].get("config", {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key].update(copy.deepcopy(value))
        else:
            result[key] = copy.deepcopy(value)
    return result


def client_registry(registry: dict[str, Any], client: str, *, enabled_only: bool = True) -> dict[str, Any]:
    """Project native config into the established client renderer input shape."""
    if client not in CLIENTS:
        raise ValueError(f"unsupported client: {client}")
    entries = enabled_repositories(registry, client) if enabled_only else registry["repos"]
    return {
        "defaults": copy.deepcopy(registry.get("defaults", {}).get(client, {})),
        "auto_enrollment_exclusions": copy.deepcopy(registry.get("auto_enrollment_exclusions", [])),
        "repos": [{**copy.deepcopy(repo["clients"][client].get("config", {})), "path": repo["path"]} for repo in entries],
    }
