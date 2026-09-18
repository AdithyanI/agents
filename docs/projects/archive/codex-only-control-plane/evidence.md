# Codex-only cleanup evidence

Completed locally on September 18, 2026. Scope is the shared development control plane and its 28 available managed repositories, including the sibling machine-scripts repo. Application provider support and historical audit/source snapshots are separate from this setup.

## Result

- Removed Claude/Copilot renderers, overlays, provider launcher switching, client selectors, hook adapters, session-maintenance jobs, and the Antigravity experiment.
- MCP schema version 3 has repository scopes only. All surviving Codex assignments exactly match the saved baseline.
- Extracted Codex preview generation into `scripts/sync-codex-previews.py` and removed client comparisons from the dashboard.
- Removed obsolete machine-script reconciliation, Copilot-specific upgrade behavior, remote-session commands, and dead Claude session-finalizer calls in Dobby.
- Updated current guidance, skill references, operational docs, and diagrams. The earlier Astra repository audit remains archived and unapplied; its proposed patches need refreshing against this cleanup before reuse.
- The ownership-aware migration changed 141 distinct local paths. Two editor files received a second cleanup pass for manual integration preferences. Three retired LaunchAgents are unloaded.
- All 65 pre-existing repo Codex config, hook, and preview files are byte-identical to the saved baseline. The generated global guidance now describes Codex-only setup.

## Recovery

Tracked source is recoverable through Git history. Machine auto-sync published the initial removal during execution (`a9bb8c7c`, `dc761438` in agents); normal repository automation handles remaining publication.

Private local backups retain the original file contents or symlink targets:

- `~/.local/state/agents-control-plane/retired-client-backups/20260918T134849Z-thvdi42f` — 141 entries.
- `~/.local/state/agents-control-plane/retired-client-backups/20260918T135215Z-_wr_o885` — two additional editor configuration versions.

Credentials, conversation history, application binaries, real skill sources, unrelated preferences, and the gateway's Claude provider implementation remain. The gateway's old session-maintenance subprocess was removed; Codex finalization remains.

## Validation

- Full shared bootstrap applied successfully, including Codex structural validation across all 28 local managed repositories.
- Retirement check: zero pending changes. All eight Codex preview environments are in sync.
- Managed Git hook checks: 28 checked, zero drift; one registered repository is absent on this machine and skipped normally.
- Plugin/runtime drift audit: no errors or warnings.
- Root `scripts/check-fast.sh` passed.
- Dashboard: TypeScript/Vite build, nine backend tests, desktop/mobile browser rendering, MCP filtering and repo navigation; no browser errors. Browser/server artifacts were removed after checking.
- Machine scripts: 25 focused tests and `ops/check-fast.sh` passed.
- Dobby engine: fast gate with 193 tests passed.
- Dobby gateway: build and 115 tests, plus its fast gate and nine production-contract tests, passed.
- Adi and Angie workspace fast checks passed; a real Adi Codex startup smoke passed with personal output suppressed.
- Migration-specific tests: 19 pass, covering private backups, preservation boundaries, idempotence, repo filters, Stop attribution, launchctl fixture isolation/failure, JSONC, command path ownership, and final empty-directory cleanup.

Final combined `scripts/check-agent-control-planes.sh` passed with 266 regression tests. A subsequent empty-directory cleanup addition passed the expanded 19-test migration suite, was applied, and passed a fresh retirement check.

## Continuation

Return to the broader Astra guidance and documentation audit as a separate task. Start from the current Codex-only sources; avoid restoring the old client framework from archived drafts. Keep the repositories themselves.
