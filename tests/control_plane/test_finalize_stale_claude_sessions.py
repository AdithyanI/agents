from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

from tests.control_plane.support import REPO_ROOT, TempDirTestCase, write_executable, write_json


def load_module():  # noqa: ANN202
    path = REPO_ROOT / "claude/scripts/finalize-stale-claude-sessions.py"
    spec = importlib.util.spec_from_file_location("finalize_stale_claude_sessions", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FinalizeStaleClaudeSessionsTest(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mod = load_module()
        self.repo = self.temp_path / "home" / "GitHub" / "ws"
        self.calls = self.temp_path / "hook-calls.jsonl"
        write_executable(
            self.repo / "scripts/hooks/finalize_claude_session.py",
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "payload = json.load(sys.stdin)\n"
            f"open({str(self.calls)!r}, 'a').write(json.dumps(payload) + '\\n')\n"
            "sys.exit(int(os.environ.get('FAKE_HOOK_EXIT', '0')))\n",
        )
        real = json.loads((REPO_ROOT / "repos/registry.json").read_text(encoding="utf-8"))
        real["repos"] = [
            {"id": "ws", "path": str(self.repo), "clients": {"codex": {"enabled": False, "config": {}}, "claude": {"enabled": True}}}
        ]
        self.registry = write_json(self.temp_path / "registry.json", real)
        self.projects = self.temp_path / "projects"
        self.sessions = self.temp_path / "sessions"
        self.sessions.mkdir()
        self.ledger = self.temp_path / "ledger.json"
        self.now = time.time()

    def transcript(self, session_id: str, *, hours_idle: float, entrypoint: str = "claude-desktop") -> Path:
        folder = self.projects / self.mod.munge_project_dir(self.repo.resolve())
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{session_id}.jsonl"
        path.write_text(json.dumps({"type": "user", "entrypoint": entrypoint, "cwd": str(self.repo)}) + "\n", encoding="utf-8")
        stamp = self.now - hours_idle * 3600
        os.utime(path, (stamp, stamp))
        return path

    def handshake(self, session_id: str, *, status: str, hours_since_status: float) -> None:
        write_json(
            self.sessions / f"{os.getpid()}-{session_id}.json",
            {"pid": os.getpid(), "sessionId": session_id, "status": status, "statusUpdatedAt": (self.now - hours_since_status * 3600) * 1000},
        )

    def run_main(self, *extra: str) -> tuple[int, dict]:
        out = io.StringIO()
        with redirect_stdout(out):
            code = self.mod.main([
                *extra,
                "--registry", str(self.registry),
                "--projects-dir", str(self.projects),
                "--sessions-dir", str(self.sessions),
                "--ledger", str(self.ledger),
                "--lock", str(self.temp_path / "lock"),
                "--now", str(self.now),
                "--json",
            ])
        return code, json.loads(out.getvalue())

    def hook_calls(self) -> list[dict]:
        if not self.calls.exists():
            return []
        return [json.loads(line) for line in self.calls.read_text().splitlines()]

    def test_munge_matches_claude_project_folder(self) -> None:
        self.assertEqual(self.mod.munge_project_dir(Path("/Users/a.b/GitHub/adi")), "-Users-a-b-GitHub-adi")

    def test_dry_run_reports_without_running_hooks(self) -> None:
        self.transcript("old", hours_idle=10)
        code, payload = self.run_main("--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual([c["sessionId"] for c in payload["data"]["candidates"]], ["old"])
        self.assertEqual(self.hook_calls(), [])
        self.assertFalse(self.ledger.exists())

    def test_apply_finalizes_idle_session_once(self) -> None:
        self.transcript("old", hours_idle=10)
        self.transcript("fresh", hours_idle=1)
        code, payload = self.run_main("--apply")
        self.assertEqual(code, 0)
        self.assertEqual(payload["data"]["finalized"], 1)
        calls = self.hook_calls()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["session_id"], "old")
        self.assertEqual(calls[0]["hook_event_name"], "FinalizeClaudeSession")
        self.assertEqual(calls[0]["reason"], "stale-cleanup")
        code, payload = self.run_main("--apply")
        self.assertEqual(len(self.hook_calls()), 1, "a finalized session must not run again")

    def test_busy_or_recently_idle_live_sessions_are_skipped(self) -> None:
        self.transcript("busy", hours_idle=10)
        self.transcript("just-idle", hours_idle=10)
        self.transcript("long-idle", hours_idle=10)
        self.handshake("busy", status="busy", hours_since_status=10)
        self.handshake("just-idle", status="idle", hours_since_status=1)
        self.handshake("long-idle", status="idle", hours_since_status=10)
        _, payload = self.run_main("--apply")
        reasons = {s["sessionId"]: s["reason"] for s in payload["data"]["skipped"]}
        self.assertEqual(reasons, {"busy": "active", "just-idle": "active"})
        self.assertEqual([c["session_id"] for c in self.hook_calls()], ["long-idle"])

    def test_headless_sessions_are_recorded_without_hook(self) -> None:
        self.transcript("automation", hours_idle=10, entrypoint="sdk-cli")
        _, payload = self.run_main("--apply")
        self.assertEqual(self.hook_calls(), [])
        ledger = json.loads(self.ledger.read_text())
        self.assertEqual(ledger["sessions"]["automation"]["status"], "not-interactive")

    def test_failures_retry_up_to_max_attempts(self) -> None:
        self.transcript("flaky", hours_idle=10)
        os.environ["FAKE_HOOK_EXIT"] = "5"
        try:
            for _ in range(3):
                code, _ = self.run_main("--apply", "--max-attempts", "2")
        finally:
            os.environ.pop("FAKE_HOOK_EXIT")
        self.assertEqual(len(self.hook_calls()), 2)
        ledger = json.loads(self.ledger.read_text())
        self.assertEqual(ledger["sessions"]["flaky"]["status"], "failed")
        self.assertEqual(ledger["sessions"]["flaky"]["attempts"], 2)

    def test_mark_only_absorbs_backlog(self) -> None:
        self.transcript("old", hours_idle=10)
        self.run_main("--mark-only")
        self.assertEqual(self.hook_calls(), [])
        self.assertEqual(json.loads(self.ledger.read_text())["sessions"]["old"]["status"], "marked")

    def test_max_sessions_defers_the_rest(self) -> None:
        for name in ("a", "b", "c"):
            self.transcript(name, hours_idle=10)
        _, payload = self.run_main("--apply", "--max-sessions", "2")
        self.assertEqual(len(self.hook_calls()), 2)
        self.assertEqual(sorted(c.get("result") for c in payload["data"]["candidates"]), ["deferred", "finalized", "finalized"])

    def test_repos_without_hook_are_not_scanned(self) -> None:
        (self.repo / "scripts/hooks/finalize_claude_session.py").unlink()
        self.transcript("old", hours_idle=10)
        _, payload = self.run_main("--apply")
        self.assertEqual(payload["data"]["repos"], [])
        self.assertEqual(payload["data"]["candidates"], [])
