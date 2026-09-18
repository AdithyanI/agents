#!/usr/bin/env python3
"""Render Codex preview actions from the shared development-server registry."""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


AGENTS_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = AGENTS_ROOT / "dev-servers" / "registry.json"
DEFAULT_PREVIEW_RUNNER = AGENTS_ROOT / "scripts" / "run-agent-preview-server.py"


def resolve_repo_root(repo: str, github_root: Path) -> Path:
    if repo.startswith(("~/", "/")):
        return Path(repo).expanduser().resolve()
    return (github_root / repo).resolve()


def ensure_str(value: Any, field: str, label: str, idx: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}[{idx}] invalid {field}: {value!r}")
    return value.strip()


def load_dev_servers(registry_file: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(registry_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {registry_file}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"JSON file must contain an object: {registry_file}")
    raw_items = data.get("managed_dev_servers", [])
    if not isinstance(raw_items, list):
        raise ValueError("managed_dev_servers must be an array")

    entries: list[dict[str, Any]] = []
    seen_repos: set[str] = set()
    seen_ports: dict[int, str] = {}
    for idx, item in enumerate(raw_items):
        if not isinstance(item, dict):
            raise ValueError(f"managed_dev_servers[{idx}] must be an object")
        repo = ensure_str(item.get("repo"), "repo", "managed_dev_servers", idx)
        if repo in seen_repos:
            raise ValueError(f"duplicate dev-server repo entries: {repo}")
        seen_repos.add(repo)
        servers_raw = item.get("servers", [])
        if not isinstance(servers_raw, list) or not servers_raw:
            raise ValueError(f"managed_dev_servers[{idx}] needs a non-empty servers array")
        if len(servers_raw) != 1:
            raise ValueError(
                f"managed_dev_servers[{idx}] must define exactly one agent preview server"
            )

        label = f"managed_dev_servers[{idx}].servers"
        server = servers_raw[0]
        if not isinstance(server, dict):
            raise ValueError(f"{label}[0] must be an object")
        name = ensure_str(server.get("name"), "name", label, 0)
        runtime = ensure_str(server.get("runtimeExecutable"), "runtimeExecutable", label, 0)
        host = str(server.get("host", "127.0.0.1")).strip() or "127.0.0.1"
        args_raw = server.get("runtimeArgs", [])
        if not isinstance(args_raw, list) or not all(isinstance(arg, str) for arg in args_raw):
            raise ValueError(f"{label}[0] runtimeArgs must be an array of strings")
        port = server.get("port")
        if not isinstance(port, int) or isinstance(port, bool):
            raise ValueError(f"{label}[0] port must be an integer")
        if not 1 <= port <= 65535:
            raise ValueError(f"{label}[0] port must be between 1 and 65535")
        if port in seen_ports:
            raise ValueError(f"{label}[0] port {port} duplicates {seen_ports[port]}")
        seen_ports[port] = f"{repo}/{name}"

        # A fixed port is shared by the runner's reuse check and the server bind.
        # Keep the command derived from the registry field rather than a second literal.
        port_token = str(port)
        for arg in args_raw:
            if port_token in arg and "{port}" not in arg:
                raise ValueError(
                    f"{label}[0] hardcodes port {port} in runtimeArgs; "
                    "use the {port} placeholder so the port stays single-source"
                )
        auto_port = server.get("autoPort", False)
        if not isinstance(auto_port, bool):
            raise ValueError(f"{label}[0] autoPort must be a boolean")
        if auto_port:
            raise ValueError(f"{label}[0] autoPort must be false for shared agent previews")

        entries.append(
            {
                "repo": repo,
                "servers": [
                    {
                        "name": name,
                        "host": host,
                        "runtimeExecutable": runtime,
                        "runtimeArgs": [
                            arg.replace("{port}", port_token).replace("{host}", host)
                            for arg in args_raw
                        ],
                        "port": port,
                        "autoPort": False,
                    }
                ],
            }
        )
    return entries


def git_path(path: Path, argument: str) -> Path | None:
    if not path.is_dir():
        return None
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", argument],
        check=False,
        capture_output=True,
        text=True,
    )
    raw = result.stdout.strip()
    if result.returncode != 0 or not raw:
        return None
    return (path / raw).resolve()


def selected_checkouts(
    entries: list[dict[str, Any]],
    github_root: Path,
    repo_filters: set[Path],
) -> list[tuple[dict[str, Any], Path]]:
    """Select registered roots, or explicitly selected linked worktrees of them."""
    filtered_roots: dict[Path, Path] = {}
    for repo in sorted(repo_filters):
        actual = git_path(repo, "--show-toplevel")
        if actual is None:
            print(f"SKIP {repo} (not an available Git checkout)", file=sys.stderr)
            continue
        if actual != repo:
            raise ValueError(f"--repo must name an exact checkout root: {repo} is inside {actual}")
        common_dir = git_path(repo, "--git-common-dir")
        if common_dir is not None:
            filtered_roots[repo] = common_dir

    selected: list[tuple[dict[str, Any], Path]] = []
    for entry in entries:
        repo = resolve_repo_root(entry["repo"], github_root)
        actual = git_path(repo, "--show-toplevel")
        if actual is None:
            if repo.exists():
                print(f"WARNING: skipping existing non-git path: {repo}", file=sys.stderr)
            continue
        if not repo_filters:
            selected.append((entry, actual))
            continue
        common_dir = git_path(actual, "--git-common-dir")
        selected.extend(
            (entry, checkout)
            for checkout, checkout_common in filtered_roots.items()
            if checkout == actual or checkout_common == common_dir
        )
    return selected


