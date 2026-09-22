from __future__ import annotations

from tests.control_plane.support import (
    REPO_ROOT,
    TempDirTestCase,
    init_git_repo,
    read_json,
    run_command,
    write_json,
)


class ManagedRepoEnrollmentTests(TempDirTestCase):
    def test_exact_exclusion_survives_repeated_auto_enrollment_and_preserves_recovery(self) -> None:
        home = self.temp_path / "home"
        github_root = home / "GitHub"
        recovery = init_git_repo(github_root / "modal_functions")
        active = init_git_repo(github_root / "win")
        similar_name = init_git_repo(github_root / "modal_functions_examples")
        (recovery / "recovery-source.py").write_text("preserved historical source\n")
        registry = self.temp_path / "repo-bootstrap.json"
        write_json(registry, {"defaults": {}, "repos": [{"path": str(active)}],
                              "auto_enrollment_exclusions": ["~/GitHub/modal_functions"]})
        command = [str(REPO_ROOT / "scripts/enroll-managed-repos.sh"), "--apply",
                   "--github-root", str(github_root), "--registry", str(registry)]
        first = run_command(command, env={"HOME": str(home)})
        second = run_command(command, env={"HOME": str(home)})
        data = read_json(registry)
        self.assertEqual({item["path"] for item in data["repos"]}, {str(active), "~/GitHub/modal_functions_examples"})
        self.assertIn("SKIP auto-enrollment excluded ~/GitHub/modal_functions", first.stdout)
        self.assertNotIn("ADD ", second.stdout)
        self.assertTrue((recovery / ".git").is_dir())
        self.assertEqual((recovery / "recovery-source.py").read_text(), "preserved historical source\n")
        self.assertTrue(similar_name.is_dir())

    def test_exclusion_does_not_implicitly_remove_existing_enrollment(self) -> None:
        github_root = self.temp_path / "GitHub"
        recovery = init_git_repo(github_root / "modal_functions")
        registry = self.temp_path / "repo-bootstrap.json"
        write_json(registry, {"defaults": {}, "repos": [{"path": str(recovery)}],
                              "auto_enrollment_exclusions": [str(recovery)]})
        before = registry.read_bytes()
        run_command([str(REPO_ROOT / "scripts/enroll-managed-repos.sh"), "--apply",
                     "--github-root", str(github_root), "--registry", str(registry)])
        self.assertEqual(before, registry.read_bytes())

    def test_invalid_exclusion_policy_fails_before_registry_mutation(self) -> None:
        github_root = self.temp_path / "GitHub"
        init_git_repo(github_root / "new")
        registry = self.temp_path / "repo-bootstrap.json"
        for invalid in ("modal_functions", [None], [""], ["relative/path"]):
            with self.subTest(invalid=invalid):
                write_json(registry, {"defaults": {}, "repos": [], "auto_enrollment_exclusions": invalid})
                before = registry.read_bytes()
                result = run_command([str(REPO_ROOT / "scripts/enroll-managed-repos.sh"), "--apply",
                                      "--github-root", str(github_root), "--registry", str(registry)], check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("auto_enrollment_exclusions", result.stderr)
                self.assertEqual(before, registry.read_bytes())

    def test_enrolls_direct_child_git_repos_without_remote_requirement(self) -> None:
        github_root = self.temp_path / "GitHub"
        already = init_git_repo(github_root / "already")
        new_repo = init_git_repo(github_root / "new-repo")
        nested_repo = init_git_repo(new_repo / "nested")
        (github_root / "not-git").mkdir(parents=True)

        registry_path = self.temp_path / ".agents/codex/config/repo-bootstrap.json"
        write_json(
            registry_path,
            {
                "defaults": {
                    "model": "gpt-5.5",
                },
                "repos": [
                    {
                        "path": str(already),
                    }
                ],
            },
        )

        result = run_command(
            [
                str(REPO_ROOT / "scripts/enroll-managed-repos.sh"),
                "--apply",
                "--github-root",
                str(github_root),
                "--registry",
                str(registry_path),
            ]
        )

        self.assertIn("ADD", result.stdout)
        data = read_json(registry_path)
        paths = [item["path"] for item in data["repos"]]
        self.assertEqual(
            [
                str(already),
                str(new_repo.resolve()),
            ],
            paths,
        )
        self.assertNotIn(str(nested_repo), paths)

    def test_dry_run_reports_missing_repos_without_writing_registry(self) -> None:
        github_root = self.temp_path / "GitHub"
        new_repo = init_git_repo(github_root / "new-repo")
        registry_path = self.temp_path / ".agents/codex/config/repo-bootstrap.json"
        write_json(registry_path, {"defaults": {}, "repos": []})
        before = registry_path.read_text(encoding="utf-8")

        result = run_command(
            [
                str(REPO_ROOT / "scripts/enroll-managed-repos.sh"),
                "--github-root",
                str(github_root),
                "--registry",
                str(registry_path),
            ]
        )

        self.assertIn(f"ADD {new_repo.resolve()}", result.stdout)
        self.assertEqual(before, registry_path.read_text(encoding="utf-8"))
