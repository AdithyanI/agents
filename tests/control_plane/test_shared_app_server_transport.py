from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from websockets.exceptions import ConnectionClosed
from websockets.sync.server import unix_serve

from hooks.scripts import stop_feedback_turn as feedback
from tests.control_plane.support import REPO_ROOT
from tests.control_plane.test_finalize_stale_codex_threads import load_thread_finalizer_module


@contextmanager
def local_app_server(codex_home: Path, thread: dict, *, withhold_read: bool = False):
    """An isolated Unix transport fixture; never connects to a running daemon."""
    socket_path = codex_home / "app-server-control" / "app-server-control.sock"
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    calls: list[str] = []
    handler_errors: list[Exception] = []
    release = threading.Event()
    handler_finished = threading.Event()

    def handle(connection):
        try:
            for encoded in connection:
                request = json.loads(encoded)
                method = request["method"]
                calls.append(method)
                if method == "initialize":
                    connection.send(json.dumps({"id": request["id"], "result": {}}))
                elif method == "initialized":
                    continue
                elif method == "thread/read":
                    if withhold_read:
                        if not release.wait(timeout=5):
                            raise AssertionError("fixture was not released after receive timeout")
                        continue
                    connection.send(json.dumps({"method": "thread/updated", "params": {"threadId": "unrelated"}}))
                    connection.send(json.dumps({"id": request["id"], "result": {"thread": thread}}))
                else:
                    raise AssertionError(f"unexpected fixture method: {method}")
        except ConnectionClosed:
            pass
        except Exception as exc:
            handler_errors.append(exc)
        finally:
            handler_finished.set()

    server = unix_serve(handle, str(socket_path), compression=None, open_timeout=2, close_timeout=1)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        with patch.dict(os.environ, {"CODEX_HOME": str(codex_home), "AGENTS_CODEX_BIN": ""}):
            yield calls
    finally:
        release.set()
        server.shutdown()
        server_thread.join(timeout=3)
        finished = handler_finished.wait(timeout=3)
        socket_path.unlink(missing_ok=True)
        if server_thread.is_alive() or not finished:
            raise AssertionError("local WebSocket fixture did not shut down")
        if handler_errors:
            raise AssertionError(f"local WebSocket fixture failed: {handler_errors[0]}") from handler_errors[0]


class SharedAppServerTransportTests(unittest.TestCase):
    def setUp(self) -> None:
        # A short repo-local socket path also fits macOS's Unix socket name limit.
        (REPO_ROOT / "tmp").mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="ws-", dir=REPO_ROOT / "tmp")
        self.codex_home = Path(self.temporary.name)
        self.finalizer = load_thread_finalizer_module()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def clients(self):
        return (
            ("stop feedback", feedback, feedback.FeedbackTurnError),
            ("thread finalizer", self.finalizer, self.finalizer.AppServerError),
        )

    def test_both_clients_read_real_history_above_one_mebibyte(self) -> None:
        history = "history evidence " * 140000
        thread = {"id": "target", "turns": [{"id": "turn", "status": "completed", "items": [{"type": "agentMessage", "text": history}]}]}
        self.assertGreater(len(json.dumps({"thread": thread}).encode()), 1024 * 1024)
        for name, module, _error in self.clients():
            with self.subTest(client=name), local_app_server(self.codex_home, thread) as calls:
                with patch.object(module.subprocess, "Popen", side_effect=AssertionError("fixture must not spawn a private app-server")):
                    with module.AppServerClient(2) as client:
                        result = client.request("thread/read", {"threadId": "target", "includeTurns": True})
                        self.assertEqual(result["thread"], thread)
                        self.assertEqual(module.MAX_APP_SERVER_MESSAGE_BYTES, 64 * 1024 * 1024)
                self.assertEqual(calls, ["initialize", "initialized", "thread/read"])

    def test_configured_message_limit_remains_enforced(self) -> None:
        # Exercise the same receive cap at a small boundary to keep this check
        # cheap, while the large-history test verifies the real 64 MiB setting.
        thread = {"id": "target", "preview": "x" * 4096}
        for name, module, error in self.clients():
            with self.subTest(client=name), patch.object(module, "MAX_APP_SERVER_MESSAGE_BYTES", 2048):
                with local_app_server(self.codex_home, thread):
                    with module.AppServerClient(2) as client:
                        with self.assertRaisesRegex(error, "1009|message too big|exceeds limit"):
                            client.request("thread/read", {"threadId": "target"})

    def test_receive_timeout_is_preserved_for_both_real_transports(self) -> None:
        for name, module, error in self.clients():
            with self.subTest(client=name), local_app_server(self.codex_home, {"id": "target"}, withhold_read=True):
                with module.AppServerClient(2) as client:
                    started = time.monotonic()
                    with self.assertRaisesRegex(error, "timed out|timeout"):
                        client.request("thread/read", {"threadId": "target"}, timeout_seconds=0.05)
                    self.assertLess(time.monotonic() - started, 1)


if __name__ == "__main__":
    unittest.main()
