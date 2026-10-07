from __future__ import annotations

import contextlib
import importlib.util
import io
import types
import unittest
from unittest.mock import Mock, patch

from tests.control_plane.support import REPO_ROOT


def load_module():
    path = REPO_ROOT / "skills-source/owned/imagegen/scripts/image_gen.py"
    spec = importlib.util.spec_from_file_location("imagegen_azure_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ImagegenAzureDisabledTests(unittest.TestCase):
    def test_cli_rejects_every_azure_operation_before_credentials_or_execution(self):
        commands = (
            ["generate", "--prompt", "public UI"],
            ["edit", "--image", "/nonexistent/reference.png", "--prompt", "public UI"],
            ["generate-batch", "--input", "/nonexistent/jobs.jsonl", "--out-dir", "tmp/unused"],
        )
        for command in commands:
            for dry_run in (False, True):
                with self.subTest(command=command[0], dry_run=dry_run):
                    module = load_module()
                    output = io.StringIO()
                    argv = ["image_gen.py", *command, "--provider", "azure"]
                    if dry_run:
                        argv.append("--dry-run")
                    with contextlib.ExitStack() as stack:
                        stack.enter_context(patch.object(module.sys, "argv", argv))
                        guards = [stack.enter_context(patch.object(module, name)) for name in (
                            "_azure_api_key", "_ensure_api_env", "_create_client",
                            "_create_async_client", "_generate", "_edit", "_generate_batch",
                        )]
                        stack.enter_context(contextlib.redirect_stderr(output))
                        with self.assertRaises(SystemExit) as caught:
                            module.main()
                        self.assertEqual(caught.exception.code, 1)
                        self.assertIn("Direct Azure image generation is disabled", output.getvalue())
                        for guard in guards:
                            guard.assert_not_called()

    def test_direct_helpers_reject_azure_before_credentials_sdk_or_network(self):
        module = load_module()
        sdk = types.SimpleNamespace(OpenAI=Mock(), AsyncOpenAI=Mock())
        operations = (
            lambda: module._ensure_api_env(False, "azure"),
            lambda: module._ensure_api_env(True, "azure"),
            lambda: module._client_options("azure"),
            lambda: module._create_client("azure"),
            lambda: module._create_async_client("azure"),
        )
        with patch.dict(module.sys.modules, {"openai": sdk}), \
                patch.object(module, "_azure_api_key") as key, \
                patch("socket.create_connection") as network, \
                contextlib.redirect_stderr(io.StringIO()):
            for operation in operations:
                with self.assertRaises(SystemExit) as caught:
                    operation()
                self.assertEqual(caught.exception.code, 1)
            key.assert_not_called()
            sdk.OpenAI.assert_not_called()
            sdk.AsyncOpenAI.assert_not_called()
            network.assert_not_called()

    def test_retained_credential_helper_never_reads_codex_credentials(self):
        module = load_module()
        with patch.object(module.Path, "home") as home, \
                patch.object(module.Path, "read_text") as read, \
                patch.object(module.Path, "stat") as stat, \
                contextlib.redirect_stderr(io.StringIO()), \
                self.assertRaises(SystemExit) as caught:
            module._azure_api_key()
        self.assertEqual(caught.exception.code, 1)
        home.assert_not_called()
        read.assert_not_called()
        stat.assert_not_called()


if __name__ == "__main__":
    unittest.main()
