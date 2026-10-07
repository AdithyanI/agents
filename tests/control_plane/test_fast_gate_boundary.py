from __future__ import annotations

from tests.control_plane.support import (
    TempDirTestCase,
    copy_repo_file,
    run_command,
    write_executable,
    write_text,
)


class FastGateBoundaryTests(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.root = self.temp_path / "repo"
        self.home = self.temp_path / "home"
        self.log = self.temp_path / "calls.log"
        for name in ("check-fast.sh", "check-agent-control-planes.sh", "check-full.sh"):
            copy_repo_file(f"scripts/{name}", self.root)
        for path in (
            "hooks/git/pre-commit",
            "scripts/check-repo-hygiene.sh",
            "scripts/check-skills-registry.sh",
            "scripts/check-plugins-registry.sh",
            "scripts/sync-managed-git-hooks.sh",
            "scripts/auto-apply-agent-control-planes.sh",
            "scripts/enroll-managed-repos.sh",
            "scripts/serve-control-plane-dashboard.sh",
            "scripts/install-control-plane-dashboard-launchagent.sh",
            "scripts/deploy-control-plane-dashboard.sh",
            "scripts/local-production-source.sh",
            "scripts/test-control-plane.sh",
            "scripts/audit-agent-runtime-drift.py",
            "tests/control_plane/test_local_production_source.sh",
        ):
            write_executable(self.root / path, '#!/bin/sh\nprintf "%s\\n" "$0 $*" >> "$GATE_LOG"\n')
        write_executable(
            self.root / "codex/scripts/check-codex-control-plane.sh",
            '#!/bin/sh\nprintf "%s\\n" "LIVE_RUNTIME_CHECK $*" >> "$GATE_LOG"\nexit 87\n',
        )
        bin_dir = self.temp_path / "bin"
        write_executable(
            bin_dir / "python3",
            '#!/bin/sh\nprintf "%s\\n" "python3 $*" >> "$GATE_LOG"\n'
            'case "$*" in *sync-native-env.py*)\n'
            '  test "$2" = "--check-sources" || exit 88\n'
            '  exit "${MAPPING_CHECK_EXIT:-0}" ;; esac\n',
        )
        write_text(
            self.home / "GitHub/scripts/setup/python-toolchain-env.sh",
            f'export PATH="{bin_dir}:$PATH"\n',
        )
        self.env = {
            "HOME": str(self.home),
            "PATH": f"{bin_dir}:/usr/bin:/bin",
            "AGENTS_MANAGED_REPO_CHECK_ROOT": str(self.root),
            "GATE_LOG": str(self.log),
        }

    def test_fast_gate_runs_source_mapping_check_without_live_runtime_check(self) -> None:
        result = run_command([str(self.root / "scripts/check-fast.sh")], env=self.env)
        calls = self.log.read_text()
        self.assertIn("sync-native-env.py --check-sources", calls)
        self.assertIn("test_codex_control_plane_check", calls)
        self.assertIn("sync-managed-git-hooks.sh --check", calls)
        self.assertNotIn("LIVE_RUNTIME_CHECK", calls)
        self.assertIn("runtime profile drift not checked", result.stdout)

    def test_fast_gate_does_not_ignore_failed_source_mapping_validation(self) -> None:
        result = run_command(
            [str(self.root / "scripts/check-fast.sh")],
            env={**self.env, "MAPPING_CHECK_EXIT": "86"},
            check=False,
        )
        self.assertEqual(result.returncode, 86)
        self.assertNotIn("[check-fast] passed", result.stdout)
        self.assertNotIn("LIVE_RUNTIME_CHECK", self.log.read_text())

    def test_full_entrypoints_invoke_live_runtime_check_and_propagate_failure(self) -> None:
        for script in ("check-agent-control-planes.sh", "check-full.sh"):
            with self.subTest(script=script):
                self.log.write_text("")
                result = run_command([str(self.root / "scripts" / script)], env=self.env, check=False)
                self.assertEqual(result.returncode, 87, result.stdout + result.stderr)
                self.assertIn("LIVE_RUNTIME_CHECK", self.log.read_text())
                self.assertNotIn("[check-full] passed", result.stdout)
