# Astra Repository Audit

## Goal

Audit every discoverable repository on this machine and prepare an evidence-backed plan to combine Astra prompting guidance with the existing agent-native operating model.

## Scope and Constraints

- Started 2026-09-17. User requested overnight work across every repository and asked whether rollout should proceed in stages.
- Inventory primary repositories, unmanaged repositories, nested clones, worktrees, deployment copies, and tool/vendor checkouts. Distinguish independent projects from copies.
- Audit guidance, documentation ownership and freshness, skill scope, execution commands, mechanical checks, and completion boundaries in proportion to each repo's purpose.
- Prepare concrete proposed revisions to shared guidance as review artifacts. Broad runtime/application changes are a later rollout stage.
- Do not copy personal workspace contents, credentials, customer records, or raw machine logs into the control-plane repo. Retain structural metadata and operational findings only.
- No new permanent centralized audit service or script. One-off inventory helpers live under `tmp/astra-repository-audit/` and are removed at closeout.
- Primary audit baseline: the OpenAI Astra article already fetched in this task, the agent-native repo playbook, repo-local contracts, and observed files. File counts are discovery signals, not quality scores.

## Done When

- [x] Machine discovery is complete with scanned roots, exclusions, inaccessible-path categories, and repository/copy classification recorded.
- [x] Every primary repository has a concise evidence-backed audit and recommended action; tool/vendor/copy repositories have an explicit disposition.
- [x] Portfolio findings distinguish confirmed defects, consolidation candidates, preserved domain constraints, and unverified runtime assumptions.
- [x] Shared global guidance and playbook revisions are concrete, reviewable, and mapped to retained operational contracts.
- [x] A staged rollout plan identifies the first changes, validation, owners, and success criteria.
- [x] Report completeness and links are checked; applicable local documentation checks pass or residual failures are explained.
- [ ] Learnings are finalized and this complete project directory is archived with the active path removed.

## Milestones

- [x] Inventory — discover and classify repositories; reconcile with the managed registry.
- [x] Repository audit — inspect every primary repo and classify all secondary checkouts.
- [x] Synthesis — prioritize shared and repo-specific changes; prepare guidance proposals.
- [ ] Validation and closeout — verify coverage and evidence, archive deliverables, and report results.

## Decisions

- Audit the entire portfolio before wide edits. Use concrete shared-guidance proposals and a staged rollout to avoid propagating an untested instruction style.
- Keep the human-intent/agent-completion model, domain boundaries, working checks, and recovery paths. Remove instruction overhead only where evidence supports it.
- Parent owns this tracker, the machine inventory, shared guidance analysis, and final synthesis. Delegated reviewers own disjoint topic reports.

## Open Questions / Blockers

- None for the audit. Rollout choice can be made from the completed proposal.

## Current Batch

| Status | Work Item | Role | Resource |
| --- | --- | --- | --- |
| done | All 28 primary repo reviews and 91 Git-location dispositions | parent + explorers | report.md |
| done | Shared drafts and independent contract review | parent + explorer | resources/guidance-proposal-review.md |
| in_progress | Validate completeness/evidence, finalize learnings, archive | parent | resources/validation.json |

## Backlog / Remaining Work

- [x] Freeze per-reviewer repository lists after discovery.
- [x] Reconcile all discoveries against reviewer coverage.
- [x] Inspect local skill triggers and root bodies, preserve workflow-specific safeguards.
- [x] Review docs duplication, broken routing, archived/active separation, and concrete cleanup candidates.
- [x] Prepare global guidance and playbook draft revisions with a contract-preservation map.
- [x] Write a compact portfolio report and staged implementation plan.
- [x] Validate report coverage, evidence paths, proposed guidance consistency, and repo hygiene.
- [ ] Finalize learnings; archive the completed project and remove disposable tools.

## Validation / Test Plan

- Inventory reconciliation: every discovered Git root has a category and disposition; every primary repo has a review.
- Evidence checks: resolve cited source paths, record working-tree/HEAD snapshot metadata, manually confirm major findings.
- Audit reads check scripts and proof routes; running unrelated app suites is outside this audit and will not be represented as runtime proof.
- Draft checks: compare original/proposed guidance and ensure critical ownership, approval, secret, generation, and completion contracts remain explicit or correctly routed.
- Use `scripts/check-repo-hygiene.sh` and the repo's applicable fast checks for committed report artifacts, accounting for archive location.

## Progress Log

- 2026-09-17: [IN-PROGRESS] Created the overnight audit goal and tracker. Read project operating rules and reused the playbook/article context from the initial two-repo sample.
- 2026-09-17: [DELEGATED] Assigned all 27 primary repositories outside `agents` to three disjoint review groups. Parent retains machine-wide discovery and shared-control-plane analysis.
- 2026-09-17: [DONE] Metadata discovery visited 336,292 directories; classified 91 Git locations, including eight unresolved worktrees and two empty cache markers. All personal-user paths were accessible; protected OS areas are explicitly limited.
- 2026-09-17: [DONE] Three independent reviewers completed all 27 assigned repos. Parent completed agents/shared skills, runtime inventory, the empty unmanaged project, and orphaned-worktree review. Target application repos remain unedited.
- 2026-09-17: [DONE] Prepared three shared guidance drafts and an unapplied patch; independent review caught four semantic losses, all incorporated. Patch applicability and repo hygiene pass.
- 2026-09-17: [DONE] Repo fast checks passed, including 41 unit tests, production-source shell check, and local Codex structural validation. Existing SwiftUI skill length validator fails as recorded audit evidence.
- 2026-09-17: [DONE] Coverage reconciliation verified all 28 primary reviews, every one of 91 Git-location dispositions, 288 local links, 228 file/line citations, unchanged canonical guidance hashes, and an applicable proposal patch. All primary HEADs remained unchanged since the structural snapshot; tracked changes are audit artifacts in agents only.
- 2026-09-17: [DONE] Finalized learnings and resolved all four independent proposal findings. Prepared complete directory archive; broad implementation remains the explicitly separate next stage.
