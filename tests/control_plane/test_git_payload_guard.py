from __future__ import annotations

import os
import sys
from unittest.mock import patch

from hooks.scripts import git_payload_guard as guard
from hooks.scripts import stop
from tests.control_plane.support import TempDirTestCase, init_git_repo, run_command


class GitPayloadGuardTests(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.repo = init_git_repo(self.temp_path / "repo", with_initial_commit=True)
        self.root = str(self.repo)

    def stage(self, *, max_file=100, max_total=256) -> None:
        guard.stage(self.root, max_file=max_file, max_total=max_total)

    def objects(self) -> set[str]:
        return {str(path.relative_to(self.repo / ".git/objects"))
                for path in (self.repo / ".git/objects").rglob("*") if path.is_file()}

    def test_rejects_large_untracked_file_before_any_object_write(self) -> None:
        (self.repo / "recording.wav").write_bytes(b"x" * 101)
        before = self.objects()
        with self.assertRaisesRegex(guard.PayloadError, "recording.wav"):
            self.stage()
        self.assertEqual(self.objects(), before)
        self.assertEqual(guard.index_sizes(self.root), {})
        self.assertTrue((self.repo / "recording.wav").exists())

    def test_rejects_aggregate_payload_before_object_write(self) -> None:
        for number in range(3):
            (self.repo / f"chunk{number}.bin").write_bytes(b"x" * 90)
        before = self.objects()
        with self.assertRaisesRegex(guard.PayloadError, "total changed content"):
            self.stage()
        self.assertEqual(self.objects(), before)

    def test_counts_already_staged_and_new_paths_together(self) -> None:
        (self.repo / "prior.bin").write_bytes(b"x" * 90)
        run_command(["git", "-C", self.root, "add", "prior.bin"])
        for name in ("one.bin", "two.bin"):
            (self.repo / name).write_bytes(b"y" * 90)
        before = self.objects()
        with self.assertRaisesRegex(guard.PayloadError, "total changed content"):
            self.stage()
        self.assertEqual(self.objects(), before)
        self.assertEqual(guard.index_sizes(self.root), {"prior.bin": 90})

    def test_ignores_ignored_payload_and_allows_normal_changes(self) -> None:
        (self.repo / ".gitignore").write_text("*.wav\n")
        (self.repo / "recording.wav").write_bytes(b"x" * 1000)
        (self.repo / "source.py").write_text("print('hello')\n")
        self.stage()
        self.assertEqual(set(guard.index_sizes(self.root)), {".gitignore", "source.py"})

    def test_does_not_follow_symlink_payload(self) -> None:
        (self.repo / ".gitignore").write_text("big.bin\n")
        (self.repo / "big.bin").write_bytes(b"x" * 1000)
        (self.repo / "link").symlink_to("big.bin")
        self.stage()
        self.assertEqual(guard.index_sizes(self.root)["link"], len("big.bin"))

    def test_handles_unusual_names_and_already_staged_rename(self) -> None:
        old = self.repo / "README.md"
        new = self.repo / "odd\n [name]:.md"
        old.rename(new)
        run_command(["git", "-C", self.root, "add", "-A"])
        self.stage()
        self.assertEqual(set(guard.index_sizes(self.root)), {new.name})

    def test_allows_deleting_tracked_large_file_without_reading_it(self) -> None:
        path = self.repo / "old.bin"
        path.write_bytes(b"x" * 1000)
        run_command(["git", "-C", self.root, "add", "old.bin"])
        run_command(["git", "-C", self.root, "commit", "-qm", "fixture large history"])
        path.unlink()
        (self.repo / "source.py").write_text("pass\n")
        self.stage()
        self.assertEqual(guard.index_sizes(self.root), {"source.py": 5})

    def test_untouched_large_history_does_not_block_source_change(self) -> None:
        (self.repo / "old.bin").write_bytes(b"x" * 1000)
        run_command(["git", "-C", self.root, "add", "old.bin"])
        run_command(["git", "-C", self.root, "commit", "-qm", "fixture large history"])
        (self.repo / "source.py").write_text("pass\n")
        self.stage()
        self.assertEqual(guard.index_sizes(self.root), {"source.py": 5})

    def test_index_check_uses_staged_blob_not_smaller_worktree(self) -> None:
        path = self.repo / "big.bin"
        path.write_bytes(b"x" * 101)
        run_command(["git", "-C", self.root, "add", "big.bin"])
        path.write_bytes(b"small")
        with self.assertRaisesRegex(guard.PayloadError, "big.bin"):
            guard.check_index(self.root, max_file=100, max_total=256)

    def test_new_file_during_validation_waits_for_next_stage(self) -> None:
        (self.repo / "source.py").write_text("pass\n")
        real_check = guard.check_sizes

        def check_and_create(sizes, **kwargs):
            real_check(sizes, **kwargs)
            (self.repo / "late.wav").write_bytes(b"x" * 1000)

        with patch.object(guard, "check_sizes", side_effect=check_and_create):
            self.stage()
        self.assertEqual(guard.index_sizes(self.root), {"source.py": 5})

    def test_clean_filter_expansion_is_rejected_at_index_boundary(self) -> None:
        run_command(["git", "-C", self.root, "config", "filter.expand.clean",
                     "printf '%0101d' 0"])
        (self.repo / ".gitattributes").write_text("small.bin filter=expand\n")
        (self.repo / "small.bin").write_bytes(b"x")
        with self.assertRaisesRegex(guard.PayloadError, "small.bin"):
            self.stage()

    def test_unborn_repository_stages_normally(self) -> None:
        empty = init_git_repo(self.temp_path / "empty")
        (empty / "source.py").write_text("pass\n")
        guard.stage(str(empty), max_file=100, max_total=256)
        self.assertEqual(guard.index_sizes(str(empty)), {"source.py": 5})

    def test_auto_publication_disables_maintenance_without_changing_config(self) -> None:
        run_command(["git", "-C", self.root, "config", "gc.auto", "25"])
        run_command(["git", "-C", self.root, "config", "maintenance.auto", "true"])
        inherited = {**os.environ, "GIT_CONFIG_COUNT": "1",
                     "GIT_CONFIG_KEY_0": "example.inherited", "GIT_CONFIG_VALUE_0": "kept"}
        for key, value in (("gc.auto", "0"), ("maintenance.auto", "false"),
                           ("example.inherited", "kept")):
            result = stop.run(["git", "config", "--get", key], self.root, env=inherited)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), value)
        with patch.dict(os.environ, inherited):
            self.assertEqual(guard.git(self.root, "config", "--get", "gc.auto").strip(), b"0")
            self.assertEqual(guard.git(self.root, "config", "--get", "maintenance.auto").strip(),
                             b"false")
            self.assertEqual(guard.git(self.root, "config", "--get", "example.inherited").strip(),
                             b"kept")
        for key, value in (("gc.auto", "25"), ("maintenance.auto", "true")):
            self.assertEqual(run_command(["git", "-C", self.root, "config", "--get", key])
                             .stdout.strip(), value)
        child = stop.run([sys.executable, "-c", "import os; print(os.environ['GIT_CONFIG_COUNT'])"],
                         self.root, env=inherited)
        self.assertEqual(child.stdout.strip(), "1")
        self.assertEqual(inherited["GIT_CONFIG_COUNT"], "1")
