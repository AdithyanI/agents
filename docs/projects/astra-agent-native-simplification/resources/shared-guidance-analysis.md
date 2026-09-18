# Shared Guidance Analysis

Analysis date: 2026-09-18. These are recommendations and review artifacts; live guidance and runtime configuration have not been changed by this batch.

## Recommendation

Start with the shared global guidance and agent-native playbook, including the references that would otherwise restore broad reading and documentation requirements. Keep the current agents repo root largely intact: the Codex-only cleanup already gave it a compact source-of-truth map and conditional validation contracts.

The agent-native model is a requirement of the rewrite. Humans set intent, priorities, acceptance criteria, taste, and material-risk boundaries. Agents own the complete authorized job, including implementation, relevant verification, durable docs, cleanup, and routine follow-through. Shorter instructions are useful only if this behavior survives.

## What Is Working

- [Global operating model](/Users/dobby/GitHub/agents/config/global.agents.md) (line 10) already makes autonomous completion and maintained docs explicit. Preserve it.
- [Repo source map](/Users/dobby/GitHub/agents/AGENTS.md) (line 9) identifies canonical inputs, while [conditional validation rules](/Users/dobby/GitHub/agents/AGENTS.md) (line 53) connect particular changes to required checks. Preserve this operational information.
- The delivery contract has executable support: [Git pre-commit hook](/Users/dobby/GitHub/agents/hooks/git/pre-commit) (line 7) invokes the owning repo's fast check; the Codex Stop implementation also contains preflight and recovery handling. Simplifying prose does not remove those gates.
- The [playbook's proof guidance](/Users/dobby/GitHub/agents/skills-source/owned/agent-native-repo-playbook/references/best-practices.md) (line 63) already distinguishes static checks from inspecting changed product behavior. Preserve that distinction.

## Highest-Value Corrections

| Current evidence | Practical implication | Proposed treatment |
| --- | --- | --- |
| [Playbook entrypoint](/Users/dobby/GitHub/agents/skills-source/owned/agent-native-repo-playbook/SKILL.md) (line 26) requires the general principles reference before task-specific references; [discovery list](/Users/dobby/GitHub/agents/skills-source/owned/agent-native-repo-playbook/SKILL.md) (line 38) spans guidance, maps, architecture, trackers, workflows, checks, skills, logs, and product paths. | A narrow guidance question can inherit a broad investigation. This is an instruction-level concern, not a measured latency result. | Put a small autonomous-delivery contract in the entrypoint; route to the specific reference needed for the requested review. Scope discovery to evidence needed for that question. |
| [Global defaults](/Users/dobby/GitHub/agents/config/global.agents.md) (line 17), [subagent defaults](/Users/dobby/GitHub/agents/config/global.agents.md) (line 39), and [Git automation](/Users/dobby/GitHub/agents/config/global.agents.md) (line 47) repeat related ownership and follow-through rules. | Important rules share space with multiple restatements. | Consolidate overlapping statements while retaining distinct operational facts, especially existing authorization, generated-file ownership, and documented Git automation. |
| [Docs reference](/Users/dobby/GitHub/agents/skills-source/owned/agent-native-repo-playbook/references/docs-structure-and-maintenance.md) (line 3) pushes a common layout; [authoring recipe](/Users/dobby/GitHub/agents/skills-source/owned/agent-native-repo-playbook/references/docs-structure-and-maintenance.md) (line 63) defaults to seven sections and a diagram. | A small factual update may expand into template-driven documentation. Local-contract precedence is less clear than in the skill entrypoint. | Make the existing repo contract authoritative. Treat the layout as a fallback and diagrams/sections as tools chosen for the topic. Update the owning document instead of adding a parallel summary. |
| [AGENTS reference](/Users/dobby/GitHub/agents/skills-source/owned/agent-native-repo-playbook/references/agents-md-best-practices.md) (line 40) routes rationale/setup to `docs/decisions` and `docs/setup`, while the normal fallback elsewhere is architecture/references. | Agents can create extra document homes simply by following different references. | Route first through the repo's own contract; otherwise use the existing architecture/references split. Retain alternative layouts when intentionally owned locally. |
| [Global browser rule](/Users/dobby/GitHub/agents/config/global.agents.md) (line 37) requires `agent-browser`, but [its registry entry](/Users/dobby/GitHub/agents/skills/registry.json) (line 396) is dormant and `~/.agents/skills/agent-browser` is absent. | The rule points to a skill unavailable through the managed global runtime. It can provoke an unnecessary skill hunt or stop. | Prefer controllable in-app browsing; use another available browser capability for automation. Decide any future skill activation in the skill-routing batch instead of implicitly installing it here. |

## Contracts the Rewrite Must Preserve

| Contract | Preservation rule |
| --- | --- |
| Human intent, agent execution | Keep responsibility for code, checks, docs, cleanup, and routine decisions with the agent. |
| Persistence | A first implementation does not complete a request that includes running, inspecting, repairing, or delivering it. |
| Existing authorization | Carry authorization across steps and turns; ask about unresolved material decisions outside it. |
| Recoverable high-permission delivery | Preserve direct-to-main as the trusted solo default where local rules allow, existing Git automation, fast deterministic gates, and recovery paths. |
| Evidence | Run required repo checks and inspect affected behavior; broaden verification when changed code, failures, or unresolved concerns warrant it. Do not waive a failing delivery gate. |
| Durable knowledge | Maintain the owning docs when durable behavior changes; keep one current source and archive completed trackers. |
| Local and cross-repo boundaries | Preserve repo-specific contracts, Dobby ownership/privacy separation, canonical generated-config sources, and real production/cost/secret constraints. |
| Improvement from failures | Repeated confusion should lead to the smallest useful code, tool, check, or local-doc improvement. |

An independent read-only review confirmed the overall direction and identified two draft risks now corrected in the proposals: conditional references must not hide the direct-delivery/recovery contract, and a shorter skill description must still match natural requests about agents stopping or instructions becoming bloated.

## Keep / Move / Remove

- **Keep:** the operating model, completion boundary, existing authorization, domain ownership, generated-file contract, required repo checks, automated Git delivery, and precise utility/secret routes that remain relevant.
- **Move behind conditional routes:** operating-model background, scoring, detailed document authoring advice, and specialized review criteria. Use the existing references rather than adding a new handbook.
- **Remove or consolidate:** repeated autonomy/subagent/Git reminders, unconditional reference reading, the stale mandatory browser-skill route, and fixed document templates presented as the default for every topic.

The current [agents root](/Users/dobby/GitHub/agents/AGENTS.md) should mostly be kept. The old pre-cleanup root replacement is obsolete and would risk losing current Codex-only contracts.

## Reviewable Proposals

- [Proposed global guidance](proposed-global.agents.md) targets `config/global.agents.md`.
- [Proposed playbook](proposed-agent-native-repo-playbook.md) targets `skills-source/owned/agent-native-repo-playbook/SKILL.md`.

Companion work belongs in the same eventual implementation batch:

1. Align `references/best-practices.md` with task-sized discovery, relevant checks, and no automatic new tests/docs for a purely superficial edit. Retain the full execution outcome and real gates.
2. Update the AGENTS/docs references described above so they cannot reintroduce conflicting placement and mandatory template rules.
3. Review `agents/openai.yaml` when applying the shorter skill description; its existing autonomous-completion default prompt already matches the goal.
4. Apply through canonical sources, then use the existing bootstrap/check workflow. The proposals do not alter model selection, plugin/skill enablement, hooks, credentials, or production state.

## Behavioral Acceptance

| Representative work | Required result | Unnecessary overhead to watch for |
| --- | --- | --- |
| Small wording correction | Read the relevant guidance/document, preserve meaning, and satisfy the owning repo's applicable gate. | Unrelated architecture reading, app-wide test suites, or a new tracker solely for the correction. |
| Authorized feature spanning an API and UI | Complete both sides and their contract, run affected checks, inspect the result, repair scoped failures, and report evidence. | Asking whether to continue after finishing only the first side. |
| Shared lifecycle-hook change | Keep full validation required by this repo, including regression and rendered-state checks. | Treating smaller prompts as permission to skip the gate. |
| Dobby work across repo boundaries | Route through the ownership skill, preserve private workspace data, and validate each touched owner as required. | Copying private context or architecture detail into a shared control-plane manual. |
| Architecture fact update | Update the owning current document; use a diagram if it explains the changed relationship. | Creating seven template sections or a second document without a distinct need. |
| A failed check or material decision | Repair failures within authorized scope, or identify the actual remaining blocker/decision without pretending completion. | Repeated permission requests for already-authorized repair or silent dismissal of a failing delivery gate. |

These are acceptance cases for upcoming real work or bounded fixtures, not results already measured. No model-performance or token-savings claim is made by this analysis.

## Sequence

1. Implement the shared-guidance proposals and companion reference corrections as one bounded batch.
2. Review skill scope and routing using observed usefulness and actual availability; the ten registered global skills are not automatically excessive.
3. Pilot on two representative tasks/repos, then refresh and implement remaining audit findings in small groups. Keep already-good repositories largely intact.

## Sources and Validation

The [OpenAI article](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) was fetched through the official OpenAI Docs MCP on 2026-09-18. Its relevant guidance is narrow skill triggers, task-dependent references, revisiting accumulated recipes, context-dependent AGENTS routes, proportionate checking, and explicit completion/persistence. It does not establish that deleting useful checks or domain knowledge improves this setup.

Local evidence was refreshed against current shared guidance, playbook references, skill registry, and Git-hook entrypoints. The prior portfolio audit remains background evidence; this batch did not repeat its repo-wide inspections or run unrelated application tests. The proposals are inactive project resources, and their operational effects remain to be validated after implementation.

Repo hygiene, whitespace, and all 24 local project links passed validation. An independent reviewer checked the refreshed proposals and found no remaining consequential loss of agent-native contracts or new permission/check ceremony.
