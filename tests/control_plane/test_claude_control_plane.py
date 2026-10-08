from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from claude.control_plane import ClaudeSyncError, STATE, atomic_write, probe_client, sync


class ClaudeControlPlaneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve() / "control"
        self.home = Path(self.tmp.name).resolve() / "home"
        self.repo = self.home / "GitHub/agents"
        self.other = self.home / "GitHub/other"
        self.repo.mkdir(parents=True)
        self.other.mkdir()
        for repo in (self.repo, self.other):
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
        self.write(self.root / "config/global.agents.md", "# Shared guidance\n")
        self.write(self.root / "claude/config/guidance.md", "# Claude overlay\n")
        self.json(self.root / "claude/config/policy.json", {"minimum_version": "2.1.281", "required": False})
        self.registry = {"version": 1, "defaults": {}, "repos": [self.entry("agents"), self.entry("other")]}
        self.json(self.root / "repos/registry.json", self.registry)
        self.skills = {"managed_skills": [
            {"skill": "global-helper", "scope": "global", "clients": ["codex", "claude"], "source_path": "skills-source/global-helper"},
            {"skill": "repo-helper", "scope": "repo", "clients": ["codex", "claude"], "repos": ["agents", "other"], "source_path": "skills-source/repo-helper"},
            {"skill": "codex-helper", "scope": "global", "source_path": "skills-source/codex-helper"},
        ], "managed_plugin_skills": [{"skill": "plugin-helper", "scope": "global", "clients": ["codex", "claude"]}]}
        for item in self.skills["managed_skills"]:
            self.write(self.root / item["source_path"] / "SKILL.md", "portable fixture")
        self.json(self.root / "skills/registry.json", self.skills)
        self.mcp = {"version": 3, "presets": {"docs": {"transport": "http", "url": "https://example.com/mcp", "repos": "all"}}}
        self.json(self.root / "mcp/config/presets.json", self.mcp)
        self.hooks = {"version": 1, "managed_hooks": []}
        self.json(self.root / "hooks/registry.json", self.hooks)
        self.json(self.home / STATE / "enabled.json", {"enabled": True})
        self.version_patch = patch("claude.control_plane.probe_client", return_value="2.1.285")
        self.version_patch.start()
        self.addCleanup(self.version_patch.stop)

    @staticmethod
    def entry(name: str) -> dict:
        return {"id": name, "path": f"~/GitHub/{name}", "clients": {"codex": {"enabled": True}, "claude": {"enabled": True}}}

    @staticmethod
    def write(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def json(self, path: Path, value: object) -> None:
        self.write(path, json.dumps(value) + "\n")

    def run_sync(self, mode: str = "apply", selected: set[Path] | None = None, **kwargs) -> int:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return sync(self.root, self.home, mode=mode, selected=selected, **kwargs)

    def hook(self, scope: str = "global") -> dict:
        return {"id": "safe-hook", "event": "SessionStart", "runtimes": ["claude"], "scope": scope, "command": "python3 safe.py --runtime {runtime}", "timeout": 5, **({"repos": ["agents"]} if scope == "repo" else {})}

    def test_apply_check_noop_and_readonly_modes(self) -> None:
        self.assertEqual(0, self.run_sync("dry-run"))
        self.assertFalse((self.home / ".claude").exists())
        self.assertEqual(1, self.run_sync("check"))
        self.assertFalse((self.home / STATE / "manifest.json").exists())
        self.assertEqual(0, self.run_sync())
        guidance = self.home / ".claude/CLAUDE.md"
        self.assertEqual("# Shared guidance\n\n# Claude overlay\n", guidance.read_text())
        self.assertFalse(guidance.is_symlink())
        self.assertTrue((self.home / ".claude/skills/global-helper").is_symlink())
        self.assertTrue((self.repo / ".claude/skills/repo-helper").is_symlink())
        self.assertFalse((self.home / ".claude/skills/codex-helper").exists())
        self.assertFalse((self.home / ".claude/skills/plugin-helper").exists())
        self.assertFalse((self.repo / "CLAUDE.md").exists())
        self.assertFalse((self.repo / ".claude/settings.json").exists())
        self.assertEqual(0, self.run_sync("check"))
        before = {p: p.lstat().st_mtime_ns for p in self.home.rglob("*")}
        self.assertEqual(0, self.run_sync())
        self.assertEqual(before, {p: p.lstat().st_mtime_ns for p in self.home.rglob("*")})

    def test_unknown_settings_servers_hooks_and_private_state_survive_disable(self) -> None:
        settings_path = self.home / ".claude/settings.json"
        custom_group = {"hooks": [{"type": "command", "command": "my-hook"}]}
        settings = {"model": "custom", "permissions": {"allow": ["Read"]}, "instructionFiles": ["CLAUDE.md"], "hooks": {"SessionStart": [custom_group]}}
        self.json(settings_path, settings)
        mcp_path = self.repo / ".mcp.json"
        handwritten = {"mcpServers": {"mine": {"type": "http", "url": "https://private.example"}}, "custom": True}
        self.json(mcp_path, handwritten)
        private = [self.home / ".claude.json", self.home / ".claude/credentials.json", self.home / ".claude/sessions/state", self.repo / ".claude/settings.local.json"]
        for path in private:
            self.write(path, "private unchanged")
        self.hooks["managed_hooks"] = [self.hook()]
        self.json(self.root / "hooks/registry.json", self.hooks)
        self.run_sync()
        updated = json.loads(settings_path.read_text())
        self.assertEqual(settings["instructionFiles"], updated["instructionFiles"])
        self.assertEqual([custom_group], updated["hooks"]["SessionStart"][:1])
        for repo in self.registry["repos"]:
            repo["clients"]["claude"]["enabled"] = False
        self.json(self.root / "repos/registry.json", self.registry)
        self.run_sync()
        self.assertEqual(settings, json.loads(settings_path.read_text()))
        self.assertEqual(handwritten, json.loads(mcp_path.read_text()))
        self.assertFalse((self.home / ".claude/CLAUDE.md").exists())
        self.assertFalse((self.repo / ".claude/skills/repo-helper").is_symlink())
        self.assertFalse((self.other / ".mcp.json").exists())
        self.assertTrue(all(path.read_text() == "private unchanged" for path in private))
        self.assertEqual(0, self.run_sync("check"))
        self.assertTrue(list((self.home / STATE / "backups").glob("*/index.json")))

    def test_scoped_prune_retains_unselected_repository(self) -> None:
        self.run_sync()
        other_mcp = (self.other / ".mcp.json").read_bytes()
        for repo in self.registry["repos"]:
            repo["clients"]["claude"]["enabled"] = False
        self.json(self.root / "repos/registry.json", self.registry)
        self.run_sync(selected={self.repo})
        self.assertFalse((self.repo / ".mcp.json").exists())
        self.assertEqual(other_mcp, (self.other / ".mcp.json").read_bytes())
        self.assertTrue((self.other / ".claude/skills/repo-helper").is_symlink())
        manifest = json.loads((self.home / STATE / "manifest.json").read_text())
        self.assertIn(str(self.other / ".mcp.json"), manifest["outputs"])

    def test_conflict_prevents_every_output_write(self) -> None:
        self.write(self.repo / ".claude/skills/repo-helper", "handwritten")
        with self.assertRaisesRegex(ClaudeSyncError, "Unmanaged file"):
            self.run_sync()
        self.assertFalse((self.home / ".claude").exists())
        self.assertFalse((self.repo / ".mcp.json").exists())
        self.assertFalse((self.home / STATE / "manifest.json").exists())

    def test_modified_managed_guidance_and_mcp_fail_before_mutation(self) -> None:
        self.run_sync()
        guidance = self.home / ".claude/CLAUDE.md"
        self.write(guidance, "personal override")
        with self.assertRaisesRegex(ClaudeSyncError, "Managed output was edited"):
            self.run_sync()
        self.write(guidance, "# Shared guidance\n\n# Claude overlay\n")
        self.json(self.repo / ".mcp.json", {"mcpServers": {"docs": {"url": "custom"}}})
        self.write(self.root / "config/global.agents.md", "new guidance")
        with self.assertRaisesRegex(ClaudeSyncError, "Managed MCP was edited"):
            self.run_sync()
        self.assertEqual("# Shared guidance\n\n# Claude overlay\n", guidance.read_text())

    def test_unowned_same_name_mcp_is_not_adopted(self) -> None:
        self.json(self.repo / ".mcp.json", {"mcpServers": {"docs": {"type": "http", "url": "https://example.com/mcp"}}})
        with self.assertRaisesRegex(ClaudeSyncError, "Unmanaged MCP name"):
            self.run_sync()
        self.assertFalse((self.home / ".claude").exists())

    def test_symlink_ancestor_and_manifest_are_protected(self) -> None:
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        (self.repo / ".claude").symlink_to(outside)
        with self.assertRaisesRegex(ClaudeSyncError, "symlink output ancestor"):
            self.run_sync()
        self.assertFalse(list(outside.iterdir()))
        self.assertFalse((self.home / ".claude").exists())
        (self.repo / ".claude").unlink()
        manifest = self.home / STATE / "manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.symlink_to(outside / "manifest")
        with self.assertRaisesRegex(ClaudeSyncError, "linked ownership manifest"):
            self.run_sync()

    def test_sparse_repo_is_skipped_without_creation(self) -> None:
        import shutil
        shutil.rmtree(self.other)
        self.assertEqual(0, self.run_sync())
        self.assertFalse(self.other.exists())
        self.assertEqual(0, self.run_sync("check"))

    def test_github_root_mapping_and_exact_selector(self) -> None:
        alternative = Path(self.tmp.name).resolve() / "different"
        target = alternative / "agents"
        target.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(target)], check=True)
        self.run_sync(github_root=alternative, selected={target})
        self.assertTrue((target / ".mcp.json").exists())
        self.assertFalse((self.repo / ".mcp.json").exists())
        with self.assertRaisesRegex(ClaudeSyncError, "Unknown exact repository"):
            self.run_sync(selected={self.home / "agents"})

    def test_removed_registry_repo_prunes_only_prior_owned_outputs(self) -> None:
        self.run_sync()
        self.write(self.other / ".claude/skills/private/SKILL.md", "personal")
        self.registry["repos"].pop()
        self.json(self.root / "repos/registry.json", self.registry)
        self.run_sync()
        self.assertFalse((self.other / ".mcp.json").exists())
        self.assertFalse((self.other / ".claude/skills/repo-helper").is_symlink())
        self.assertEqual("personal", (self.other / ".claude/skills/private/SKILL.md").read_text())

    def test_updates_backup_original_content_and_links(self) -> None:
        self.run_sync()
        self.write(self.root / "config/global.agents.md", "new guidance")
        self.skills["managed_skills"][0]["scope"] = "dormant"
        self.json(self.root / "skills/registry.json", self.skills)
        self.run_sync()
        backups = [json.loads(p.read_text()) for p in (self.home / STATE / "backups").glob("*/index.json")]
        flattened = [row for backup in backups for row in backup]
        self.assertTrue(any(row["before"]["kind"] == "link" for row in flattened))
        self.assertTrue(any(row["before"]["value"] == "# Shared guidance\n\n# Claude overlay\n" for row in flattened))

    def test_optional_absent_client_has_no_outputs(self) -> None:
        with patch("claude.control_plane.probe_client", return_value=None):
            self.assertEqual(0, self.run_sync())
        self.assertFalse((self.home / ".claude").exists())
        self.assertFalse((self.home / STATE / "manifest.json").exists())

    def test_machine_is_disabled_by_default_without_mutation(self) -> None:
        (self.home / STATE / "enabled.json").unlink()
        before = {p: p.lstat().st_mtime_ns for p in self.home.rglob("*")}
        for mode in ("apply", "dry-run", "check"):
            self.assertEqual(0, self.run_sync(mode))
        self.assertEqual(before, {p: p.lstat().st_mtime_ns for p in self.home.rglob("*")})
        self.assertFalse((self.home / ".claude").exists())
        self.assertEqual(0, self.run_sync(enable=True))
        self.assertEqual({"enabled": True}, json.loads((self.home / STATE / "enabled.json").read_text()))
        self.assertEqual(0, self.run_sync("check"))

    def test_machine_disable_cleans_outputs_without_cli(self) -> None:
        self.run_sync()
        with patch("claude.control_plane.probe_client", side_effect=AssertionError("disable must not require CLI")):
            self.assertEqual(0, self.run_sync(disable=True))
        self.assertFalse((self.home / ".claude/CLAUDE.md").exists())
        self.assertFalse((self.repo / ".mcp.json").exists())
        self.assertEqual({"enabled": False}, json.loads((self.home / STATE / "enabled.json").read_text()))
        self.assertEqual(0, self.run_sync("check"))
        self.assertEqual(0, self.run_sync())
        self.assertFalse((self.home / ".claude/CLAUDE.md").exists())

    def test_machine_enablement_requires_apply_and_disable_is_whole_machine(self) -> None:
        with self.assertRaisesRegex(ClaudeSyncError, "require --apply"):
            self.run_sync("dry-run", enable=True)
        with self.assertRaisesRegex(ClaudeSyncError, "entire machine"):
            self.run_sync(selected={self.repo}, disable=True)

    def test_failed_enable_does_not_opt_machine_in(self) -> None:
        enablement = self.home / STATE / "enabled.json"
        enablement.unlink()
        self.write(self.home / ".claude/CLAUDE.md", "personal")
        with self.assertRaisesRegex(ClaudeSyncError, "Unmanaged file"):
            self.run_sync(enable=True)
        self.assertFalse(enablement.exists())

    def test_existing_non_git_root_is_skipped_and_sparse_globals_preserved(self) -> None:
        import shutil
        self.run_sync()
        guidance = (self.home / ".claude/CLAUDE.md").read_text()
        shutil.rmtree(self.repo / ".git")
        shutil.rmtree(self.other)
        self.run_sync(selected={self.repo})
        self.assertEqual(guidance, (self.home / ".claude/CLAUDE.md").read_text())
        self.assertTrue((self.repo / ".mcp.json").exists())
        self.assertEqual(0, self.run_sync("check", selected={self.repo}))

    def test_unsupported_claude_config_is_rejected(self) -> None:
        self.registry["repos"][0]["clients"]["claude"]["config"] = {"model": "ignored"}
        self.json(self.root / "repos/registry.json", self.registry)
        with self.assertRaisesRegex(ClaudeSyncError, "Unsupported Claude config"):
            self.run_sync()
        self.assertFalse((self.home / ".claude").exists())

    def test_manifest_write_failure_rolls_back_and_retry_succeeds(self) -> None:
        manifest = self.home / STATE / "manifest.json"
        def fail_manifest(path, target):
            if path == manifest:
                raise OSError("simulated manifest failure")
            atomic_write(path, target)
        with patch("claude.control_plane.atomic_write", side_effect=fail_manifest):
            with self.assertRaisesRegex(OSError, "simulated manifest failure"):
                self.run_sync()
        self.assertFalse(manifest.exists())
        self.assertFalse((self.home / ".claude/CLAUDE.md").exists())
        self.assertFalse((self.repo / ".mcp.json").exists())
        self.assertFalse((self.home / STATE / "pending.json").exists())
        self.assertEqual(0, self.run_sync())
        self.assertEqual(0, self.run_sync("check"))

    def test_interrupted_journal_recovers_on_next_apply(self) -> None:
        self.run_sync()
        guidance = self.home / ".claude/CLAUDE.md"
        before = {"kind": "file", "value": guidance.read_text()}
        after = {"kind": "file", "value": "interrupted update"}
        self.write(guidance, after["value"])
        self.json(self.home / STATE / "pending.json", {"version": 1, "changes": [{"path": str(guidance), "before": before, "after": after, "owner": {"scope": "global", "kind": "text"}}]})
        with self.assertRaisesRegex(ClaudeSyncError, "needs recovery"):
            self.run_sync("check")
        self.assertEqual(0, self.run_sync())
        self.assertEqual(before["value"], guidance.read_text())
        self.assertEqual(0, self.run_sync("check"))

    def git_status(self, repo: Path) -> str:
        return subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, check=True).stdout

    def test_repo_local_skills_are_mirrored_and_outputs_stay_out_of_git(self) -> None:
        self.write(self.repo / ".agents/skills/local-skill/SKILL.md", "repo-owned")
        self.skills["unmanaged_repo_local_skills"] = [{"repo": "agents", "skill": "local-skill"}]
        self.json(self.root / "skills/registry.json", self.skills)
        exclude = self.repo / ".git/info/exclude"
        self.write(exclude, "# user pattern\n*.scratch\n")

        self.assertEqual(0, self.run_sync())
        link = self.repo / ".claude/skills/local-skill"
        self.assertEqual("../../.agents/skills/local-skill", os.readlink(link))
        self.assertEqual("repo-owned", (link / "SKILL.md").read_text())
        text = exclude.read_text()
        self.assertTrue(text.startswith("# user pattern\n*.scratch\n\n"))
        for entry in ("/.claude/skills/local-skill", "/.claude/skills/repo-helper", "/.mcp.json"):
            self.assertIn(entry + "\n", text)
        # Only the repo's own skill source is visible to Git; generated outputs are excluded.
        self.assertEqual(self.git_status(self.repo), "?? .agents/skills/local-skill/SKILL.md\n")
        self.assertEqual(self.git_status(self.other), "")
        self.assertEqual(0, self.run_sync("check"))

        for repo in self.registry["repos"]:
            repo["clients"]["claude"]["enabled"] = False
        self.json(self.root / "repos/registry.json", self.registry)
        self.assertEqual(0, self.run_sync())
        self.assertEqual("# user pattern\n*.scratch\n", exclude.read_text())
        self.assertFalse(link.is_symlink())

    def test_tracked_json_target_and_missing_local_skill_are_refused(self) -> None:
        self.json(self.other / ".mcp.json", {"mcpServers": {}})
        subprocess.run(["git", "-C", str(self.other), "add", ".mcp.json"], check=True)
        with self.assertRaisesRegex(ClaudeSyncError, "tracked"):
            self.run_sync()
        subprocess.run(["git", "-C", str(self.other), "rm", "-q", "--cached", ".mcp.json"], check=True)
        self.skills["unmanaged_repo_local_skills"] = [{"repo": "agents", "skill": "absent-skill"}]
        self.json(self.root / "skills/registry.json", self.skills)
        with self.assertRaisesRegex(ClaudeSyncError, "Declared repo-local skill is missing"):
            self.run_sync()
        self.assertFalse((self.home / STATE / "manifest.json").exists())


class ClaudeClientProbeTests(unittest.TestCase):
    def test_optional_missing_and_required_missing(self) -> None:
        with patch("claude.control_plane.shutil.which", return_value=None):
            self.assertIsNone(probe_client({}))
            with self.assertRaisesRegex(ClaudeSyncError, "Required Claude"):
                probe_client({"required": True})

    def test_old_version_fails_and_supported_version_succeeds(self) -> None:
        with patch("claude.control_plane.shutil.which", return_value="/usr/bin/claude"), patch("claude.control_plane.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "2.1.275 (Claude Code)\n", "")
            with self.assertRaisesRegex(ClaudeSyncError, "upgrade Claude Code"):
                probe_client({"minimum_version": "2.1.281"})
            run.return_value.stdout = "2.1.285 (Claude Code)\n"
            self.assertEqual("2.1.285", probe_client({"minimum_version": "2.1.281"}))


if __name__ == "__main__":
    unittest.main()
