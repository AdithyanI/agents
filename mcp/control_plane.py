from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_PRESET_KEYS = {"args", "command", "cwd", "env", "repos", "transport", "url"}


class McpRegistryError(ValueError):
    """Raised when the Codex MCP catalog cannot be rendered safely."""


@dataclass(frozen=True)
class McpCatalog:
    definitions: dict[str, dict[str, Any]]
    repo_paths: tuple[str, ...]
    assignments: dict[str, tuple[str, ...]]
    scopes: dict[str, str | list[str]]

    def presets_for(self, repo: str) -> list[tuple[str, dict[str, Any]]]:
        return [(name, self.definitions[name]) for name in self.assignments.get(repo, ())]

    def repos_for(self, preset: str) -> list[str]:
        return [repo for repo in self.repo_paths if preset in self.assignments[repo]]


def _validate_definition(name: str, raw: Any) -> tuple[dict[str, Any], Any]:
    label = f"presets.{name}"
    if not isinstance(raw, dict):
        raise McpRegistryError(f"{label} must be an object")
    unknown = sorted(set(raw) - _PRESET_KEYS)
    if unknown:
        raise McpRegistryError(f"{label} has unsupported keys: {', '.join(unknown)}")

    transport = raw.get("transport")
    if transport not in {"http", "stdio"}:
        raise McpRegistryError(f"{label}.transport must be `http` or `stdio`")
    if transport == "http":
        if not isinstance(raw.get("url"), str) or not raw["url"].strip():
            raise McpRegistryError(f"{label}.url must be a non-empty string")
        forbidden = sorted(key for key in ("args", "command", "cwd", "env") if key in raw)
        if forbidden:
            raise McpRegistryError(
                f"{label} http transport must not set: {', '.join(forbidden)}"
            )
    else:
        if not isinstance(raw.get("command"), str) or not raw["command"].strip():
            raise McpRegistryError(f"{label}.command must be a non-empty string")
        if "url" in raw:
            raise McpRegistryError(f"{label} stdio transport must not set url")
        args = raw.get("args", [])
        if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
            raise McpRegistryError(f"{label}.args must be an array of strings")
        env = raw.get("env", {})
        if not isinstance(env, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in env.items()
        ):
            raise McpRegistryError(f"{label}.env must be an object of string values")
        if "cwd" in raw and (not isinstance(raw["cwd"], str) or not raw["cwd"].strip()):
            raise McpRegistryError(f"{label}.cwd must be a non-empty string")

    definition = {key: value for key, value in raw.items() if key != "repos"}
    return definition, raw.get("repos")


def load_mcp_catalog_data(data: Any, repo_entries: Any) -> McpCatalog:
    if not isinstance(data, dict):
        raise McpRegistryError("MCP registry root must be an object")
    unknown_root = sorted(set(data) - {"version", "presets"})
    if unknown_root:
        raise McpRegistryError("MCP registry has unsupported top-level keys: " + ", ".join(unknown_root))
    if data.get("version") != 3:
        raise McpRegistryError("MCP registry version must be 3")
    presets = data.get("presets")
    if not isinstance(presets, dict):
        raise McpRegistryError("MCP registry presets must be an object")
    if not isinstance(repo_entries, list) or not repo_entries:
        raise McpRegistryError("repo-bootstrap repos must be a non-empty array")

    repo_paths: list[str] = []
    for idx, entry in enumerate(repo_entries):
        if not isinstance(entry, dict):
            raise McpRegistryError(f"repo-bootstrap repos[{idx}] must be an object")
        path = entry.get("path")
        if not isinstance(path, str) or not path.strip():
            raise McpRegistryError(f"repo-bootstrap repos[{idx}].path must be a non-empty string")
        normalized = path.strip()
        if normalized in repo_paths:
            raise McpRegistryError(f"duplicate repo-bootstrap path: {normalized}")
        repo_paths.append(normalized)

    definitions: dict[str, dict[str, Any]] = {}
    assignments: dict[str, list[str]] = {repo: [] for repo in repo_paths}
    scopes: dict[str, str | list[str]] = {}
    for raw_name, raw_definition in presets.items():
        name = str(raw_name).strip()
        if not name or name in definitions:
            raise McpRegistryError("MCP preset names must be non-empty and unique")
        definition, scope = _validate_definition(name, raw_definition)
        if scope == "all":
            selected = repo_paths
        else:
            if not isinstance(scope, list) or not all(isinstance(repo, str) and repo.strip() for repo in scope):
                raise McpRegistryError(f"presets.{name}.repos must be `all` or an array of strings")
            selected = list(dict.fromkeys(repo.strip() for repo in scope))
            unknown = [repo for repo in selected if repo not in assignments]
            if unknown:
                raise McpRegistryError(f"presets.{name}.repos references repos missing from repo-bootstrap.json: {', '.join(unknown)}")
        definitions[name] = definition
        scopes[name] = "all" if scope == "all" else selected
        for repo in selected:
            assignments[repo].append(name)
    return McpCatalog(definitions, tuple(repo_paths), {repo: tuple(sorted(names)) for repo, names in assignments.items()}, scopes)


def load_mcp_catalog(registry_path: Path, repo_entries: Any) -> McpCatalog:
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise McpRegistryError(f"invalid JSON in {registry_path}: {exc}") from exc
    return load_mcp_catalog_data(data, repo_entries)
