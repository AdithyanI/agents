#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import uuid
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from socketserver import TCPServer, ThreadingMixIn
from typing import Any
from urllib.parse import unquote, urlparse

_AGENTS_ROOT = Path(__file__).resolve().parent.parent
if str(_AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENTS_ROOT))

from mcp.control_plane import load_mcp_catalog_data  # noqa: E402

SCHEMA_VERSION = "2.0"
COMMAND = "control-plane-dashboard"

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2


REGISTRY_SOURCES = {
    "skills": "skills/registry.json",
    "plugins": "plugins/registry.json",
    "mcp": "mcp/config/presets.json",
    "hooks": "hooks/registry.json",
    "repos": "codex/config/repo-bootstrap.json",
    "dev_servers": "dev-servers/registry.json",
    "codex_global": "codex/config/global.config.toml",
    "global_guidance": "config/global.agents.md",
}


def build_capability_board(counts: dict[str, Any]) -> list[dict[str, Any]]:
    """Codex capability delivery, populated with canonical registry counts."""
    return [
        {
            "key": "knowledge", "name": "Knowledge",
            "desc": "Global guidance the agent wakes up with",
            "source": "config/global.agents.md", "count": None,
            "status": "stable", "note": "~/.codex/AGENTS.md",
        },
        {
            "key": "skills", "name": "Skills",
            "desc": "Reusable procedures",
            "source": "skills/registry.json", "count": counts.get("skills"),
            "status": "stable", "note": "~/.agents/skills + repo",
        },
        {
            "key": "mcp", "name": "Tools · MCP",
            "desc": "External endpoints the agent can call",
            "source": "mcp/config/presets.json", "count": counts.get("mcp"),
            "status": "stable", "note": ".codex/config.toml by repository",
        },
        {
            "key": "plugins", "name": "Plugins",
            "desc": "Codex-native capability bundles",
            "source": "plugins/registry.json", "count": counts.get("plugins"),
            "status": "stable", "note": "~/.codex/config.toml",
        },
        {
            "key": "lifecycle", "name": "Lifecycle",
            "desc": "Hooks around each turn — commit, checks, finalize",
            "source": "hooks/registry.json", "count": counts.get("hooks"),
            "status": "stable", "note": "SessionStart · Prompt · Stop",
        },
        {
            "key": "runtime", "name": "Runtime config",
            "desc": "Per-repo behavior and exposure",
            "source": "codex/config/repo-bootstrap.json", "count": counts.get("repos"),
            "status": "stable", "note": ".codex/config.toml",
        },
        {
            "key": "dev", "name": "Agent Preview",
            "desc": "One fixed local preview target per repo",
            "source": "dev-servers/registry.json", "count": counts.get("dev_servers"),
            "status": "stable", "note": ".codex/environments/environment.toml",
        },
    ]


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def meta(request_id: str, started_at: float) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "duration_ms": int((time.time() - started_at) * 1000),
        "timestamp_utc": utc_timestamp(),
    }


def finish_ok(
    command: str,
    request_id: str,
    started_at: float,
    data: dict[str, Any],
    *,
    plain: bool,
) -> int:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "status": "ok",
        "data": data,
        "error": None,
        "meta": meta(request_id, started_at),
    }
    if plain:
        print_plain_data(data)
    else:
        print(json.dumps(payload, indent=2))
    return EXIT_SUCCESS


def finish_error(
    command: str,
    request_id: str,
    started_at: float,
    *,
    code: str,
    message: str,
    hint: str,
    exit_code: int,
    plain: bool,
) -> int:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "status": "error",
        "data": {},
        "error": {
            "code": code,
            "message": message,
            "retryable": False,
            "hint": hint,
        },
        "meta": meta(request_id, started_at),
    }
    if plain:
        print(f"error {code}: {message}", file=sys.stderr)
        print(hint, file=sys.stderr)
    else:
        print(json.dumps(payload, indent=2))
    return exit_code


