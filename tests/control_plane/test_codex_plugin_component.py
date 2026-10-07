from __future__ import annotations

import json
import tomllib

from tests.control_plane.support import REPO_ROOT, TempDirTestCase, run_command, write_json, write_text


class CodexPluginComponentTests(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.canonical = self.temp_path / "canonical"
        self.runtime = self.temp_path / "home/.codex"
        self.github = self.temp_path / "GitHub"
        self.registry = self.temp_path / "plugins/registry.json"
        self.registry_data = {"version": 1, "managed_plugins": [{"plugin": "fixture", "marketplace": "openai-bundled", "enabled": False, "scope": "global"}], "unmanaged_repo_local_plugins": []}
        write_json(self.registry, self.registry_data)
        write_text(self.canonical / "global.config.toml", 'model_provider = "azure"\n[model_providers.azure]\nenv_key = "AZURE_OPENAI_API_KEY"\n[features]\nhooks = false\n[plugins."template@local"]\nenabled = true\n')
        write_text(self.canonical / "secrets.env.map", "AZURE_OPENAI_API_KEY=integration--credential\n")
        self.materializer = write_text(self.github / "scripts/sync/materialize_machine_env.py", "import json,sys\nfrom pathlib import Path\nPath(__file__).with_suffix('.args').write_text(json.dumps(sys.argv[1:]))\nprint('canonical credential fixture unavailable')\nraise SystemExit(87)\n")
        self.config = write_text(self.runtime / "config.toml", '''# Existing client state must survive component maintenance.
model_provider = "azure"
model = "gpt-6-sol"
model_reasoning_effort = "medium"
[model_providers.azure]
env_key = "AZURE_OPENAI_API_KEY"
base_url = "https://fixture.invalid/openai/v1"
[features]
hooks = true
[hooks.state]
fixture_digest = "accepted"
[profiles.custom]
model = "client-choice"
[projects."/fixture/repo"]
trust_level = "trusted"
[marketplaces.fixture]
source = "/fixture/marketplace"
[plugins."fixture@openai-bundled"]
enabled = true
custom_preference = "keep"
[plugins."native-added@marketplace"]
enabled = true
client_setting = "preserve exactly"
[plugins."native-added@marketplace".permissions]
network = true
''')
        self.unrelated_files = {
            "auth.json": '{"auth_mode":"chatgpt","tokens":{"access_token":"fixture"}}\n',
            ".credentials.json": '{"fixture":"oauth-state"}\n',
            ".env": "export AZURE_OPENAI_API_KEY=fixture\n",
            "hooks.json": '{"hooks":{}}\n',
            "custom.config.toml": 'model = "runtime-profile"\n',
        }
        for name, value in self.unrelated_files.items():
            write_text(self.runtime / name, value)

    def run_sync(self, *flags: str, check: bool = True):
        return run_command(["bash", str(REPO_ROOT / "codex/scripts/sync-config.sh"), "--canonical-dir", str(self.canonical), "--plugin-registry", str(self.registry), "--global-config", str(self.config), "--github-root", str(self.github), *flags], check=check)

    def assert_unrelated_files_untouched(self) -> None:
        for name, value in self.unrelated_files.items():
            self.assertEqual((self.runtime / name).read_text(), value, name)

    def test_plugins_only_repairs_drift_and_preserves_every_other_parsed_field(self) -> None:
        before = tomllib.loads(self.config.read_text())
        result = self.run_sync("--plugins-only", "--apply")
        after = tomllib.loads(self.config.read_text())
        self.assertFalse(after["plugins"]["fixture@openai-bundled"]["enabled"])
        self.assertEqual(after["plugins"]["fixture@openai-bundled"]["custom_preference"], "keep")
        self.assertTrue(after["plugins"]["template@local"]["enabled"])
        self.assertEqual(after["plugins"]["native-added@marketplace"], before["plugins"]["native-added@marketplace"])
        self.assertIn('[plugins."native-added@marketplace"]\nenabled = true\nclient_setting = "preserve exactly"\n[plugins."native-added@marketplace".permissions]\nnetwork = true\n', self.config.read_text())
        before.pop("plugins")
        after.pop("plugins")
        self.assertEqual(after, before)
        self.assertIn("Managed Codex Plugins", result.stdout)
        self.assertFalse(self.materializer.with_suffix(".args").exists())
        self.assert_unrelated_files_untouched()
        modified_at = self.config.stat().st_mtime_ns
        self.run_sync("--plugins-only", "--apply")
        self.assertEqual(self.config.stat().st_mtime_ns, modified_at)

    def test_invalid_registry_cannot_be_hidden_by_process_substitution(self) -> None:
        before = self.config.read_bytes()
        for invalid in ("not JSON", json.dumps({**self.registry_data, "managed_plugins": self.registry_data["managed_plugins"] * 2}), json.dumps({"managed_plugins": [{"plugin": "fixture", "marketplace": "local", "enabled": "false"}]})):
            with self.subTest(registry=invalid):
                self.registry.write_text(invalid)
                result = self.run_sync("--plugins-only", "--apply", check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.config.read_bytes(), before)
                self.assert_unrelated_files_untouched()

    def test_plugins_only_dry_run_reports_drift_without_writes(self) -> None:
        before = self.config.read_bytes()
        result = self.run_sync("--plugins-only")
        self.assertIn("-enabled = true", result.stdout)
        self.assertIn("+enabled = false", result.stdout)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse(self.materializer.with_suffix(".args").exists())
        self.assert_unrelated_files_untouched()

    def test_normal_full_sync_still_requires_canonical_credential_preflight(self) -> None:
        before = self.config.read_bytes()
        result = self.run_sync("--apply", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("native credentials are not ready", result.stderr)
        self.assertIn("--apply", json.loads(self.materializer.with_suffix(".args").read_text()))
        self.assertEqual(self.config.read_bytes(), before)
        self.assert_unrelated_files_untouched()

    def test_ambiguous_component_scope_is_rejected_without_writes(self) -> None:
        before = self.config.read_bytes()
        result = self.run_sync("--plugins-only", "--global-only", "--apply", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mutually exclusive", result.stderr)
        self.assertEqual(self.config.read_bytes(), before)


if __name__ == "__main__":
    import unittest
    unittest.main()
