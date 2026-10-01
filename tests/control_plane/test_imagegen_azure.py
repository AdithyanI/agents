from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import AsyncMock, patch

from tests.control_plane.support import REPO_ROOT


def load_module():
    path = REPO_ROOT / "skills-source/owned/imagegen/scripts/image_gen.py"
    spec = importlib.util.spec_from_file_location("imagegen_azure_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ImagegenAzureTests(unittest.TestCase):
    def test_direct_route_uses_generated_credential_and_no_sdk_retries(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".codex/.env"
            path.parent.mkdir()
            path.write_text("export AZURE_OPENAI_API_KEY='fixture-key'\n")
            path.chmod(0o600)
            with patch.object(module.Path, "home", return_value=Path(directory)):
                options = module._client_options("azure")
                self.assertEqual(options["base_url"], module.AZURE_BASE_URL)
                self.assertEqual(options["api_key"], "fixture-key")
                self.assertEqual(options["max_retries"], 0)
                path.chmod(0o644)
                output = io.StringIO()
                with contextlib.redirect_stderr(output), self.assertRaises(SystemExit):
                    module._azure_api_key()
                self.assertNotIn("fixture-key", output.getvalue())

    def test_model_selection_preserves_native_size_without_network(self):
        module = load_module()
        for model in ("gpt-image-2.5-sunburst", "gpt-image-2.5-flare"):
            output = io.StringIO()
            with patch.object(module.sys, "argv", ["image_gen.py", "generate", "--provider", "azure",
                    "--model", model, "--prompt", "public UI", "--size", "1536x864", "--dry-run"]), \
                    patch.object(module, "_azure_api_key") as key, contextlib.redirect_stdout(output):
                self.assertEqual(module.main(), 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["model"], model)
            self.assertEqual(payload["size"], "1536x864")
            self.assertEqual(payload["output_aspect_ratio"], "none")
            key.assert_not_called()

    def test_direct_batch_timeout_is_not_resubmitted_or_exposed(self):
        module = load_module()
        generate = AsyncMock(side_effect=TimeoutError("fixture-key"))
        client = types.SimpleNamespace(images=types.SimpleNamespace(generate=generate))
        with tempfile.TemporaryDirectory() as directory:
            jobs = Path(directory) / "jobs.jsonl"
            jobs.write_text(json.dumps({"prompt": "public UI"}) + "\n")
            output = io.StringIO()
            with patch.object(module.sys, "argv", ["image_gen.py", "generate-batch", "--provider", "azure",
                    "--model", "gpt-image-2.5-sunburst", "--input", str(jobs), "--out-dir", directory]), \
                    patch.object(module, "_ensure_api_env"), \
                    patch.object(module, "_create_async_client", return_value=client), \
                    contextlib.redirect_stderr(output), self.assertRaises(SystemExit) as caught:
                module.main()
            self.assertEqual(caught.exception.code, 1)
            self.assertEqual(generate.await_count, 1)
            self.assertNotIn("fixture-key", output.getvalue())
