# Shared Guidance and Control-Plane Audit

Snapshot: 2026-09-17. This is an evidence-backed proposal; canonical guidance, registries, runtime links, and application code have not been changed by this audit.

## Assessment

The operating model is sound: humans set intent; agents finish implementation and verification; mechanical checks and managed Git automation support recovery. The strongest improvements concern stale routing, unconditional context loading, and duplicated operational detail. The audit does not establish that a smaller number of files or skills would by itself improve outcomes.

## Confirmed Findings

| Priority | Evidence | Consequence | Recommended action |
| --- | --- | --- | --- |
| First | `config/global.agents.md:37` requires `$agent-browser`, but `skills/registry.json` marks it dormant and neither global runtime skill directory links it. | The global fallback names a capability agents are not necessarily offered. | Route to a callable browser capability; resolve the intended agent-browser scope before linking it again. Do not make installation a prerequisite for unrelated work. |
| First | `~/.agents/skills/chart-visualization` is a regular directory with a `SKILL.md`, absent from `skills/registry.json`. | The machine's global skill set differs from the canonical registry and the Claude global set. | Classify this skill through the existing lifecycle: adopt/register with a justified scope, or make it dormant after preserving its source. The audit performs no chart API calls. |
| First | Tracked `.agents/skills/omni-flash-video/SKILL.md` in `adithyan-ai-videos` and `.agents/skills/fli-daily-intelligence/SKILL.md` in `frontier-lab-intelligence` are absent from `unmanaged_repo_local_skills`. | Canonical inventory misses two locally authored skills; the FLI workflow also conflicts with its parked state. | Register valid local skills after reviewing their current purpose; reconcile the parked FLI workflow before exposing it as active guidance. |
| First | `skills-source/external/find-skills/SKILL.md:14–23,49–75` treats ordinary “how do I” and “can you help” tasks as skill discovery and prescribes leaderboard/search steps. | Common work can trigger capability shopping and broaden the installed instruction set unnecessarily. | Narrow the description/body to explicit skill-discovery or missing-capability requests. Preserve the external-source refresh contract. |
| First | `skills-source/owned/agent-native-repo-playbook/SKILL.md:26,38–42` requires the principles reference and broadly lists discovery surfaces for every use. | The audit skill recreates the article's mandatory-reading pattern. | Put the small essential operating model in the root; select references and evidence according to the requested review. |
| Next | `AGENTS.md` is 14,946 bytes and repeats renderer details already described in `docs/references/agent-control-plane-operations.md`, Codex/Copilot operations, and canonical registries. | Root context contains many facts irrelevant to most tasks. | Keep source ownership, conditional routing, and change-specific validation. Put field-level and renderer-specific detail in the existing owner reference. |
| Next | `config/global.agents.md` is 7,569 bytes; its generated-surface paragraph, repeated docs rules, subagent examples, and Git automation explanation overlap with this repo and skills. | Every repo receives control-plane implementation detail and overlapping general advice. | Keep a compact global operating contract and route control-plane work to `agents`. Preserve the actual auto-publication and no-manual-commit expectations. |
| Next | `docs/AGENTS.md:17–23` and `docs/references/AGENTS.md:3–9` repeat the same placement and retention policy; the latter mainly adds a links list. | A nested instruction file exists chiefly as navigation, contrary to the parent policy. | Merge unique routing into the existing docs entry point; remove the nested instruction surface after checking incoming references. |
| Next | `dashboard-app/AGENTS.md:42–45` tells editors to change tokens in the adi-design skill; `skills-source/owned/adi-design/SKILL.md:14–18,46–48` names the separate `adi-design` repo as canon. | Two sources give different first edit locations. | Update dashboard guidance to the canonical design repo and retain the vendored-token refresh step. |
| Next | `skills-source/owned/client-interface-guidelines/SKILL.md:17–23` mandates four sequential reference loads; `:48` requires additive compatibility while global guidance defaults to clean migration without requested compatibility. | A short root can still force substantial context and unclear compatibility decisions. | Route by interface concern; clarify compatibility according to actual consumers and explicit contract commitments. Preserve structured errors and noninteractive behavior where callers depend on them. |
| Later | `skills-source/owned/imagegen/SKILL.md:14–86` prescribes a worklog/iteration workflow and `:198` always requires a taxonomy classification. | Small image requests can inherit process intended for substantial creative work. | Retain visual inspection and provider/storage contracts; make persistent worklogs and taxonomy useful tools selected by task complexity. |
| Later | `skills-source/external/openai-docs/SKILL.md:101,107–115,131` contains broad approval/installation/stop branches in a lookup skill. | An authorized multi-repo task or simple docs question may be pulled into an avoidable interruption. | Keep official-source routing; qualify these branches by task scope, current capabilities, and existing authorization. Coordinate with upstream rather than silently forking external content. |

