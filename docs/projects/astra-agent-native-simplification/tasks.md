# Astra and Agent-Native Simplification

## Goal

Simplify shared guidance, skills, and repository documentation while preserving Adi's workflow: humans set intent; agents complete authorized work with minimal coordination. Code is authoritative for implementation; documentation should explain useful context that code does not readily reveal.

## Why / Impact

The original concern was accumulated instructions, overlapping skills, scattered docs, and references that keep adding context and maintenance work. Success means clear current authority and reliable execution with less unnecessary reading and ceremony. File or skill count alone is not a quality measure.

## Scope / Non-Goals

- Cover the 28 primary repositories from the completed audit, starting with shared guidance and proceeding in bounded repository groups.
- Review global guidance, the agent-native playbook and its references, skill descriptions/scope, repo `AGENTS.md`, and competing or stale operational docs.
- Repair broken routes and inappropriate intermediate approval checkpoints; preserve real ownership, privacy, production, cost, and recovery boundaries.
- Keep all repositories. Repository deletion, app uninstallation, historical-data cleanup, and a new centralized management framework are outside this project.
- Preserve useful domain knowledge, public content, private workspaces, working Codex capabilities, and repo-owned checks.

## Context / Constraints

- Started: 2026-09-18. User asked to return to the original task and keep a project so we can work on it together.
- Original source: [OpenAI's Astra article](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra), supplied by the user. Working principles: narrow skill triggers, task-dependent references, current repo guidance, proportionate validation, and explicit completion boundaries.
- The [repository audit](../archive/astra-repository-audit/report.md) is complete: 28 primary repos and 91 classified Git locations. Use its findings as leads and recheck touched files before changing them.
- The [Codex-only cleanup](../archive/codex-only-control-plane/evidence.md) is complete. Claude/Copilot/Antigravity development setup was removed; Codex is the sole managed development client. Do not reopen that cleanup or restore its old integrations.
- The old [shared-guidance drafts and review](../archive/astra-repository-audit/resources/guidance-proposal-review.md) predate the Codex-only cleanup. Refresh their ideas against current source; do not apply their old patch wholesale.
- Canonical starting files: `config/global.agents.md`, root `AGENTS.md`, `skills-source/owned/agent-native-repo-playbook/SKILL.md` and its references, then `skills/registry.json` and `plugins/registry.json` when capability scope is addressed.
- This tracker is the single active continuation point. Link existing evidence instead of copying the audit into another report tree.
- September 18 steering: the user authorized implementation across all repositories, including skill and documentation cleanup, and requested a concise plan first. Preserve agent-native execution; avoid extra frameworks, mandatory documentation, and instructions that constrain reasoning without a concrete benefit. The supplied Ryan Lopopolo quotation reinforces this preference; further social-media research is optional and unnecessary to start.

## Done When

- [ ] Shared instructions retain operational constraints and autonomous completion while eliminating unnecessary duplication and mandatory reading itineraries.
- [ ] Skill descriptions and placement give useful routing; referenced capabilities exist and registry/runtime mismatches are resolved.
- [ ] Each primary repo has a recorded outcome: corrected, consolidated, or deliberately kept as-is, with a reason.
- [ ] Current docs have clear owners and working links; moved/deleted documents leave no stale incoming routes or lost unique contracts.
- [ ] Important routing or ownership changes receive focused navigation review; required checks pass for changed behavior and generated outputs. Do not invent product work or claim measured model-performance gains.
- [ ] Concise results and any useful learnings are recorded here, and the completed project directory is archived.

## Milestones

- [x] Continuity — recover the original intent, completed audit, and cleanup outcome in one active tracker. Validate linked local sources.
- [ ] Shared guidance — analysis and reviewed proposals are complete; implement global/playbook and companion-reference simplification. Validate preserved contracts and required bootstrap/checks.
- [ ] Skill routing — review global defaults, precise triggers, repo placement, and distribution mismatches. Validate registry and runtime agreement.
- [ ] Repository rollout — refresh audit findings and implement justified corrections in bounded groups; record explicit keep decisions for already-good repos. Validate each group's actual contracts and affected checks.
- [ ] Closeout — check routes and outstanding work, finalize learnings, and archive this whole project directory.

## Decisions

- Keep the agent-native operating model; simplify the instructions supporting it.
- Start with shared guidance because it affects every task. Use the completed audit as leads; recheck current source rather than perform another broad audit.
- Keep short orientation, source ownership, non-obvious constraints, and useful commands. Remove documentation that only narrates discoverable code; do not move every deleted paragraph into a new reference.
- Use conditional references for knowledge worth retaining. Preserve unique operational and domain facts before removing duplicate documents.
- Keep useful checks mechanical and proportionate. Do not replace working checks with more reminder text or introduce arbitrary line/token targets.
- Preserve Codex-only setup. References to Claude as an application provider or historical evidence are not automatically obsolete development setup.
- Implementation is authorized across the 28 primary repos. Latest request is to explain the plan and whether more investigation is needed: enough context exists to start; only targeted checks at each change are needed.

## Current Batch

| Status | Work Item | Role | Resource |
| --- | --- | --- | --- |
| done | Reconstruct original intent, completed work, constraints, and rollout plan | parent | This tracker and linked archives |
| done | Analyze current shared guidance and prepare refreshed global/playbook proposals with preserved agent-native contracts | parent | [Analysis and proposals](resources/shared-guidance-analysis.md) |
| done | Independently review current contracts and the refreshed proposals; no remaining consequential losses found | explorer | [Contract preservation](resources/shared-guidance-analysis.md) |
| done | Narrow the execution plan to justified subtraction and independently check it for unnecessary ceremony | parent + explorer | Decisions and execution approach below |
| in progress | Simplify shared guidance, companion references, skill routing and distribution; integrate results | parent | [Implementation scope](resources/shared-guidance-analysis.md) |
| in progress | Recheck and clean eight product/media repos; preserve domain contracts and validate affected surfaces | product_media_audit | win, aipodcasting, modal_functions, local-transcription, adithyan-ai-videos, aip-cognitive-revolution, futureoflife-podcast, thoughtforms-life |
| in progress | Recheck and clean nine Dobby/operations repos; preserve private-workspace and service boundaries | dobby_operations_audit | adi, angie, dobby-engine, dobby-gateway, dobby-ios, documents, home-automation, platform-ops, scripts |
| in progress | Recheck and clean ten apps/content repos; retain public content and deliberate parked state | apps_content_rollout | .github, adi-design, aipodcasting-website, blog-personal, focus, frontier-lab-intelligence, litellm, meeting-capture, stadia-macos-controller, trenopoulospraxis |

## Execution Approach

1. Trim shared global guidance and the agent-native playbook, including companion references. Preserve autonomy, carried authorization, source ownership, existing checks, and recovery boundaries. Keep root repo guidance that is already useful.
2. Review skills by purpose and actual routing. Shorten overly broad triggers and fix missing or misplaced capabilities through canonical sources; do not delete useful capabilities just to reduce the count.
3. Split current repository corrections among focused subagents. Check each proposed removal against code, current guidance, and incoming links. Keep public content, private records, and unique domain knowledge; leave already-good repositories alone.
4. Run affected existing checks. Use independent navigation review only for important routing or ownership changes; ordinary wording cleanup and duplicate removal need diff and incoming-link checks. Record one concise outcome per repository here, resolve actual failures, and archive the project on completion. No new universal docs layout, audit tooling, or demonstration feature is needed.

## Backlog / Remaining Work

- [ ] Complete the shared-guidance change with companion reference updates, then validate and record its practical effect.
- [ ] Recheck reported browser fallback and skill inventory mismatches before choosing any scope changes.
- [ ] Review overly broad or long skill descriptions and loaded detail; retain specialist safeguards and correct source ownership.
- [ ] Fix confirmed stale authorities, broken paths, outdated commands, and artificial approval checkpoints from the audit in small repository groups.
- [ ] Consolidate repeated operational topics while preserving public content, useful architecture, and historical evidence.
- [ ] Record per-repo validation and explicit keep decisions; track any newly discovered implementation defects separately from prose cleanup.
- [ ] Record useful learnings in this tracker at closeout, then archive with the project skill's whole-directory helper.

## Validation / Test Plan

- For guidance edits, compare before/after operational meaning: authorization, ownership, privacy, generated-file boundaries, completion, and recovery must remain clear.
- Check local links and incoming references after moves. Run repo-owned hygiene checks; do not run unrelated application suites for tracker-only edits.
- For shared skill/registry/runtime changes, use the existing bootstrap and required checks: `scripts/bootstrap-machine-agent-control-planes.sh --apply`, `scripts/check-agent-control-planes.sh`, and scoped component checks as applicable.
- For repo implementation changes, follow that repo's affected checks and product proof paths. Do not invent a larger feature solely to demonstrate the guidance.
- Use focused source-navigation reviews only when important routing or ownership changes could leave agents without necessary context. Smaller instructions alone do not demonstrate better execution.

## Open Questions / Blockers

- No blocking question or additional broad research is needed. Existing proposals are leads, not a requirement to preserve every paragraph or introduce more references.

## Progress Log

- 2026-09-17: [DONE] Original machine-wide repository audit completed and archived; implementation drafts remained proposals.
- 2026-09-18: [DONE] Codex-only setup cleanup completed and archived. Its evidence includes 28-repo validation, unchanged Codex runtime files, and passing regression checks.
- 2026-09-18: [DONE] Created this active continuation project at the user's request; preserved the original objective and linked completed work. Shared-guidance implementation is the next batch.

- 2026-09-18: [DONE] Analyzed current shared guidance against the official Astra article and existing agent-native contracts. Prepared two inactive proposals and a concrete keep/move/remove analysis. Confirmed the mandatory browser skill is dormant. Independent review found no remaining consequential contract losses in the refreshed proposals. Canonical guidance, registries, hooks, and runtime were unchanged in this analysis batch.
- Validation: repo hygiene and whitespace checks passed; all 24 project-local links resolve. Application tests were unnecessary for this analysis-only batch. The broader project remains active for implementation and pilot work.
- 2026-09-18: User authorized code-first simplification across all primary repos and asked for a lightweight plan. Replaced the earlier analysis-only restriction and mandatory pilot with targeted edits, bounded repository groups, and existing validation. No live guidance, skills, or runtime settings changed in this planning step.
- Validation: independent plan review confirmed the approach and narrowed navigation reviews to changes that warrant them. Repo hygiene and whitespace checks passed; application suites were unnecessary for this tracker-only update.
