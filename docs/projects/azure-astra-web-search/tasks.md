# Azure Astra web search

## Goal

Enable Azure-hosted web search only in the existing `azure-astra` Codex profile,
with verified subscription isolation and a documented way to undo the trial.

## Context / Constraints

- Started 2026-09-16. The user authorized enabling the previously tested
  standard-Responses workaround in the Azure profile and requested a resumable
  project record in case it regresses.
- `codex-azure` selects `azure-astra`; `codex-openai` selects `chatgpt`.
- Keep the global/desktop default and subscription profile unchanged. A CLI
  profile is not automatically selected by the desktop's provider default.
- Derive a machine-local model catalog from Codex's existing catalog; change
  only Astra's `use_responses_lite` to `false`. Never commit runtime catalog
  contents, credentials, or conversation history.
- Keep `web_search = "live"` and disable `features.standalone_web_search` only
  in the Azure profile. Its separate `/alpha/search` endpoint returned 404.
- Prior temporary tests succeeded in CLI 0.154.0 and desktop engine
  0.154.0-alpha.6.2: native search, shell execution, and input caching worked.
  Azure returned `reasoning.context = "all_turns"` with and without an explicit
  context setting. Context-window metadata must remain unchanged.

## Done When

- [ ] The canonical Azure profile and its derived runtime catalog are applied.
- [ ] A real request through `codex-azure` searches using the native tool.
- [ ] The subscription path retains the normal catalog and Lite behavior.
- [ ] Rollback, refresh, limits, and future diagnosis are documented.
- [ ] Required checks pass and this completed enablement tracker is archived.

## Milestones

- [ ] M1 — Implement reproducible profile-scoped catalog generation and apply it.
- [ ] M2 — Validate native search, profile isolation, context metadata, and rollback.
- [ ] M3 — Finish the operational reference and archive the project record.

## Decisions

- Use the existing Azure profile; do not create another paid service or MCP.
- Treat this as a compatibility workaround, not an official one-click Azure
  search setting or proof of long-task performance parity.
- Keep long-session quality, compaction, and comparative billing as future
  checks if the user reports a regression; do not claim they were benchmarked.

## Open Questions / Blockers

- None for the authorized enablement. Full-session performance is unmeasured.

## Current Batch

| Status | Work Item | Role | Resource |
| --- | --- | --- | --- |
| in_progress | Apply the scoped catalog and profile settings | parent | `codex/config/azure-astra.config.toml` |
| todo | Verify actual Azure search and subscription isolation | parent | `resources/verification.json` |
| todo | Document rollback, refresh, and resume; archive | parent | `docs/references/codex-azure-astra.md` |

## Validation / Test Plan

- Run focused catalog generation/isolation tests and existing Codex sync tests.
- Apply via `codex/scripts/sync-config.sh --apply` and run the Codex
  control-plane validation plus `scripts/check-fast.sh`.
- Use ephemeral sessions with lifecycle hooks and unrelated integrations
  disabled. Record only provider, tool outcomes, and usage; discard scratch
  conversation data. Do not alter model/protocol settings in the Azure smoke:
  the installed profile itself must supply the fix.
- Verify a CLI rollback override resolves to the normal catalog.

## Backlog / Remaining Work

- [ ] Implement and apply the minimal catalog generator.
- [ ] Complete focused checks and native runtime verification.
- [ ] Update the operational reference with rollback and future triage.
- [ ] Record lessons and archive the complete project directory.

## Resume If Search Regresses

Start with `docs/references/codex-azure-astra.md` and the verification record.
Check the effective provider/profile, CLI version, source catalog freshness,
and actual search tool event before changing Azure resources. Refresh the
derived catalog or use the documented rollback. Reopen this archived tracker
as an active project only if new implementation work is required.

## Progress Log

- 2026-09-16: [IN-PROGRESS] Created tracker after explicit authorization; no
  saved web-search configuration had been changed during earlier research.
