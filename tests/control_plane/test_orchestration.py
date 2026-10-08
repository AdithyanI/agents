from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from tests.control_plane.support import (
    repository_registry,
    REPO_ROOT,
    TempDirTestCase,
    commit_all,
    copy_repo_file,
    init_git_repo,
    run_command,
    write_executable,
    write_json,
    write_text,
)


STUB_SCRIPT = """#!/usr/bin/env bash
set -euo pipefail
printf '%s|%s\\n' "$(basename "$0")" "$*" >> "${LOG_FILE:?}"
"""


PYTHON_STUB = """import os
from pathlib import Path
from unittest.mock import patch
import os
import sys
with Path(os.environ["LOG_FILE"]).open("a") as log:
    log.write(Path(__file__).name + "|" + " ".join(sys.argv[1:]) + "\\n")
"""


def restored_claude_state(home: Path, repo: Path) -> dict[Path, bytes]:
    """Seed managed setup and private runtime data a normal sync must preserve."""
    files = [
        write_text(home / ".claude/CLAUDE.md", "Restored Claude guidance\n"),
        write_json(home / ".claude/settings.json", {"permissions": {"defaultMode": "default"}, "theme": "dark"}),
        write_json(home / ".claude.json", {"oauthAccount": {"token": "PRIVATE_TEST_TOKEN"}, "projects": {str(repo): {"hasTrustDialogAccepted": True}}}),
        write_json(home / ".claude/.credentials.json", {"token": "PRIVATE_TEST_TOKEN"}),
        write_text(home / ".claude/projects/session.jsonl", '{"message":"private history"}\n'),
        write_text(home / ".claude/plans/current.md", "private plan\n"),
        write_text(repo / ".claude/CLAUDE.md", "@../AGENTS.md\n"),
        write_json(repo / ".claude/settings.local.json", {"permissions": {"allow": ["Read"]}, "custom": True}),
    ]
    return {path: path.read_bytes() for path in files}


def copy_runtime_resolver(root: Path) -> None:
    for source in ("codex/runtime.py", "hooks/__init__.py", "hooks/scripts/stop_feedback_turn.py"):
        copy_repo_file(source, root)