def load_json(path: Path, warnings: list[dict[str, Any]]) -> dict[str, Any]:
    if not path.is_file():
        warnings.append(
            {
                "severity": "error",
                "code": "missing_source",
                "message": f"Missing source file: {path}",
                "source": str(path),
            }
        )
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        warnings.append(
            {
                "severity": "error",
                "code": "invalid_json",
                "message": f"Invalid JSON in {path}: {exc}",
                "source": str(path),
            }
        )
        return {}
    if not isinstance(value, dict):
        warnings.append(
            {
                "severity": "error",
                "code": "invalid_source_shape",
                "message": f"Expected top-level JSON object in {path}",
                "source": str(path),
            }
        )
        return {}
    return value


def clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        cleaned = item.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            out.append(cleaned)
    return out


def repo_name(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if value.endswith("/"):
        value = value.rstrip("/")
    if value.startswith("~/"):
        return Path(value[2:]).name
    if value.startswith("/"):
        return Path(value).name
    return value


def expand_repo_path(raw: str) -> Path:
    value = raw.strip()
    if value == "~":
        return Path.home().resolve()
    if value.startswith("~/"):
        return (Path.home() / value[2:]).resolve()
    return Path(value).expanduser().resolve()


def repo_key(raw: str) -> str:
    return repo_name(raw).lower()


def relation_key(kind: str, name: str) -> str:
    return f"{kind}:{name}"


def read_skill_openai_metadata(
    root: Path,
    source_path: str,
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "codex_allow_implicit_invocation": True,
        "codex_invocation": "implicit + explicit",
    }
    if not source_path:
        return metadata

    openai_yaml = root / source_path / "agents" / "openai.yaml"
    if not openai_yaml.is_file():
        return metadata

    metadata["openai_yaml_path"] = str(Path(source_path) / "agents" / "openai.yaml")
    try:
        import yaml  # type: ignore[import-untyped]

        parsed = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))
    except ImportError:
        warnings.append(
            {
                "severity": "warning",
                "code": "missing_yaml_dependency",
                "message": f"Could not parse Codex skill metadata without PyYAML: {openai_yaml}",
                "source": str(Path(source_path) / "agents" / "openai.yaml"),
            }
        )
        return metadata
    except (OSError, yaml.YAMLError) as exc:  # type: ignore[name-defined]
        warnings.append(
            {
                "severity": "warning",
                "code": "invalid_openai_yaml",
                "message": f"Could not parse Codex skill metadata for {source_path}: {exc}",
                "source": str(Path(source_path) / "agents" / "openai.yaml"),
            }
        )
        return metadata

    if not isinstance(parsed, dict):
        return metadata

    policy = parsed.get("policy")
    if not isinstance(policy, dict):
        return metadata

    allow_implicit = policy.get("allow_implicit_invocation")
    if allow_implicit is None:
        return metadata
    if not isinstance(allow_implicit, bool):
        warnings.append(
            {
                "severity": "warning",
                "code": "invalid_openai_yaml_policy",
                "message": (
                    f"Skill {source_path} policy.allow_implicit_invocation must be a boolean "
                    f"when present."
                ),
                "source": str(Path(source_path) / "agents" / "openai.yaml"),
            }
        )
        return metadata

    metadata["codex_allow_implicit_invocation"] = allow_implicit
    metadata["codex_invocation"] = "implicit + explicit" if allow_implicit else "explicit only"
    return metadata


