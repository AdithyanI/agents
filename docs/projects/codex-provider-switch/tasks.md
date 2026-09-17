# Machine-local Codex provider switch

## Goal
Install a small native menu bar switch on MacBook and Mac mini that independently selects Azure or the Codex subscription for new desktop and ordinary terminal sessions.

## Context / Constraints
- Started September 17, 2026. User authorized implementation and setup on both Macs.
- Temporary two-week Azure use: keep the implementation small, with no expiry scheduler or separate Codex homes.
- Shared skills, plugins, hooks, credentials, and provider definitions retain existing ownership.
- Preserve each machine's existing default during migration. Never restart the active Codex app automatically.
- Source and provider policy belong in agents; scripts launchers remain explicit per-process choices.

## Done When
- [x] Local selection survives shared sync and does not propagate between Macs.
- [x] Both profiles and ordinary CLI/desktop config resolve correctly, including search and authentication settings.
- [x] Native menu app installed, running, and enabled at login on both machines.
- [x] Tests, checks, runtime proof, docs, and cleanup complete.

## Milestones
- [x] Provider selection helper, renderer integration, and focused regression tests.
- [x] Native menu app and installer built and verified.
- [x] Both-machine install and independence proof.
- [x] Documentation, learnings, and tracker archive.

## Decisions
- One local selection file outside Git/Syncthing; renderer consumes it after shared baseline.
- Public helper: scripts/codex-provider.py status|azure|subscription; JSON default, --plain, --no-input, --apply; mutations default to dry-run.
- Successful data includes selected (azure|subscription), effective_provider, persisted, config_in_sync, applied, restart_required, scope=this_machine.
- UI uses that helper asynchronously; selecting a provider never quits Codex. Explain reopening/new-task requirement in the menu.
- Provider overlay is allowlisted; reasoning effort and service tier remain client-owned.

## Current Batch
| Status | Work Item | Role | Resource |
| --- | --- | --- | --- |
| done | Provider, tests and real runtime verification | parent | resources/verification.json |
| done | Native menu and installer, independent review | worker | codex/menu-bar/ |
| done | Both-machine install, independence, documentation | parent | resources/verification.json |

## Backlog / Remaining Work
- [x] Shared sync and both explicit launcher checks.
- [x] Git-based rollout, both Macs, native menu proof.
- [x] Update ownership and operator docs; finalize learnings and archive.

## Open Questions / Blockers
Terminal validation found MacBook Homebrew Codex 0.147 rejects Astra; installer
now aligns ~/bin/codex with the installed desktop engine. Reinstall/retest that
small follow-up on both Macs before final archive.

## Validation / Test Plan
- Two isolated homes with opposite selections; repeated sync; invalid/missing dependencies preserve prior config.
- Focused provider tests and existing Codex control-plane tests; full repo checks after apply.
- Native Swift build plus actual menu verification; installed engine config/thread startup checks without paid inference where sufficient.
- Compare config, auth, hooks and unaffected state before/after switching on each machine.

## Progress Log
- 2026-09-17: [DONE] Inspected shared renderer, credentials/catalog dependencies, local Xcode and remote SSH. Both provider profiles exist.

- 2026-09-17: [DONE] Native menu installed/running on MacBook. Both local provider settings survived shared sync; bundled engine started ephemeral tasks with openai/azure respectively. Credentials and hooks were byte-identical afterward; Azure restored.
- 2026-09-17: [DONE] 290 hermetic regression tests and shared control-plane checks passed before the catalog guard; 12 focused tests passed after it. Older CLI cache can omit Astra: retain only an existing validated Azure snapshot to avoid breaking shared sync.

- 2026-09-17: [DONE] Git auto-sync published ffb7a605. Mini pulled through Git, shared bootstrap/check passed (291 tests), menu installed and running. Real opposite selections survived sync on both Macs; both restored to Azure.
- 2026-09-17: [DONE] Menu source/installer delegation stayed isolated; parent integrated provider logic, reviewed implementation, and verified both machines. No review findings.
