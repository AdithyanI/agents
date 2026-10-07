#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any


DEFAULT_INITIAL_DELAY_SECONDS = 2.0
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_TURN_TIMEOUT_SECONDS = 900.0
DEFAULT_RETRY_SECONDS = 2.0
DEFAULT_RETRIES = 10
# Long tool-heavy threads exceed the WebSocket library's 1 MiB default.
# Keep a finite ceiling while allowing complete repository discovery responses.
MAX_APP_SERVER_MESSAGE_BYTES = 64 * 1024 * 1024


class FeedbackTurnError(Exception):
    pass


def resolve_codex_executable() -> str:
    """Keep desktop history reads on the desktop's bundled protocol version."""
    override = os.environ.get("AGENTS_CODEX_BIN", "").strip()
    if override:
        executable = shutil.which(override)
        if not executable:
            raise FeedbackTurnError(f"AGENTS_CODEX_BIN is not executable: {override}")
        return executable
    if sys.platform == "darwin":
        for root in (Path("/Applications"), Path.home() / "Applications"):
            for app in ("ChatGPT.app", "Codex.app"):
                resources = root / app / "Contents" / "Resources"
                for relative in ("codex-cli/bin/codex", "codex"):
                    candidate = resources / relative
                    if candidate.is_file() and os.access(candidate, os.X_OK):
                        return str(candidate)
    return shutil.which("codex") or "codex"