def shell_home_path(path: Path) -> str:
    try:
        rel = path.resolve().relative_to(Path.home().resolve())
    except ValueError:
        return str(path)
    return "${HOME}/" + rel.as_posix()


def shell_quote_command_part(part: str) -> str:
    if part.startswith("${HOME}/"):
        return '"' + part.replace('"', '\\"') + '"'
    return shlex.quote(part)


def expand_dev_server_runtime_value(value: str, github_root: Path, repo_root: Path) -> str:
    return value.replace("{github_root}", shell_home_path(github_root)).replace(
        "{repo_root}", shell_home_path(repo_root)
    )


def preview_command_parts(
    server: dict[str, Any],
    preview_runner: Path,
    github_root: Path,
    repo_root: Path,
) -> list[str]:
    wrapped = [
        "python3",
        shell_home_path(preview_runner),
        "--host",
        server["host"],
        "--port",
        str(server["port"]),
        "--",
        expand_dev_server_runtime_value(server["runtimeExecutable"], github_root, repo_root),
        *[
            expand_dev_server_runtime_value(arg, github_root, repo_root)
            for arg in server["runtimeArgs"]
        ],
    ]
    return ["/bin/bash", "-lc", " ".join(shell_quote_command_part(part) for part in wrapped)]


def toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def codex_environment_text(
    entry: dict[str, Any],
    preview_runner: Path,
    github_root: Path,
    repo_root: Path,
) -> str:
    actions: list[str] = []
    for server in entry["servers"]:
        command = " ".join(
            shlex.quote(part)
            for part in preview_command_parts(server, preview_runner, github_root, repo_root)
        )
        actions.append(
            "\n".join(
                [
                    "[[actions]]",
                    f"name = {toml_string(server['name'])}",
                    'icon = "run"',
                    f"command = {toml_string(command)}",
                ]
            )
        )
    return "\n".join(
        [
            "# THIS IS AUTOGENERATED. DO NOT EDIT MANUALLY",
            "version = 1",
            f"name = {toml_string(entry['repo'])}",
            "",
            "[setup]",
            'script = ""',
            "",
            "\n\n".join(actions),
            "",
        ]
    )


def run_sync(args: argparse.Namespace) -> bool:
    registry = Path(args.dev_servers_registry).expanduser().resolve()
    github_root = Path(args.github_root).expanduser().resolve()
    preview_runner = Path(args.preview_runner).expanduser().resolve()
    entries = load_dev_servers(registry)
    repo_filters = {Path(raw).expanduser().resolve() for raw in args.repo}
    selected = selected_checkouts(entries, github_root, repo_filters)
    drift = False
    for entry, repo in selected:
        target = repo / ".codex" / "environments" / "environment.toml"
        desired = codex_environment_text(entry, preview_runner, github_root, repo)
        existing = target.read_text(encoding="utf-8") if target.is_file() else ""
        if existing == desired:
            print(f"UNCHANGED {target}")
            continue
        drift = True
        if args.check:
            print(f"OUT OF SYNC {target} (Codex agent preview environment)", file=sys.stderr)
        else:
            print(f"SYNC {target} (Codex agent preview environment)")
        if args.apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(desired, encoding="utf-8")
    return drift


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render or check per-repo Codex preview environments from the development-server registry."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Write generated preview environments.")
    mode.add_argument("--check", action="store_true", help="Check for drift without writing; exit 1 if out of sync.")
    mode.add_argument("--dry-run", action="store_true", help="Show proposed writes without applying them (default).")
    parser.add_argument(
        "--repo", action="append", default=[],
        help="Limit output to an exact checkout path, including a linked worktree; repeatable.",
    )
    parser.add_argument("--github-root", default=str(Path.home() / "GitHub"), help="Root for registry repo names.")
    parser.add_argument("--dev-servers-registry", default=str(DEFAULT_REGISTRY), help="Canonical development-server registry JSON.")
    parser.add_argument("--preview-runner", default=str(DEFAULT_PREVIEW_RUNNER), help="Shared fixed-port preview runner path.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        drift = run_sync(args)
    except (OSError, ValueError) as exc:
        print(f"Codex preview sync failed: {exc}", file=sys.stderr)
        return 2
    if args.check:
        if drift:
            return 1
        print("Codex preview environments are in sync.")
    elif args.apply:
        print("Apply complete.")
    else:
        print("Dry run complete. Re-run with --apply to write Codex preview environments.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
