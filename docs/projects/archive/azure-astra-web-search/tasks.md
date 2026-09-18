# Azure Astra web search

> Retired on September 18, 2026 at the user's request. The standard Responses
> override, generated catalog, and forced search settings were removed. This
> archive preserves the experiment; current behavior is documented in
> `docs/references/codex-azure-astra.md`.

## Goal

Enable Azure-hosted web search in the existing `azure-astra` Codex profile and,
following the explicit follow-up request, the Mac app/shared global default,
with verified subscription isolation and a documented rollback.

## Context / Constraints

- Started 2026-09-16. The user authorized enabling the previously tested
  standard-Responses workaround in the Azure profile and requested a resumable
  project record in case it regresses.
- `codex-azure` selects `azure-astra`; `codex-openai` selects `chatgpt`.
- Initial scope was CLI-only. The user subsequently authorized applying the
  same workaround to the desktop/shared default. A CLI profile is not
  automatically selected by the desktop provider default. Keep the existing
  subscription path usable through an explicit normal-catalog/search override.
- Derive a machine-local model catalog from Codex's existing catalog; change
  only Astra's `use_responses_lite` to `false`. Never commit runtime catalog
  contents, credentials, or conversation history.
- Keep `web_search = "live"` and disable `features.standalone_web_search` only
  for the global Azure default and Azure profile. Its separate `/alpha/search`
  endpoint returned 404. Restore standalone search in the subscription profile.
- Prior temporary tests succeeded in CLI 0.154.0 and desktop engine
  0.154.0-alpha.6.2: native search, shell execution, and input caching worked.
  Azure returned `reasoning.context = "all_turns"` with and without an explicit
  context setting. Context-window metadata must remain unchanged.

## Done When

- [x] The canonical Azure profile and its derived runtime catalog are applied.
- [x] A real request through `codex-azure` searches using the native tool.
- [x] The subscription path retains the normal catalog and Lite behavior.
- [x] Rollback, refresh, limits, and future diagnosis are documented.
- [x] Required checks pass and this completed enablement tracker is archived.

## Milestones

- [x] M1 — Implement reproducible profile-scoped catalog generation and apply it.
- [x] M2 — Validate native search, profile isolation, context metadata, and rollback.
- [x] M3 — Finish the operational reference and archive the initial project record.
- [x] M4 — Apply and verify the subsequently requested desktop/global default.

## Decisions

- Use the existing Azure profile; do not create another paid service or MCP.
- Treat this as a compatibility workaround, not an official one-click Azure
  search setting or proof of long-task performance parity.
- Keep long-session quality, compaction, and comparative billing as future
  checks if the user reports a regression; do not claim they were benchmarked.

## Open Questions / Blockers

- None for the authorized enablement. Full-session performance is unmeasured.

## Current Batch

Desktop-default follow-up completed; earlier validation records describe the
initial CLI-only phase.

| Status | Work Item | Role | Resource |
| --- | --- | --- | --- |
| done | Apply the scoped catalog and profile settings | parent | `codex/config/azure-astra.config.toml` |
| done | Verify actual Azure search and subscription isolation | parent | `resources/verification.json` |
| done | Archive the initial enablement | parent | `docs/references/codex-azure-astra.md` |
| done | Apply and verify the desktop/global default, then re-archive | parent | `resources/desktop-verification.json` |

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

- [x] Implement and apply the minimal catalog generator.
- [x] Complete focused checks and native runtime verification.
- [x] Update the operational reference with rollback and future triage.
- [x] Record lessons and archive the complete project directory.

## Resume If Search Regresses

Start with `docs/references/codex-azure-astra.md` and the verification record.
Check the effective provider/profile, CLI version, source catalog freshness,
and actual search tool event before changing Azure resources. Refresh the
derived catalog or use the documented rollback. Reopen this archived tracker
as an active project only if new implementation work is required.

## Progress Log

- 2026-09-16: [IN-PROGRESS] Created tracker after explicit authorization; no
  saved web-search configuration had been changed during earlier research.
- 2026-09-16: [DONE] Applied the canonical Azure profile through config sync.
  Generator preserves the normal cache and all fields except Astra's Lite flag.
  Relative catalog resolution worked from an unrelated temporary working directory.
- 2026-09-16: [DONE] The saved `codex-azure` profile completed shell execution
  and two native searches, returning the official Microsoft documentation URL.
  Usage: 44,136 input, 19,849 cached input, 157 output tokens. These are smoke
  totals, not a steady-state efficiency benchmark.
- 2026-09-16: [DONE] `codex-openai` retained provider `openai`, normal Lite
  metadata, and working native search. Original unprofiled `codex` retained
  provider `azure` and completed shell execution. Global and subscription
  config hashes are unchanged. The generated catalog differs from the normal
  catalog only in Astra's flag; context limits remain identical.
- 2026-09-16: [DONE] Seven focused tests and all 276 control-plane tests passed;
  repo fast checks, Codex structural validation, shell syntax, and diff checks
  passed. Added generator regression tests to the permanent fast gate.
- 2026-09-16: [DONE] Documented rationale, ownership, refresh, rollback,
  known catalog-refresh warning, and unbenchmarked behavior in the Azure
  reference. Reviewed `learnings.md`; no cross-repo ownership change occurred.
- 2026-09-16: [DONE] Archived all three project files with the project helper;
  confirmed `source_removed: true` and no active directory remains. The final
  post-archive fast check passed, including the new catalog tests and live
  Codex structural validation. Enablement is complete; resume only for a new
  regression or an explicitly requested extended comparison.

- 2026-09-16: [IN-PROGRESS] Reopened the whole tracker for the explicit Mac app
  default request. Applied the same existing Azure catalog/search settings
  globally and explicit normal catalog/search settings in `chatgpt`. No new
  launcher or service was added. Documented snapshot refresh and rollback.

- 2026-09-16: [DONE] The desktop bundled engine loaded the saved global settings
  without profile/model/provider/search/protocol overrides, loaded native Azure
  credentials, and completed one hosted search. `codex-openai` completed one
  native search with its explicit normal catalog/search overrides. Context
  metadata is unchanged and only Astra's protocol flag differs between catalogs.
- 2026-09-16: [DONE] Codex structural/runtime validation passed. The first fast
  check correctly caught archived links while the tracker was temporarily active;
  final validation runs after returning the complete directory to the archive.
  Desktop UI activation remains the user's restart/new-task check.

- 2026-09-16: [DONE] Archived all four project files; confirmed the active copy
  was removed. Final post-archive fast checks and `git diff --check` passed.

- 2026-09-16: [DONE] At the user's request, ran a fresh ephemeral two-turn
  desktop app-server probe against saved Azure defaults. File editing, shell
  assertions, hosted search, follow-up context recall, and caching passed. Added
  sanitized evidence to the existing desktop verification record. No additional
  configuration change or service was needed; long-session parity is unmeasured.

- 2026-09-16: [DONE] Investigated a later empty-result report without changing
  saved configuration. Direct Azure search returned 11 readable results and three
  citation annotations; a fresh desktop-bundled Codex process returned a source
  quotation. Search in the affected task recovered on retry, including the
  original batched query, but native page opening still returned no content.
  Added `resources/retrieval-verification.json` and corrected the evidence rule:
  earlier event-plus-URL smoke records prove dispatch, not usable retrieval.
  Root cause remains unknown; no new implementation or active tracker was needed.
