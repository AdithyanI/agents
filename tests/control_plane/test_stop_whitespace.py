from __future__ import annotations

import os
from unittest.mock import patch

from hooks.scripts import stop
from tests.control_plane.support import TempDirTestCase, init_git_repo, run_command


class StopWhitespaceTests(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.repo = init_git_repo(self.temp_path / "repo", with_initial_commit=True)

    def stage(self) -> None:
        run_command(["git", "-C", str(self.repo), "add", "-A"])

    def repair(self) -> None:
        stop.repair_staged_blank_eof(str(self.repo))

    def test_preserves_content_line_endings_and_file_mode(self) -> None:
        run_command(["git", "-C", str(self.repo), "config", "color.ui", "always"])
        bodies = {
            "episode.srt": b"1\n00:00:00,000 --> 00:00:01,000\nWords.\n\n",
            "windows.txt": b"one\r\n\r\ntwo\r\n\r\n\r\n",
            "line breaks.md": b"intentional Markdown break  \nnext line\n\n",
            "empty.txt": b"\n\n",
            'odd:\t\n\"[name].txt': b"body\n\n",
        }
        expected = {
            "episode.srt": bodies["episode.srt"][:-1],
            "windows.txt": b"one\r\n\r\ntwo\r\n",
            "line breaks.md": b"intentional Markdown break  \nnext line\n",
            "empty.txt": b"\n\n",  # Git does not flag a wholly blank added file.
            'odd:\t\n\"[name].txt': b"body\n",
        }
        for name, body in bodies.items():
            (self.repo / name).write_bytes(body)
        (self.repo / "episode.srt").chmod(0o755)
        self.stage()
        self.repair()
        for name, body in expected.items():
            self.assertEqual((self.repo / name).read_bytes(), body)
        self.assertEqual((self.repo / "episode.srt").stat().st_mode & 0o777, 0o755)
        # The existing consolidation loop, not the helper, owns restaging.
        self.assertEqual(
            run_command(["git", "-C", str(self.repo), "show", ":episode.srt"]).stdout,
            bodies["episode.srt"].decode(),
        )
        self.stage()
        self.repair()
        self.assertEqual((self.repo / "episode.srt").read_bytes(), expected["episode.srt"])

    def test_respects_git_attributes_and_ignores_binary_and_symlink_targets(self) -> None:
        (self.repo / ".gitattributes").write_text("keep.txt -whitespace\n", encoding="utf-8")
        (self.repo / "keep.txt").write_bytes(b"intentional\n\n")
        (self.repo / "binary.dat").write_bytes(b"\x00binary\n\n")
        outside = self.temp_path / "outside.txt"
        outside.write_bytes(b"outside\n\n")
        (self.repo / "link.txt").symlink_to(outside)
        (self.repo / "fix.txt").write_bytes(b"fix\n\n")
        self.stage()
        self.repair()
        self.assertEqual((self.repo / "fix.txt").read_bytes(), b"fix\n")
        self.assertEqual((self.repo / "keep.txt").read_bytes(), b"intentional\n\n")
        self.assertEqual((self.repo / "binary.dat").read_bytes(), b"\x00binary\n\n")
        self.assertTrue((self.repo / "link.txt").is_symlink())
        self.assertEqual(outside.read_bytes(), b"outside\n\n")

    def test_respects_core_whitespace_opt_out(self) -> None:
        path = self.repo / "keep.txt"
        path.write_bytes(b"intentional\n\n")
        run_command(["git", "-C", str(self.repo), "config", "core.whitespace", "-blank-at-eof"])
        self.stage()
        self.repair()
        self.assertEqual(path.read_bytes(), b"intentional\n\n")

    def test_leaves_unstaged_changes_intact(self) -> None:
        path = self.repo / "episode.srt"
        path.write_bytes(b"staged\n\n")
        self.stage()
        path.write_bytes(b"new concurrent edit\n\n")
        self.repair()
        self.assertEqual(path.read_bytes(), b"new concurrent edit\n\n")

    def test_rechecks_bytes_if_file_changes_during_git_inspection(self) -> None:
        path = self.repo / "episode.srt"
        path.write_bytes(b"staged\n\n")
        self.stage()
        original_run = stop.subprocess.run

        def change_after_inspection(command, **kwargs):
            result = original_run(command, **kwargs)
            if "--quiet" in command:
                path.write_bytes(b"new concurrent edit\n\n")
            return result

        with patch.object(stop.subprocess, "run", side_effect=change_after_inspection):
            self.repair()
        self.assertEqual(path.read_bytes(), b"new concurrent edit\n\n")

    def test_io_failure_leaves_original_for_normal_check_feedback(self) -> None:
        path = self.repo / "episode.srt"
        path.write_bytes(b"staged\n\n")
        self.stage()
        original_open = os.open

        def fail_target(target, flags, *args, **kwargs):
            if target == path.resolve():
                raise PermissionError("read-only fixture")
            return original_open(target, flags, *args, **kwargs)

        with patch.object(stop.os, "open", side_effect=fail_target):
            self.repair()
        self.assertEqual(path.read_bytes(), b"staged\n\n")
