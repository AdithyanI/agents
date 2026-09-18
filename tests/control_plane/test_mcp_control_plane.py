from __future__ import annotations

import unittest

from mcp.control_plane import McpRegistryError, load_mcp_catalog_data

REPOS = [{"path": "~/GitHub/agents"}, {"path": "~/GitHub/frontier-lab-intelligence"}]


class McpControlPlaneTests(unittest.TestCase):
    def catalog(self, scope, **fields):
        return load_mcp_catalog_data({"version": 3, "presets": {"docs": {
            "transport": "http", "url": "https://example.com/mcp", "repos": scope, **fields,
        }}}, REPOS)

    def test_explicit_scope_does_not_leak_to_other_repos(self) -> None:
        catalog = self.catalog(["~/GitHub/agents"])
        self.assertEqual([name for name, _ in catalog.presets_for("~/GitHub/agents")], ["docs"])
        self.assertEqual(catalog.presets_for("~/GitHub/frontier-lab-intelligence"), [])
        self.assertEqual(catalog.repos_for("docs"), ["~/GitHub/agents"])

    def test_all_and_unassigned_scopes(self) -> None:
        self.assertEqual(len(self.catalog("all").repos_for("docs")), 2)
        self.assertEqual(self.catalog([]).repos_for("docs"), [])

    def test_unknown_repo_fails_before_rendering(self) -> None:
        with self.assertRaisesRegex(McpRegistryError, "missing from repo-bootstrap.json"):
            self.catalog(["~/GitHub/not-managed"])

    def test_retired_client_target_schema_is_rejected(self) -> None:
        with self.assertRaisesRegex(McpRegistryError, "unsupported keys: targets"):
            self.catalog("all", targets=[{"clients": ["copilot"], "repos": "all"}])
        with self.assertRaisesRegex(McpRegistryError, "version must be 3"):
            load_mcp_catalog_data({"version": 2, "presets": {}}, REPOS)

    def test_invalid_transport_and_scope_do_not_render(self) -> None:
        for fields, message in (({"transport": "other"}, "transport"), ({"command": "npx"}, "http transport")):
            with self.subTest(fields=fields), self.assertRaisesRegex(McpRegistryError, message):
                self.catalog("all", **fields)
        with self.assertRaisesRegex(McpRegistryError, "array of strings"):
            self.catalog([None])

    def test_stdio_definition_preserves_runtime_fields(self) -> None:
        definition = {"transport": "stdio", "command": "tool", "args": ["serve"], "env": {"MODE": "test"}, "cwd": "/tmp"}
        catalog = load_mcp_catalog_data({"version": 3, "presets": {"tool": {**definition, "repos": "all"}}}, REPOS)
        self.assertEqual(catalog.presets_for("~/GitHub/agents"), [("tool", definition)])


if __name__ == "__main__":
    unittest.main()
