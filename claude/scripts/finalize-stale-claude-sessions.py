#!/usr/bin/env python3
"""Finalize idle Claude Code sessions in managed repos.

Claude twin of `codex/scripts/finalize-stale-codex-threads.py`. Claude has no
App Server to list threads, so this scans each enabled repo's transcript folder
(`~/.claude/projects/<munged-repo-path>/<session-id>.jsonl`). A session is a
candidate when its transcript has been idle past the cutoff, it came from an
interactive entrypoint (Claude Desktop or the CLI, not `claude -p` automation),
no live process is still using it (a `~/.claude/sessions/<pid>.json` handshake
that is busy or went idle after the cutoff; desktop keeps idle sessions alive), and
the per-machine ledger has not already finalized it.

For each candidate it runs the repo's own policy hook,
`scripts/hooks/finalize_claude_session.py`, with a `FinalizeClaudeSession`
payload. Repos without that hook are not scanned. The ledger records a session
only after the hook succeeds, so each session is finalized at most once;
failures are retried up to `--max-attempts` runs.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))
from repos.repo_registry import enabled_repositories, load_registry  # noqa: E402

SCHEMA_VERSION = "1.0"
COMMAND = "finalize-stale-claude-sessions"
HOOK_EVENT = "FinalizeClaudeSession"
REPO_HOOK = Path("scripts/hooks/finalize_claude_session.py")
INTERACTIVE_ENTRYPOINTS = frozenset({"claude-desktop", "cli"})
DEFAULT_OLDER_THAN_HOURS = 6.0
DEFAULT_MAX_SESSIONS = 4
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_HOOK_TIMEOUT_SECONDS = 1200.0
STATE_DIR = Path.home() / ".local" / "state" / "claude-control-plane"
DEFAULT_LEDGER = STATE_DIR / "finalized-claude-sessions.json"
DEFAULT_LOCK = STATE_DIR / "finalize-stale-claude-sessions.lock"
DEFAULT_REGISTRY = ROOT_DIR / "repos" / "registry.json"
DEFAULT_PROJECTS_DIR = Path.home() / ".claude" / "projects"
DEFAULT_SESSIONS_DIR = Path.home() / ".claude" / "sessions"
MAX_ERROR_CHARS = 4000


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def munge_project_dir(repo: Path) -> str:
    """Claude names a project folder after its cwd with every non-alphanumeric as '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(repo))


def load_ledger(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"schemaVersion": 1, "sessions": {}}
    if not isinstance(data, dict) or not isinstance(data.get("sessions"), dict):
        return {"schemaVersion": 1, "sessions": {}}
    return data


