from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from unittest.mock import patch

from hooks.scripts import git_secret_guard as guard
from tests.control_plane.support import TempDirTestCase, init_git_repo, run_command

# Built at runtime so the positive-test credential is never itself published.
TOKEN = "ghp_" + "A1b2C3d4" * 4 + "E5f6"


class GitSecretGuardTests(TempDirTestCase):
    def setUp(self) -> None:
        # The verified tool is a fixed test dependency, like Python/Git; checks
        # never install or download it. Keep it when fixtures isolate HOME.
        tool = guard.scanner_path()
        super().setUp()
        self.tool_env = patch.dict(os.environ, {"AGENTS_GITLEAKS_BIN": str(tool)})
        self.tool_env.start()
        self.addCleanup(self.tool_env.stop)
        self.repo = init_git_repo(self.temp_path / "repo", with_initial_commit=True)
        self.root = str(self.repo)

    def put(self, name: str, text: str) -> None:
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        run_command(["git", "-C", self.root, "add", "--", name])

    def test_rejects_real_provider_pattern_without_exposing_value(self) -> None:
        self.put("credentials.env", "GITHUB_TOKEN=" + TOKEN + "\n")
        with self.assertRaises(guard.ScanError) as caught:
            guard.check_index(self.root)
        message = str(caught.exception)
        self.assertIn("credentials.env", message)
        self.assertIn("github-pat", message)
        self.assertNotIn(TOKEN, message)
        self.assertNotIn(TOKEN[4:12], message)

    def test_scans_staged_blob_even_if_worktree_has_been_cleaned(self) -> None:
        self.put("settings.txt", "GITHUB_TOKEN=" + TOKEN + "\n")
        (self.repo / "settings.txt").write_text("GITHUB_TOKEN=placeholder\n")
        with self.assertRaises(guard.ScanError):
            guard.check_index(self.root)
        self.assertEqual((self.repo / "settings.txt").read_text(), "GITHUB_TOKEN=placeholder\n")

    def test_placeholder_deleted_secret_and_ignored_untracked_secret_do_not_block(self) -> None:
        self.put("example.env", "GITHUB_TOKEN=your-token-here\n")
        self.put(".gitignore", ".env\n")
        (self.repo / ".env").write_text("GITHUB_TOKEN=" + TOKEN + "\n")
        guard.check_index(self.root)
        run_command(["git", "-C", self.root, "commit", "-qm", "safe placeholders"])
        self.put("retired.env", "GITHUB_TOKEN=" + TOKEN + "\n")
        run_command(["git", "-C", self.root, "commit", "-qm", "test historical secret"])
        (self.repo / "retired.env").unlink()
        run_command(["git", "-C", self.root, "add", "-u"])
        guard.check_index(self.root)

    def test_repo_config_inline_comments_and_environment_cannot_disable_rules(self) -> None:
        self.put("credentials.env", "GITHUB_TOKEN=" + TOKEN + " # gitleaks:allow\n")
        self.put(".gitleaks.toml", "title='disable'\n")
        self.put(".gitleaksignore", "*\n")
        with patch.dict(os.environ, {"GITLEAKS_CONFIG_TOML": "title='disable'"}):
            with self.assertRaises(guard.ScanError):
                guard.check_index(self.root)

    def test_symlink_target_is_not_followed_and_unusual_names_are_scanned(self) -> None:
        outside = self.temp_path / "private.txt"
        outside.write_text("GITHUB_TOKEN=" + TOKEN + "\n")
        (self.repo / "link.txt").symlink_to(outside)
        run_command(["git", "-C", self.root, "add", "link.txt"])
        guard.check_index(self.root)
        self.put("odd\n [name]:.txt", "GITHUB_TOKEN=" + TOKEN + "\n")
        with self.assertRaises(guard.ScanError):
            guard.check_index(self.root)

    def test_missing_or_replaced_scanner_fails_closed_and_leaves_index(self) -> None:
        self.put("source.py", "print('safe')\n")
        before = run_command(["git", "-C", self.root, "write-tree"]).stdout
        fake = self.temp_path / "gitleaks"
        fake.write_text("#!/bin/sh\nexit 0\n")
        fake.chmod(0o700)
        with patch.dict(os.environ, {"AGENTS_GITLEAKS_BIN": str(fake)}):
            with self.assertRaisesRegex(guard.ScanError, "missing or changed"):
                guard.check_index(self.root)
        self.assertEqual(run_command(["git", "-C", self.root, "write-tree"]).stdout, before)

    def test_exact_fixture_exception_does_not_allow_changed_or_other_path(self) -> None:
        value = "GITHUB_TOKEN=" + TOKEN + "\n"
        self.put("fixture.py", value)
        exception = {("fixture.py", hashlib.sha256(value.encode()).hexdigest(), "github-pat", 1)}
        with patch.object(guard, "approved_fixtures", return_value=exception):
            guard.check_index(self.root)
            self.put("fixture.py", value + "# changed\n")
            with self.assertRaises(guard.ScanError):
                guard.check_index(self.root)
            self.put("fixture.py", value)
            self.put("production.py", value)
            with self.assertRaises(guard.ScanError):
                guard.check_index(self.root)

    def test_push_scans_intermediate_commits_even_after_secret_removed(self) -> None:
        before = run_command(["git", "-C", self.root, "rev-parse", "HEAD"]).stdout.strip()
        self.put("secret.env", "GITHUB_TOKEN=" + TOKEN + "\n")
        run_command(["git", "-C", self.root, "commit", "-qm", "fixture secret"])
        (self.repo / "secret.env").unlink()
        run_command(["git", "-C", self.root, "add", "-u"])
        run_command(["git", "-C", self.root, "commit", "-qm", "remove fixture"])
        head = run_command(["git", "-C", self.root, "rev-parse", "HEAD"]).stdout.strip()
        blobs = guard.outgoing_blobs(self.root, "origin", f"refs/heads/main {head} refs/heads/main {before}\n")
        findings = guard.scan_blobs(self.root, blobs)
        self.assertEqual([row["rule"] for row in findings], ["github-pat"])
        self.assertEqual(guard.scan_blobs(self.root, guard.tree_blobs(self.root, "HEAD")), [])

    def test_push_deletion_has_no_content_and_unknown_remote_tip_blocks(self) -> None:
        head = run_command(["git", "-C", self.root, "rev-parse", "HEAD"]).stdout.strip()
        self.assertEqual(guard.outgoing_blobs(self.root, "origin", f"(delete) {'0' * 40} refs/heads/main {head}"), set())
        with self.assertRaises(guard.ScanError):
            guard.outgoing_blobs(self.root, "origin", f"refs/heads/main {head} refs/heads/main {'a' * 40}")

    def test_cli_diagnostics_are_redacted(self) -> None:
        self.put("credential.env", "GITHUB_TOKEN=" + TOKEN + "\n")
        result = subprocess.run(["python3", str(guard.CONTROL_ROOT / "hooks/scripts/git_secret_guard.py"),
                                 "check-index", "--repo", self.root], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(TOKEN, result.stdout + result.stderr)
        self.assertIn("github-pat", result.stderr)
