from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from hooks.scripts import stop_feedback_turn as feedback
from tests.control_plane.support import TempDirTestCase, write_executable


class StopCodexExecutableTests(TempDirTestCase):
    def test_explicit_executable_overrides_desktop_bundle(self) -> None:
        executable = write_executable(self.temp_path / "custom-codex", "#!/bin/sh\nexit 0\n")
        with patch.dict(os.environ, {"AGENTS_CODEX_BIN": str(executable)}):
            self.assertEqual(feedback.resolve_codex_executable(), str(executable))

    def test_invalid_override_does_not_fall_back(self) -> None:
        with patch.dict(os.environ, {"AGENTS_CODEX_BIN": str(self.temp_path / "missing")}):
            with self.assertRaisesRegex(feedback.FeedbackTurnError, "not executable"):
                feedback.resolve_codex_executable()

    def test_desktop_reader_is_selected_over_stale_path_cli(self) -> None:
        bundled = Path("/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex")
        with (
            patch.dict(os.environ, {"AGENTS_CODEX_BIN": ""}),
            patch.object(feedback.sys, "platform", "darwin"),
            patch.object(Path, "is_file", autospec=True, side_effect=lambda path: path == bundled),
            patch.object(feedback.os, "access", return_value=True),
            patch.object(feedback.shutil, "which", return_value="/old/bin/codex") as which,
        ):
            self.assertEqual(feedback.resolve_codex_executable(), str(bundled))
            which.assert_not_called()

    def test_older_desktop_bundle_layout(self) -> None:
        bundled = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
        with (
            patch.dict(os.environ, {"AGENTS_CODEX_BIN": ""}),
            patch.object(feedback.sys, "platform", "darwin"),
            patch.object(Path, "is_file", autospec=True, side_effect=lambda path: path == bundled),
            patch.object(feedback.os, "access", return_value=True),
        ):
            self.assertEqual(feedback.resolve_codex_executable(), str(bundled))

    def test_missing_or_nonexecutable_bundle_uses_path(self) -> None:
        for present in (False, True):
            with (
                self.subTest(present=present),
                patch.dict(os.environ, {"AGENTS_CODEX_BIN": ""}),
                patch.object(feedback.sys, "platform", "darwin"),
                patch.object(Path, "is_file", return_value=present),
                patch.object(feedback.os, "access", return_value=False),
                patch.object(feedback.shutil, "which", return_value="/bin/codex"),
            ):
                self.assertEqual(feedback.resolve_codex_executable(), "/bin/codex")

    def test_non_macos_uses_path_without_probing_bundles(self) -> None:
        with (
            patch.dict(os.environ, {"AGENTS_CODEX_BIN": ""}),
            patch.object(feedback.sys, "platform", "linux"),
            patch.object(Path, "is_file") as is_file,
            patch.object(feedback.shutil, "which", return_value="/bin/codex"),
        ):
            self.assertEqual(feedback.resolve_codex_executable(), "/bin/codex")
            is_file.assert_not_called()

    def test_client_launch_uses_selected_executable(self) -> None:
        with (
            patch.dict(os.environ, {"CODEX_HOME": str(self.temp_path), "AGENTS_CODEX_BIN": ""}),
            patch.object(feedback, "resolve_codex_executable", return_value="/desktop/codex"),
            patch.object(feedback.subprocess, "Popen", side_effect=OSError("fixture launch failure")) as launch,
        ):
            with self.assertRaisesRegex(feedback.FeedbackTurnError, "/desktop/codex"):
                feedback.AppServerClient(1).start()
            self.assertEqual(launch.call_args.args[0], ["/desktop/codex", "app-server"])

    def test_shared_daemon_reads_activity_without_spawning_a_private_server(self) -> None:
        socket_path = self.temp_path / "app-server-control/app-server-control.sock"
        socket_path.parent.mkdir()
        socket_path.touch()
        connection = Mock()
        connection.recv.side_effect = [
            json.dumps({"id": 1, "result": {}}),
            json.dumps({"method": "thread/updated", "params": {"threadId": "other"}}),
            json.dumps({"id": 2, "result": {"thread": {"id": "target", "turns": []}}}),
        ]
        connect = Mock(return_value=connection)
        with (
            patch.dict(os.environ, {"CODEX_HOME": str(self.temp_path), "AGENTS_CODEX_BIN": ""}),
            patch.dict(sys.modules, {"websockets.sync.client": SimpleNamespace(unix_connect=connect)}),
            patch.object(feedback.subprocess, "Popen") as spawn,
        ):
            with feedback.AppServerClient(2) as client:
                result = client.request("thread/read", {"threadId": "target", "includeTurns": True})
        self.assertEqual(result["thread"]["id"], "target")
        self.assertEqual(connect.call_args.args, (str(socket_path),))
        self.assertIsNone(connect.call_args.kwargs["compression"])
        self.assertEqual(connect.call_args.kwargs["max_size"], 64 * 1024 * 1024)
        self.assertEqual(
            [json.loads(call.args[0])["method"] for call in connection.send.call_args_list],
            ["initialize", "initialized", "thread/read"],
        )
        spawn.assert_not_called()
        connection.close.assert_called_once()

    def test_broken_shared_daemon_does_not_fall_back_to_incomplete_private_history(self) -> None:
        socket_path = self.temp_path / "app-server-control/app-server-control.sock"
        socket_path.parent.mkdir()
        socket_path.symlink_to(self.temp_path / "missing-socket")
        connect = Mock(side_effect=OSError("connection refused"))
        with (
            patch.dict(os.environ, {"CODEX_HOME": str(self.temp_path), "AGENTS_CODEX_BIN": ""}),
            patch.dict(sys.modules, {"websockets.sync.client": SimpleNamespace(unix_connect=connect)}),
            patch.object(feedback.subprocess, "Popen") as spawn,
        ):
            with self.assertRaisesRegex(feedback.FeedbackTurnError, "Cannot connect to shared app-server"):
                with feedback.AppServerClient(2):
                    self.fail("connection should fail")
        spawn.assert_not_called()

    def test_explicit_executable_bypasses_shared_daemon(self) -> None:
        with (
            patch.dict(os.environ, {"AGENTS_CODEX_BIN": "/custom/codex"}),
            patch.object(feedback, "resolve_codex_executable", return_value="/custom/codex"),
            patch.object(feedback.AppServerClient, "_start_shared") as shared,
            patch.object(feedback.subprocess, "Popen", side_effect=OSError("fixture launch failure")),
        ):
            with self.assertRaisesRegex(feedback.FeedbackTurnError, "/custom/codex"):
                feedback.AppServerClient(1).start()
        shared.assert_not_called()

    def test_failed_initialization_closes_the_transport(self) -> None:
        socket_path = self.temp_path / "app-server-control/app-server-control.sock"
        socket_path.parent.mkdir()
        socket_path.touch()
        connection = Mock()
        connection.recv.side_effect = TimeoutError("initialize timeout")
        with (
            patch.dict(os.environ, {"CODEX_HOME": str(self.temp_path), "AGENTS_CODEX_BIN": ""}),
            patch.dict(sys.modules, {"websockets.sync.client": SimpleNamespace(unix_connect=Mock(return_value=connection))}),
        ):
            with self.assertRaisesRegex(feedback.FeedbackTurnError, "initialize timeout"):
                with feedback.AppServerClient(1):
                    self.fail("initialization should fail")
        connection.close.assert_called_once()
