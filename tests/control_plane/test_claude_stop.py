from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from hooks.scripts import stop
from tests.control_plane.support import (
    REPO_ROOT,
    TempDirTestCase,
    init_git_repo,
    run_command,
    write_executable,
)

SCRIPTS = REPO_ROOT / "hooks/scripts"


class ClaudeStopTests(TempDirTestCase):
    def make_published_repo(self, name: str) -> tuple[Path, Path]:
        remote = init_git_repo(self.temp_path / f"{name}-remote.git")
        run_command(["git", "-C", str(remote), "config", "receive.denyCurrentBranch", "updateInstead"])
        repo = init_git_repo(self.temp_path / name, with_initial_commit=True)
        run_command(["git", "-C", str(repo), "remote", "add", "origin", str(remote)])
        run_command(["git", "-C", str(repo), "push", "-u", "origin", "main"])
        return repo, remote

    def hook(self, script: str, payload: Any, *, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / script), "--runtime", "claude"],
            input=payload if isinstance(payload, str) else json.dumps(payload),
            cwd=cwd, capture_output=True, text=True, check=False, timeout=120,
        )

    def tool_use(self, session: str, cwd: Path, tool: str, tool_input: dict[str, Any]) -> None:
        result = self.hook("claude_tool_use.py", {
            "hook_event_name": "PostToolUse", "session_id": session, "cwd": str(cwd),
            "tool_name": tool, "tool_input": tool_input, "tool_response": {},
        }, cwd=cwd)
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)

    def stop_hook(self, session: str, cwd: Path, **extra: Any) -> subprocess.CompletedProcess[str]:
        result = self.hook("stop.py", {
            "hook_event_name": "Stop", "session_id": session, "cwd": str(cwd),
            "stop_hook_active": False, **extra,
        }, cwd=cwd)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def remote_file(self, remote: Path, name: str) -> str:
        return run_command(["git", "-C", str(remote), "show", f"HEAD:{name}"], check=False).stdout

    def test_tool_registrations_and_starting_repo_are_checked_committed_and_pushed(self) -> None:
        primary, primary_remote = self.make_published_repo("primary")
        sibling, sibling_remote = self.make_published_repo("sibling")
        shell, shell_remote = self.make_published_repo("shell target")
        untouched, _ = self.make_published_repo("untouched")
        (primary / "primary.txt").write_text("primary\n", encoding="utf-8")
        (sibling / "sibling.txt").write_text("sibling\n", encoding="utf-8")
        (shell / "generated.txt").write_text("generated\n", encoding="utf-8")
        (untouched / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")

        self.tool_use("s1", primary, "Write", {"file_path": str(sibling / "sibling.txt"), "content": "sibling\n"})
        self.tool_use("s1", primary, "Bash", {"command": f"python3 gen.py --out '{shell}/generated.txt'"})
        result = self.stop_hook("s1", primary)

        self.assertEqual(result.stdout, "")
        for repo, remote, name in (
            (primary, primary_remote, "primary.txt"),
            (sibling, sibling_remote, "sibling.txt"),
            (shell, shell_remote, "generated.txt"),
        ):
            self.assertEqual(run_command(["git", "-C", str(repo), "status", "--porcelain"]).stdout, "")
            self.assertEqual(self.remote_file(remote, name), name.split(".")[0] + "\n")
        self.assertIn("unrelated.txt", run_command(["git", "-C", str(untouched), "status", "--porcelain"]).stdout)
        self.assertFalse(stop.codex_transaction_path("s1").exists())

    def test_failing_fast_check_blocks_once_then_warns_and_preserves_work(self) -> None:
        repo, remote = self.make_published_repo("repo")
        write_executable(repo / "scripts/check-fast.sh", "#!/bin/sh\necho fast-check-failed >&2\nexit 1\n")
        (repo / "change.txt").write_text("change\n", encoding="utf-8")
        before = run_command(["git", "-C", str(remote), "rev-parse", "HEAD"]).stdout

        first = json.loads(self.stop_hook("s2", repo).stdout)
        self.assertEqual(first["decision"], "block")
        self.assertIn("fast-check-failed", first["reason"])
        retry = json.loads(self.stop_hook("s2", repo, stop_hook_active=True).stdout)
        self.assertNotIn("decision", retry)
        self.assertIn("fast-check-failed", retry["systemMessage"])

        self.assertEqual(run_command(["git", "-C", str(remote), "rev-parse", "HEAD"]).stdout, before)
        self.assertIn("change.txt", run_command(["git", "-C", str(repo), "status", "--porcelain"]).stdout)

    def test_clean_session_and_missing_identity_publish_nothing(self) -> None:
        repo, remote = self.make_published_repo("repo")
        before = run_command(["git", "-C", str(remote), "rev-parse", "HEAD"]).stdout
        self.assertEqual(self.stop_hook("clean", repo).stdout, "")

        (repo / "change.txt").write_text("change\n", encoding="utf-8")
        result = self.hook("stop.py", {"hook_event_name": "Stop", "cwd": str(repo)}, cwd=repo)
        self.assertIn("missing session_id", json.loads(result.stdout)["systemMessage"])
        self.assertEqual(run_command(["git", "-C", str(remote), "rev-parse", "HEAD"]).stdout, before)

    def test_deleted_scratch_repository_does_not_block_publication(self) -> None:
        repo, remote = self.make_published_repo("repo")
        scratch = init_git_repo(self.temp_path / "scratch")
        (scratch / "draft.txt").write_text("draft\n", encoding="utf-8")
        (repo / "change.txt").write_text("change\n", encoding="utf-8")
        self.tool_use("s4", repo, "Write", {"file_path": str(scratch / "draft.txt")})
        self.tool_use("s4", repo, "Bash", {"command": f"git -C {scratch} status"})
        run_command(["rm", "-rf", str(scratch)])

        self.assertEqual(self.stop_hook("s4", repo).stdout, "")
        self.assertEqual(self.remote_file(remote, "change.txt"), "change\n")
        self.assertFalse(stop.codex_transaction_path("s4").exists())

    def test_tool_use_attribution_is_best_effort_and_silent(self) -> None:
        repo, _ = self.make_published_repo("repo")
        outside = self.temp_path / "not-a-repo"
        outside.mkdir()
        self.tool_use("s3", outside, "Write", {"file_path": str(outside / "notes.txt")})
        self.tool_use("s3", outside, "Read", {"file_path": str(repo / "README.md")})
        for raw in ("not json", "[]", json.dumps({"hook_event_name": "Stop", "session_id": "s3"})):
            result = self.hook("claude_tool_use.py", raw, cwd=outside)
            self.assertEqual((result.returncode, result.stdout), (0, ""))
        self.assertFalse(stop.codex_transaction_path("s3").exists())

        # Relative file paths resolve against the hook cwd.
        self.tool_use("s3", repo, "Edit", {"file_path": "README.md"})
        recorded = stop.load_codex_transaction("s3")
        self.assertEqual(list(recorded), [str(repo.resolve())])
        self.assertEqual(recorded[str(repo.resolve())].paths, {"README.md"})
