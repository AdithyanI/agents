from __future__ import annotations

import json
import tomllib

from tests.control_plane.support import REPO_ROOT, TempDirTestCase, run_command, write_text


class CodexHooksComponentTests(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.runtime = self.temp_path / "home/.codex"
        self.config = write_text(self.runtime / "config.toml", '''# Native app choices.
notify = ["/fixture/Computer Use.app/notify", "turn-ended"]
model = "client-model"
service_tier = "priority"
profile = "custom"
[features]
hooks = false
apps = true
[plugins."native-plugin@local"]
enabled = true
[plugins."native-plugin@local".permissions]
network = true
[profiles.custom]
model = "another-model"
[hooks.state."unrelated"]
trusted_hash = "keep"
''')
        self.hooks = write_text(self.runtime / "hooks.json", '{"hooks":{}}\n')
        self.other_files = {
            "auth.json": '{"fixture":"private-runtime-state"}\n',
            ".credentials.json": '{"fixture":"oauth-state"}\n',
            ".env": "FIXTURE=private\n",
            "custom.config.toml": 'model = "client-model"\n',
        }
        for name, content in self.other_files.items():
            write_text(self.runtime / name, content)

    def run_sync(self, *args: str, check: bool = True):
        # Missing unrelated inputs prove the component has no provider/plugin
        # dependency and cannot materialize credentials or install packages.
        return run_command([
            "bash", str(REPO_ROOT / "codex/scripts/sync-config.sh"),
            "--hooks-only", "--global-config", str(self.config),
            "--global-hooks", str(self.hooks),
            "--canonical-dir", str(self.temp_path / "absent"),
            "--plugin-registry", str(self.temp_path / "absent-plugins.json"),
            *args,
        ], check=check)

    def test_apply_only_enables_hooks_and_renders_canonical_commands(self) -> None:
        before = tomllib.loads(self.config.read_text())
        self.run_sync("--apply")
        after = tomllib.loads(self.config.read_text())
        before["features"]["hooks"] = True
        self.assertEqual(after, before)
        hook_data = json.loads(self.hooks.read_text())
        self.assertEqual(hook_data["hooks"]["Stop"][0]["hooks"][0]["command"],
                         'python3 "$HOME/GitHub/agents/hooks/scripts/stop.py" --runtime codex')
        for name, content in self.other_files.items():
            self.assertEqual((self.runtime / name).read_text(), content)
        times = [path.stat().st_mtime_ns for path in (self.config, self.hooks)]
        self.run_sync("--apply")
        self.assertEqual([path.stat().st_mtime_ns for path in (self.config, self.hooks)], times)

    def test_dry_run_and_invalid_registry_leave_runtime_untouched(self) -> None:
        before = [path.read_bytes() for path in (self.config, self.hooks)]
        result = self.run_sync()
        self.assertIn("+hooks = true", result.stdout)
        self.assertEqual([path.read_bytes() for path in (self.config, self.hooks)], before)
        invalid = write_text(self.temp_path / "invalid-hooks.json", "not JSON")
        result = self.run_sync("--apply", "--hooks-registry", str(invalid), check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([path.read_bytes() for path in (self.config, self.hooks)], before)

    def test_new_features_table_preserves_existing_app_settings(self) -> None:
        self.config.write_text('service_tier = "priority"\n[plugins."native@local"]\nenabled = true\n')
        before = tomllib.loads(self.config.read_text())
        self.hooks.unlink()
        self.run_sync("--apply")
        self.assertEqual(tomllib.loads(self.config.read_text()), {**before, "features": {"hooks": True}})
        self.assertTrue(self.hooks.is_file())

    def test_ambiguous_component_scope_fails_before_writes(self) -> None:
        before = self.config.read_bytes()
        for flag in ("--plugins-only", "--global-only"):
            result = self.run_sync("--apply", flag, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mutually exclusive", result.stderr)
            self.assertEqual(self.config.read_bytes(), before)
