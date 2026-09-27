from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

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
            patch.object(feedback, "resolve_codex_executable", return_value="/desktop/codex"),
            patch.object(feedback.subprocess, "Popen", side_effect=OSError("fixture launch failure")) as launch,
        ):
            with self.assertRaisesRegex(feedback.FeedbackTurnError, "/desktop/codex"):
                feedback.AppServerClient(1).start()
            self.assertEqual(launch.call_args.args[0], ["/desktop/codex", "app-server"])