def base_item(
    *,
    kind: str,
    name: str,
    title: str | None = None,
    scope: str | None = None,
    status: str | None = None,
    source: str,
    repos: list[str] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    details = details or {}
    repos = repos or []
    search_parts = [
        kind,
        name,
        title or "",
        scope or "",
        status or "",
        " ".join(repos),
        " ".join(str(value) for value in details.values() if isinstance(value, (str, int, float, bool))),
    ]
    return {
        "id": relation_key(kind, name),
        "kind": kind,
        "name": name,
        "title": title or name,
        "scope": scope or "unknown",
        "status": status or "active",
        "repos": repos,
        "source": source,
        "details": details,
        "search_text": " ".join(search_parts).lower(),
    }


def append_managed_skill_items(
    *,
    root: Path,
    skills_registry: dict[str, Any],
    registry_key: str,
    skills: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    entries = skills_registry.get(registry_key, [])
    if not isinstance(entries, list):
        warnings.append(
            {
                "severity": "error",
                "code": "invalid_skills_shape",
                "message": f"skills/registry.json {registry_key} must be a list.",
                "source": REGISTRY_SOURCES["skills"],
            }
        )
        return

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("skill", "")).strip()
        if not name:
            continue
        scope = str(entry.get("scope", "unknown")).strip() or "unknown"
        source_path = str(entry.get("source_path", "")).strip()
        repos_for_entry = clean_list(entry.get("repos"))
        if scope == "repo" and not repos_for_entry:
            warnings.append(
                {
                    "severity": "warning",
                    "code": "repo_scope_without_repos",
                    "message": f"Skill {name} is repo-scoped but has no repos.",
                    "source": REGISTRY_SOURCES["skills"],
                }
            )
        if source_path and not (root / source_path).exists():
            warnings.append(
                {
                    "severity": "warning",
                    "code": "missing_skill_source",
                    "message": f"Skill {name} source path does not exist: {source_path}",
                    "source": REGISTRY_SOURCES["skills"],
                }
            )
        details = {
            "origin": entry.get("origin"),
            "source_path": source_path,
            "upstream_ref": entry.get("upstream_ref"),
        }
        details.update(read_skill_openai_metadata(root, source_path, warnings))
        title = None
        if registry_key == "managed_plugin_skills":
            source_plugin = str(entry.get("source_plugin", "")).strip()
            details["source_plugin"] = source_plugin
            if source_plugin:
                title = f"{source_plugin}:{name}"
        skills.append(
            base_item(
                kind="skill",
                name=name,
                title=title,
                scope=scope,
                status="dormant" if scope == "dormant" else "active",
                source=REGISTRY_SOURCES["skills"],
                repos=repos_for_entry,
                details=details,
            )
        )


def _config_group(title: str, source: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"title": title, "source": source, "rows": rows}


def _scalar_value(value: Any) -> str:
    if isinstance(value, bool):
        return "on" if value else "off"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "—"
    if value is None:
        return "—"
    return str(value)


def build_global_config(
    root: Path,
    plugins_registry: dict[str, Any],
    repo_bootstrap: dict[str, Any],
    warnings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Codex configuration from canonical files, without inspecting runtime state."""
    codex_src = REGISTRY_SOURCES["codex_global"]
    none_row = [{"label": "(none)", "value": "—", "tone": "muted"}]

    codex_cfg: dict[str, Any] = {}
    codex_path = root / codex_src
    if codex_path.exists():
        import tomllib

        try:
            codex_cfg = tomllib.loads(codex_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            warnings.append(
                {
                    "severity": "error",
                    "code": "invalid_codex_global",
                    "message": f"Could not parse {codex_src}: {exc}",
                    "source": codex_src,
                }
            )

    codex_default_rows = [
        {"label": k, "value": _scalar_value(v)} for k, v in codex_cfg.items() if not isinstance(v, dict)
    ]
    codex_feature_rows = [
        {"label": k, "value": "on" if v else "off", "tone": "on" if v else "off"}
        for k, v in (codex_cfg.get("features") or {}).items()
    ]
    codex_plugin_rows = [
        {
            "label": str(p.get("plugin")),
            "value": "enabled" if p.get("enabled") else "disabled",
            "tone": "on" if p.get("enabled") else "off",
        }
        for p in plugins_registry.get("managed_plugins", [])
        if isinstance(p, dict) and p.get("scope") == "global"
    ]
    defaults = repo_bootstrap.get("defaults", {})
    defaults = defaults if isinstance(defaults, dict) else {}

    codex_groups = [_config_group("Runtime defaults", codex_src, codex_default_rows or none_row)]
    if codex_feature_rows:
        codex_groups.append(_config_group("Features", codex_src, codex_feature_rows))
    codex_groups += [
        _config_group(
            "Repo defaults",
            REGISTRY_SOURCES["repos"],
            [{"label": k, "value": _scalar_value(v)} for k, v in defaults.items()] or none_row,
        ),
        _config_group("Global plugins", REGISTRY_SOURCES["plugins"], codex_plugin_rows or none_row),
        _config_group(
            "MCP delivery",
            REGISTRY_SOURCES["mcp"],
            [{"label": "Scope", "value": "All managed repos or selected repos", "tone": "muted"}],
        ),
    ]

    return codex_groups


def build_control_plane_data(root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    warnings: list[dict[str, Any]] = []
    sources = {
        name: {
            "path": relative,
            "absolute_path": str(root / relative),
        }
        for name, relative in REGISTRY_SOURCES.items()
    }

    skills_registry = load_json(root / REGISTRY_SOURCES["skills"], warnings)
    plugins_registry = load_json(root / REGISTRY_SOURCES["plugins"], warnings)
    mcp_registry = load_json(root / REGISTRY_SOURCES["mcp"], warnings)
    hooks_registry = load_json(root / REGISTRY_SOURCES["hooks"], warnings)
    repo_bootstrap = load_json(root / REGISTRY_SOURCES["repos"], warnings)
    dev_servers_registry = load_json(root / REGISTRY_SOURCES["dev_servers"], warnings)

    repo_entries = repo_bootstrap.get("repos", [])
    if not isinstance(repo_entries, list):
        repo_entries = []
        warnings.append(
            {
                "severity": "error",
                "code": "invalid_repos_shape",
                "message": "codex/config/repo-bootstrap.json repos must be a list.",
                "source": REGISTRY_SOURCES["repos"],
            }
        )

    repos: list[dict[str, Any]] = []
    repo_lookup: dict[str, dict[str, Any]] = {}
    for entry in repo_entries:
        if not isinstance(entry, dict):
            continue
        path = str(entry.get("path", "")).strip()
        if not path:
            warnings.append(
                {
                    "severity": "warning",
                    "code": "repo_missing_path",
                    "message": "Repo bootstrap entry is missing a path.",
                    "source": REGISTRY_SOURCES["repos"],
                }
            )
            continue
        name = repo_name(path)
        expanded_path = expand_repo_path(path)
        exists = expanded_path.exists()
        if not exists:
            warnings.append(
                {
                    "severity": "warning",
                    "code": "managed_repo_missing",
                    "message": f"Managed repo path does not exist: {path}",
                    "source": REGISTRY_SOURCES["repos"],
                }
            )
        repo = base_item(
            kind="repo",
            name=name,
            scope="managed",
            status="configured",
            source=REGISTRY_SOURCES["repos"],
            details={
                "path": path,
                "absolute_path": str(expanded_path),
                "exists": exists,
                "personality": entry.get("personality"),
                "features": entry.get("features") if isinstance(entry.get("features"), dict) else {},
            },
        )
        repos.append(repo)
        repo_lookup[repo_key(path)] = repo
        repo_lookup[repo_key(name)] = repo

    skills: list[dict[str, Any]] = []
    for registry_key in ("managed_skills", "managed_plugin_skills"):
        append_managed_skill_items(
            root=root,
            skills_registry=skills_registry,
            registry_key=registry_key,
            skills=skills,
            warnings=warnings,
        )

    for entry in skills_registry.get("unmanaged_repo_local_skills", []):
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("skill", "")).strip()
        repo = str(entry.get("repo", "")).strip()
        if not name:
            continue
        item = base_item(
            kind="skill",
            name=name,
            title=f"{name} ({repo_name(repo)})",
            scope="repo-local",
            status="unmanaged",
            source=REGISTRY_SOURCES["skills"],
            repos=[repo] if repo else [],
            details={
                "origin": "repo-local",
                "repo": repo,
            },
        )
        item["id"] = relation_key("skill", f"{repo_name(repo)}:{name}")
        skills.append(item)

    plugins: list[dict[str, Any]] = []
    for entry in plugins_registry.get("managed_plugins", []):
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("plugin", "")).strip()
        if not name:
            continue
        scope = str(entry.get("scope", "unknown")).strip() or "unknown"
        repos_for_entry = clean_list(entry.get("repos"))
        enabled = bool(entry.get("enabled", False))
        if scope == "repo" and not repos_for_entry:
            warnings.append(
                {
                    "severity": "warning",
                    "code": "repo_scope_without_repos",
                    "message": f"Plugin {name} is repo-scoped but has no repos.",
                    "source": REGISTRY_SOURCES["plugins"],
                }
            )
        plugins.append(
            base_item(
                kind="plugin",
                name=name,
                scope=scope,
                status="enabled" if enabled else "disabled",
                source=REGISTRY_SOURCES["plugins"],
                repos=repos_for_entry,
                details={
                    "marketplace": entry.get("marketplace"),
                    "category": entry.get("category"),
                    "enabled": enabled,
                },
            )
        )

    for entry in plugins_registry.get("unmanaged_repo_local_plugins", []):
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("plugin", "")).strip()
        repo = str(entry.get("repo", "")).strip()
        if not name:
            continue
        item = base_item(
            kind="plugin",
            name=name,
            title=f"{name} ({repo_name(repo)})",
            scope="repo-local",
            status="unmanaged",
            source=REGISTRY_SOURCES["plugins"],
            repos=[repo] if repo else [],
            details={
                "marketplace": entry.get("marketplace"),
                "category": entry.get("category"),
                "repo": repo,
            },
        )
        item["id"] = relation_key("plugin", f"{repo_name(repo)}:{name}")
        plugins.append(item)

    mcp_presets: list[dict[str, Any]] = []
    preset_defs = mcp_registry.get("presets", {})
    if not isinstance(preset_defs, dict):
        preset_defs = {}
        warnings.append(
            {
                "severity": "error",
                "code": "invalid_mcp_shape",
                "message": "mcp/config/presets.json presets must be an object.",
                "source": REGISTRY_SOURCES["mcp"],
            }
        )
    try:
        mcp_catalog = load_mcp_catalog_data(mcp_registry, repo_entries)
    except ValueError as exc:
        mcp_catalog = None
        warnings.append(
            {
                "severity": "error",
                "code": "invalid_mcp_registry",
                "message": str(exc),
                "source": REGISTRY_SOURCES["mcp"],
            }
        )

    for name, config in sorted(preset_defs.items()):
        if not isinstance(config, dict):
            config = {}
        assigned_repo_refs = mcp_catalog.repos_for(str(name)) if mcp_catalog else []
        assigned_repos = sorted(repo_name(repo) for repo in assigned_repo_refs)
        is_global = bool(mcp_catalog and mcp_catalog.scopes[str(name)] == "all")
        scope = "global" if is_global else "targeted" if assigned_repos else "unassigned"
        mcp_presets.append(
            base_item(
                kind="mcp",
                name=str(name),
                scope=scope,
                status="assigned" if assigned_repos else "unassigned",
                source=REGISTRY_SOURCES["mcp"],
                repos=assigned_repos,
                details={
                    "transport": config.get("transport"),
                    "url": config.get("url"),
                    "command": config.get("command"),
                    "global": is_global,
                },
            )
        )

    hooks: list[dict[str, Any]] = []
    for entry in hooks_registry.get("managed_hooks", []):
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("id", "")).strip()
        if not name:
            continue
        scope = str(entry.get("scope", "unknown")).strip() or "unknown"
        repos_for_entry = clean_list(entry.get("repos"))
        hooks.append(
            base_item(
                kind="hook",
                name=name,
                title=str(entry.get("event", name)),
                scope=scope,
                status="enabled" if bool(entry.get("enabled", False)) else "disabled",
                source=REGISTRY_SOURCES["hooks"],
                repos=repos_for_entry,
                details={
                    "event": entry.get("event"),
                    "timeout": entry.get("timeout"),
                    "command": entry.get("command"),
                    "matchers": entry.get("matchers") if isinstance(entry.get("matchers"), dict) else {},
                },
            )
        )

    dev_servers: list[dict[str, Any]] = []
    raw_dev_servers = dev_servers_registry.get("managed_dev_servers", [])
    if not isinstance(raw_dev_servers, list):
        raw_dev_servers = []
        warnings.append(
            {
                "severity": "error",
                "code": "invalid_dev_servers_shape",
                "message": "dev-servers/registry.json managed_dev_servers must be a list.",
                "source": REGISTRY_SOURCES["dev_servers"],
            }
        )
    for entry in raw_dev_servers:
        if not isinstance(entry, dict):
            continue
        repo = str(entry.get("repo", "")).strip()
        if not repo:
            continue
        servers = entry.get("servers", [])
        servers = servers if isinstance(servers, list) else []
        server_names = []
        for server in servers:
            if not isinstance(server, dict):
                continue
            name = str(server.get("name", "")).strip()
            port = server.get("port")
            if name and isinstance(port, int):
                server_names.append(f"{name} :{port}")
            elif name:
                server_names.append(name)
        ports = [s.get("port") for s in servers if isinstance(s, dict) and "port" in s]
        dev_servers.append(
            base_item(
                kind="dev_server",
                name=repo_name(repo),
                title=f"{repo_name(repo)} agent preview",
                scope="repo",
                status="active" if servers else "empty",
                source=REGISTRY_SOURCES["dev_servers"],
                repos=[repo],
                details={
                    "servers": [n for n in server_names if n],
                    "server_count": len(servers),
                    "ports": ports,
                },
            )
        )

    attach_repo_counts(repos, skills, plugins, mcp_presets, hooks, dev_servers)

    items = skills + plugins + mcp_presets + repos + hooks + dev_servers
    global_config = build_global_config(root, plugins_registry, repo_bootstrap, warnings)
    counts = {
        "items": len(items),
        "skills": len(skills),
        "plugins": len(plugins),
        "mcp": len(mcp_presets),
        "repos": len(repos),
        "hooks": len(hooks),
        "dev_servers": len(dev_servers),
        "warnings": len(warnings),
        "global": sum(1 for item in items if item["scope"] == "global"),
        "repo_scoped": sum(1 for item in items if "repo" in item["scope"]),
        "disabled": sum(1 for item in items if item["status"] == "disabled"),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_timestamp(),
        "repo_root": str(root),
        "sources": sources,
        "counts": counts,
        "capabilities": build_capability_board(counts),
        "global_config": global_config,
        "warnings": warnings,
        "items": items,
        "groups": {
            "skills": skills,
            "plugins": plugins,
            "mcp": mcp_presets,
            "repos": repos,
            "hooks": hooks,
            "dev_servers": dev_servers,
        },
    }


def attach_repo_counts(
    repos: list[dict[str, Any]],
    skills: list[dict[str, Any]],
    plugins: list[dict[str, Any]],
    mcp_presets: list[dict[str, Any]],
    hooks: list[dict[str, Any]],
    dev_servers: list[dict[str, Any]] | None = None,
) -> None:
    dev_servers = dev_servers or []
    for repo in repos:
        key = repo_key(repo["name"])
        repo["details"]["skill_count"] = sum(item_applies_to_repo(item, key) for item in skills)
        repo["details"]["plugin_count"] = sum(item_applies_to_repo(item, key) for item in plugins)
        repo["details"]["mcp_count"] = sum(item_applies_to_repo(item, key) for item in mcp_presets)
        repo["details"]["hook_count"] = sum(item_applies_to_repo(item, key) for item in hooks)
        repo["details"]["dev_count"] = sum(
            item["details"].get("server_count", 0)
            for item in dev_servers
            if item_applies_to_repo(item, key)
        )


def item_applies_to_repo(item: dict[str, Any], repo: str) -> bool:
    if item["scope"] == "global":
        return True
    return any(repo_key(value) == repo for value in item.get("repos", []))


def print_plain_data(data: dict[str, Any]) -> None:
    counts = data["counts"]
    print(
        "ok "
        f"items={counts['items']} "
        f"skills={counts['skills']} "
        f"plugins={counts['plugins']} "
        f"mcp={counts['mcp']} "
        f"repos={counts['repos']} "
        f"hooks={counts['hooks']} "
        f"warnings={counts['warnings']}"
    )


class DashboardServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        root: Path,
        dashboard_root: Path | None = None,
        release_sha: str = "development",
    ):
        super().__init__(server_address, handler_class)
        self.root = root.expanduser().resolve()
        self.dashboard_root = (dashboard_root or self.root / "dashboard").expanduser().resolve()
        self.release_sha = release_sha
        self.server_name = str(server_address[0])
        self.server_port = int(self.server_address[1])


class DashboardHandler(BaseHTTPRequestHandler):
    server: DashboardServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/api/control-plane":
            payload = build_control_plane_data(self.server.root)
            payload["release_sha"] = self.server.release_sha
            self.send_json(payload)
            return
        if path.startswith("/source/"):
            if os.environ.get("AGENTS_DASHBOARD_ENABLE_SOURCE") != "1":
                self.send_error(HTTPStatus.FORBIDDEN, "Source browsing disabled")
                return
            self.send_source(path.removeprefix("/source/"))
            return
        if path in {"", "/"}:
            self.send_static("index.html")
            return
        if path in {"/dashboard", "/dashboard/"}:
            self.redirect("/")
            return
        if path.startswith("/dashboard/"):
            relative = path.removeprefix("/dashboard/")
            if not relative:
                relative = "index.html"
            self.send_static(relative)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[control-plane-dashboard] {self.address_string()} - {fmt % args}", file=sys.stderr)

    def redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", location)
        self.end_headers()

    def send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_source(self, relative: str) -> None:
        target = safe_join(self.server.root, relative)
        if target is None or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Source not found")
            return
        content_type = mimetypes.guess_type(str(target))[0] or "text/plain"
        self.send_file(target, content_type)

    def send_static(self, relative: str) -> None:
        target = safe_join(self.server.dashboard_root, relative)
        if target is None or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Asset not found")
            return
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if target.suffix == ".js":
            content_type = "text/javascript"
        self.send_file(target, content_type)

    def send_file(self, target: Path, content_type: str) -> None:
        body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def safe_join(root: Path, relative: str) -> Path | None:
    root = root.expanduser().resolve()
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target


def command_data(args: argparse.Namespace) -> int:
    request_id = f"{COMMAND}-data-{uuid.uuid4()}"
    started_at = time.time()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        return finish_error(
            f"{COMMAND} data",
            request_id,
            started_at,
            code="E_ROOT_NOT_FOUND",
            message=f"Repository root does not exist: {root}",
            hint="Pass --root pointing at the agents control-plane repository.",
            exit_code=EXIT_USAGE,
            plain=args.plain,
        )
    data = build_control_plane_data(root)
    return finish_ok(f"{COMMAND} data", request_id, started_at, data, plain=args.plain)


def command_serve(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: repository root does not exist: {root}", file=sys.stderr)
        return EXIT_USAGE
    dashboard_root = (
        Path(args.dashboard_root).expanduser().resolve()
        if args.dashboard_root
        else root / "dashboard"
    )
    dashboard_index = dashboard_root / "index.html"
    if not dashboard_index.is_file():
        print(f"ERROR: dashboard assets not found under {dashboard_root}", file=sys.stderr)
        return EXIT_FAILURE

    server = DashboardServer(
        (args.host, args.port),
        DashboardHandler,
        root,
        dashboard_root,
        args.release_sha,
    )
    host, port = server.server_address
    url = f"http://{host}:{port}/dashboard/"
    print(f"Control plane dashboard: {url}", file=sys.stderr)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping control plane dashboard.", file=sys.stderr)
    finally:
        server.server_close()
    return EXIT_SUCCESS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve and inspect the local agents control-plane dashboard."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    data_parser = subparsers.add_parser(
        "data",
        help="Emit the normalized dashboard data contract.",
    )
    data_parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Path to the agents control-plane repository root.",
    )
    data_parser.add_argument(
        "--plain",
        action="store_true",
        help="Emit stable plain-text summary output instead of JSON.",
    )
    data_parser.add_argument(
        "--no-input",
        action="store_true",
        help="Accepted for agent-safe non-interactive operation; prompts are never used.",
    )
    data_parser.set_defaults(func=command_data)

    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the local dashboard web server.",
    )
    serve_parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Path to the agents control-plane repository root.",
    )
    serve_parser.add_argument(
        "--dashboard-root",
        help="Built dashboard asset directory (default: <root>/dashboard).",
    )
    serve_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface to bind (default: 127.0.0.1).",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8765")),
        help="Port to bind (default: $PORT or 8765). Use 0 to request an available port.",
    )
    serve_parser.add_argument(
        "--release-sha",
        default="development",
        help="Exact production source revision exposed by the health payload.",
    )
    serve_parser.add_argument(
        "--open",
        action="store_true",
        help="Open the dashboard URL in the default browser after the server starts.",
    )
    serve_parser.add_argument(
        "--no-input",
        action="store_true",
        help="Accepted for agent-safe non-interactive operation; prompts are never used.",
    )
    serve_parser.set_defaults(func=command_serve)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
