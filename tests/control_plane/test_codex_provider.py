from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
import tomllib

from tests.control_plane.support import (
    REPO_ROOT, TempDirTestCase, default_mcp_registry, make_control_plane_root,
    run_command, write_json, write_text,
)

spec = importlib.util.spec_from_file_location("provider_selection", REPO_ROOT / "codex/scripts/provider_selection.py")
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)


class CodexProviderTests(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.canonical = REPO_ROOT / "codex/config"
        self.home = self.temp_path / "home"
        self.config = self.make_home(self.home)

    def make_home(self, home):
        config = write_text(home / ".codex/config.toml",
            'model = "gpt-6-astra"\nmodel_provider = "azure"\nmodel_reasoning_effort = "xhigh"\n'
            'model_catalog_json = "model-catalogs/azure-astra.json"\n'
            '[features]\nstandalone_web_search = false\nhooks = true\n'
            '[model_providers.azure]\nbase_url = "https://fixture.example/openai/v1"\nenv_key = "AZURE_OPENAI_API_KEY"\n'
            '[plugins."example@fixture"]\nenabled = true\n[projects."/fixture"]\ntrust_level = "trusted"\n')
        write_json(home / ".codex/models_cache.json", {"models": [{"slug": "gpt-6-astra", "use_responses_lite": True}]})
        write_json(home / ".codex/model-catalogs/azure-astra.json", {"models": [{"slug": "gpt-6-astra", "use_responses_lite": False}]})
        write_text(home / ".codex/.env", "AZURE_OPENAI_API_KEY=fixture-secret\n")
        write_json(home / ".codex/auth.json", {"auth_mode": "chatgpt", "tokens": {"access_token": "fixture-login"}})
        return config

    def cli(self, *args, home=None):
        return run_command([sys.executable, str(REPO_ROOT / "scripts/codex-provider.py"), *args],
                           env={"HOME": str(home or self.home)}, check=False)

    def test_contract_dry_run_errors_and_plain(self):
        before = self.config.read_bytes()
        result = self.cli("subscription", "--no-input")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(set(data), {"schema_version", "command", "status", "data", "error", "meta"})
        self.assertFalse(data["data"]["applied"])
        self.assertEqual(data["data"]["requested"], "subscription")
        self.assertEqual(before, self.config.read_bytes())
        self.assertFalse((self.home / ".local").exists())
        self.assertIn("This Mac: azure", self.cli("status", "--plain").stdout)
        bad = self.cli("unknown", "--no-input")
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(json.loads(bad.stdout)["error"]["code"], "E_VALIDATION")

    def test_round_trip_preserves_credentials_hooks_trust_and_reasoning(self):
        before = tomllib.loads(self.config.read_text())
        protected = {name: (self.config.parent / name).read_bytes() for name in ["auth.json", ".env", "models_cache.json"]}
        for choice, expected in [("subscription", "openai"), ("azure", "azure")]:
            result = self.cli(choice, "--apply", "--no-input")
            self.assertEqual(result.returncode, 0, result.stdout)
            data = json.loads(result.stdout)["data"]
            self.assertEqual(data["effective_provider"], expected)
            self.assertTrue(data["config_in_sync"])
            after = tomllib.loads(self.config.read_text())
            for key in ["plugins", "projects", "model_reasoning_effort", "model_providers"]:
                self.assertEqual(after[key], before[key])
            self.assertTrue(after["features"]["hooks"])
        self.assertNotIn("forced_login_method", after)
        for name, original in protected.items():
            self.assertEqual((self.config.parent / name).read_bytes(), original)

    def test_failed_preflight_and_invalid_local_state_do_not_write(self):
        before = self.config.read_bytes()
        (self.config.parent / "auth.json").unlink()
        result = self.cli("subscription", "--apply")
        self.assertEqual(result.returncode, 3)
        self.assertEqual(before, self.config.read_bytes())
        self.assertFalse((self.home / ".local").exists())
        write_text(self.home / ".local/state/codex-control-plane/provider", "typo\n")
        self.assertEqual(self.cli("status").returncode, 2)
        self.assertEqual(before, self.config.read_bytes())
        self.assertEqual(self.cli("azure", "--apply").returncode, 0, "explicit selection repairs invalid preference")

    def test_write_failure_rolls_back_preference(self):
        with patch.dict(os.environ, {"HOME": str(self.home)}):
            before = self.config.read_bytes()
            original_write = provider.atomic_write
            def fail_config(path, text):
                if path == self.config:
                    raise OSError("fixture write failure")
                original_write(path, text)
            with patch.object(provider, "atomic_write", side_effect=fail_config):
                with self.assertRaises(OSError):
                    provider.switch(self.config, self.canonical, "subscription", True, 1)
            self.assertFalse(provider.state_path().exists())
            self.assertEqual(before, self.config.read_bytes())

    def test_switch_times_out_behind_sync_lock_without_writes(self):
        with provider.config_lock(self.config):
            result = self.cli("subscription", "--apply", "--timeout", "0.1")
        self.assertEqual(result.returncode, 5)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "E_TIMEOUT")
        self.assertEqual(tomllib.loads(self.config.read_text())["model_provider"], "azure")

    def test_shared_sync_preserves_opposite_machine_choices_and_migrates_once(self):
        root = make_control_plane_root(self.temp_path)
        write_json(root / "mcp/config/presets.json", default_mcp_registry())
        write_json(root / "plugins/registry.json", {
            "version": 1, "paths": {"github_root": str(self.temp_path)},
            "managed_plugins": [], "unmanaged_repo_local_plugins": []})
        for name in provider.PROFILES.values():
            write_text(root / "codex/config" / name, (self.canonical / name).read_text())
        other = self.temp_path / "other"
        self.make_home(other)
        self.assertEqual(self.cli("subscription", "--apply").returncode, 0)
        for home, choice in [(self.home, "subscription"), (other, "azure")]:
            config = home / ".codex/config.toml"
            for _ in range(2):
                run_command([str(REPO_ROOT / "codex/scripts/sync-config.sh"), "--apply",
                    "--global-config", str(config), "--global-hooks", str(home / ".codex/hooks.json"),
                    "--canonical-dir", str(root / "codex/config"), "--mcp-registry", str(root / "mcp/config/presets.json"),
                    "--plugin-registry", str(root / "plugins/registry.json"), "--hooks-registry", str(root / "hooks/registry.json")],
                    env={"HOME": str(home)})
                data = json.loads(self.cli("status", home=home).stdout)["data"]
                self.assertEqual(data["selected"], choice)
                self.assertTrue(data["persisted"])
                self.assertTrue(data["config_in_sync"])
                run_command([sys.executable, str(REPO_ROOT / "codex/scripts/provider_selection.py"), "check",
                             str(root / "codex/config"), str(config)], env={"HOME": str(home)})
        self.assertEqual(json.loads(self.cli("status").stdout)["data"]["selected"], "subscription")
