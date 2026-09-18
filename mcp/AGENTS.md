# Codex MCP Registry

`config/presets.json` owns neutral MCP definitions and their repository scopes. `../codex/config/repo-bootstrap.json` owns the managed repository inventory.

- Use schema version 3. Each preset defines its transport fields and `repos`, either `"all"` or an array of managed repository paths. An empty array means unassigned.
- Keep assignment here rather than in repo-bootstrap or generated config. There is no client selector.
- Codex renders selected definitions into each repo's `.codex/config.toml`.
- Do not store runtime-specific TOML blocks here. The renderer translates neutral transport fields.
- After changing definitions or scopes, run shared bootstrap/check and verify affected repository output. Exact-path `--repo` filters are supported.
