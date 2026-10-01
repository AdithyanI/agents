from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import urllib.error

from mcp import azure_web_research as research
from tests.control_plane.support import REPO_ROOT, TempDirTestCase, run_command, write_text


def fixture_response(status="completed"):
    return {
        "id": "resp_fixture", "status": status, "model": "fixture-search",
        "output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "content": [{"type": "output_text", "text": "A cited answer.",
                "annotations": [{"type": "url_citation", "url": "https://example.com/source",
                                 "title": "Source", "start_index": 2, "end_index": 7}]}]},
            {"type": "web_search_call", "action": {"type": "search", "query": "fixture query",
                "sources": [{"url": "https://example.com/source"}, {"url": "https://example.com/second"}]},
                "results": [{"url": "https://example.com/source", "title": "Source", "snippet": "Evidence."},
                            {"url": "https://example.com/second", "title": "Second", "snippet": "More evidence."}]},
        ],
        "usage": {"input_tokens": 100, "output_tokens": 20},
        "tool_usage": {"web_search": {"num_requests": 4}},
    }


class AzureWebResearchTests(TempDirTestCase):
    def test_response_order_sources_and_provider_billing_count(self):
        data = research.parse_response(fixture_response(), 1)
        self.assertEqual(data["answer"], "A cited answer.")
        self.assertEqual(data["bing_requests"], 4)
        self.assertEqual(len(data["search_actions"]), 1)
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(len(data["sources"]), 2)
        self.assertEqual(data["sources"][0]["title"], "Source")
        self.assertEqual(data["citations"][0]["url"], "https://example.com/source")

    def test_unsearched_and_incomplete_responses_are_not_success(self):
        response = fixture_response()
        response["output"] = response["output"][:2]
        with self.assertRaises(research.ResearchError) as caught:
            research.parse_response(response, 8)
        self.assertEqual(caught.exception.code, "E_NO_SEARCH")
        with self.assertRaises(research.ResearchError) as caught:
            research.parse_response(fixture_response("incomplete"), 8)
        self.assertEqual(caught.exception.code, "E_INCOMPLETE")
        self.assertEqual(caught.exception.data["bing_requests"], 4)
        self.assertEqual(caught.exception.data["answer"], "A cited answer.")

    def test_payload_is_bounded_and_sends_only_the_supplied_question(self):
        config = {"search_model": "quick", "research_model": "thorough"}
        args = research.validate("search", {"query": "  public question  ", "domains": ["developer.apple.com"]})
        quick = research.request_payload("search", args, config)
        self.assertEqual(quick["input"], "public question")
        self.assertFalse(quick["store"])
        self.assertEqual(quick["model"], "quick")
        self.assertEqual(quick["tools"][0]["filters"]["allowed_domains"], ["developer.apple.com"])
        deep = research.request_payload("research", args, config)
        self.assertEqual(deep["model"], "thorough")
        self.assertEqual(deep["reasoning"]["effort"], "high")
        self.assertNotIn("previous_response_id", deep)
        self.assertNotIn("conversation", deep)
        self.assertNotIn("metadata", deep)

    def test_invalid_arguments_fail_before_network_or_credentials(self):
        cases = [{"query": ""}, {"query": "q", "limit": True}, {"query": "q", "timeout": 301},
                 {"query": "q", "timeout": float("nan")}, {"query": "q", "domains": ["https://example.com"]},
                 {"query": "q", "domains": ["example.com/path"]}, {"query": "q", "secret": "not-allowed"}]
        with patch.object(research, "post_response") as post:
            for arguments in cases:
                with self.subTest(arguments=arguments):
                    result, code = research.execute("search", arguments)
                    self.assertEqual(code, 2)
                    self.assertEqual(result["error"]["code"], "E_VALIDATION")
            post.assert_not_called()

    def test_credential_reads_generated_export_and_requires_owner_only(self):
        path = write_text(self.temp_path / ".codex/.env", "# generated\nexport AZURE_OPENAI_API_KEY='fixture-key'\n")
        path.chmod(0o600)
        with patch.object(Path, "home", return_value=self.temp_path):
            self.assertEqual(research.credential(), "fixture-key")
            path.chmod(0o644)
            with self.assertRaises(research.ResearchError) as caught:
                research.credential()
            self.assertEqual(caught.exception.code, "E_AUTH")
            self.assertNotIn("fixture-key", str(caught.exception))

    def test_http_failures_never_expose_reflected_credentials_or_retry(self):
        error = urllib.error.HTTPError("https://example.com", 429, "quota", {}, io.BytesIO(b"fixture-secret"))
        with patch.object(research, "credential", return_value="fixture-secret"), \
             patch.object(research.urllib.request, "urlopen", side_effect=error) as post:
            with self.assertRaises(research.ResearchError) as caught:
                research.post_response({"endpoint": "https://example.com"}, {}, 1)
        post.assert_called_once()
        self.assertEqual(caught.exception.code, "E_AZURE")
        self.assertTrue(caught.exception.retryable)
        self.assertNotIn("fixture-secret", str(caught.exception))

    def test_timeout_does_not_claim_retry_is_safe(self):
        with patch.object(research, "credential", return_value="fixture-secret"), \
             patch.object(research.urllib.request, "urlopen", side_effect=TimeoutError) as post:
            with self.assertRaises(research.ResearchError) as caught:
                research.post_response({"endpoint": "https://example.com"}, {}, 1)
        post.assert_called_once()
        self.assertEqual(caught.exception.exit_code, 5)
        self.assertFalse(caught.exception.retryable)
        self.assertIn("unknown", str(caught.exception))

    def test_config_rejects_non_azure_credential_destinations(self):
        path = write_text(self.temp_path / "config.json", json.dumps({"endpoint": "https://example.com/openai/v1",
                                                                    "search_model": "q", "research_model": "r"}))
        with patch.object(research, "CONFIG", path):
            with self.assertRaises(research.ResearchError) as caught:
                research.load_config()
        self.assertEqual(caught.exception.code, "E_CONFIG")

    def test_cli_json_success_plain_no_input_and_invalid_usage(self):
        child = (
            "import sys\nfrom unittest.mock import patch\n"
            f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
            "from mcp import azure_web_research as r\n"
            "with patch.object(r, 'post_response', return_value=" + repr(fixture_response()) + "):\n"
            "    raise SystemExit(r.main())\n"
        )
        result = run_command([sys.executable, "-c", child, "search", "public question", "--no-input"])
        envelope = json.loads(result.stdout)
        self.assertEqual(set(envelope), {"schema_version", "command", "status", "data", "error", "meta"})
        self.assertEqual(envelope["status"], "ok")
        self.assertEqual(envelope["data"]["bing_requests"], 4)
        result = run_command([sys.executable, "-c", child, "search", "public question", "--plain", "--no-input"])
        self.assertIn("A cited answer.", result.stdout)
        self.assertIn("Bing requests: 4", result.stdout)
        result = run_command([sys.executable, "-m", "mcp.azure_web_research", "search", "q", "--limit", "no"],
                             cwd=REPO_ROOT, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "E_VALIDATION")

    def test_mcp_stdio_handshake_listing_and_validation_without_network(self):
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "web_search", "arguments": {"query": ""}}},
        ]
        result = subprocess.run([sys.executable, "-m", "mcp.azure_web_research", "serve"], cwd=REPO_ROOT,
                                input="\n".join(json.dumps(item) for item in requests) + "\n",
                                capture_output=True, text=True, timeout=10, check=True)
        responses = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual([item["id"] for item in responses], [1, 2, 3])
        self.assertEqual(responses[0]["result"]["protocolVersion"], "2025-03-26")
        self.assertEqual([tool["name"] for tool in responses[1]["result"]["tools"]], ["web_search", "web_research"])
        self.assertTrue(responses[2]["result"]["isError"])
        self.assertEqual(responses[2]["result"]["structuredContent"]["error"]["code"], "E_VALIDATION")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
