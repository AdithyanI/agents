from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import plistlib
import sys
import tomllib

from tests.control_plane.support import REPO_ROOT, TempDirTestCase, run_command, write_text


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


retirement = load_module('retire_codex_provider', 'scripts/retire-codex-provider.py')
installer = load_module('install_codex_cli', 'scripts/install-codex-cli.py')


class CodexProviderRetirementTests(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.home = self.temp_path / 'home'
        self.config = write_text(self.home / '.codex/config.toml',
            'model_provider = "azure"\nmodel = "gpt-6.1-sol"\nmodel_reasoning_effort = "xhigh"\n'
            'model_catalog_json = "model-catalogs/azure-gpt6.json"\n'
            'model_context_window = 400000\nmodel_auto_compact_token_limit = 350000\n'
            'service_tier = "fast"\n[features]\nhooks = true\nstandalone_web_search = false\n'
            '[model_providers.azure]\nenv_key = "AZURE_OPENAI_API_KEY"\n'
            '[model_providers.custom]\nname = "Keep"\n[plugins."keep@local"]\nenabled = true\n')
        self.env = write_text(self.home / '.codex/.env', '# generated\nAZURE_OPENAI_API_KEY=fixture-secret\nOTHER_TOKEN=keep\n')
        self.auth = write_text(self.home / '.codex/auth.json', '{"fixture":"do not change"}\n')
        self.cache = write_text(self.home / '.codex/models_cache.json', '{"fixture":"native cache"}\n')
        self.state = write_text(self.home / '.local/state/codex-control-plane/provider', 'azure\n')
        for relative in ['.codex/azure-astra.config.toml', '.codex/model-catalogs/azure-gpt6.json', '.codex/model-catalogs/azure-astra.json']:
            write_text(self.home / relative, 'owned artifact\n')

    def test_dry_run_then_apply_is_selective_and_idempotent(self):
        before = self.config.read_bytes()
        result = retirement.retire(self.home, False)
        self.assertTrue(result['changed_paths'])
        self.assertEqual(before, self.config.read_bytes())
        self.assertNotIn('fixture-secret', json.dumps(result))
        retirement.retire(self.home, True)
        config = tomllib.loads(self.config.read_text())
        for key in ['model_provider', 'model_catalog_json', 'model_context_window', 'model_auto_compact_token_limit']:
            self.assertNotIn(key, config)
        self.assertEqual(config['model'], 'gpt-6.1-sol')
        self.assertEqual(config['model_reasoning_effort'], 'xhigh')
        self.assertEqual(config['service_tier'], 'fast')
        self.assertEqual(config['features'], {'hooks': True})
        self.assertEqual(config['model_providers'], {'custom': {'name': 'Keep'}})
        self.assertEqual(config['plugins'], {'keep@local': {'enabled': True}})
        self.assertEqual(self.env.read_text(), '# generated\nOTHER_TOKEN=keep\n')
        self.assertEqual(self.auth.read_text(), '{"fixture":"do not change"}\n')
        self.assertEqual(self.cache.read_text(), '{"fixture":"native cache"}\n')
        self.assertFalse(self.state.exists())
        backup = self.home / '.local/state/codex-control-plane/backups/retired-provider/config.toml'
        self.assertEqual(backup.read_bytes(), before)
        self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
        self.assertEqual(retirement.retire(self.home, True)['changed_paths'], [])

    def test_subscription_selection_is_released_without_changing_native_preferences(self):
        self.state.write_text('subscription\n')
        self.config.write_text('model_provider = "openai"\nforced_login_method = "chatgpt"\nmodel = "chosen"\n')
        retirement.retire(self.home, True)
        self.assertEqual(tomllib.loads(self.config.read_text()), {'model': 'chosen'})
        self.assertNotIn('model_provider', self.config.read_text())

    def test_unmanaged_selection_and_context_are_preserved(self):
        self.state.unlink()
        self.config.write_text('model_provider = "openai"\nforced_login_method = "chatgpt"\nmodel_context_window = 400000\n')
        before = self.config.read_text()
        retirement.retire(self.home, True)
        self.assertEqual(self.config.read_text(), before)

    def test_unrelated_app_fails_preflight_before_any_edit(self):
        app = self.home / 'Applications/Codex Provider.app/Contents'
        app.mkdir(parents=True)
        (app / 'Info.plist').write_bytes(plistlib.dumps({'CFBundleIdentifier': 'unrelated'}))
        before = self.config.read_bytes()
        with self.assertRaises(ValueError):
            retirement.retire(self.home, True)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertIn('AZURE_OPENAI_API_KEY', self.env.read_text())

    def test_runtime_symlink_is_not_followed(self):
        self.env.unlink()
        target = write_text(self.temp_path / 'other.env', 'AZURE_OPENAI_API_KEY=untouched\n')
        self.env.symlink_to(target)
        with self.assertRaises(ValueError):
            retirement.retire(self.home, True)
        self.assertEqual(target.read_text(), 'AZURE_OPENAI_API_KEY=untouched\n')

    def test_cli_emits_paths_without_credential_values(self):
        result = run_command([sys.executable, str(REPO_ROOT / 'scripts/retire-codex-provider.py'), '--dry-run', '--no-input'], env={'HOME': str(self.home)})
        self.assertEqual(json.loads(result.stdout)['status'], 'ok')
        self.assertNotIn('fixture-secret', result.stdout + result.stderr)

    def test_desktop_cli_links_include_adjacent_code_mode_host_only(self):
        resources = self.temp_path / 'resources'
        for name in ['codex', 'codex-code-mode-host']:
            write_text(resources / 'codex-cli/bin' / name, 'native companion')
        native = write_text(resources / 'codex-cli/CodexCLI.app/Contents/MacOS/codex', 'native executable')
        targets = installer.codex_command_targets(self.home, resources)
        self.assertEqual(set(path.name for path in targets), {'codex', 'codex-code-mode-host'})
        self.assertEqual(targets[self.home / 'bin/codex'], native)
        self.assertEqual(targets[self.home / 'bin/codex-code-mode-host'], resources / 'codex-cli/bin/codex-code-mode-host')
