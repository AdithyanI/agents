from __future__ import annotations

import json
import importlib.util
import io
from contextlib import redirect_stderr
import subprocess
import sys
from unittest.mock import patch

from tests.control_plane.support import REPO_ROOT, TempDirTestCase, run_command, write_text


class CodexNativeEnvTests(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.canonical = self.temp_path / "canonical"
        self.runtime = self.temp_path / "runtime"
        self.github = self.temp_path / "GitHub"
        self.template = write_text(
            self.canonical / "global.config.toml",
            'model_provider = "azure"\n[model_providers.azure]\n'
            'env_key = "AZURE_OPENAI_API_KEY"\n',
        )
        self.mapping = write_text(
            self.canonical / "secrets.env.map",
            "AZURE_OPENAI_API_KEY=litellm--azure-openai-api-key\n",
        )
        # scripts tests the real materializer; this tests the repo boundary
        # without a dependency on a sibling checkout or the host's secrets.
        self.materializer = write_text(
            self.github / "scripts/sync/materialize_machine_env.py",
            "import json,sys\nfrom pathlib import Path\nfrom types import SimpleNamespace\n"
            "sys.path.insert(0,str(Path(__file__).parent))\n"
            "def _parse_mapping_file(path):\n"
            "    Path(__file__).with_suffix('.source-check').write_text(str(path))\n"
            "    return [SimpleNamespace(secret_name=line.split('=',1)[1].strip()) for line in path.read_text().splitlines() if line and not line.startswith('#')]\n"
            "if __name__ == '__main__':\n"
            "    Path(__file__).with_suffix('.args').write_text(json.dumps(sys.argv[1:]))\n",
        )
        self.store_contract = write_text(
            self.materializer.parent / "local_secret_store.py",
            "class LocalSecretStoreError(RuntimeError): pass\n"
            "def secret_path(*, root, scope_name, secret_name):\n"
            "    assert scope_name == 'shared'\n"
            "    if '/' in secret_name: raise LocalSecretStoreError('invalid secret name')\n"
            "    return root / 'scopes' / scope_name / secret_name\n"
            "def read_secret(*args, **kwargs):\n"
            "    raise AssertionError('source validation must not read credentials')\n",
        )

    def run_env(self, *args: str, check: bool = True):
        return run_command([
            sys.executable, str(REPO_ROOT / "codex/scripts/sync-native-env.py"),
            "--canonical-dir", str(self.canonical), "--runtime-dir", str(self.runtime),
            "--github-root", str(self.github), *args,
        ], check=check)

    def test_modes_delegate_to_scripts_with_native_target_and_no_allow_missing(self) -> None:
        for mode in ("--dry-run", "--apply", "--check"):
            with self.subTest(mode=mode):
                self.run_env(mode)
                args = json.loads(self.materializer.with_suffix(".args").read_text())
                expected = [
                    "--secret-scope", "shared", "--mapping-file", str(self.mapping),
                    "--output-file", str(self.runtime / ".env"),
                ]
                if mode != "--dry-run":
                    expected.append(mode)
                self.assertEqual(args, expected)

    def test_default_dry_run_does_not_create_runtime_directory(self) -> None:
        self.run_env()
        self.assertFalse(self.runtime.exists())

    def test_source_check_uses_owner_mapping_contract_without_reading_credentials(self) -> None:
        result = self.run_env("--check-sources")
        self.assertIn("live credentials not checked", result.stdout)
        self.assertEqual(self.materializer.with_suffix(".source-check").read_text(), str(self.mapping))
        self.assertFalse(self.materializer.with_suffix(".args").exists())
        self.assertFalse(self.runtime.exists())

    def test_source_check_rejects_missing_provider_mapping(self) -> None:
        self.mapping.write_text("OTHER_KEY=integration--key\n")
        result = self.run_env("--check-sources", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires AZURE_OPENAI_API_KEY", result.stderr)
        self.assertFalse(self.materializer.with_suffix(".args").exists())

    def test_source_check_propagates_owner_mapping_parser_failure(self) -> None:
        self.mapping.write_text("AZURE_OPENAI_API_KEY=integration--first\nAZURE_OPENAI_API_KEY=integration--second\n")
        self.materializer.write_text(
            self.materializer.read_text()
            + "\ndef _parse_mapping_file(path):\n"
            + "    raise ValueError('Duplicate env var mapping at ' + str(path))\n"
        )
        result = self.run_env("--check-sources", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Duplicate env var mapping", result.stderr)
        self.assertFalse(self.materializer.with_suffix(".args").exists())

    def test_source_check_preserves_shared_scope_name_contract(self) -> None:
        self.mapping.write_text("AZURE_OPENAI_API_KEY=../outside-store\n")
        result = self.run_env("--check-sources", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid secret name", result.stderr)
        self.assertFalse(self.materializer.with_suffix(".args").exists())

    def test_default_full_check_invokes_credentials_and_fails_on_timeout(self) -> None:
        path = REPO_ROOT / "codex/scripts/sync-native-env.py"
        spec = importlib.util.spec_from_file_location("sync_native_env_timeout_fixture", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        arguments = [str(path), "--canonical-dir", str(self.canonical), "--runtime-dir", str(self.runtime), "--github-root", str(self.github), "--check"]
        stderr = io.StringIO()
        with patch.object(sys, "argv", arguments), patch.object(module.subprocess, "run", side_effect=subprocess.TimeoutExpired("materializer", 30)) as invoke, redirect_stderr(stderr):
            self.assertEqual(module.main(), 1)
        self.assertIn("--check", invoke.call_args.args[0])
        self.assertEqual(invoke.call_args.kwargs["timeout"], 30)
        self.assertIn("timed out", stderr.getvalue())
        self.assertFalse(self.runtime.exists())

    def test_provider_without_mapping_fails_before_materializer(self) -> None:
        self.mapping.unlink()
        result = self.run_env("--apply", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires AZURE_OPENAI_API_KEY", result.stderr)
        self.assertFalse(self.materializer.with_suffix(".args").exists())

    def test_subscription_without_native_mapping_has_no_secret_dependency(self) -> None:
        self.template.write_text('model_provider = "openai"\n')
        self.mapping.unlink()
        self.materializer.unlink()
        self.run_env("--check")
        self.run_env("--apply")
        self.assertFalse(self.runtime.exists())

    def test_azure_profile_requires_mapping_even_with_subscription_default(self) -> None:
        self.template.write_text('[model_providers.azure]\nenv_key = "AZURE_OPENAI_API_KEY"\n')
        write_text(self.canonical / "azure-astra.config.toml", 'model_provider = "azure"\n')
        self.mapping.unlink()
        result = self.run_env("--apply", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires AZURE_OPENAI_API_KEY", result.stderr)

    def test_missing_scripts_dependency_is_actionable(self) -> None:
        self.materializer.unlink()
        result = self.run_env("--apply", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sync the scripts repo", result.stderr)

    def test_failed_preflight_preserves_preexisting_provider_config_and_hooks(self) -> None:
        self.materializer.write_text("print('Missing required local secret')\nraise SystemExit(1)\n")
        config = write_text(self.runtime / "config.toml", 'model_provider = "openai"\n')
        hooks = write_text(self.runtime / "hooks.json", '{"hooks":{}}\n')
        result = run_command([
            "bash", str(REPO_ROOT / "codex/scripts/sync-config.sh"), "--apply",
            "--canonical-dir", str(self.canonical), "--github-root", str(self.github),
            "--global-config", str(config), "--global-hooks", str(hooks),
        ], check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("native credentials are not ready", result.stderr)
        self.assertEqual(config.read_text(), 'model_provider = "openai"\n')
        self.assertEqual(hooks.read_text(), '{"hooks":{}}\n')
        self.assertFalse((self.runtime / ".env").exists())

    def test_control_plane_check_propagates_credential_failure_without_writes(self) -> None:
        self.materializer.write_text(self.materializer.read_text() + "\nprint('output file is missing')\nraise SystemExit(1)\n")
        result = run_command([
            "bash", str(REPO_ROOT / "codex/scripts/check-codex-control-plane.sh"),
            "--canonical-dir", str(self.canonical), "--github-root", str(self.github),
            "--global-config", str(self.runtime / "config.toml"),
        ], check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("output file is missing", result.stderr)
        self.assertIn("--check", json.loads(self.materializer.with_suffix(".args").read_text()))
        self.assertFalse(self.runtime.exists())