## Skill Exposure

The registry contains 40 standalone entries: 10 global, 19 repo-scoped, and 11 dormant; 9 additional plugin-derived skills are explicitly assigned to iOS. Dormant sources are not equivalent to runtime context. The local Codex global directory adds one unregistered chart skill, giving 11 filesystem-discovered global standalone skills. App/bundled skills form a separate layer and were not inferred from the registry alone.

The biggest description outlier is the repo-scoped `swiftui-whats-new-27` (2,696 YAML-parsed characters at inspection). `impeccable` (895), `adi-design` (646), and `dobby-system` (627) also contain details that could live after invocation. These are concrete shortening candidates, not evidence that truncation occurred in this task.

The existing skill-creator validator was run against the SwiftUI outlier and
failed with `Description is too long (2696 characters). Maximum is 1024
characters.` This confirms a local validation-contract violation. Full
YAML-parsed metadata for all 40 standalone and 9 plugin-derived entries is in
`skill-catalog-snapshot.json`; source-scalar counts in earlier group snapshots
may include YAML quoting/escapes and differ slightly.

Suggested scope review:

- Keep the operating tools broadly available where useful: project continuity, secret materialization, and repo-review guidance. Their descriptions should be narrow enough not to trigger on ordinary coding.
- Review `adi-design` and `impeccable` together: brand facts and general UI craft can coexist, but domain-specific brand authority must be clear and backend-only repos need not advertise both.
- Review `find-skills` and `skill-creator` for explicit discovery/authoring rather than default task execution. Global availability may remain useful; narrowing their triggers is the first change.
- Keep specialized provider, media, finance, and deployment skills when they encode real local commands or failure modes. Their procedural detail is not automatically obsolete because Astra reasons better.
- Preserve external/upstream content ownership. Any local adaptation should be deliberate and remain compatible with the existing refresh mechanism.

## Documentation Consolidation

`docs/architecture/codex-sync-simple.md` and the sync section of `codex-control-plane-script-flows.md` overlap. Retain a concise overview in `codex-control-plane.md` and exact script flow in the latter; consider merging the simple page after checking whether it serves a distinct human audience. This is a consolidation candidate, not a proven defect.

The operations documents contain genuine schema and runtime facts. Do not delete them by length. Make their ownership clear: shared bootstrap/client distribution in `agent-control-plane-operations.md`, Codex-only commands in `codex-control-plane-operations.md`, Copilot-only runtime specifics in its reference, and hook payload/behavior in `repo-lifecycle-hook-adapter.md`.

## Keep / Move / Delete

- **Keep:** canonical-source ownership; managed runtime generation; explicit completion; repo-specific checks; correct secret handling; repo/workspace boundaries; safe Git finalization; actual deployment recovery.
- **Move:** renderer details out of global/root guidance into their existing operations reference; long examples out of skill descriptions into task references; historical proof into project archives.
- **Delete after reconciliation:** duplicated advice and topic summaries; absent-capability mandates; obsolete source routes; compulsory intermediate review points that do not correspond to a real unresolved user decision.

## Validation and Limits

Reviewed canonical guidance, registry entries, runtime skill links, root/nested docs, check scripts, and selected skill bodies. No application tests or deploys were run for this review. Registry validation alone does not prove that skill triggers, docs routing, or their prose are correct. The proposed pilot should test small edits, cross-repo work, provider changes, and long-running completion with fresh task contexts before broader rollout.
