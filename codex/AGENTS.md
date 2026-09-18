# Codex Control Plane

This subtree owns Codex-specific templates, scripts, shell/Ghostty integration, and terminal helpers invoked by Keyboard Maestro. Generic machine shell/bootstrap wiring belongs in `~/GitHub/scripts`; runtime state belongs in `~/.codex`.

- Edit canonical inputs and use the root bootstrap/check workflow. MCP scope belongs in `../mcp/config/presets.json`; repo behavior and exact trust roots belong in `config/repo-bootstrap.json`.
- Keep auth, sessions, runtime databases, logs, caches, and secret values out of this repo. Preserve the app-managed nested checkout at `~/.codex/vendor_imports/skills`.
- Native credentials are materialized through `scripts/sync-native-env.py` and `config/secrets.env.map`; verify the generated environment without printing values.
- Keep active provider choice machine-local. Use `../scripts/codex-provider.py` or the native menu; see `../docs/references/codex-provider-switch.md`.
- Keep managed backups under `~/.local/state/codex-control-plane/`, not beside live config.

For ownership exceptions, read `../docs/references/codex-control-plane-ownership.md`. For finalization, runtime recovery, or component commands, use `../docs/references/codex-control-plane-operations.md`. Shared architecture is in `../docs/architecture/codex-control-plane.md`.
