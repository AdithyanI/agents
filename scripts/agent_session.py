"""Subscription-only, noninteractive native client sessions for repo automation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from claude.control_plane import desktop_engine
from codex.runtime import available_codex_executable

# Clear inference credentials/routes only in child environments. Tools may still
# need unrelated service credentials, and the caller's environment stays intact.
INFERENCE_OVERRIDES = frozenset({
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_BASE", "OPENAI_API_HOST",
    "CODEX_API_KEY", "CODEX_ACCESS_TOKEN", "CODEX_INTERNAL_ORIGINATOR_OVERRIDE",
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
    "ANTHROPIC_CUSTOM_HEADERS", "ANTHROPIC_FOUNDRY_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR", "CLAUDE_CODE_SESSION_ACCESS_TOKEN",
    "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_API_KEY_FILE_DESCRIPTOR", "CLAUDE_CODE_SIMPLE",
})
CLAUDE_SETTINGS = {
    "forceLoginMethod": "claudeai", "apiKeyHelper": "",
    # Settings can otherwise reintroduce credentials stripped from the process
    # environment. Apply the same override to auth status and inference.
    "env": {key: ("0" if key.startswith("CLAUDE_CODE_USE_") else "")
            for key in INFERENCE_OVERRIDES if key.startswith(("ANTHROPIC_", "CLAUDE_CODE_"))},
}


class SessionError(Exception):
    def __init__(self, code: str, message: str, exit_code: int, hint: str = "", retryable: bool = False):
        self.code, self.message, self.exit_code = code, message, exit_code
        self.hint, self.retryable = hint, retryable
        super().__init__(message)


def child_environment(environ=None):
    return {key: value for key, value in (os.environ if environ is None else environ).items()
            if key not in INFERENCE_OVERRIDES}


def resolve_client(client: str) -> str:
    if client == "codex":
        executable = available_codex_executable()
    else:
        override = os.environ.get("AGENTS_CLAUDE_BIN", "").strip()
        executable = shutil.which(override) if override else str(desktop_engine() or shutil.which("claude") or "")
    if not executable:
        raise SessionError("E_CLIENT", f"The requested {client} client is unavailable.", 4,
                           "Install or repair this client; no other client was attempted.")
    return executable


def client_prefix(client: str, executable: str) -> list[str]:
    if client == "codex":
        return [executable, "-c", 'model_provider="openai"']
    return [executable, "--settings", json.dumps(CLAUDE_SETTINGS, separators=(",", ":"))]


def require_subscription(client: str, prefix: list[str], cwd: Path, environ: dict[str, str]) -> str:
    # Check before adding forced_login_method: incompatible Codex login enforcement
    # may log out an API-key account. Rejection here leaves its auth state alone.
    command = prefix + (["login", "status"] if client == "codex" else ["auth", "status", "--json"])
    try:
        status = subprocess.run(command, cwd=cwd, env=environ, stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise SessionError("E_AUTH_STATUS", "The client could not verify subscription login.", 3,
                           "Check this client's login status manually; no login was started.") from None
    accepted = False
    method = "chatgpt" if client == "codex" else "claude.ai"
    if client == "codex":
        lines = (status.stdout + "\n" + status.stderr).lower().splitlines()
        accepted = status.returncode == 0 and any(line.strip() == "logged in using chatgpt" for line in lines)
    else:
        try:
            value = json.loads(status.stdout)
            accepted = (status.returncode == 0 and isinstance(value, dict)
                        and value.get("loggedIn") is True and value.get("authMethod") == "claude.ai"
                        and value.get("apiProvider") == "firstParty"
                        and value.get("subscriptionType") in {"pro", "max", "team", "enterprise"})
        except (ValueError, TypeError):
            pass
    if not accepted:
        raise SessionError("E_SUBSCRIPTION_REQUIRED", f"{client} is not verified as using a subscription login.", 3,
                           "Sign in to this client with the intended subscription account, then use new attempt paths. API billing is not supported.")
    return method


def session_command(args, prefix: list[str]) -> list[str]:
    if args.client == "codex":
        command = prefix + ["-c", 'forced_login_method="chatgpt"',
                            "-c", 'chatgpt_base_url="https://chatgpt.com/backend-api/"',
                            "-c", 'approval_policy="never"']
        if args.effort:
            command += ["-c", "model_reasoning_effort=" + json.dumps(args.effort)]
        command += ["exec", "--json", "--color", "never", "--cd", str(args.cwd),
                    "--sandbox", "danger-full-access" if args.trusted else "read-only"]
        if args.model:
            command += ["--model", args.model]
        return command + ["-"]
    command = prefix + ["--print", "--output-format", "stream-json", "--verbose",
                        "--permission-prompts", "none"]
    command += (["--dangerously-skip-permissions"] if args.trusted
                else ["--permission-mode", "plan"])
    if args.model:
        command += ["--model", args.model]
    if args.effort:
        command += ["--effort", args.effort]
    return command


def process_snapshot() -> dict[int, tuple[int, int, str]]:
    """Identity includes start time; never use process names to choose victims."""
    result = subprocess.run(["ps", "-axo", "pid=,ppid=,pgid=,lstart="],
                            capture_output=True, text=True, timeout=3, check=True)
    rows = {}
    for line in result.stdout.splitlines():
        fields = line.split(maxsplit=3)
        if len(fields) == 4:
            rows[int(fields[0])] = (int(fields[1]), int(fields[2]), fields[3])
    return rows


def track_processes(proc, owned):
    rows = process_snapshot()
    current = {pid: row for pid, row in rows.items()
               if pid in owned and owned[pid][2] == row[2]}
    # The original process group also catches tools created between snapshots.
    if proc.poll() is None or current:
        current.update((pid, row) for pid, row in rows.items() if row[1] == proc.pid)
    if proc.poll() is None and proc.pid in rows:
        current[proc.pid] = rows[proc.pid]
    while True:
        children = {pid: row for pid, row in rows.items() if row[0] in current}
        if all(pid in current for pid in children):
            break
        current.update(children)
    return current


def stop_processes(proc, owned):
    """Bounded TERM/KILL cleanup includes observed children that called setsid."""
    owned = track_processes(proc, owned)
    for action in (signal.SIGTERM, signal.SIGKILL):
        current = process_snapshot()
        # Children first so a still-running parent can reap them.
        for pid in sorted(owned, key=lambda value: value == proc.pid):
            if pid in current and current[pid][2] == owned[pid][2]:
                try:
                    os.kill(pid, action)
                except ProcessLookupError:
                    pass
        if action == signal.SIGTERM:
            time.sleep(0.25)
            owned = track_processes(proc, owned)
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        raise SessionError("E_CLEANUP", "The client could not be stopped within the cleanup deadline.", 5) from None


def run_process(command, args, environ, transcript, stderr):
    proc = None
    owned = {}
    started = time.monotonic()
    try:
        with args.prompt_file.open("rb") as prompt:
            proc = subprocess.Popen(command, cwd=args.cwd, env=environ, stdin=prompt,
                                    stdout=transcript, stderr=stderr, start_new_session=True)
            next_scan = 0.0
            while proc.poll() is None:
                now = time.monotonic()
                if now >= next_scan:
                    owned = track_processes(proc, owned)
                    next_scan = now + 1
                if now - started >= args.timeout_minutes * 60:
                    raise SessionError("E_TIMEOUT", "The agent session exceeded its deadline.", 5,
                                       "Inspect the retained evidence before starting a new attempt.", True)
                time.sleep(min(0.1, max(0.001, args.timeout_minutes * 60 - (now - started))))
            return proc.returncode
    finally:
        if proc is not None:
            stop_processes(proc, owned)


def completion(path: Path, client: str) -> tuple[str | None, bool]:
    session_id, terminal = None, False
    with path.open(errors="replace") as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            identity = event.get("thread_id" if client == "codex" else "session_id")
            if isinstance(identity, str) and identity.strip():
                if session_id and identity != session_id:
                    return session_id, False
                session_id = identity
            if client == "codex" and event.get("type") in {"turn.completed", "turn.failed"}:
                terminal = event["type"] == "turn.completed"
            elif client == "claude" and event.get("type") == "result":
                terminal = event.get("subtype") == "success" and event.get("is_error") is False
    return session_id, bool(session_id and terminal)


def envelope(data: dict[str, Any], error: SessionError | None):
    return {"schema_version": 1, "command": "run-agent-session", "status": "error" if error else "ok",
            "data": data, "error": None if error is None else {
                "code": error.code, "message": error.message, "retryable": error.retryable, "hint": error.hint}, "meta": {}}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def interrupted(*_):
    raise KeyboardInterrupt


def execute(args):
    args.cwd = args.cwd.expanduser().resolve(strict=True)
    args.prompt_file = args.prompt_file.expanduser().resolve(strict=True)
    if not args.cwd.is_dir() or not args.prompt_file.is_file():
        raise SessionError("E_INPUT", "Use an existing owning directory and prompt file.", 2)
    prompt = args.prompt_file.read_bytes()
    if not prompt.strip():
        raise SessionError("E_INPUT", "The prompt file is empty.", 2)
    if not math.isfinite(args.timeout_minutes) or args.timeout_minutes <= 0:
        raise SessionError("E_INPUT", "Timeout minutes must be finite and positive.", 2)
    args.transcript = args.transcript.expanduser().absolute()
    args.result_file = args.result_file.expanduser().absolute()
    stderr_path = Path(str(args.transcript) + ".stderr.log")
    paths = [args.transcript, stderr_path, args.result_file]
    if len({path.resolve() for path in paths + [args.prompt_file]}) != 4:
        raise SessionError("E_OUTPUT", "Prompt, transcript, stderr log and result paths must be distinct.", 2)
    created, streams = [], []
    try:
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created.append(path)
            streams.append(os.fdopen(fd, "w"))
    except OSError:
        for stream in streams:
            stream.close()
        for path in created:
            path.unlink()
        raise SessionError("E_OUTPUT", "Output paths must be new, writable files; existing evidence was preserved.", 2,
                           "Use fresh paths for each attempt.") from None
    started = time.monotonic()
    data = {"client": args.client, "cwd": str(args.cwd), "session_id": None, "thread_id": None,
            "completed": False, "exit_code": None, "timed_out": False,
            "transcript": str(args.transcript), "stderr_log": str(stderr_path), "result_file": str(args.result_file),
            "started_at": timestamp(), "trusted": args.trusted, "auth_method": None,
            "prompt_sha256": hashlib.sha256(prompt).hexdigest(), "model": args.model, "effort": args.effort}
    error = None
    try:
        executable = resolve_client(args.client)
        data["executable"] = executable
        environ = child_environment()
        prefix = client_prefix(args.client, executable)
        data["auth_method"] = require_subscription(args.client, prefix, args.cwd, environ)
        data["exit_code"] = run_process(session_command(args, prefix), args, environ, streams[0], streams[1])
    except SessionError as failure:
        error = failure
        data["timed_out"] = failure.code == "E_TIMEOUT"
    except KeyboardInterrupt:
        error = SessionError("E_INTERRUPTED", "The agent session was interrupted.", 5,
                             "Inspect its retained evidence before starting a new attempt.")
    except (OSError, subprocess.SubprocessError):
        error = SessionError("E_CLIENT_EXECUTION", "The requested client could not run successfully.", 4,
                             "Inspect its retained transcript and stderr log.")
    finally:
        streams[0].close()
        streams[1].close()
    data["session_id"], data["completed"] = completion(args.transcript, args.client)
    if args.client == "codex":
        data["thread_id"] = data["session_id"]
    if error is None and (data["exit_code"] != 0 or not data["completed"]):
        error = SessionError("E_INCOMPLETE", "The client did not exit successfully with a completed session event.", 4,
                             "Inspect the retained evidence; a business report alone does not prove client completion.")
    data["completed"] = data["completed"] and error is None
    data.update(finished_at=timestamp(), duration_seconds=round(time.monotonic() - started, 3))
    result = envelope(data, error)
    with streams[2] as output:
        json.dump(result, output, indent=2, sort_keys=True)
        output.write("\n")
    return result, error.exit_code if error else 0


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise SessionError("E_USAGE", message, 2, "Inspect --help.")


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument("--client", choices=("codex", "claude"), required=True)
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--transcript", type=Path, required=True)
    parser.add_argument("--result-file", type=Path, required=True)
    parser.add_argument("--timeout-minutes", type=float, default=60)
    parser.add_argument("--trusted", action="store_true", help="Broad unattended local access for an already trusted workflow.")
    parser.add_argument("--model", help="Omit to retain the client's configured model.")
    parser.add_argument("--effort")
    parser.add_argument("--no-input", action="store_true", help="Accepted for automation; this runner never prompts.")
    parser.add_argument("--plain", action="store_true")
    args = None
    previous = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGTERM, interrupted)
    try:
        args = parser.parse_args(argv)
        result, code = execute(args)
    except SessionError as error:
        result, code = envelope({}, error), error.exit_code
    except (OSError, ValueError):
        result, code = envelope({}, SessionError("E_INPUT", "Inputs could not be read or validated.", 2)), 2
    finally:
        signal.signal(signal.SIGTERM, previous)
    if args and args.plain:
        print(f"{args.client}: {result['status']}" + (f" — {result['error']['message']}" if result["error"] else ""))
    else:
        print(json.dumps(result, sort_keys=True))
    return code
