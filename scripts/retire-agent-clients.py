#!/usr/bin/env python3
"""Retire generated non-Codex setup; this is a migration, not a client renderer.

Ownership constants intentionally survive deletion of the retired renderers and
overlays. Private histories, credentials, skill sources, and unknown settings are
never cleanup targets. Bootstrap may run this repeatedly on either machine.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import datetime as dt
import json
import os
from pathlib import Path
import plistlib
import pwd
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from hooks.scripts.stop import register_current_codex_transaction_paths  # noqa: E402

CLAUDE_ALLOW = {
    "Agent", "Bash", "Edit", "Glob", "Grep", "LS", "MultiEdit", "NotebookEdit",
    "Read", "Task", "TodoWrite", "WebFetch", "WebSearch", "Workflow", "Write",
}
CLAUDE_OVERRIDES = {
    "fewer-permission-prompts", "keybindings-help", "loop", "review",
    "security-review", "init", "code-review", "simplify", "verify", "run",
    "schedule", "update-config",
}
COPILOT_KEYS = {
    "askUser", "autoUpdate", "banner", "beep", "effortLevel", "ide.autoConnect",
    "ide.openDiffOnEdit", "memory", "notifications", "showTipsOnStartup",
}
COPILOT_DISABLED_SKILLS = {
    "af", "agent-merge", "agentfinder", "create-canvas", "customize-cloud-agent",
}
MCP_HTTP = {
    "openaiDeveloperDocs": "https://developers.openai.com/mcp",
    "cloudflare-api": "https://mcp.cloudflare.com/mcp",
    "cloudflare-docs": "https://docs.mcp.cloudflare.com/mcp",
    "figma": "http://127.0.0.1:3845/mcp",
}
JOBS = {
    "claude-session-archiver": "codex/scripts/archive-stale-claude-sessions.py",
    "claude-session-finalizer": "codex/scripts/finalize-stale-claude-sessions.py",
    "copilot-session-pruner": "scripts/prune-stale-copilot-sessions.py",
}


def expand_path(raw: str, home: Path) -> Path:
    if raw == "~":
        return home
    if raw.startswith("~/"):
        return home / raw[2:]
    return Path(raw).absolute()


def parse_json(text: str, path: Path) -> dict[str, Any]:
    """Accept JSONC used by Copilot/VS Code without altering strings or URLs."""
    result: list[str] = []
    i = 0
    in_string = False
    escaped = False
    while i < len(text):
        char = text[i]
        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            i += 1
        elif char == '"':
            in_string = True
            result.append(char)
            i += 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise ValueError(f"Unterminated JSON comment: {path}")
            result.append(" ")
            i = end + 2
        else:
            result.append(char)
            i += 1
    # Comments may sit between a trailing comma and the closing delimiter.
    # Remove commas only after comment stripping, still respecting JSON strings.
    uncommented = "".join(result)
    result = []
    in_string = escaped = False
    for i, char in enumerate(uncommented):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == ",":
            j = i + 1
            while j < len(uncommented) and uncommented[j].isspace():
                j += 1
            if j < len(uncommented) and uncommented[j] in "}]":
                continue
        result.append(char)
    try:
        data = json.loads("".join(result))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError(f"Invalid JSON object: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def prune_keys(data: dict[str, Any], keys: set[str]) -> None:
    for key in keys:
        data.pop(key, None)


def prune_list(data: dict[str, Any], key: str, owned: Callable[[Any], bool]) -> None:
    current = data.get(key)
    if not isinstance(current, list):
        return
    kept = [item for item in current if not owned(item)]
    if kept == current:
        return
    if kept:
        data[key] = kept
    else:
        data.pop(key)


def prune_nested(data: dict[str, Any], key: str, keys: set[str]) -> None:
    nested = data.get(key)
    if isinstance(nested, dict):
        prune_keys(nested, keys)
        if not nested:
            data.pop(key)


def protected_preference(key: str, value: Any) -> bool:
    """Preserve credential-bearing and Codex fields even in a retired namespace."""
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    if any(part in normalized for part in ("auth", "token", "secret", "password", "credential", "apikey", "privatekey", "keychain", "codex", "chatgpt")):
        return True
    if key.lower() in {"env", "headers"}:
        return True
    if isinstance(value, dict):
        return any(protected_preference(child, item) for child, item in value.items())
    if isinstance(value, list):
        return any(protected_preference("", item) for item in value)
    return False


def prune_retired_editor_preferences(data: dict[str, Any]) -> None:
    retired_host_keys = {"claudeMultiRootEnabled", "copilotMultiRootEnabled", "copilotSdkLogLevel", "migrateLegacyCopilotCliEnabled"}
    for key, value in list(data.items()):
        retired = key in retired_host_keys or key == "github.copilot" or key.startswith(("github.copilot.", "claudeAgent."))
        if retired and not protected_preference(key, value):
            data.pop(key)


@dataclass
class Change:
    path: Path
    before: bytes | str
    after: bytes | None = None
    label: str | None = None


class Retirement:
    def __init__(self, home: Path, github_root: Path, repos: list[dict[str, Any]],
                 repo_filters: set[Path] | None = None):
        self.home = home
        self.github_root = github_root
        self.repos = repos
        self.repo_filters = repo_filters or set()
        self.control_roots = {ROOT, home / "GitHub/agents", github_root / "agents"}
        self.trusted = {home / ".agents", github_root, *self.control_roots}
        self.trusted.update(entry["root"] for entry in repos)
        self.changes: list[Change] = []
        self.backup_dir: Path | None = None

    def safe_path(self, path: Path) -> bool:
        # Never traverse a directory symlink into an unrelated settings tree.
        for parent in path.parents:
            if parent.is_symlink():
                return False
        return True

    def snapshot(self, path: Path) -> bytes | str | None:
        if not self.safe_path(path):
            return None
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            return None
        if stat.S_ISLNK(mode):
            return os.readlink(path)
        if not stat.S_ISREG(mode):
            return None
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as source:
            return source.read()

    def remove_file(self, path: Path, predicate: Callable[[str], bool] | None = None,
                    label: str | None = None) -> None:
        current = self.snapshot(path)
        if not isinstance(current, bytes):
            return
        if predicate is not None:
            try:
                if not predicate(current.decode("utf-8")):
                    return
            except UnicodeError:
                return
        self.changes.append(Change(path, current, label=label))

    def remove_link(self, path: Path, owned: Callable[[Path], bool]) -> None:
        current = self.snapshot(path)
        if isinstance(current, str):
            target = (path.parent / current).resolve()
            if owned(target):
                self.changes.append(Change(path, current))

    def edit_json(self, path: Path, edit: Callable[[dict[str, Any]], None],
                  metadata: dict[str, Any] | None = None) -> None:
        current = self.snapshot(path)
        if not isinstance(current, bytes):
            return
        try:
            data = parse_json(current.decode("utf-8"), path)
        except UnicodeError as exc:
            raise ValueError(f"Invalid JSON encoding: {path}") from exc
        desired = copy.deepcopy(data)
        edit(desired)
        if desired == data:
            return
        # Remove an empty generated envelope only after an owned value changed.
        for key, value in (metadata or {}).items():
            if desired.get(key) == value:
                desired.pop(key)
        after = (json.dumps(desired, indent=2, ensure_ascii=False) + "\n").encode() if desired else None
        self.changes.append(Change(path, current, after))

    def owned_trust(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        path = expand_path(value, self.home)
        # The retired Copilot renderer seeded every direct child of GitHub.
        return path in self.trusted or path.parent == self.github_root

    def owned_hook(self, hook: Any) -> bool:
        if not isinstance(hook, dict):
            return False
        command = hook.get("command", hook.get("bash"))
        if not isinstance(command, str):
            return False
        command = command.replace("${HOME}", str(self.home)).replace("$HOME", str(self.home)).replace("~/", str(self.home) + "/")
        roots = [root / "hooks/scripts" for root in self.control_roots]
        roots.append(self.home / ".agents/hooks/scripts")
        def script_token(path: Path) -> bool:
            return re.search(r"(?:^|[\s\"'])" + re.escape(str(path)) + r"(?=$|[\s\"';])", command) is not None
        for root in roots:
            if any(script_token(root / name) for name in ("claude_stop.py", "antigravity_stop.py")):
                return True
            if re.search(r"--runtime[ =]+(?:claude|copilot)(?:[\s\"']|$)", command):
                if any(script_token(root / name) for name in ("session_start.py", "user_prompt_submit.py", "stop.py")):
                    return True
        return False

    def prune_hooks(self, data: dict[str, Any]) -> None:
        events = data.get("hooks")
        if not isinstance(events, dict):
            return
        for event, entries in list(events.items()):
            if not isinstance(entries, list):
                continue
            kept: list[Any] = []
            for entry in entries:
                if self.owned_hook(entry):
                    continue
                if isinstance(entry, dict) and isinstance(entry.get("hooks"), list):
                    handlers = entry["hooks"]
                    remaining = [hook for hook in handlers if not self.owned_hook(hook)]
                    if remaining != handlers:
                        if remaining:
                            kept.append({**entry, "hooks": remaining})
                        continue
                kept.append(entry)
            if kept != entries:
                if kept:
                    events[event] = kept
                else:
                    events.pop(event)
        if not events:
            data.pop("hooks", None)

    def prune_mcp(self, data: dict[str, Any]) -> None:
        servers = data.get("mcpServers")
        if not isinstance(servers, dict):
            return
        for name, server in list(servers.items()):
            if not isinstance(server, dict):
                continue
            expected = {"type": "http", "url": MCP_HTTP[name]} if name in MCP_HTTP else None
            if name == "playwright":
                expected = {"type": "local", "command": "npx", "args": ["-y", "@playwright/mcp@latest"]}
            # Same-name custom endpoints/options are not evidence of ownership.
            if expected is not None and server in (expected, {**expected, "tools": ["*"]}):
                servers.pop(name)
        if not servers:
            data.pop("mcpServers", None)

    def skills(self, directory: Path, repo: Path | None = None) -> None:
        if not self.safe_path(directory / "placeholder") or not directory.is_dir():
            return
        roots = [root / child for root in self.control_roots for child in ("skills-source", "plugins-source")]
        roots.append(self.home / ".agents/skills")
        if repo is not None:
            roots.append(repo / ".agents/skills")
        for path in sorted(directory.iterdir()):
            self.remove_link(path, lambda target: any(target.is_relative_to(root) for root in roots))

    def repo(self, entry: dict[str, Any]) -> None:
        root = entry["root"]
        if not root.is_dir() or root.is_symlink() or (self.repo_filters and root not in self.repo_filters):
            return
        identity = entry.get("model_instructions_file")
        identity_reference = None
        if isinstance(identity, str) and identity:
            identity_reference = Path(os.path.abspath(root / ".codex" / identity))
        for relative in ("CLAUDE.md", ".claude/CLAUDE.md", ".github/copilot-instructions.md"):
            guidance = root / relative
            # The identity route must keep working even if it is itself a link.
            if guidance == identity_reference:
                continue
            # A guidance symlink is setup, its destination remains private source.
            self.remove_link(guidance, lambda target: True)
            self.remove_file(guidance)
        # Dedicated preview configurations have no credentials/history ownership.
        self.remove_file(root / ".claude/launch.json")
        self.remove_file(root / ".github/github-app.yml", lambda text: text.startswith("# THIS IS AUTOGENERATED. DO NOT EDIT MANUALLY.\n") and "# Source: ~/GitHub/agents/dev-servers/registry.json" in text)
        def repo_settings(data: dict[str, Any]) -> None:
            # Repository permissions/hooks are dedicated retired-client setup.
            # Keep env/auth and any unknown content instead of deleting blindly.
            prune_keys(data, {"permissions", "hooks", "autoMemoryEnabled", "enableAllProjectMcpServers", "enabledMcpjsonServers", "disabledMcpjsonServers"})
        for filename in ("settings.json", "settings.local.json"):
            self.edit_json(root / ".claude" / filename, repo_settings, {"$schema": "https://json.schemastore.org/claude-code-settings.json"})
        for target in (root / ".mcp.json", root / ".github/mcp.json"):
            self.edit_json(target, self.prune_mcp)
        for relative in (".claude/skills", ".github/skills"):
            self.skills(root / relative, root)

    def claude_settings(self, data: dict[str, Any]) -> None:
        prune_keys(data, {"skipDangerousModePermissionPrompt", "skipAutoPermissionPrompt", "skipWorkflowUsageWarning", "enableAllProjectMcpServers", "includeGitInstructions"})
        if data.get("effortLevel") == "high":
            data.pop("effortLevel")
        permissions = data.get("permissions")
        if isinstance(permissions, dict):
            prune_list(permissions, "allow", lambda item: isinstance(item, str) and item in CLAUDE_ALLOW)
            prune_list(permissions, "additionalDirectories", self.owned_trust)
            prune_keys(permissions, {"defaultMode", "skipDangerousModePermissionPrompt"})
            if not permissions:
                data.pop("permissions")
        prune_nested(data, "enabledPlugins", {"anthropic-skills@inline"})
        prune_nested(data, "skillOverrides", CLAUDE_OVERRIDES)
        prune_list(data, "sshConfigs", lambda item: isinstance(item, dict) and item.get("id") == "macmini")
        self.prune_hooks(data)

    def claude_state(self, data: dict[str, Any]) -> None:
        if data.get("autoUpdates") is False:
            data.pop("autoUpdates")
        projects = data.get("projects")
        if isinstance(projects, dict):
            for path, entry in list(projects.items()):
                if self.owned_trust(path) and isinstance(entry, dict):
                    prune_keys(entry, {"hasTrustDialogAccepted", "hasCompletedProjectOnboarding"})
                    if not entry:
                        projects.pop(path)
            if not projects:
                data.pop("projects")

    def copilot_settings(self, data: dict[str, Any]) -> None:
        prune_keys(data, COPILOT_KEYS)
        prune_list(data, "disabledSkills", lambda item: isinstance(item, str) and item in COPILOT_DISABLED_SKILLS)
        tabs = data.get("tabs")
        if isinstance(tabs, dict):
            prune_list(tabs, "hide", lambda item: item in ("issues", "pull-requests", "gists"))
            if not tabs:
                data.pop("tabs")
        prune_list(data, "trustedFolders", self.owned_trust)

    def globals(self) -> None:
        guidance_sources = {root / "config/global.agents.md" for root in self.control_roots}
        for relative in (".claude/CLAUDE.md", ".copilot/copilot-instructions.md", ".gemini/GEMINI.md"):
            self.remove_link(self.home / relative, lambda target: target in guidance_sources)
        for relative in (".claude/skills", ".copilot/skills", ".gemini/antigravity-cli/skills"):
            self.skills(self.home / relative)
        for client, markers in {
            "claude": ("CLAUDE_REAL_BIN:-$default_real_cli", "claude launcher cannot find executable real CLI:", 'exec "$real_cli" --dangerously-skip-permissions "$@"'),
            "copilot": ("COPILOT_REAL_CLI_PATH:-", "managed Copilot launcher cannot find executable:", "COPILOT_DISABLE_MANAGED_DEFAULTS"),
            "agy": ("AGY_REAL_BIN:-$default_real_cli", "agy launcher cannot find executable real CLI:", 'exec "$real_cli" --dangerously-skip-permissions "$@"'),
        }.items():
            self.remove_file(self.home / "bin" / client, lambda text, markers=markers: text.startswith("#!/usr/bin/env bash\nset -euo pipefail\n") and all(marker in text for marker in markers))
        self.edit_json(self.home / ".claude/settings.json", self.claude_settings, {"$schema": "https://json.schemastore.org/claude-code-settings.json"})
        self.edit_json(self.home / ".claude.json", self.claude_state)
        self.edit_json(self.home / "Library/Application Support/Claude/config.json", lambda data: data.pop("chromeExtensionEnabled", None))
        self.edit_json(self.home / ".copilot/settings.json", self.copilot_settings)
        self.edit_json(self.home / ".copilot/config.json", lambda data: prune_list(data, "trustedFolders", self.owned_trust))
        self.edit_json(self.home / ".copilot/mcp-config.json", self.prune_mcp)
        self.edit_json(self.home / ".copilot/hooks/agents-control-plane.json", self.prune_hooks, {"version": 1})
        self.edit_json(self.home / ".gemini/config/hooks.json", self.prune_hooks)
        def antigravity_settings(data: dict[str, Any]) -> None:
            if data.get("toolPermission") == "always-proceed":
                data.pop("toolPermission")
            prune_list(data, "trustedWorkspaces", self.owned_trust)
        self.edit_json(self.home / ".gemini/antigravity-cli/settings.json", antigravity_settings)
        def vscode_host(data: dict[str, Any]) -> None:
            prune_keys(data, {"globalAutoApproveEnabled", "autoReplyEnabled", "terminalAutoApproveEnabled"})
            prune_nested(data, "terminalAutoApproveRules", {"curl", "/.*/"})
            prune_retired_editor_preferences(data)
        self.edit_json(self.home / ".vscode-server/data/User/globalStorage/agent-host-config.json", vscode_host)
        def vscode_settings(data: dict[str, Any]) -> None:
            prune_keys(data, {"chat.permissions.default", "chat.tools.global.autoApprove", "chat.useAgentSkills", "github.copilot.chat.githubMcpServer.enabled"})
            prune_nested(data, "chat.defaultConfiguration", {"approvals", "mode"})
            prune_nested(data, "chat.mcp.discovery.enabled", {"claude-desktop", "windsurf", "cursor-global", "cursor-workspace"})
            prune_retired_editor_preferences(data)
        self.edit_json(self.home / "Library/Application Support/Code/User/settings.json", vscode_settings)

    def jobs(self) -> None:
        directory = self.home / "Library/LaunchAgents"
        if not self.safe_path(directory / "placeholder") or not directory.is_dir():
            return
        for path in sorted(directory.glob("*.plist")):
            suffix = next((name for name in JOBS if path.name.endswith("." + name + ".plist")), None)
            if suffix is None:
                continue
            current = self.snapshot(path)
            if not isinstance(current, bytes):
                continue
            try:
                data = plistlib.loads(current)
            except plistlib.InvalidFileException as exc:
                raise ValueError(f"Invalid retired-job plist: {path}") from exc
            if not isinstance(data, dict):
                raise ValueError(f"Expected retired-job plist dictionary: {path}")
            expected_scripts = {str(root / JOBS[suffix]) for root in self.control_roots}
            args = data.get("ProgramArguments", [])
            if data.get("Label") == path.stem and isinstance(args, list) and args and args[0] in expected_scripts:
                self.changes.append(Change(path, current, label=path.stem))

    def plan(self) -> None:
        self.jobs()
        self.globals()
        for entry in self.repos:
            self.repo(entry)

    def backup(self, change: Change) -> None:
        if self.backup_dir is None:
            base = self.home / ".local/state/agents-control-plane/retired-client-backups"
            if not self.safe_path(base / "placeholder"):
                raise ValueError("Refusing symlinked retirement backup directory")
            base.mkdir(parents=True, exist_ok=True, mode=0o700)
            base.chmod(0o700)
            prefix = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ-")
            self.backup_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=base))
        target = self.backup_dir / change.path.as_posix().lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        content = change.before if isinstance(change.before, bytes) else json.dumps({"symlink": change.before}).encode()
        if isinstance(change.before, str):
            target = target.with_name(target.name + ".symlink.json")
        with target.open("xb") as backup:
            os.chmod(target, 0o600)
            backup.write(content)

    def unload(self, label: str, path: Path) -> None:
        # --home fixtures must NEVER unload the real account's jobs, even if
        # HOME was overridden by the test runner. Consult the account database.
        actual_home = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
        if self.home.resolve() != actual_home or sys.platform != "darwin":
            return
        domain = f"gui/{os.getuid()}"
        status = subprocess.run(["/bin/launchctl", "print", f"{domain}/{label}"], capture_output=True, text=True, timeout=15, check=False)
        if status.returncode != 0:
            if "Could not find service" in status.stderr:
                return
            raise RuntimeError(f"Cannot inspect retired LaunchAgent: {label}")
        result = subprocess.run(["/bin/launchctl", "bootout", domain, str(path)], capture_output=True, text=True, timeout=15, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Cannot unload retired LaunchAgent: {label}")

    def apply(self) -> None:
        touched: set[Path] = set()
        try:
            for change in self.changes:
                if self.snapshot(change.path) != change.before:
                    raise RuntimeError(f"File changed after retirement planning: {change.path}")
                self.backup(change)
                if change.label is not None:
                    self.unload(change.label, change.path)
                if change.after is None:
                    change.path.unlink()
                else:
                    mode = stat.S_IMODE(change.path.stat().st_mode)
                    fd, name = tempfile.mkstemp(prefix=".retire-client-", dir=change.path.parent)
                    try:
                        with os.fdopen(fd, "wb") as output:
                            output.write(change.after)
                            os.fchmod(output.fileno(), mode)
                        os.replace(name, change.path)
                    finally:
                        Path(name).unlink(missing_ok=True)
                touched.add(change.path)
        finally:
            # Runtime settings/backups never enter publication, even if a legacy
            # checkout surrounds the user's home. Include partial successful work.
            repo_touched = {path for path in touched if any(path.is_relative_to(entry["root"]) for entry in self.repos)}
            if repo_touched:
                registered = register_current_codex_transaction_paths(repo_touched)
                for root, item in sorted(registered.items()):
                    print(f"REGISTER CODEX STOP {root}: {' '.join(sorted(item.paths))}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Back up and retire owned setup.")
    mode.add_argument("--check", action="store_true", help="Exit 1 while owned setup remains; never write.")
    mode.add_argument("--dry-run", action="store_true", help="Report planned paths without writing (default).")
    parser.add_argument("--home", default=str(Path.home()), help="Target home; non-account homes disable launchctl.")
    parser.add_argument("--github-root", help="Target GitHub root (default: HOME/GitHub).")
    parser.add_argument("--repo-registry", default=str(ROOT / "codex/config/repo-bootstrap.json"))
    parser.add_argument("--repo", action="append", default=[], help="Exact managed repo path; repeatable. Global cleanup still runs.")
    args = parser.parse_args(argv)
    try:
        home = Path(args.home).expanduser().resolve()
        github_root = (expand_path(args.github_root, home) if args.github_root else home / "GitHub").resolve()
        registry = expand_path(args.repo_registry, home)
        entries = parse_json(registry.read_text(encoding="utf-8"), registry).get("repos")
        if not isinstance(entries, list):
            raise ValueError(f"Missing repos array: {registry}")
        repos = []
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not entry["path"]:
                raise ValueError(f"Invalid repo entry: {registry}")
            raw = entry["path"]
            root = github_root / raw[len("~/GitHub/"):] if raw.startswith("~/GitHub/") else expand_path(raw, home)
            repos.append({**entry, "root": root})
        filters = {expand_path(raw, home) for raw in args.repo}
        if filters - {entry["root"] for entry in repos}:
            raise ValueError("--repo must exactly match a managed repo path")
        retirement = Retirement(home, github_root, repos, filters)
        retirement.plan()
        for change in retirement.changes:
            print(f"{'UPDATE' if change.after is not None else 'REMOVE'} {change.path}")
        if args.apply:
            retirement.apply()
        print(f"{'APPLIED' if args.apply else 'PENDING' if retirement.changes else 'PASS'}: {len(retirement.changes)} retired-client setup change(s)")
        if retirement.backup_dir is not None:
            print(f"BACKUP {retirement.backup_dir}")
        return 1 if args.check and retirement.changes else 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
