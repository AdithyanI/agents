# Codex Control Plane

This subtree owns Codex-specific templates, scripts, shell/Ghostty integration, and terminal helpers invoked by Keyboard Maestro. Generic machine shell/bootstrap wiring belongs in `~/GitHub/scripts`; runtime state belongs in `~/.codex`.

- Edit canonical inputs and use the root bootstrap/check workflow. MCP scope belongs in `../mcp/config/presets.json`; repo behavior and exact trust roots belong in `../repos/registry.json`.
- Keep auth, sessions, runtime databases, logs, caches, and secret values out of this repo. Preserve the app-managed nested checkout at `~/.codex/vendor_imports/skills`.
- Leave provider, model discovery, authentication and thread selections to native Codex. Shared sync manages capabilities and explicit automation profiles, without selecting a global provider or model.
- Keep managed backups under `~/.local/state/codex-control-plane/`, not beside live config.

For ownership exceptions, read `../docs/references/codex-control-plane-ownership.md`. For finalization, runtime recovery, or component commands, use `../docs/references/codex-control-plane-operations.md`. Shared architecture is in `../docs/architecture/codex-control-plane.md`.
