from __future__ import annotations

import os
from unittest.mock import patch

from codex import runtime
from tests.control_plane.support import TempDirTestCase, write_executable


class OptionalCodexRuntimeTests(TempDirTestCase):
    def test_explicit_executable_is_authoritative_and_independent_of_host_installation(self):
        executable = write_executable(self.temp_path / "fixture-codex", "#!/bin/sh\nexit 0\n")
        with patch.dict(os.environ, {"CODEX_BIN": str(executable)}), patch.object(runtime, "resolve_codex_executable") as fallback:
            self.assertEqual(runtime.available_codex_executable(), str(executable))
            fallback.assert_not_called()
        with patch.dict(os.environ, {"CODEX_BIN": str(self.temp_path / "absent")}), patch.object(runtime, "resolve_codex_executable") as fallback:
            self.assertIsNone(runtime.available_codex_executable())
            fallback.assert_not_called()

    def test_default_reuses_verified_desktop_resolver(self):
        executable = write_executable(self.temp_path / "desktop-codex", "#!/bin/sh\nexit 0\n")
        with patch.dict(os.environ, {"CODEX_BIN": ""}), patch.object(runtime, "resolve_codex_executable", return_value=str(executable)) as resolver:
            self.assertEqual(runtime.available_codex_executable(), str(executable))
            resolver.assert_called_once_with()

    def test_missing_desktop_and_path_cli_is_optional(self):
        with patch.dict(os.environ, {"CODEX_BIN": ""}), patch.object(runtime, "resolve_codex_executable", return_value="codex"), patch.object(runtime.shutil, "which", return_value=None):
            self.assertIsNone(runtime.available_codex_executable())

    def test_missing_existing_agents_override_does_not_fall_back(self):
        with patch.dict(os.environ, {"CODEX_BIN": "", "AGENTS_CODEX_BIN": str(self.temp_path / "absent")}):
            self.assertIsNone(runtime.available_codex_executable())
