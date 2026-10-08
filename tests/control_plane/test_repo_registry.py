from __future__ import annotations

import copy
from pathlib import Path

from repos.repo_registry import client_config, client_registry, enabled_repositories, load_registry, resolve_path, validate_registry
from tests.control_plane.support import REPO_ROOT, TempDirTestCase, default_mcp_registry, init_git_repo, make_control_plane_root, repository_registry, run_command, write_json


class NeutralRepoRegistryTests(TempDirTestCase):
    def fixture(self):
        registry = repository_registry({"defaults": {"features": {"hooks": True, "apps": False}}, "repos": [{"path": "~/GitHub/pilot", "features": {"apps": True}}, {"path": "~/GitHub/claude-only"}]})
        registry["repos"][0]["clients"]["claude"]["enabled"] = True
        registry["repos"][1]["clients"]["codex"]["enabled"] = False
        registry["repos"][1]["clients"]["claude"]["enabled"] = True
        return registry

    def test_explicit_client_selection_preserves_shared_identity(self):
        registry = validate_registry(self.fixture(), home=self.temp_path)
        self.assertEqual([item["id"] for item in enabled_repositories(registry, "codex")], ["repo-0"])
        self.assertEqual([item["id"] for item in enabled_repositories(registry, "claude")], ["repo-0", "repo-1"])
        self.assertEqual(len(enabled_repositories(registry)), 2)
        projection = client_registry(registry, "codex")
        self.assertEqual(projection["repos"], [{"path": "~/GitHub/pilot", "features": {"apps": True}}])
        self.assertEqual(client_config(registry, registry["repos"][0], "codex"), {"features": {"hooks": True, "apps": True}})
        projection["defaults"]["features"]["hooks"] = False
        self.assertTrue(registry["defaults"]["codex"]["features"]["hooks"])
        registry["repos"][0]["path"] = "~/Work/renamed"
        self.assertEqual(enabled_repositories(registry, "codex")[0]["id"], "repo-0")
        self.assertEqual(resolve_path("~/Work/renamed", self.temp_path), (self.temp_path / "Work/renamed").resolve())

    def test_ambiguous_identity_and_implicit_client_enablement_are_rejected(self):
        mutations = [
            lambda data: data["repos"][1].update(id="repo-0"),
            lambda data: data["repos"][1].update(path=str(self.temp_path / "GitHub/pilot")),
            lambda data: data["repos"][0]["clients"].pop("claude"),
            lambda data: data["repos"][0]["clients"]["codex"].update(enabled="false"),
            lambda data: data["repos"][0]["clients"]["codex"]["config"].update(path="~/Wrong"),
        ]
        for mutate in mutations:
            data = copy.deepcopy(self.fixture())
            mutate(data)
            with self.assertRaises(ValueError):
                validate_registry(data, home=self.temp_path)

    def test_canonical_registry_enables_both_clients_everywhere(self):
        data = load_registry(REPO_ROOT / "repos/registry.json")
        self.assertEqual(len(enabled_repositories(data, "claude")), len(data["repos"]))
        self.assertEqual(len(enabled_repositories(data, "codex")), len(data["repos"]))
        self.assertIn("github", {repo["id"] for repo in data["repos"]})

    def test_codex_renderer_ignores_claude_only_repo_but_validates_its_mcp_assignment(self):
        root = make_control_plane_root(self.temp_path)
        codex_repo = init_git_repo(self.temp_path / "codex-repo")
        claude_repo = init_git_repo(self.temp_path / "claude-repo")
        data = repository_registry({"repos": [{"path": str(codex_repo)}, {"path": str(claude_repo)}]})
        data["repos"][1]["clients"] = {"codex": {"enabled": False}, "claude": {"enabled": True}}
        write_json(root / "repos/registry.json", data)
        mcp = default_mcp_registry()
        mcp["presets"]["cloudflare-docs"]["repos"] = [str(claude_repo)]
        write_json(root / "mcp/config/presets.json", mcp)
        run_command([str(REPO_ROOT / "codex/scripts/sync-repo-codex-configs.sh"), "--apply", "--registry", str(root / "repos/registry.json"), "--mcp-registry", str(root / "mcp/config/presets.json"), "--plugin-registry", str(root / "plugins/registry.json")])
        self.assertTrue((codex_repo / ".codex/config.toml").is_file())
        self.assertFalse((claude_repo / ".codex").exists())

    def test_trust_sync_revokes_disabled_codex_and_preserves_unrelated_roots(self):
        enabled = init_git_repo(self.temp_path / "enabled").resolve()
        disabled = init_git_repo(self.temp_path / "disabled").resolve()
        data = repository_registry({"repos": [{"path": str(enabled)}, {"path": str(disabled)}]})
        data["repos"][1]["clients"]["codex"]["enabled"] = False
        registry = write_json(self.temp_path / "repos.json", data)
        config = self.temp_path / "config.toml"
        config.write_text(f'[projects."{disabled}"]\ntrust_level = "trusted"\n\n[projects."/unrelated"]\ntrust_level = "trusted"\n')
        run_command([str(REPO_ROOT / "codex/scripts/sync-trusted-projects.sh"), "--apply", "--registry", str(registry), "--global-config", str(config)])
        self.assertIn(str(enabled), config.read_text())
        self.assertNotIn(str(disabled), config.read_text())
        self.assertIn("/unrelated", config.read_text())

    def test_shared_git_hooks_apply_to_claude_only_repositories(self):
        repo = init_git_repo(self.temp_path / "claude-only").resolve()
        data = repository_registry({"repos": [{"path": str(repo)}]})
        data["repos"][0]["clients"] = {"codex": {"enabled": False}, "claude": {"enabled": True}}
        registry = write_json(self.temp_path / "repos.json", data)
        run_command([str(REPO_ROOT / "scripts/sync-managed-git-hooks.sh"), "--apply", "--registry", str(registry)])
        actual = run_command(["git", "-C", str(repo), "config", "--local", "--get", "core.hooksPath"])
        self.assertEqual(actual.stdout.strip(), str(REPO_ROOT / "hooks/git"))

    def test_invalid_registry_fails_shell_consumers_without_mutation(self):
        config = self.temp_path / "config.toml"
        config.write_text('model = "user-choice"\n')
        registry = write_json(self.temp_path / "repos.json", {"version": 1, "repos": [{"path": "~/GitHub/pilot"}]})
        for script, extra in (("codex/scripts/sync-trusted-projects.sh", ["--global-config", str(config)]), ("scripts/sync-managed-git-hooks.sh", [])):
            with self.subTest(script=script):
                result = run_command([str(REPO_ROOT / script), "--apply", "--registry", str(registry), *extra], check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("repository ID", result.stderr)
                self.assertEqual(config.read_text(), 'model = "user-choice"\n')
