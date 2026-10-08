# Shared MCP Registry

`config/presets.json` owns neutral MCP definitions and their repository scopes. `../repos/registry.json` owns the managed repository inventory.

- Use schema version 3. Each preset defines its transport fields and `repos`, either `"all"` or an array of managed repository paths. An empty array means unassigned.
- Keep assignment here rather than in the repository registry or generated config. Renderers select repositories using explicit client enablement in the repository registry.
- Codex renders selected definitions into each enabled repo's `.codex/config.toml`; the Claude renderer translates them into its native project MCP surface.
- Do not store runtime-specific TOML blocks here. The renderer translates neutral transport fields.
- After changing definitions or scopes, run shared bootstrap/check and verify affected repository output. Exact-path `--repo` filters are supported.