def save_ledger(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def active_session_ids(sessions_dir: Path, cutoff: float) -> set[str]:
    """Sessions a live process is still using.

    Claude Desktop keeps a process alive for every open session, often for days,
    so a live pid alone does not mean the session is in use. A handshake blocks
    finalization only while it is not idle or went idle after the cutoff.
    """
    active: set[str] = set()
    for handshake in sessions_dir.glob("*.json"):
        try:
            data = json.loads(handshake.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        session_id = data.get("sessionId")
        pid = data.get("pid")
        if not (isinstance(session_id, str) and isinstance(pid, int) and pid_alive(pid)):
            continue
        status_at = data.get("statusUpdatedAt") or data.get("updatedAt") or 0
        idle_since = status_at / 1000 if isinstance(status_at, (int, float)) else 0
        if data.get("status") != "idle" or idle_since > cutoff:
            active.add(session_id)
    return active


def transcript_entrypoints(path: Path, *, max_lines: int = 200) -> set[str]:
    """Entrypoints from the opening lines; later `claude -p --resume` turns don't count."""
    found: set[str] = set()
    try:
        with path.open(encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if index >= max_lines:
                    break
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                value = entry.get("entrypoint") if isinstance(entry, dict) else None
                if isinstance(value, str):
                    found.add(value)
                    break
    except OSError:
        pass
    return found


def managed_repos(registry_path: Path, only: list[str]) -> list[Path]:
    repos: list[Path] = []
    seen: set[Path] = set()
    for entry in enabled_repositories(load_registry(registry_path)):
        raw = entry.get("path")
        if not isinstance(raw, str) or not raw.strip():
            continue
        path = Path(os.path.expanduser(raw.strip())).resolve()
        if path in seen:
            continue
        seen.add(path)
        repos.append(path)
    if only:
        wanted = {Path(os.path.expanduser(item)).resolve() for item in only}
        repos = [repo for repo in repos if repo in wanted]
    return [repo for repo in repos if (repo / REPO_HOOK).is_file()]


def list_candidates(
    *,
    repos: list[Path],
    projects_dir: Path,
    sessions_dir: Path,
    ledger: dict[str, Any],
    cutoff: float,
    max_attempts: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    live = active_session_ids(sessions_dir, cutoff)
    candidates: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for repo in repos:
        folder = projects_dir / munge_project_dir(repo)
        for transcript in sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime):
            session_id = transcript.stem
            record = ledger["sessions"].get(session_id) or {}
            if record.get("status") in {"finalized", "marked", "not-interactive"}:
                continue
            if record.get("status") == "failed" and int(record.get("attempts", 0)) >= max_attempts:
                continue
            mtime = transcript.stat().st_mtime
            base = {"sessionId": session_id, "repo": str(repo), "transcript": str(transcript), "idleSince": datetime.fromtimestamp(mtime, UTC).isoformat(timespec="seconds")}
            if mtime > cutoff:
                skipped.append({**base, "reason": "recent"})
                continue
            if session_id in live:
                skipped.append({**base, "reason": "active"})
                continue
            entrypoints = transcript_entrypoints(transcript)
            if entrypoints and not entrypoints & INTERACTIVE_ENTRYPOINTS:
                candidates.append({**base, "action": "not-interactive", "entrypoints": sorted(entrypoints)})
                continue
            candidates.append({**base, "action": "finalize"})
    return candidates, skipped


def run_repo_hook(repo: Path, session_id: str, timeout: float) -> tuple[bool, str]:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "hook_event_name": HOOK_EVENT,
        "session_id": session_id,
        "cwd": str(repo),
        "reason": "stale-cleanup",
    }
    try:
        result = subprocess.run(
            [sys.executable, str(repo / REPO_HOOK)],
            cwd=repo,
            input=json.dumps(payload),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return False, f"repo hook timed out after {exc.timeout}s"
    except OSError as exc:
        return False, f"repo hook failed to start: {exc}"
    if result.returncode != 0:
        output = "\n".join(part for part in (result.stderr, result.stdout) if part.strip())
        return False, (output or f"repo hook exited {result.returncode}")[-MAX_ERROR_CHARS:]
    return True, ""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Finalize eligible sessions.")
    mode.add_argument("--dry-run", action="store_true", help="Only report eligible sessions (default).")
    mode.add_argument("--mark-only", action="store_true", help="Record eligible sessions as handled without running repo hooks (absorb a backlog).")
    parser.add_argument("--older-than-hours", type=float, default=DEFAULT_OLDER_THAN_HOURS)
    parser.add_argument("--max-sessions", type=int, default=DEFAULT_MAX_SESSIONS, help="Maximum sessions to finalize per run; 0 means unlimited.")
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--hook-timeout-seconds", type=float, default=DEFAULT_HOOK_TIMEOUT_SECONDS)
    parser.add_argument("--repo", action="append", default=[], help="Limit to an exact repo path. Repeatable.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--projects-dir", type=Path, default=DEFAULT_PROJECTS_DIR)
    parser.add_argument("--sessions-dir", type=Path, default=DEFAULT_SESSIONS_DIR)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--now", type=float, help="Override current epoch seconds (tests).")
    parser.add_argument("--json", action="store_true", help="Emit a JSON envelope.")
    parser.add_argument("--plain", action="store_true", help="Emit compact plain text (default).")
    parser.add_argument("--no-input", action="store_true", help="Accepted for non-interactive callers.")
    return parser.parse_args(argv)


def emit(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    data = payload["data"]
    print(f"{payload['status']} mode={data['mode']} candidates={len(data['candidates'])} finalized={data['finalized']} failed={data['failed']} skipped={len(data['skipped'])}")
    for item in data["candidates"]:
        print(f"  {item.get('result', item['action'])} {item['sessionId']} repo={item['repo']} idleSince={item['idleSince']}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    mode = "apply" if args.apply else "mark-only" if args.mark_only else "dry-run"
    args.lock.parent.mkdir(parents=True, exist_ok=True)
    with args.lock.open("w") as lock_handle:
        try:
            fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"{COMMAND}: another run holds {args.lock}", file=sys.stderr)
            return 0
        return run(args, mode)


def run(args: argparse.Namespace, mode: str) -> int:
    now = args.now if args.now is not None else time.time()
    cutoff = now - args.older_than_hours * 3600
    ledger = load_ledger(args.ledger)
    repos = managed_repos(args.registry, args.repo)
    candidates, skipped = list_candidates(
        repos=repos,
        projects_dir=args.projects_dir,
        sessions_dir=args.sessions_dir,
        ledger=ledger,
        cutoff=cutoff,
        max_attempts=args.max_attempts,
    )

    finalized = failed = 0
    budget = args.max_sessions if args.max_sessions > 0 else len(candidates)
    for item in candidates:
        session_id = item["sessionId"]
        entry = ledger["sessions"].get(session_id) or {}
        if mode == "dry-run":
            continue
        if item["action"] == "not-interactive":
            ledger["sessions"][session_id] = {"status": "not-interactive", "repo": item["repo"], "at": utc_now()}
            item["result"] = "not-interactive"
        elif mode == "mark-only":
            ledger["sessions"][session_id] = {"status": "marked", "repo": item["repo"], "at": utc_now()}
            item["result"] = "marked"
        elif budget <= 0:
            item["result"] = "deferred"
            continue
        else:
            budget -= 1
            ok, error = run_repo_hook(Path(item["repo"]), session_id, args.hook_timeout_seconds)
            attempts = int(entry.get("attempts", 0)) + 1
            if ok:
                finalized += 1
                ledger["sessions"][session_id] = {"status": "finalized", "repo": item["repo"], "at": utc_now(), "attempts": attempts}
                item["result"] = "finalized"
            else:
                failed += 1
                ledger["sessions"][session_id] = {"status": "failed", "repo": item["repo"], "at": utc_now(), "attempts": attempts, "error": error}
                item["result"] = "failed"
                item["error"] = error
        save_ledger(args.ledger, ledger)

    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "command": COMMAND,
        "status": "error" if failed else "ok",
        "data": {
            "mode": mode,
            "olderThanHours": args.older_than_hours,
            "repos": [str(repo) for repo in repos],
            "candidates": candidates,
            "skipped": skipped,
            "finalized": finalized,
            "failed": failed,
            "ledger": str(args.ledger),
        },
    }
    emit(args, payload)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
