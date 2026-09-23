from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import patch

from hooks.control_plane import (
    HookRegistryError,
    load_hooks_registry,
    render_codex_hooks,
)
from hooks.scripts.codex_turn_changes import CodexTurnChanges
from tests.control_plane.support import (
    REPO_ROOT,
    TempDirTestCase,
    default_mcp_registry,
    init_git_repo,
    make_control_plane_root,
    read_json,
    run_command,
    write_executable,
    write_json,
    write_text,
)


class HooksControlPlaneTests(TempDirTestCase):
    def load_stop_module(self):  # noqa: ANN201
        stop_path = REPO_ROOT / "hooks/scripts/stop.py"
        spec = importlib.util.spec_from_file_location("hooks_stop", stop_path)
        if spec is None or spec.loader is None:
            raise AssertionError(f"Failed to load Stop hook module from {stop_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_stop_publication_notifies_local_production_asynchronously(self) -> None:
        module = self.load_stop_module()
        notifier = self.temp_path / "GitHub/scripts/sync/local-production-notify.sh"
        write_executable(notifier, "#!/usr/bin/env bash\nexit 0\n")
        result = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps({"data": {"outcome": "queued"}}),
            stderr="",
        )
        messages: list[str] = []
        with (
            patch.object(module.Path, "home", return_value=self.temp_path),
            patch.object(module, "current_branch_name", return_value="main"),
            patch.object(module, "run", return_value=result) as run_mock,
            patch.object(module, "log", side_effect=lambda _runtime, message: messages.append(message)),
        ):
            module.notify_local_production("codex", "/tmp/example", "abc123")

        command = run_mock.call_args.args[0]
        self.assertEqual(command[0], str(notifier))
        self.assertIn("--apply", command)
        self.assertEqual(command[command.index("--repo") + 1], "/tmp/example")
        self.assertEqual(command[command.index("--sha") + 1], "abc123")
        self.assertIn("outcome=queued", messages[-1])

    def test_stop_publication_skips_non_main_branch(self) -> None:
        module = self.load_stop_module()
        messages: list[str] = []
        with (
            patch.object(module, "current_branch_name", return_value="codex/example"),
            patch.object(module, "run") as run_mock,
            patch.object(module, "log", side_effect=lambda _runtime, message: messages.append(message)),
        ):
            module.notify_local_production("codex", "/tmp/example", "abc123")

        run_mock.assert_not_called()
        self.assertIn("branch=codex/example", messages[-1])

    def test_stop_publication_notify_failure_does_not_fail_git_finalization(self) -> None:
        module = self.load_stop_module()
        notifier = self.temp_path / "GitHub/scripts/sync/local-production-notify.sh"
        write_executable(notifier, "#!/usr/bin/env bash\nexit 4\n")
        result = subprocess.CompletedProcess(args=[], returncode=4, stdout="", stderr="unavailable")
        messages: list[str] = []
        with (
            patch.object(module.Path, "home", return_value=self.temp_path),
            patch.object(module, "current_branch_name", return_value="main"),
            patch.object(module, "run", return_value=result),
            patch.object(module, "log", side_effect=lambda _runtime, message: messages.append(message)),
        ):
            self.assertIsNone(module.notify_local_production("codex", "/tmp/example", "abc123"))

        self.assertIn("warn local-production-notify", messages[-1])

    def test_registry_renders_codex_hooks(self) -> None:
        registry = load_hooks_registry(REPO_ROOT / "hooks/registry.json")

        global_codex_hooks = render_codex_hooks(registry)
        self.assertEqual(set(global_codex_hooks["hooks"].keys()), {"Stop"})
        self.assertEqual(
            global_codex_hooks["hooks"]["Stop"][0]["hooks"][0]["command"],
            'python3 "$HOME/GitHub/agents/hooks/scripts/stop.py" --runtime codex',
        )
        self.assertEqual(
            global_codex_hooks["hooks"]["Stop"][0]["hooks"][0]["timeout"],
            900,
        )

        codex_hooks = render_codex_hooks(registry, repo_name="adi")
        self.assertEqual(
            set(codex_hooks["hooks"].keys()),
            {"SessionStart"},
        )
        self.assertEqual(
            codex_hooks["hooks"]["SessionStart"][0]["matcher"],
            "startup|clear|compact",
        )
        self.assertEqual(
            set(render_codex_hooks(registry, repo_name="win")["hooks"].keys()),
            set(),
        )

    def test_registry_rejects_unsupported_runtime(self) -> None:
        registry_path = self.temp_path / "hooks/registry.json"
        write_json(
            registry_path,
            {
                "managed_hooks": [
                    {
                        "command": "python3 hook.py --runtime {runtime}",
                        "enabled": True,
                        "event": "Stop",
                        "id": "bad-runtime",
                        "runtimes": ["unknown"],
                        "scope": "global",
                        "timeout": 5,
                    }
                ],
                "version": 1,
            },
        )

        with self.assertRaises(HookRegistryError):
            load_hooks_registry(registry_path)

    def test_registry_rejects_matchers_for_events_without_matchers(self) -> None:
        registry_path = self.temp_path / "hooks/registry.json"
        write_json(
            registry_path,
            {
                "managed_hooks": [
                    {
                        "command": "python3 hook.py --runtime {runtime}",
                        "enabled": True,
                        "event": "Stop",
                        "id": "bad-stop-matcher",
                        "matchers": {
                            "codex": "anything",
                        },
                        "runtimes": ["codex"],
                        "scope": "global",
                        "timeout": 5,
                    }
                ],
                "version": 1,
            },
        )

        with self.assertRaises(HookRegistryError):
            load_hooks_registry(registry_path)

    def test_hook_runners_are_silent_on_success(self) -> None:
        script_by_event = {
            "SessionStart": REPO_ROOT / "hooks/scripts/session_start.py",
            "UserPromptSubmit": REPO_ROOT / "hooks/scripts/user_prompt_submit.py",
        }
        home = self.temp_path / "home"
        for event in (
            "SessionStart",
            "UserPromptSubmit",
        ):
            payload = {
                "cwd": str(self.temp_path),
                "hook_event_name": event,
                "model": "gpt-5.5",
                "session_id": "session",
                "transcript_path": None,
            }
            result = subprocess.run(
                [
                    sys.executable,
                    str(script_by_event[event]),
                    "--runtime",
                    "codex",
                ],
                input=json.dumps(payload),
                env={**os.environ, "HOME": str(home)},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")

    def test_stop_runner_is_silent_after_successful_discovery(self) -> None:
        module = self.load_stop_module()
        payload = {
            "cwd": str(self.temp_path),
            "hook_event_name": "Stop",
            "session_id": "session",
        }
        changes = CodexTurnChanges(
            thread_id="session", session_id="session", parent_thread_id="",
            descendant_thread_ids=(), turn_id="turn", turn_started_at=100,
            touched_paths=(),
        )
        stdout, stderr = StringIO(), StringIO()
        # A successful runner requires successful activity discovery. Keep this
        # fixture independent of the machine's live Codex App Server.
        with (
            patch.object(module, "collect_codex_turn_changes", return_value=changes),
            patch.object(sys, "argv", ["stop.py", "--runtime", "codex"]),
            patch.object(sys, "stdin", StringIO(json.dumps(payload))),
            redirect_stdout(stdout), redirect_stderr(stderr),
        ):
            self.assertEqual(module.main(), 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_session_start_runs_repo_script_from_git_root(self) -> None:
        repo = init_git_repo(self.temp_path / "repo")
        nested = repo / "nested"
        nested.mkdir()
        write_executable(
            repo / "scripts/hooks/session_start.py",
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import json",
                    "import os",
                    "payload = json.load(__import__('sys').stdin)",
                    'print("repo=" + os.environ["AGENT_REPO_ROOT"])',
                    'print("runtime=" + os.environ["AGENT_HOOK_RUNTIME"])',
                    'print("cwd=" + os.getcwd())',
                    'print("event=" + payload["hook_event_name"])',
                    'print("schema=" + payload["schema_version"])',
                    'print("repo_root=" + payload["repo_root"])',
                    'print("raw_cwd=" + payload["raw_payload"]["cwd"])',
                    "",
                ]
            ),
        )
        payload = {
            "cwd": str(nested),
            "hook_event_name": "SessionStart",
            "model": "gpt-5.5",
            "session_id": "session",
            "source": "startup",
            "transcript_path": None,
        }

        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "hooks/scripts/session_start.py"),
                "--runtime",
                "codex",
            ],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        expected_repo = repo.resolve()
        output = json.loads(result.stdout)
        self.assertEqual(
            output,
            {
                "hookSpecificOutput": {
                    "additionalContext": (
                        f"repo={expected_repo}\nruntime=codex\ncwd={expected_repo}\nevent=SessionStart\n"
                        f"schema=1.0\nrepo_root={expected_repo}\nraw_cwd={nested}\n"
                    ),
                    "hookEventName": "SessionStart",
                }
            },
        )

    def test_session_start_is_silent_when_repo_script_is_absent(self) -> None:
        repo = init_git_repo(self.temp_path / "repo")
        payload = {
            "cwd": str(repo),
            "hook_event_name": "SessionStart",
            "model": "gpt-5.5",
            "session_id": "session",
            "source": "startup",
            "transcript_path": None,
        }

        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "hooks/scripts/session_start.py"),
                "--runtime",
                "codex",
            ],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_user_prompt_submit_runs_repo_script_from_git_root(self) -> None:
        repo = init_git_repo(self.temp_path / "repo")
        nested = repo / "nested"
        nested.mkdir()
        write_executable(
            repo / "scripts/hooks/user_prompt_submit.py",
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import json",
                    "import os",
                    "payload = json.load(__import__('sys').stdin)",
                    'print("repo=" + os.environ["AGENT_REPO_ROOT"])',
                    'print("runtime=" + os.environ["AGENT_HOOK_RUNTIME"])',
                    'print("cwd=" + os.getcwd())',
                    'print("event=" + payload["hook_event_name"])',
                    'print("prompt=" + payload["prompt"])',
                    'print("schema=" + payload["schema_version"])',
                    'print("repo_root=" + payload["repo_root"])',
                    'print("raw_turn=" + payload["raw_payload"]["turn_id"])',
                    "",
                ]
            ),
        )
        payload = {
            "cwd": str(nested),
            "hook_event_name": "UserPromptSubmit",
            "model": "gpt-5.5",
            "prompt": "ship it",
            "session_id": "session",
            "transcript_path": None,
            "turn_id": "turn",
        }

        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "hooks/scripts/user_prompt_submit.py"),
                "--runtime",
                "codex",
            ],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        expected_repo = repo.resolve()
        output = json.loads(result.stdout)
        self.assertEqual(
            output,
            {
                "hookSpecificOutput": {
                    "additionalContext": (
                        f"repo={expected_repo}\nruntime=codex\ncwd={expected_repo}\nevent=UserPromptSubmit\nprompt=ship it\n"
                        f"schema=1.0\nrepo_root={expected_repo}\nraw_turn=turn\n"
                    ),
                    "hookEventName": "UserPromptSubmit",
                }
            },
        )

    def test_user_prompt_submit_ignores_mismatched_event_payload(self) -> None:
        repo = init_git_repo(self.temp_path / "repo")
        marker = repo / "tmp/user-prompt-ran.txt"
        write_executable(
            repo / "scripts/hooks/user_prompt_submit.py",
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import pathlib",
                    "pathlib.Path('tmp').mkdir(exist_ok=True)",
                    "pathlib.Path('tmp/user-prompt-ran.txt').write_text('ran', encoding='utf-8')",
                    "",
                ]
            ),
        )
        payload = {
            "cwd": str(repo),
            "hook_event_name": "SessionStart",
            "prompt": "wrong event",
        }

        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "hooks/scripts/user_prompt_submit.py"),
                "--runtime",
                "codex",
            ],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertFalse(marker.exists())

    def test_codex_sync_config_preserves_picker_defaults_and_renders_global_stop_hook(self) -> None:
        root = make_control_plane_root(self.temp_path)
        home = self.temp_path / "home"
        bundled_marketplace = self.temp_path / "ChatGPT.app/Contents/Resources/plugins/openai-bundled"
        write_json(root / "mcp/config/presets.json", default_mcp_registry())
        write_json(
            root / "plugins/registry.json",
            {
                "version": 1,
                "paths": {
                    "github_root": str(self.temp_path),
                },
                "managed_plugins": [
                    {
                        "plugin": "computer-use",
                        "marketplace": "openai-bundled",
                        "enabled": True,
                        "scope": "global",
                        "repos": [],
                        "category": "Productivity",
                    },
                    {
                        "plugin": "build-ios-apps",
                        "marketplace": "openai-curated",
                        "enabled": True,
                        "scope": "repo",
                        "repos": ["adi"],
                        "category": "Coding",
                    },
                ],
                "unmanaged_repo_local_plugins": [],
            },
        )
        write_json(
            bundled_marketplace / "plugins/computer-use/.codex-plugin/plugin.json",
            {"name": "computer-use", "version": "1.0.0"},
        )
        write_json(
            bundled_marketplace / ".agents/plugins/marketplace.json",
            {
                "name": "openai-bundled",
                "plugins": [{"name": "computer-use", "source": {"source": "local", "path": "./plugins/computer-use"}}],
            },
        )
        write_text(
            home / ".codex/config.toml",
            'model = "gpt-5.6-sol"\n'
            'model_reasoning_effort = "xhigh"\n'
            'plan_mode_reasoning_effort = "max"\n'
            'service_tier = "fast"\n'
            'profile = "autofix"\n'
            '[profiles.autofix]\nmodel = "gpt-5.4"\n'
            '[profiles.autofix.features]\napps = false\n'
            '[plugins."build-ios-apps@openai-curated"]\nenabled = true\n',
        )
        profile = 'model = "gpt-6-astra"\nmodel_provider = "azure"\n'
        profile_cache = '[tui.model_availability_nux]\n"gpt-6-astra" = 2\n'
        write_text(root / "codex/config/azure-astra.config.toml", profile)
        write_text(
            home / ".codex/azure-astra.config.toml",
            'model = "gpt-5.5"\nmodel_provider = "openai"\n'
            '\n[tui]\nnotifications = false\n\n'
            + profile_cache
            + '\n[tui.model_availability_nux_other]\ncount = 99\n',
        )

        run_command(
            [
                str(REPO_ROOT / "codex/scripts/sync-config.sh"),
                "--apply",
                "--global-only",
                "--global-config",
                str(home / ".codex/config.toml"),
                "--global-hooks",
                str(home / ".codex/hooks.json"),
                "--canonical-dir",
                str(root / "codex/config"),
                "--mcp-registry",
                str(root / "mcp/config/presets.json"),
                "--plugin-registry",
                str(root / "plugins/registry.json"),
                "--hooks-registry",
                str(root / "hooks/registry.json"),
            ],
            env={
                "HOME": str(home),
                "CODEX_BUNDLED_MARKETPLACE": str(bundled_marketplace),
            },
        )

        rendered_config = (home / ".codex/config.toml").read_text(encoding="utf-8")
        self.assertNotIn('\nmodel = ', rendered_config)
        self.assertIn('model_reasoning_effort = "xhigh"', rendered_config)
        self.assertIn('plan_mode_reasoning_effort = "max"', rendered_config)
        self.assertNotIn('\nservice_tier = ', rendered_config)
        self.assertIn("hooks = true", rendered_config)
        self.assertIn('[plugins."computer-use@openai-bundled"]', rendered_config)
        self.assertNotIn("build-ios-apps@openai-curated", rendered_config)
        self.assertIn(
            f'path = "{home}/.codex/skills/.system/plugin-creator/SKILL.md"',
            rendered_config,
        )
        self.assertNotIn("notify =", rendered_config)
        self.assertNotIn('profile = "autofix"', rendered_config)
        self.assertNotIn("[profiles.autofix]", rendered_config)
        self.assertEqual(
            (home / ".codex/azure-astra.config.toml").read_text(encoding="utf-8"),
            profile + "\n" + profile_cache + "\n",
        )
        self.assertEqual(
            (root / "codex/config/azure-astra.config.toml").read_text(encoding="utf-8"),
            profile,
        )

        hooks = read_json(home / ".codex/hooks.json")
        self.assertEqual(
            hooks["hooks"]["Stop"][0]["hooks"][0]["command"],
            'python3 "$HOME/GitHub/agents/hooks/scripts/stop.py" --runtime codex',
        )

    def test_codex_sync_config_uses_managed_bundled_marketplace_and_caches_enabled_plugins(self) -> None:
        root = make_control_plane_root(self.temp_path)
        home = self.temp_path / "home"
        bundled_marketplace = self.temp_path / "ChatGPT.app/Contents/Resources/plugins/openai-bundled"
        managed_marketplace = home / ".codex/.tmp/bundled-marketplaces/openai-bundled"
        write_json(root / "mcp/config/presets.json", default_mcp_registry())
        write_json(
            root / "plugins/registry.json",
            {
                "version": 1,
                "paths": {
                    "github_root": str(self.temp_path),
                },
                "managed_plugins": [
                    {
                        "plugin": "chrome",
                        "marketplace": "openai-bundled",
                        "enabled": True,
                        "scope": "global",
                        "repos": [],
                        "category": "Productivity",
                    },
                    {
                        "plugin": "browser",
                        "marketplace": "openai-bundled",
                        "enabled": False,
                        "scope": "global",
                        "repos": [],
                        "category": "Engineering",
                    },
                ],
                "unmanaged_repo_local_plugins": [],
            },
        )
        write_json(
            bundled_marketplace / ".agents/plugins/marketplace.json",
            {
                "name": "openai-bundled",
                "plugins": [
                    {"name": "chrome", "source": {"source": "local", "path": "./plugins/chrome"}},
                    {"name": "browser", "source": {"source": "local", "path": "./plugins/browser"}},
                    {"name": "visualize", "source": {"source": "local", "path": "./plugins/visualize"}},
                ],
            },
        )
        write_json(
            bundled_marketplace / "plugins/chrome/.codex-plugin/plugin.json",
            {"name": "chrome", "version": "0.1.7"},
        )
        write_json(
            bundled_marketplace / "plugins/browser/.codex-plugin/plugin.json",
            {"name": "browser", "version": "0.1.0-alpha2"},
        )
        write_json(
            bundled_marketplace / "plugins/visualize/.codex-plugin/plugin.json",
            {"name": "visualize", "version": "0.1.0"},
        )
        write_json(
            home / ".codex/plugins/cache/openai-bundled/browser-use/0.1.0-alpha2/.codex-plugin/plugin.json",
            {"name": "browser-use", "version": "0.1.0-alpha2"},
        )
        write_json(
            home / ".codex/plugins/cache/openai-bundled/visualize/0.1.0/.codex-plugin/plugin.json",
            {"name": "visualize", "version": "0.1.0"},
        )
        write_text(managed_marketplace / "plugins/chrome/stale.txt", "stale\n")

        command = [
                str(REPO_ROOT / "codex/scripts/sync-config.sh"),
                "--apply",
                "--global-only",
                "--global-config",
                str(home / ".codex/config.toml"),
                "--global-hooks",
                str(home / ".codex/hooks.json"),
                "--canonical-dir",
                str(root / "codex/config"),
                "--mcp-registry",
                str(root / "mcp/config/presets.json"),
                "--plugin-registry",
                str(root / "plugins/registry.json"),
                "--hooks-registry",
                str(root / "hooks/registry.json"),
        ]
        env = {"HOME": str(home), "CODEX_BUNDLED_MARKETPLACE": str(bundled_marketplace)}
        run_command(command, env=env)

        rendered_config = (home / ".codex/config.toml").read_text(encoding="utf-8")
        self.assertIn("[marketplaces.openai-bundled]", rendered_config)
        self.assertIn(f'source = "{managed_marketplace}"', rendered_config)
        self.assertIn('[plugins."chrome@openai-bundled"]', rendered_config)
        self.assertIn('[plugins."browser@openai-bundled"]', rendered_config)
        self.assertEqual(
            (managed_marketplace / ".agents/plugins/marketplace.json").read_bytes(),
            (bundled_marketplace / ".agents/plugins/marketplace.json").read_bytes(),
        )
        self.assertTrue((managed_marketplace / "plugins").is_symlink())
        self.assertEqual((managed_marketplace / "plugins").resolve(), (bundled_marketplace / "plugins").resolve())
        self.assertTrue(
            (home / ".codex/plugins/cache/openai-bundled/chrome/0.1.7/.codex-plugin/plugin.json").is_file()
        )
        self.assertFalse((home / ".codex/plugins/cache/openai-bundled/browser-use").exists())
        self.assertTrue((home / ".codex/plugins/cache/openai-bundled/visualize").exists())

        app_manifest = {"name": "openai-bundled", "plugins": [{"name": "chrome", "source": {"source": "local", "path": "./plugins/chrome"}}]}
        write_json(managed_marketplace / ".agents/plugins/marketplace.json", app_manifest)
        (managed_marketplace / "plugins").unlink()
        write_text(managed_marketplace / "plugins/chrome/app-owned.txt", "app-owned\n")
        run_command(command, env=env)
        self.assertEqual(
            json.loads((managed_marketplace / ".agents/plugins/marketplace.json").read_text()),
            app_manifest,
        )
        self.assertTrue((managed_marketplace / "plugins/chrome/app-owned.txt").is_file())

    def test_stop_hook_has_tracking_upstream_false_for_new_local_branch(self) -> None:
        module = self.load_stop_module()
        remote = init_git_repo(self.temp_path / "remote.git")
        run_command(["git", "-C", str(remote), "config", "receive.denyCurrentBranch", "updateInstead"])
        repo = init_git_repo(self.temp_path / "repo", with_initial_commit=True)
        run_command(["git", "-C", str(repo), "remote", "add", "origin", str(remote)])
        run_command(["git", "-C", str(repo), "push", "-u", "origin", "main"])
        run_command(["git", "-C", str(repo), "checkout", "-b", "feature/test"])

        self.assertFalse(module.has_tracking_upstream(str(repo)))

    def test_hook_runners_reject_retired_runtimes(self) -> None:
        for script in ("session_start.py", "user_prompt_submit.py", "stop.py"):
            for runtime in ("claude", "copilot", "antigravity"):
                with self.subTest(script=script, runtime=runtime):
                    result = subprocess.run(
                        [sys.executable, str(REPO_ROOT / "hooks/scripts" / script),
                         "--runtime", runtime],
                        input="{}", capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("invalid choice", result.stderr)
                    self.assertEqual(result.stdout, "")

    def test_stop_hook_uses_initial_push_for_branch_without_upstream(self) -> None:
        module = self.load_stop_module()
        remote = init_git_repo(self.temp_path / "remote.git")
        run_command(["git", "-C", str(remote), "config", "receive.denyCurrentBranch", "updateInstead"])
        repo = init_git_repo(self.temp_path / "repo", with_initial_commit=True)
        run_command(["git", "-C", str(repo), "remote", "add", "origin", str(remote)])
        run_command(["git", "-C", str(repo), "push", "-u", "origin", "main"])
        run_command(["git", "-C", str(repo), "checkout", "-b", "feature/test"])
        (repo / "note.txt").write_text("hello\n", encoding="utf-8")
        run_command(["git", "-C", str(repo), "add", "note.txt"])
        run_command(["git", "-C", str(repo), "commit", "-m", "fixture change"])

        result, command, _title = module.push_committed_repo(str(repo))

        self.assertIsNotNone(result)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(command, ["git", "push", "-u", "origin", "HEAD"])
        upstream = run_command([
            "git", "-C", str(repo), "rev-parse", "--abbrev-ref",
            "--symbolic-full-name", "@{upstream}",
        ])
        self.assertEqual(upstream.stdout.strip(), "origin/feature/test")

    def test_stop_hook_uses_optimistic_push_for_branch_with_upstream(self) -> None:
        module = self.load_stop_module()
        completed = subprocess.CompletedProcess([], 0, "", "")
        with (
            patch.object(module, "resolve_push_remote", return_value="origin"),
            patch.object(module, "has_tracking_upstream", return_value=True),
            patch.object(module, "run", return_value=completed) as run_mock,
        ):
            result, command, _title = module.push_committed_repo(str(self.temp_path))

        self.assertEqual(result.returncode, 0)
        self.assertEqual(command, ["git", "push", "origin", "HEAD"])
        run_mock.assert_called_once_with(
            command, str(self.temp_path), timeout=module.GIT_PUSH_TIMEOUT_SEC,
        )

    def test_stop_hook_rebases_and_retries_push_when_remote_is_ahead(self) -> None:
        module = self.load_stop_module()
        repo = init_git_repo(self.temp_path / "repo", with_initial_commit=True)
        write_executable(repo / "scripts/check-fast.sh", "#!/bin/sh\nexit 0\n")
        captured_commands: list[list[str]] = []
        push_attempts = 0

        def fake_run(args, cwd, *, timeout, env=None):  # noqa: ANN001, ARG001
            nonlocal push_attempts
            captured_commands.append(list(args))
            if args == ["git", "push", "origin", "HEAD"]:
                push_attempts += 1
                if push_attempts == 1:
                    return subprocess.CompletedProcess(
                        args, 1, "", "! [rejected] HEAD -> main (fetch first)\n",
                    )
            return subprocess.CompletedProcess(args, 0, "", "")

        with (
            patch.object(module, "resolve_push_remote", return_value="origin"),
            patch.object(module, "has_tracking_upstream", return_value=True),
            patch.object(module, "run", side_effect=fake_run),
        ):
            result, _command, _title = module.push_committed_repo(str(repo))

        self.assertEqual(result.returncode, 0)
        self.assertEqual(push_attempts, 2)
        self.assertEqual(captured_commands, [
            ["git", "push", "origin", "HEAD"],
            ["git", "pull", "--rebase"],
            ["bash", "scripts/check-fast.sh"],
            ["git", "status", "--porcelain"],
            ["git", "push", "origin", "HEAD"],
        ])

    def test_stop_hook_blocks_when_post_rebase_fast_check_fails(self) -> None:
        module = self.load_stop_module()
        repo = init_git_repo(self.temp_path / "repo", with_initial_commit=True)
        write_executable(repo / "scripts/check-fast.sh", "#!/bin/sh\nexit 1\n")
        push_attempts = 0

        def fake_run(args, cwd, *, timeout, env=None):  # noqa: ANN001, ARG001
            nonlocal push_attempts
            if args == ["git", "push", "origin", "HEAD"]:
                push_attempts += 1
                return subprocess.CompletedProcess(
                    args, 1, "", "! [rejected] HEAD -> main (fetch first)\n",
                )
            if args == ["bash", "scripts/check-fast.sh"]:
                return subprocess.CompletedProcess(args, 17, "", "rebased tree failed validation\n")
            return subprocess.CompletedProcess(args, 0, "", "")

        with (
            patch.object(module, "resolve_push_remote", return_value="origin"),
            patch.object(module, "has_tracking_upstream", return_value=True),
            patch.object(module, "run", side_effect=fake_run),
        ):
            result, command, title = module.push_committed_repo(str(repo))

        self.assertEqual(result.returncode, 17)
        self.assertEqual(command, ["bash", "scripts/check-fast.sh"])
        self.assertEqual(title, "scripts/check-fast.sh after git pull --rebase")
        self.assertIn("rebased tree failed validation", result.stderr)
        self.assertEqual(push_attempts, 1)

    def test_codex_stop_blocks_on_repo_check_failure_before_commit(self) -> None:
        module = self.load_stop_module()
        repo = init_git_repo(self.temp_path / "repo", with_initial_commit=True)
        original_head = run_command(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout
        write_executable(
            repo / "scripts/check-fast.sh",
            "#!/bin/sh\nprintf 'repo check failed\\n' >&2\nexit 1\n",
        )
        (repo / "note.txt").write_text("hello\n", encoding="utf-8")
        changes = CodexTurnChanges(
            thread_id="thread", session_id="thread", parent_thread_id="",
            descendant_thread_ids=(), turn_id="turn", turn_started_at=100,
            touched_paths=(str(repo / "note.txt"),),
        )
        with (
            patch.dict(os.environ, {"HOME": str(self.temp_path / "test-home")}),
            patch.object(module, "collect_codex_turn_changes", return_value=changes),
            patch.object(module, "log"),
        ):
            output = module.process_codex_repositories(
                str(repo), {"hook_event_name": "Stop", "session_id": "thread"},
            )

        self.assertIsNotNone(output)
        self.assertEqual(output["decision"], "block")
        self.assertIn("repo check failed", output["reason"])
        self.assertEqual(
            run_command(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout,
            original_head,
        )

    def test_stop_feedback_turn_starts_app_server_turn(self) -> None:
        fake_bin = self.temp_path / "bin"
        fake_bin.mkdir()
        calls_path = self.temp_path / "calls.jsonl"
        reason_file = self.temp_path / "reason.txt"
        reason_file.write_text("repo check failed\n", encoding="utf-8")
        write_executable(
            fake_bin / "codex",
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import json",
                    "import os",
                    "import sys",
                    "calls_path = os.environ['FAKE_CODEX_CALLS']",
                    "def emit(value):",
                    "    print(json.dumps(value), flush=True)",
                    "for line in sys.stdin:",
                    "    message = json.loads(line)",
                    "    with open(calls_path, 'a', encoding='utf-8') as handle:",
                    "        handle.write(json.dumps(message, sort_keys=True) + '\\n')",
                    "    method = message.get('method')",
                    "    request_id = message.get('id')",
                    "    if request_id is None:",
                    "        continue",
                    "    if method == 'turn/start':",
                    "        params = message.get('params') or {}",
                    "        text = params['input'][0]['text']",
                    "        if not text.startswith('Hook feedback\\n\\nrepo check failed'):",
                    "            emit({'id': request_id, 'error': {'message': 'bad prompt'}})",
                    "            continue",
                    "        emit({'id': request_id, 'result': {'turn': {'id': 'turn-1'}}})",
                    "        emit({'method': 'turn/completed', 'params': {'threadId': params['threadId'], 'turnId': 'turn-1', 'status': 'completed'}})",
                    "        continue",
                    "    emit({'id': request_id, 'result': {}})",
                    "",
                ]
            ),
        )

        result = run_command(
            [
                sys.executable,
                str(REPO_ROOT / "hooks/scripts/stop_feedback_turn.py"),
                "--thread-id",
                "thread-1",
                "--cwd",
                str(self.temp_path),
                "--reason-file",
                str(reason_file),
                "--initial-delay-seconds",
                "0",
                "--timeout-seconds",
                "2",
                "--turn-timeout-seconds",
                "2",
            ],
            env={
                "PATH": f"{fake_bin}:{os.environ.get('PATH', '')}",
                "FAKE_CODEX_CALLS": str(calls_path),
            },
        )

        self.assertEqual(result.returncode, 0)
        calls = [json.loads(line) for line in calls_path.read_text(encoding="utf-8").splitlines()]
        methods = [call.get("method") for call in calls]
        self.assertIn("initialize", methods)
        self.assertIn("thread/resume", methods)
        self.assertIn("turn/start", methods)
        self.assertFalse(reason_file.exists())
