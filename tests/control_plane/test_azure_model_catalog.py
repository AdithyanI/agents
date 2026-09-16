from __future__ import annotations

import copy
import json
import sys

from tests.control_plane.support import REPO_ROOT, TempDirTestCase, run_command, write_json, write_text


class AzureModelCatalogTests(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.canonical = self.temp_path / "canonical"
        self.runtime = self.temp_path / "runtime"
        self.profile = write_text(
            self.canonical / "azure-astra.config.toml",
            'model = "gpt-6-astra"\nmodel_provider = "azure"\n'
            'model_catalog_json = "model-catalogs/azure-astra.json"\n',
        )
        self.models = [
            {
                "slug": "gpt-6-astra", "use_responses_lite": True,
                "context_window": 272000, "effective_context_window_percent": 95,
                "model_messages": {"base_instructions": "fixture instructions"},
                "future_field": {"preserve": True},
            },
            {"slug": "gpt-5.6-luna", "use_responses_lite": True, "context_window": 272000},
        ]
        self.source = write_json(self.runtime / "models_cache.json", {"models": self.models, "etag": "fixture"})
        self.target = self.runtime / "model-catalogs/azure-astra.json"

    def run_catalog(self, *args: str, check: bool = True):
        return run_command(
            [sys.executable, str(REPO_ROOT / "codex/scripts/sync-azure-model-catalog.py"),
             "--canonical-dir", str(self.canonical), "--runtime-dir", str(self.runtime), *args],
            check=check,
        )

    def test_apply_preserves_source_context_instructions_and_other_models(self) -> None:
        before = self.source.read_bytes()
        self.run_catalog()
        self.assertFalse(self.target.parent.exists(), "dry-run must not create runtime assets")
        self.run_catalog("--apply")
        expected = copy.deepcopy(self.models)
        expected[0]["use_responses_lite"] = False
        self.assertEqual(json.loads(self.target.read_text()), {"models": expected})
        self.assertEqual(self.source.read_bytes(), before, "subscription catalog must remain untouched")
        timestamp = self.target.stat().st_mtime_ns
        self.run_catalog("--apply")
        self.assertEqual(self.target.stat().st_mtime_ns, timestamp)
        self.run_catalog("--check")

    def test_refresh_updates_metadata_and_invalid_source_preserves_last_good_output(self) -> None:
        self.run_catalog("--apply")
        self.models[0]["context_window"] = 300000
        write_json(self.source, {"models": self.models})
        # Runtime validation is structural; cache refreshes alone must not break health checks.
        self.run_catalog("--check")
        self.run_catalog("--apply")
        self.assertEqual(json.loads(self.target.read_text())["models"][0]["context_window"], 300000)
        before = self.target.read_bytes()
        write_json(self.source, {"models": self.models[1:]})
        result = self.run_catalog("--apply", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("including gpt-6-astra", result.stderr)
        self.assertEqual(self.target.read_bytes(), before)

    def test_check_rejects_missing_or_disabled_workaround(self) -> None:
        self.assertNotEqual(self.run_catalog("--check", check=False).returncode, 0)
        write_json(self.target, {"models": self.models})
        result = self.run_catalog("--check", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must use standard Responses", result.stderr)

    def test_profile_without_catalog_has_no_cache_dependency(self) -> None:
        self.profile.write_text('model_provider = "azure"\n')
        self.source.unlink()
        self.run_catalog("--apply")
        self.run_catalog("--check")
        self.assertFalse(self.target.exists())

    def test_rejects_duplicate_models_and_wrong_provider(self) -> None:
        write_json(self.source, {"models": [*self.models, self.models[0]]})
        self.assertNotEqual(self.run_catalog("--apply", check=False).returncode, 0)
        self.profile.write_text(self.profile.read_text().replace('"azure"', '"openai"'))
        result = self.run_catalog("--apply", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("scoped to the Azure Astra profile", result.stderr)