class AvailableCodexTestCase(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.codex_bin = write_executable(self.temp_path / "fixture-codex", "#!/bin/sh\nexit 0\n")
        override = patch.dict(os.environ, {"CODEX_BIN": str(self.codex_bin)})
        override.start()
        self.addCleanup(override.stop)


class SharedBootstrapWrapperTests(AvailableCodexTestCase):
    def _make_stub_control_plane(self) -> tuple[Path, Path]:
        root = self.temp_path / "stub-agents"
        copy_runtime_resolver(root)
        log_path = self.temp_path / "bootstrap.log"
        script_path = copy_repo_file(
            "scripts/bootstrap-machine-agent-control-planes.sh",
            root,
        )
        script_path.chmod(0o755)
        write_executable(root / "scripts/sync-skills-registry.sh", STUB_SCRIPT)
        write_executable(root / "scripts/sync-plugins-registry.sh", STUB_SCRIPT)
        write_executable(root / "scripts/sync-codex-plugin-installs.py", STUB_SCRIPT)
        write_executable(root / "scripts/sync-managed-git-hooks.sh", STUB_SCRIPT)
        write_executable(root / "codex/scripts/bootstrap-machine-codex.sh", STUB_SCRIPT)
        write_text(root / "scripts/retire-agent-clients.py", "raise RuntimeError('Retirement must remain opt-in')\n")
        write_text(root / "scripts/sync-codex-previews.py", PYTHON_STUB)
        write_text(root / "claude/scripts/sync-claude.py", PYTHON_STUB)
        return root, log_path

    def test_apply_mode_runs_shared_bootstrap_steps_with_forwarded_args(self) -> None:
        root, log_path = self._make_stub_control_plane()
        github_root = self.temp_path / "GitHub"
        repo_a = self.temp_path / "repo-a"
        repo_b = self.temp_path / "repo-b"
        home = self.temp_path / "home"

        result = run_command(
            [
                str(root / "scripts/bootstrap-machine-agent-control-planes.sh"),
                "--apply",
                "--github-root",
                str(github_root),
                "--repo",
                str(repo_a),
                "--repo",
                str(repo_b),
            ],
            env={"HOME": str(home), "LOG_FILE": str(log_path)},
        )

        self.assertEqual(
            [
                f"sync-skills-registry.sh|--apply --repo {repo_a} --repo {repo_b}",
                "sync-plugins-registry.sh|--apply",
                f"sync-codex-plugin-installs.py|--apply --no-input --codex-bin {self.codex_bin}",
                f"sync-codex-previews.py|--apply --github-root {github_root} --repo {repo_a} --repo {repo_b}",
                f"sync-managed-git-hooks.sh|--apply --repo {repo_a} --repo {repo_b}",
                f"bootstrap-machine-codex.sh|--apply --github-root {github_root} --repo {repo_a} --repo {repo_b}",
                f"sync-claude.py|--apply --github-root {github_root} --repo {repo_a} --repo {repo_b}",
            ],
            log_path.read_text(encoding="utf-8").splitlines(),
        )

    def test_normal_bootstrap_never_retires_restored_claude_or_private_state(self) -> None:
        root, log_path = self._make_stub_control_plane()
        home = self.temp_path / "home"
        repo = home / "GitHub/target"
        before = restored_claude_state(home, repo)

        for mode in ("--dry-run", "--apply"):
            with self.subTest(mode=mode):
                result = run_command(
                    [str(root / "scripts/bootstrap-machine-agent-control-planes.sh"), mode, "--repo", str(repo)],
                    env={"HOME": str(home), "LOG_FILE": str(log_path)},
                )
                self.assertEqual({path: path.read_bytes() for path in before}, before)
                self.assertNotIn("retire-agent-clients", result.stdout)
                self.assertFalse((home / ".local/state/agents-control-plane/retired-client-backups").exists())

    def test_absent_codex_keeps_shared_bootstrap_and_claude_running(self) -> None:
        root, log_path = self._make_stub_control_plane()
        # An optional client must not require even its component executables.
        (root / "codex/scripts/bootstrap-machine-codex.sh").unlink()
        (root / "scripts/sync-codex-plugin-installs.py").unlink()
        (root / "scripts/sync-codex-previews.py").unlink()
        repo = self.temp_path / "claude-pilot"
        result = run_command([
            str(root / "scripts/bootstrap-machine-agent-control-planes.sh"), "--apply", "--repo", str(repo),
        ], env={"CODEX_BIN": str(self.temp_path / "absent-codex"), "LOG_FILE": str(log_path)})
        self.assertIn("SKIP: Codex executable unavailable", result.stdout)
        self.assertEqual(log_path.read_text().splitlines(), [
            f"sync-skills-registry.sh|--apply --repo {repo}",
            "sync-plugins-registry.sh|--apply",
            f"sync-managed-git-hooks.sh|--apply --repo {repo}",
            f"sync-claude.py|--apply --github-root {self.temp_path / 'home/GitHub'} --repo {repo}",
        ])

    def test_present_codex_failure_is_not_treated_as_optional(self) -> None:
        root, log_path = self._make_stub_control_plane()
        write_executable(root / "codex/scripts/bootstrap-machine-codex.sh", STUB_SCRIPT + "exit 9\n")
        result = run_command([str(root / "scripts/bootstrap-machine-agent-control-planes.sh"), "--apply"],
                             env={"LOG_FILE": str(log_path)}, check=False)
        self.assertEqual(result.returncode, 9)
        self.assertNotIn("SKIP: Codex", result.stdout)



class SharedCheckWrapperTests(AvailableCodexTestCase):
    def _make_stub_control_plane(self) -> tuple[Path, Path]:
        root = self.temp_path / "stub-agents"
        copy_runtime_resolver(root)
        log_path = self.temp_path / "check.log"
        script_path = copy_repo_file(
            "scripts/check-agent-control-planes.sh",
            root,
        )
        script_path.chmod(0o755)
        write_executable(root / "scripts/check-repo-hygiene.sh", STUB_SCRIPT)
        write_executable(root / "scripts/check-skills-registry.sh", STUB_SCRIPT)
        write_executable(root / "scripts/check-plugins-registry.sh", STUB_SCRIPT)
        write_executable(root / "scripts/sync-managed-git-hooks.sh", STUB_SCRIPT)
        write_executable(root / "codex/scripts/check-codex-control-plane.sh", STUB_SCRIPT)
        write_executable(root / "scripts/audit-agent-runtime-drift.py", STUB_SCRIPT)
        write_executable(root / "scripts/test-control-plane.sh", STUB_SCRIPT)
        write_text(root / "scripts/retire-agent-clients.py", "raise RuntimeError('Retirement must remain opt-in')\n")
        write_text(root / "scripts/sync-codex-previews.py", PYTHON_STUB)
        write_text(root / "claude/scripts/sync-claude.py", PYTHON_STUB)
        return root, log_path

    def test_repo_filter_is_forwarded_to_codex_checks(self) -> None:
        root, log_path = self._make_stub_control_plane()
        repo_a = self.temp_path / "repo-a"
        repo_b = self.temp_path / "repo-b"

        run_command(
            [
                str(root / "scripts/check-agent-control-planes.sh"),
                "--repo",
                str(repo_a),
                "--repo",
                str(repo_b),
            ],
            env={"LOG_FILE": str(log_path)},
        )

        self.assertEqual(
            [
                "check-repo-hygiene.sh|",
                "check-skills-registry.sh|",
                "check-plugins-registry.sh|",
                f"sync-codex-previews.py|--check --repo {repo_a} --repo {repo_b}",
                f"sync-managed-git-hooks.sh|--check --repo {repo_a} --repo {repo_b}",
                f"check-codex-control-plane.sh|--repo {repo_a} --repo {repo_b}",
                f"sync-claude.py|--check --repo {repo_a} --repo {repo_b}",
                "audit-agent-runtime-drift.py|--plain --skip-control-plane-check --no-input",
                "test-control-plane.sh|",
            ],
            log_path.read_text(encoding="utf-8").splitlines(),
        )

    def test_health_check_accepts_restored_claude_without_touching_private_state(self) -> None:
        root, log_path = self._make_stub_control_plane()
        home = self.temp_path / "home"
        repo = home / "GitHub/target"
        before = restored_claude_state(home, repo)

        result = run_command(
            [str(root / "scripts/check-agent-control-planes.sh"), "--repo", str(repo)],
            env={"HOME": str(home), "LOG_FILE": str(log_path)},
        )

        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.assertNotIn("retire-agent-clients", result.stdout)
        self.assertFalse((home / ".local/state/agents-control-plane/retired-client-backups").exists())

    def test_absent_codex_keeps_shared_claude_and_test_checks(self) -> None:
        root, log_path = self._make_stub_control_plane()
        (root / "codex/scripts/check-codex-control-plane.sh").unlink()
        (root / "scripts/sync-codex-previews.py").unlink()
        repo = self.temp_path / "claude-pilot"
        result = run_command([str(root / "scripts/check-agent-control-planes.sh"), "--repo", str(repo)],
                             env={"CODEX_BIN": str(self.temp_path / "absent-codex"), "LOG_FILE": str(log_path)})
        self.assertIn("SKIP: Codex executable unavailable", result.stdout)
        self.assertEqual(log_path.read_text().splitlines(), [
            "check-repo-hygiene.sh|", "check-skills-registry.sh|", "check-plugins-registry.sh|",
            f"sync-managed-git-hooks.sh|--check --repo {repo}",
            f"sync-claude.py|--check --repo {repo}",
            "audit-agent-runtime-drift.py|--plain --skip-control-plane-check --no-input",
            "test-control-plane.sh|",
        ])

    def test_present_codex_drift_fails_shared_check(self) -> None:
        root, log_path = self._make_stub_control_plane()
        write_executable(root / "codex/scripts/check-codex-control-plane.sh", STUB_SCRIPT + "exit 17\n")
        result = run_command([str(root / "scripts/check-agent-control-planes.sh")],
                             env={"LOG_FILE": str(log_path)}, check=False)
        self.assertEqual(result.returncode, 17)
        self.assertIn("check-codex-control-plane.sh|", log_path.read_text())
        self.assertNotIn("SKIP: Codex", result.stdout)



class AutoApplyRoutingTests(AvailableCodexTestCase):
    def _make_agents_repo(self) -> tuple[Path, Path, Path]:
        root = init_git_repo(self.temp_path / "agents-repo")
        copy_runtime_resolver(root)
        log_path = self.temp_path / "auto-apply.log"
        stamp_file = self.temp_path / "last-reconciled.sha"

        for relative_path in (
            "plugins/registry.json",
            "skills/registry.json",
            "mcp/config/presets.json",
            "repos/registry.json",
            "hooks/registry.json",
            "dev-servers/registry.json",
        ):
            write_text(root / relative_path, "{}\n")

        write_executable(root / "scripts/bootstrap-machine-agent-control-planes.sh", STUB_SCRIPT)
        write_executable(root / "scripts/sync-skills-registry.sh", STUB_SCRIPT)
        write_executable(root / "scripts/sync-plugins-registry.sh", STUB_SCRIPT)
        write_executable(root / "scripts/sync-managed-git-hooks.sh", STUB_SCRIPT)
        write_executable(root / "codex/scripts/bootstrap-machine-codex.sh", STUB_SCRIPT)
        write_text(root / "claude/scripts/sync-claude.py", PYTHON_STUB)
        commit_all(root, "initial")
        return root, log_path, stamp_file

    def _run_auto_apply(
        self,
        root: Path,
        log_path: Path,
        stamp_file: Path,
        *,
        env: dict[str, str] | None = None,
    ) -> str:
        home = self.temp_path / "home"
        result = run_command(
            [
                str(REPO_ROOT / "scripts/auto-apply-agent-control-planes.sh"),
                "--apply",
                "--agents-repo",
                str(root),
                "--github-root",
                str(self.temp_path / "GitHub"),
                "--stamp-file",
                str(stamp_file),
            ],
            env={
                "HOME": str(home),
                "LOG_FILE": str(log_path),
                **(env or {}),
            },
        )
        return result.stdout

    def test_first_reconcile_runs_root_bootstrap_only(self) -> None:
        root, log_path, stamp_file = self._make_agents_repo()

        output = self._run_auto_apply(root, log_path, stamp_file)

        self.assertIn("APPLY: no prior reconcile stamp", output)
        self.assertEqual(
            [
                f"bootstrap-machine-agent-control-planes.sh|--apply --github-root {self.temp_path / 'GitHub'}",
            ],
            log_path.read_text(encoding="utf-8").splitlines(),
        )
        head_sha = run_command(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
        ).stdout.strip()
        self.assertEqual(head_sha, stamp_file.read_text(encoding="utf-8").strip())

    def test_skills_registry_change_triggers_skill_sync_and_codex_bootstrap(self) -> None:
        root, log_path, stamp_file = self._make_agents_repo()
        baseline_sha = run_command(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
        ).stdout.strip()
        write_text(stamp_file, baseline_sha + "\n")

        write_json(
            root / "skills/registry.json",
            {
                "managed_skills": [],
                "paths": {
                    "github_root": "~/GitHub",
                },
                "unmanaged_repo_local_skills": [],
            },
        )
        commit_all(root, "update skills registry")

        output = self._run_auto_apply(root, log_path, stamp_file)

        self.assertIn("APPLY: detected shared agent control-plane changes", output)
        self.assertEqual(
            [
                "sync-skills-registry.sh|--apply",
                f"bootstrap-machine-codex.sh|--apply --github-root {self.temp_path / 'GitHub'}",
                f"sync-claude.py|--apply --github-root {self.temp_path / 'GitHub'}",
            ],
            log_path.read_text(encoding="utf-8").splitlines(),
        )

    def test_plugins_registry_change_triggers_plugin_sync_and_codex_bootstrap(self) -> None:
        root, log_path, stamp_file = self._make_agents_repo()
        baseline_sha = run_command(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
        ).stdout.strip()
        write_text(stamp_file, baseline_sha + "\n")

        write_json(
            root / "plugins/registry.json",
            {
                "version": 1,
                "paths": {
                    "github_root": "~/GitHub",
                },
                "managed_plugins": [],
                "unmanaged_repo_local_plugins": [],
            },
        )
        commit_all(root, "update plugins registry")

        output = self._run_auto_apply(root, log_path, stamp_file)

        self.assertIn("APPLY: detected shared agent control-plane changes", output)
        self.assertEqual(
            [
                "sync-plugins-registry.sh|--apply",
                f"bootstrap-machine-codex.sh|--apply --github-root {self.temp_path / 'GitHub'}",
            ],
            log_path.read_text(encoding="utf-8").splitlines(),
        )

    def test_hooks_registry_change_triggers_codex_bootstrap(self) -> None:
        root, log_path, stamp_file = self._make_agents_repo()
        baseline_sha = run_command(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
        ).stdout.strip()
        write_text(stamp_file, baseline_sha + "\n")

        write_json(
            root / "hooks/registry.json",
            {
                "managed_hooks": [],
                "version": 1,
            },
        )
        commit_all(root, "update hooks registry")

        output = self._run_auto_apply(root, log_path, stamp_file)

        self.assertIn("APPLY: detected shared agent control-plane changes", output)
        self.assertEqual(
            [
                f"bootstrap-machine-codex.sh|--apply --github-root {self.temp_path / 'GitHub'}",
                f"sync-claude.py|--apply --github-root {self.temp_path / 'GitHub'}",
            ],
            log_path.read_text(encoding="utf-8").splitlines(),
        )

    def test_neutral_registry_and_loader_changes_reconcile_all_client_surfaces(self) -> None:
        root, log_path, stamp_file = self._make_agents_repo()
        baseline_sha = run_command(["git", "-C", str(root), "rev-parse", "HEAD"]).stdout.strip()
        write_text(stamp_file, baseline_sha + "\n")

        for source in ("repos/registry.json", "repos/repo_registry.py"):
            with self.subTest(source=source):
                write_text(root / source, "# changed repository source\n")
                commit_all(root, "update " + source)
                if log_path.exists():
                    log_path.unlink()
                self._run_auto_apply(root, log_path, stamp_file)
                self.assertEqual(log_path.read_text().splitlines(), [
                    f"bootstrap-machine-agent-control-planes.sh|--apply --github-root {self.temp_path / 'GitHub'}",
                ])
                current_sha = run_command(["git", "-C", str(root), "rev-parse", "HEAD"]).stdout.strip()
                self.assertEqual(stamp_file.read_text().strip(), current_sha)

    def test_claude_renderer_change_reconciles_claude_once(self) -> None:
        root, log_path, stamp_file = self._make_agents_repo()
        baseline_sha = run_command(["git", "-C", str(root), "rev-parse", "HEAD"]).stdout.strip()
        write_text(stamp_file, baseline_sha + "\n")
        write_text(root / "claude/scripts/sync-claude.py", PYTHON_STUB + "\n# updated renderer\n")
        commit_all(root, "update Claude renderer")

        self._run_auto_apply(root, log_path, stamp_file)
        expected = [f"sync-claude.py|--apply --github-root {self.temp_path / 'GitHub'}"]
        self.assertEqual(log_path.read_text().splitlines(), expected)
        output = self._run_auto_apply(root, log_path, stamp_file)
        self.assertIn("SKIP: already reconciled", output)
        self.assertEqual(log_path.read_text().splitlines(), expected)

    def test_shared_skill_renderer_changes_reconcile_skills_and_both_clients(self) -> None:
        root, log_path, stamp_file = self._make_agents_repo()
        baseline_sha = run_command(["git", "-C", str(root), "rev-parse", "HEAD"]).stdout.strip()
        write_text(stamp_file, baseline_sha + "\n")
        for source in ("scripts/sync-skills-registry.py", "scripts/sync-skills-registry.sh"):
            with self.subTest(source=source):
                if source.endswith(".sh"):
                    write_executable(root / source, STUB_SCRIPT + "\n# updated renderer\n")
                else:
                    write_text(root / source, "# updated renderer\n")
                commit_all(root, "update " + source)
                if log_path.exists():
                    log_path.unlink()
                self._run_auto_apply(root, log_path, stamp_file)
                self.assertEqual(log_path.read_text().splitlines(), [
                    "sync-skills-registry.sh|--apply",
                    f"bootstrap-machine-codex.sh|--apply --github-root {self.temp_path / 'GitHub'}",
                    f"sync-claude.py|--apply --github-root {self.temp_path / 'GitHub'}",
                ])

    def test_root_bootstrap_wrapper_change_runs_root_bootstrap(self) -> None:
        root, log_path, stamp_file = self._make_agents_repo()
        baseline_sha = run_command(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
        ).stdout.strip()
        write_text(stamp_file, baseline_sha + "\n")

        write_executable(
            root / "scripts/bootstrap-machine-agent-control-planes.sh",
            STUB_SCRIPT + "\n# changed\n",
        )
        commit_all(root, "update root bootstrap wrapper")

        output = self._run_auto_apply(
            root,
            log_path,
            stamp_file,
            env={"PATH": "/usr/bin:/bin"},
        )

        self.assertIn("APPLY: detected shared agent control-plane changes", output)
        self.assertEqual(
            [
                f"bootstrap-machine-agent-control-planes.sh|--apply --github-root {self.temp_path / 'GitHub'}",
            ],
            log_path.read_text(encoding="utf-8").splitlines(),
        )

    def test_dev_server_registry_change_runs_root_bootstrap(self) -> None:
        root, log_path, stamp_file = self._make_agents_repo()
        baseline_sha = run_command(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
        ).stdout.strip()
        write_text(stamp_file, baseline_sha + "\n")

        write_json(
            root / "dev-servers/registry.json",
            {
                "version": 1,
                "managed_dev_servers": [
                    {
                        "repo": "repo-a",
                        "servers": [
                            {
                                "name": "Preview",
                                "runtimeExecutable": "pnpm",
                                "runtimeArgs": ["dev"],
                                "port": 3000,
                            }
                        ],
                    }
                ],
            },
        )
        commit_all(root, "update dev server registry")

        output = self._run_auto_apply(root, log_path, stamp_file)

        self.assertIn("APPLY: detected shared agent control-plane changes", output)
        self.assertEqual(
            [
                f"bootstrap-machine-agent-control-planes.sh|--apply --github-root {self.temp_path / 'GitHub'}",
            ],
            log_path.read_text(encoding="utf-8").splitlines(),
        )

    def test_mcp_scope_change_runs_shared_bootstrap(self) -> None:
        root, log_path, stamp_file = self._make_agents_repo()
        baseline_sha = run_command(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
        ).stdout.strip()
        write_text(stamp_file, baseline_sha + "\n")

        write_json(
            root / "mcp/config/presets.json",
            {
                "version": 3,
                "presets": {
                    "playwright": {
                        "transport": "stdio",
                        "command": "npx",
                        "args": ["-y", "@playwright/mcp@latest"],
                        "repos": ["~/GitHub/agents"],
                    }
                },
            },
        )
        commit_all(root, "update MCP targets")

        output = self._run_auto_apply(root, log_path, stamp_file)

        self.assertIn("APPLY: detected shared agent control-plane changes", output)
        self.assertEqual(
            [
                f"bootstrap-machine-agent-control-planes.sh|--apply --github-root {self.temp_path / 'GitHub'}",
            ],
            log_path.read_text(encoding="utf-8").splitlines(),
        )

    def test_repo_inventory_change_runs_shared_bootstrap(self) -> None:
        root, log_path, stamp_file = self._make_agents_repo()
        baseline_sha = run_command(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
        ).stdout.strip()
        write_text(stamp_file, baseline_sha + "\n")

        write_json(
            root / "repos/registry.json",
            repository_registry({
                "defaults": {},
                "repos": [{"path": "~/GitHub/agents"}],
            }),
        )
        commit_all(root, "update repo inventory")

        output = self._run_auto_apply(root, log_path, stamp_file)

        self.assertIn("APPLY: detected shared agent control-plane changes", output)
        self.assertEqual(
            [
                f"bootstrap-machine-agent-control-planes.sh|--apply --github-root {self.temp_path / 'GitHub'}",
            ],
            log_path.read_text(encoding="utf-8").splitlines(),
        )

    def test_absent_codex_does_not_block_shared_skill_or_claude_reconcile(self) -> None:
        root, log_path, stamp_file = self._make_agents_repo()
        baseline_sha = run_command(["git", "-C", str(root), "rev-parse", "HEAD"]).stdout.strip()
        write_text(stamp_file, baseline_sha + "\n")
        write_text(root / "skills/registry.json", '{"managed_skills": []}\n')
        (root / "codex/scripts/bootstrap-machine-codex.sh").unlink()
        commit_all(root, "update shared skills on a Claude machine")
        output = self._run_auto_apply(root, log_path, stamp_file,
                                     env={"CODEX_BIN": str(self.temp_path / "absent-codex")})
        self.assertIn("SKIP: Codex executable unavailable", output)
        self.assertEqual(log_path.read_text().splitlines(), [
            "sync-skills-registry.sh|--apply",
            f"sync-claude.py|--apply --github-root {self.temp_path / 'GitHub'}",
        ])
        current_sha = run_command(["git", "-C", str(root), "rev-parse", "HEAD"]).stdout.strip()
        self.assertEqual(stamp_file.read_text().strip(), current_sha)
