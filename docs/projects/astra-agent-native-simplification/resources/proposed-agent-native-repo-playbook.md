---
name: agent-native-repo-playbook
description: Audit or improve a solo developer's agent-native repo guidance, docs, checks, and completion workflow. Use for repository workflow reviews or recurring agent confusion, premature stopping, and instruction overhead.
---

# Agent-Native Repo Playbook

> Proposal for the canonical playbook; not an installed skill.

Humans set intent, priorities, acceptance criteria, taste, and material-risk boundaries. Agents own the complete authorized job: implementation, verification, docs, cleanup, and routine follow-through. Improve the repository so a cold agent can finish that job with little human coordination.

For audit/review requests, analyze and recommend. For implementation requests, carry the authorized change through its complete outcome. Respect existing authorization and the repo's local contracts.

## Choose the Relevant Reference

- Guidance routing, duplication, or AGENTS review: `references/agents-md-best-practices.md`.
- Documentation ownership, placement, or freshness: `references/docs-structure-and-maintenance.md`.
- Requested readiness scoring: `references/harness-readiness-rubric.md`.
- Broader operating-model design: `references/best-practices.md`.

Read applicable repo guidance and enough source, commands, or product evidence to answer the request. Scope discovery to the question; a portfolio audit needs explicit coverage, while a narrow correction needs only its relevant context.

## Agent-Native Contract

- Carry authorized work through implementation, relevant checks, inspection, repair, docs, and cleanup. Keep routine implementation decisions with the agent; preserve material decisions that belong to the human.
- Favor recoverable direct-to-main delivery in trusted solo repos unless local guidance requires another flow. Use existing repo checks and Git lifecycle automation; do not add branch or approval ceremony without a concrete need.
- Keep required fast checks deterministic, local, quick, and actionable. Inspect affected product/service behavior when relevant, and broaden validation when evidence warrants it. A failing delivery gate must be repaired within scope or reported as a real blocker.
- Keep current knowledge in the owning docs. Use the repo's docs contract and conditional routes; do not create a second source of truth to summarize the first.
- Keep cross-repo ownership and privacy orientation in its canonical skill, and implementation facts in the owning repo.
- Turn repeated failure into the smallest effective code, tool, check, or local-guidance fix. Use a project tracker when work needs durable execution state and archive it when completed.

## Review Questions

- Can the agent find the relevant authority, commands, and executable feedback?
- Do instructions add local knowledge or protect a real boundary? Keep those; consolidate repetition and remove obsolete recipes.
- Are skill triggers precise, with specialized detail loaded only when needed?
- Can authorized work finish without artificial intermediate checkpoints?
- Are current contracts, active plans, and historical evidence distinguishable, with useful recovery paths?

## Evidence and Handoff

For an audit, explain what works, the most consequential gaps, and concrete next actions. Include Keep/Move/Remove decisions when guidance is in scope. Ground findings in files or observed behavior and distinguish confirmed defects from improvement candidates and untested assumptions. Use scoring only when requested; file counts are not quality scores.

For implementation, finish the scoped outcome and report compact evidence, changes to the harness, and relevant remaining limitations. Scale proof to the change while honoring required repo gates. A first implementation is insufficient when the request includes running, inspecting, or repairing it.

Prefer improvements to existing tools and docs over new policy layers. Do not introduce permanent centralized audit scripts unless the user explicitly requests them.
