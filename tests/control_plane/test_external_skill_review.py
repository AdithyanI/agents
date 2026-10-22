from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from unittest import mock

from tests.control_plane.support import REPO_ROOT, TempDirTestCase, commit_all, init_git_repo, run_command, write_json

spec = importlib.util.spec_from_file_location("external_review", REPO_ROOT / "scripts/refresh-external-skills.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ExternalSkillReviewTests(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.root = init_git_repo(self.temp_path / "control")
        self.source = self.root / "skills-source/external/example"
        self.source.mkdir(parents=True)
        (self.source / "SKILL.md").write_text("accepted content\n")
        self.registry = write_json(self.root / "skills/registry.json", {"managed_skills": [{"skill": "example", "origin": "external", "source_path": "skills-source/external/example", "upstream_ref": "owner/repo:skill@main"}]})
        commit_all(self.root, "accepted")
        self.upstream = init_git_repo(self.temp_path / "upstream")
        (self.upstream / "skill").mkdir()
        (self.upstream / "skill/SKILL.md").write_text("candidate instructions\n")
        commit_all(self.upstream, "candidate")
        self.sha = run_command(["git", "-C", str(self.upstream), "rev-parse", "HEAD"]).stdout.strip()

    def run_refresh(self, *args):
        with mock.patch.object(sys, "argv", ["refresh", str(self.registry), *args]), mock.patch.object(module, "sparse_checkout_repo", return_value=self.upstream):
            return module.main()

    def test_scheduled_check_leaves_active_instructions_and_registry_unchanged(self):
        before = self.registry.read_bytes()
        candidate = self.temp_path / "review"
        self.assertEqual(self.run_refresh("--candidate-dir", str(candidate)), 0)
        self.assertEqual((self.source / "SKILL.md").read_text(), "accepted content\n")
        self.assertEqual(self.registry.read_bytes(), before)
        self.assertEqual((candidate / "example" / self.sha / "SKILL.md").read_text(), "candidate instructions\n")

    def test_apply_requires_explicit_review_and_rejects_branch_movement(self):
        with self.assertRaises(SystemExit) as failed:
            self.run_refresh("--apply")
        self.assertEqual(failed.exception.code, 2)
        before = self.registry.read_bytes()
        self.assertEqual(self.run_refresh("--apply", "--skill", "example", "--reviewed-revision", "0" * 40), 1)
        self.assertEqual(self.registry.read_bytes(), before)
        self.assertEqual((self.source / "SKILL.md").read_text(), "accepted content\n")

    def test_exact_reviewed_revision_is_promoted_and_recorded(self):
        self.assertEqual(self.run_refresh("--apply", "--skill", "example", "--reviewed-revision", self.sha), 0)
        self.assertEqual((self.source / "SKILL.md").read_text(), "candidate instructions\n")
        self.assertEqual(json.loads(self.registry.read_text())["managed_skills"][0]["accepted_revision"], self.sha)

    def test_review_cannot_copy_symlink_escape(self):
        (self.upstream / "skill/escaped").symlink_to(self.temp_path)
        self.assertEqual(self.run_refresh("--apply", "--skill", "example", "--reviewed-revision", self.sha), 1)
        self.assertEqual((self.source / "SKILL.md").read_text(), "accepted content\n")
