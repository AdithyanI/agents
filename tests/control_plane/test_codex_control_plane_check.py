from __future__ import annotations

from tests.control_plane.support import (
    REPO_ROOT,
    TempDirTestCase,
    default_mcp_registry,
    init_git_repo,
    make_control_plane_root,
    run_command,
    write_json,
    write_text,
)


class CodexControlPlaneCheckTests(TempDirTestCase):
    def _make_codex_repo_fixture(self):  # noqa: ANN202
        root = make_control_plane_root(self.temp_path)
        home = self.temp_path / "home"
        github_root = home / "GitHub"
        adi = init_git_repo(github_root / "adi")

        write_json(
            root / "codex/config/repo-bootstrap.json",
            {
                "defaults": {"personality": "friendly"},
                "repos": [
                    {
                        "path": str(adi),
                    }
                ],
            },
        )
        mcp_registry = default_mcp_registry()
        mcp_registry["presets"]["cloudflare-docs"]["repos"] = [str(adi)]
        mcp_registry["presets"]["fixture-stdio"] = {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "fixture-mcp@latest", "mcp"],
            "repos": [str(adi)],
        }
        write_json(root / "mcp/config/presets.json", mcp_registry)
        return root, home, adi

    def _check_command(self, root, home, repo):  # noqa: ANN001, ANN202
        return [
            str(REPO_ROOT / "codex/scripts/check-codex-control-plane.sh"),
            "--canonical-dir",
            str(root / "codex/config"),
            "--global-config",
            str(home / ".codex/config.toml"),
            "--registry",
            str(root / "codex/config/repo-bootstrap.json"),
            "--mcp-registry",
            str(root / "mcp/config/presets.json"),
            "--hooks-registry",
            str(root / "hooks/registry.json"),
            "--plugin-registry",
            str(root / "plugins/registry.json"),
            "--repo",
            str(repo),
        ]

    def _render_repo_configs(self, root, home):  # noqa: ANN001
        run_command(
            [
                str(REPO_ROOT / "codex/scripts/sync-repo-codex-configs.sh"),
                "--apply",
                "--registry",
                str(root / "codex/config/repo-bootstrap.json"),
                "--mcp-registry",
                str(root / "mcp/config/presets.json"),
                "--hooks-registry",
                str(root / "hooks/registry.json"),
                "--plugin-registry",
                str(root / "plugins/registry.json"),
            ],
            env={"HOME": str(home)},
        )

    def test_check_script_passes_for_rendered_repo_configs_and_mcp_assignments(self) -> None:
        root, home, adi = self._make_codex_repo_fixture()

        env = {"HOME": str(home)}
        self._render_repo_configs(root, home)

        result = run_command(
            self._check_command(root, home, adi),
            env=env,
        )

        self.assertIn("OK: Codex control plane validation passed", result.stdout)
        self.assertTrue((adi / ".codex/config.toml").is_file())
        self.assertTrue((adi / ".codex/hooks.json").is_file())

    def test_check_script_rejects_client_owned_global_thread_selection(self) -> None:
        root, home, adi = self._make_codex_repo_fixture()
        global_template = root / "codex/config/global.config.toml"
        global_template.write_text(
            'model_reasoning_effort = "high"\n'
            + global_template.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        result = run_command(
            self._check_command(root, home, adi),
            env={"HOME": str(home)},
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("client-owned thread selection", result.stderr)

    def test_profile_check_ignores_only_model_availability_nux(self) -> None:
        root, home, adi = self._make_codex_repo_fixture()
        self._render_repo_configs(root, home)
        profile = 'model = "gpt-6-astra"\nmodel_provider = "azure"\n'
        cache = '\n[tui.model_availability_nux]\n"gpt-6-astra" = 2\n'
        write_text(root / "codex/config/azure-astra.config.toml", profile)
        runtime = home / ".codex/azure-astra.config.toml"

        for fallback in ("", "1"):
            env = {"HOME": str(home), "CODEX_FORCE_TOML_FALLBACK": fallback}
            with self.subTest(fallback=fallback, drift="none"):
                write_text(runtime, profile + cache)
                result = run_command(self._check_command(root, home, adi), env=env)
                self.assertIn("OK: Codex control plane validation passed", result.stdout)

            for label, contents in (
                ("model", profile.replace("gpt-6-astra", "gpt-5.5") + cache),
                ("provider", profile.replace('"azure"', '"openai"') + cache),
                ("tui", profile + '\n[tui]\nnotifications = false\n' + cache),
                ("adjacent table", profile + cache + '\n[tui.model_availability_nux_other]\ncount = 2\n'),
            ):
                with self.subTest(fallback=fallback, drift=label):
                    write_text(runtime, contents)
                    result = run_command(
                        self._check_command(root, home, adi), env=env, check=False
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Codex profile is out of sync", result.stderr)

    def test_global_selection_allows_only_a_paired_custom_provider_default(self) -> None:
        root, home, adi = self._make_codex_repo_fixture()
        self._render_repo_configs(root, home)
        global_template = root / "codex/config/global.config.toml"
        custom_provider = '\n[model_providers.azure]\nname = "Azure"\n'
        paired_default = 'model = "gpt-6-astra"\nmodel_provider = "azure"\n'
        cases = (
            ("paired custom provider", paired_default + custom_provider, True),
            ("model alone", 'model = "gpt-6-astra"\n' + custom_provider, False),
            ("provider alone", 'model_provider = "azure"\n' + custom_provider, False),
            ("undefined provider", paired_default, False),
            ("blank model", paired_default.replace('"gpt-6-astra"', '""') + custom_provider, False),
            ("openai model pin", (paired_default + custom_provider).replace("azure", "openai"), False),
            ("reasoning effort", paired_default + 'model_reasoning_effort = "high"\n' + custom_provider, False),
            ("service tier", paired_default + 'service_tier = "fast"\n' + custom_provider, False),
            ("fast mode", paired_default + custom_provider + '\n[features]\nfast_mode = true\n', False),
        )
        for fallback in ("", "1"):
            for label, contents, allowed in cases:
                with self.subTest(fallback=fallback, selection=label):
                    write_text(global_template, contents)
                    result = run_command(
                        self._check_command(root, home, adi),
                        env={"HOME": str(home), "CODEX_FORCE_TOML_FALLBACK": fallback},
                        check=False,
                    )
                    if allowed:
                        self.assertEqual(result.returncode, 0, result.stderr)
                    else:
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("client-owned thread selection", result.stderr)

    def test_paired_custom_provider_is_still_rejected_in_repo_defaults(self) -> None:
        root, home, adi = self._make_codex_repo_fixture()
        write_json(
            root / "codex/config/repo-bootstrap.json",
            {
                "defaults": {
                    "model": "gpt-6-astra",
                    "model_provider": "azure",
                    "model_providers": {"azure": {"name": "Azure"}},
                },
                "repos": [{"path": str(adi)}],
            },
        )
        result = run_command(
            self._check_command(root, home, adi), env={"HOME": str(home)}, check=False
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("defaults set client-owned thread selection", result.stderr)

    def test_check_script_rejects_legacy_embedded_profiles(self) -> None:
        root, home, adi = self._make_codex_repo_fixture()
        write_text(
            home / ".codex/config.toml",
            '[profiles.autofix]\nmodel = "gpt-5.4"\n',
        )

        result = run_command(
            self._check_command(root, home, adi),
            env={"HOME": str(home)},
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("legacy embedded profiles", result.stderr)

    def test_check_script_fails_for_deprecated_codex_feature_flag(self) -> None:
        root, home, adi = self._make_codex_repo_fixture()
        global_template = root / "codex/config/global.config.toml"
        global_template.write_text(
            global_template.read_text(encoding="utf-8").replace(
                "hooks = true",
                "codex_hooks = true",
            ),
            encoding="utf-8",
        )

        result = run_command(
            self._check_command(root, home, adi),
            env={"HOME": str(home), "CODEX_FEATURES_LIST_OUTPUT": "hooks stable true\n"},
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("uses deprecated Codex feature flag `codex_hooks`", result.stderr)

    def test_check_script_fails_when_repo_config_missing_for_managed_repo(self) -> None:
        root, home, adi = self._make_codex_repo_fixture()

        result = run_command(
            self._check_command(root, home, adi),
            env={"HOME": str(home)},
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("repo-local Codex files are out of sync", result.stderr)
        self.assertIn(".codex/config.toml", result.stderr)

    def test_check_script_fails_when_global_plugin_config_is_missing(self) -> None:
        root, home, adi = self._make_codex_repo_fixture()
        self._render_repo_configs(root, home)
        write_json(
            root / "codex/config/bundled-skills-policy.json",
            {"version": 1, "roots": {}},
        )
        write_text(
            home / ".codex/config.toml",
            'model = "gpt-5.5"\n\n[features]\nhooks = false\n',
        )

        result = run_command(
            self._check_command(root, home, adi),
            env={
                "HOME": str(home),
                "CODEX_BUNDLED_MARKETPLACE": str(home / "missing-bundled-marketplace"),
            },
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "global Codex config missing managed plugin `computer-use@openai-bundled`",
            result.stderr,
        )

    def test_check_script_fails_when_repo_config_drifted_from_registry(self) -> None:
        root, home, adi = self._make_codex_repo_fixture()
        self._render_repo_configs(root, home)
        config_path = adi / ".codex/config.toml"
        config_path.write_text(
            config_path.read_text(encoding="utf-8").replace(
                'personality = "friendly"',
                'personality = "pragmatic"',
            ),
            encoding="utf-8",
        )

        result = run_command(
            self._check_command(root, home, adi),
            env={"HOME": str(home)},
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("repo-local Codex files are out of sync", result.stderr)
        self.assertIn('-personality = "pragmatic"', result.stderr)
        self.assertIn('+personality = "friendly"', result.stderr)

    def test_check_script_fails_for_unclassified_bundled_codex_skill(self) -> None:
        root, home, adi = self._make_codex_repo_fixture()
        write_text(
            home / ".codex/skills/.system/new-bundled-skill/SKILL.md",
            "---\nname: new-bundled-skill\ndescription: Fixture.\n---\n",
        )

        result = run_command(
            self._check_command(root, home, adi),
            env={"HOME": str(home)},
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unclassified bundled Codex skill(s)", result.stderr)
        self.assertIn("new-bundled-skill", result.stderr)
        self.assertIn("bundled-skills-policy.json", result.stderr)
