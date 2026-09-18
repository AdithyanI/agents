# Codex-only control plane

## Goal

Remove Claude, Copilot, and unused agent-setup integrations from the shared control plane, machine scripts, and managed runtime surfaces while preserving working Codex capabilities.

## Context and scope

- Started 2026-09-18. User explicitly authorized complete removal, including `../scripts/`, with Git history providing recovery for tracked code.
- Codex is the only supported development client. No dormant multi-client flag framework.
- Preserve application product behavior, private workspaces, credentials, conversations, and unrelated VS Code settings. Remove retired-client setup, including dedicated manual per-repo instructions/permissions and editor integration preferences; preserve unrelated shared settings and data.
- Codex preview rendering currently lives in `sync-claude.py`; move it before retiring that script.
- Existing archived Astra audit is background evidence, not an active implementation tracker.

## Done when

- [ ] Codex-only bootstrap, reconciliation, registries, previews, hooks, dashboard, and checks work without retired client modules.
- [ ] Claude/Copilot setup and unused agent experiments are removed from `agents` and machine-owned `scripts`.
- [ ] Managed obsolete files and background jobs are removed without removing user data or unrelated configuration.
- [ ] Global/root guidance and current operational docs describe the resulting system.
- [ ] Required checks pass, repeat bootstrap is stable, and surviving Codex capabilities are verified.
- [ ] Evidence and learnings are recorded and the project is archived.

## Decisions

- Delete obsolete integrations rather than maintain inactive implementations.
- Use ownership checks for shared global settings/MCPs/jobs; retire dedicated repo client setup completely with private backups. Do not delete whole application state directories.
- Historical audits and vendored upstream examples are not active setup and need no blanket text scrub.
- Main agent owns integration, shared registries, runtime migration, documentation, validation, and final report.

## Current batch

| Status | Work | Owner |
| --- | --- | --- |
| in_progress | Bootstrap, registries, runtime cleanup, guidance, integration | parent |
| complete | Retire agent setup in sibling machine-scripts repo; 25 focused tests and fast checks passed | machine scripts worker |
| in_progress | Ownership-aware installed-file/job migration | machine scripts worker |
| complete | Standalone Codex preview renderer; 13 tests and byte-identical preview output | preview worker |
| complete | Codex-only dashboard; 9 backend tests, UI build, desktop/mobile browser proof | preview worker |
| complete | Retired hook/session-maintenance adapters; surviving Codex hooks unchanged | hooks worker |
| complete | Removed orphaned Dobby Claude finalizer wiring; engine 193 tests, gateway 115 tests, four repo fast checks and Codex startup smoke | hooks worker |

## Validation

- Focused hermetic tests for changed contracts, then `scripts/check-fast.sh` and `scripts/check-agent-control-planes.sh` including full control-plane regression tests.
- Machine-scripts `ops/check-fast.sh` and focused tests for changed sync/install behavior.
- Bootstrap apply, repeat dry-run/check, absence of retired managed surfaces/jobs, and Codex preview/config/hooks checks.
- Check other changed repositories as required by their local guidance; record any genuine environment limits.

## Progress

- 2026-09-18: Began implementation after explicit authorization; initial agents working tree clean.

- 2026-09-18: Removed active client dimensions from MCP schema and repo bootstrap; Codex MCP assignments exactly match the baseline. Standalone Codex previews replace the old Claude-owned renderer. Updated current guidance and operations docs; archived audit evidence remains unchanged.
- Validation so far: 73 focused MCP/bootstrap/Stop regressions and 10 orchestration tests pass. Full regression suite passed 248 tests; root fast gate passed.

- Machine auto-sync published the source changes and ran retirement during implementation. Verified all 65 saved Codex config/hook/preview files remain byte-identical; all three retired jobs are unloaded. Private backup run: `~/.local/state/agents-control-plane/retired-client-backups/20260918T134849Z-thvdi42f`.
- Migration review identified JSONC comment/trailing-comma parsing and hook-path-boundary edge cases; fixes and focused regression coverage are being added before final validation.

## Open questions / blockers

None.