class AppServerClient:
    def __init__(self, timeout_seconds: float) -> None:
        self.timeout_seconds = timeout_seconds
        self.proc: subprocess.Popen[str] | None = None
        self.connection: Any = None
        self.messages: queue.Queue[dict[str, Any]] = queue.Queue()
        self.stderr_lines: list[str] = []
        self.next_id = 1

    def __enter__(self) -> "AppServerClient":
        try:
            self.start()
        except Exception:
            self.close()
            raise
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def start(self) -> None:
        codex_dir = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
        socket_path = codex_dir / "app-server-control" / "app-server-control.sock"
        if (not os.environ.get("AGENTS_CODEX_BIN", "").strip()
                and (socket_path.exists() or socket_path.is_symlink())):
            self._start_shared(socket_path)
        else:
            self._start_stdio()
        self.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "agents_stop_feedback_turn",
                    "title": "Agents Stop Hook Feedback Turn",
                    "version": "1",
                },
                "capabilities": {"experimentalApi": False},
            },
        )
        self.notify("initialized", {})

    def _start_shared(self, socket_path: Path) -> None:
        try:
            from websockets.sync.client import unix_connect
        except ImportError as exc:
            raise FeedbackTurnError(
                "Missing WebSocket dependency; run "
                "codex/scripts/install-thread-finalizer-deps.sh --apply"
            ) from exc
        try:
            self.connection = unix_connect(
                str(socket_path), uri="ws://localhost/rpc", compression=None,
                user_agent_header=None, open_timeout=self.timeout_seconds, close_timeout=2,
                max_size=MAX_APP_SERVER_MESSAGE_BYTES,
            )
        except Exception as exc:
            raise FeedbackTurnError(f"Cannot connect to shared app-server at {socket_path}: {exc}") from exc

    def _start_stdio(self) -> None:
        executable = resolve_codex_executable()
        try:
            self.proc = subprocess.Popen(
                [executable, "app-server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            raise FeedbackTurnError(f"failed to start {executable} app-server: {exc}") from exc

        assert self.proc.stdout is not None
        assert self.proc.stderr is not None
        threading.Thread(target=self._read_stdout, args=(self.proc.stdout,), daemon=True).start()
        threading.Thread(target=self._read_stderr, args=(self.proc.stderr,), daemon=True).start()

    def close(self) -> None:
        if self.connection is not None:
            connection = self.connection
            self.connection = None
            connection.close()
        if self.proc is None:
            return
        proc = self.proc
        self.proc = None
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

    def _read_stdout(self, stream: Any) -> None:
        for line in stream:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                self.messages.put(payload)

    def _read_stderr(self, stream: Any) -> None:
        for line in stream:
            text = line.rstrip("\n")
            if text:
                self.stderr_lines.append(text)
                del self.stderr_lines[:-80]

    def _write(self, message: dict[str, Any]) -> None:
        if self.connection is not None:
            try:
                self.connection.send(json.dumps(message, separators=(",", ":")))
            except Exception as exc:
                raise FeedbackTurnError(f"shared app-server send failed: {exc}") from exc
            return
        if self.proc is None or self.proc.stdin is None:
            raise FeedbackTurnError("app-server is not running")
        if self.proc.poll() is not None:
            raise FeedbackTurnError(f"app-server exited with code {self.proc.returncode}")
        self.proc.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._write({"method": method, "params": params})

    def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        message: dict[str, Any] = {"method": method, "id": request_id}
        if params is not None:
            message["params"] = params
        self._write(message)
        return self._read_response(request_id, method=method, timeout_seconds=timeout_seconds or self.timeout_seconds)

    def _next_message(self, *, timeout_seconds: float) -> dict[str, Any]:
        if self.connection is not None:
            try:
                payload = json.loads(self.connection.recv(timeout=timeout_seconds))
            except Exception as exc:
                raise FeedbackTurnError(f"shared app-server receive failed: {exc}") from exc
            if not isinstance(payload, dict):
                raise FeedbackTurnError("shared app-server returned a non-object message")
            return payload
        if self.proc is not None and self.proc.poll() is not None and self.messages.empty():
            stderr_tail = "\n".join(self.stderr_lines[-20:])
            raise FeedbackTurnError(
                f"app-server exited with code {self.proc.returncode}"
                + (f"\nstderr:\n{stderr_tail}" if stderr_tail else "")
            )
        try:
            return self.messages.get(timeout=timeout_seconds)
        except queue.Empty as exc:
            stderr_tail = "\n".join(self.stderr_lines[-20:])
            raise FeedbackTurnError(
                "timed out waiting for app-server message"
                + (f"\nstderr:\n{stderr_tail}" if stderr_tail else "")
            ) from exc

    def _read_response(self, request_id: int, *, method: str, timeout_seconds: float) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise FeedbackTurnError(f"timed out waiting for {method} response id={request_id}")
            payload = self._next_message(timeout_seconds=remaining)
            if "id" in payload and "method" in payload:
                self._handle_server_request(payload)
                continue
            if payload.get("id") != request_id:
                continue
            if "error" in payload:
                error = payload["error"]
                message = error.get("message") if isinstance(error, dict) else str(error)
                raise FeedbackTurnError(f"{method} failed: {message}")
            result = payload.get("result")
            return result if isinstance(result, dict) else {}

    def _handle_server_request(self, msg: dict[str, Any]) -> None:
        req_id = msg.get("id")
        method = msg.get("method")
        if req_id is None:
            return
        if method in {
            "item/commandExecution/requestApproval",
            "item/fileChange/requestApproval",
        }:
            self._write({"id": req_id, "result": {"decision": "acceptForSession"}})
            return
        if method in {"applyPatchApproval", "execCommandApproval"}:
            self._write({"id": req_id, "result": {"decision": "approved_for_session"}})
            return
        if isinstance(method, str) and method.startswith("item/") and method.endswith("/requestApproval"):
            self._write({"id": req_id, "result": {"decision": "decline"}})
            return
        self._write({"id": req_id, "result": {}})

    def wait_for_turn_completed(self, thread_id: str, turn_id: str, *, timeout_seconds: float) -> str:
        deadline = time.monotonic() + timeout_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise FeedbackTurnError(f"timed out waiting for turn/completed turn={turn_id}")
            payload = self._next_message(timeout_seconds=remaining)
            if "id" in payload and "method" in payload:
                self._handle_server_request(payload)
                continue
            if payload.get("method") != "turn/completed":
                continue
            params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
            if params.get("threadId") != thread_id:
                continue
            turn = params.get("turn") if isinstance(params.get("turn"), dict) else {}
            completed_turn_id = params.get("turnId") or turn.get("id")
            if completed_turn_id != turn_id:
                continue
            status = params.get("status") or turn.get("status") or "completed"
            return str(status)


def log(message: str) -> None:
    try:
        log_dir = Path.home() / ".local/state/agents-control-plane/log"
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "hooks-stop-feedback-turn.log").open("a", encoding="utf-8") as handle:
            handle.write(message.rstrip() + "\n")
    except Exception:
        pass


def load_reason(path: Path) -> str:
    try:
        reason = path.read_text(encoding="utf-8")
    finally:
        try:
            path.unlink()
        except OSError:
            pass
    if not reason.strip():
        raise FeedbackTurnError("reason file is empty")
    return reason


def extract_turn_id(response: dict[str, Any]) -> str:
    turn = response.get("turn")
    if isinstance(turn, dict) and isinstance(turn.get("id"), str):
        return turn["id"]
    turn_id = response.get("turnId")
    if isinstance(turn_id, str):
        return turn_id
    raise FeedbackTurnError("turn/start did not return a turn id")


def start_feedback_turn(args: argparse.Namespace) -> None:
    if args.initial_delay_seconds > 0:
        time.sleep(args.initial_delay_seconds)
    reason = load_reason(Path(args.reason_file).expanduser())
    prompt = "Hook feedback\n\n" + reason

    last_error: Exception | None = None
    for attempt in range(args.retries + 1):
        try:
            with AppServerClient(args.timeout_seconds) as client:
                client.request(
                    "thread/resume",
                    {"threadId": args.thread_id, "experimentalRawEvents": False},
                )
                response = client.request(
                    "turn/start",
                    {
                        "threadId": args.thread_id,
                        "input": [{"type": "text", "text": prompt, "text_elements": []}],
                        "cwd": args.cwd,
                    },
                )
                turn_id = extract_turn_id(response)
                status = client.wait_for_turn_completed(
                    args.thread_id,
                    turn_id,
                    timeout_seconds=args.turn_timeout_seconds,
                )
                log(f"ok thread={args.thread_id} turn={turn_id} status={status}")
                return
        except Exception as exc:
            last_error = exc
            text = str(exc)
            if "active turn" not in text.lower() and "in progress" not in text.lower():
                break
            if attempt < args.retries:
                time.sleep(args.retry_seconds)

    raise FeedbackTurnError(str(last_error) if last_error else "failed to start feedback turn")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start a follow-up Codex turn containing Stop-hook feedback.")
    parser.add_argument("--thread-id", required=True)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--reason-file", required=True)
    parser.add_argument("--initial-delay-seconds", type=float, default=DEFAULT_INITIAL_DELAY_SECONDS)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--turn-timeout-seconds", type=float, default=DEFAULT_TURN_TIMEOUT_SECONDS)
    parser.add_argument("--retry-seconds", type=float, default=DEFAULT_RETRY_SECONDS)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        start_feedback_turn(args)
        return 0
    except Exception as exc:
        log(f"error thread={args.thread_id} error={exc}")
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
