---
name: agent-native-repo-playbook
description: Audit or improve repo guidance, skills, documentation, and autonomous completion workflows. Use when agents repeatedly get confused or stop early, instructions have accumulated, or the user requests an agent-native repository review.
---

# Agent-Native Repo Playbook

Humans set intent, priorities, taste, acceptance criteria, and material-risk boundaries. Agents own the complete authorized job. Improve the repository so an agent arriving without prior context can find the relevant authority, act, verify the outcome, and finish with little human coordination.

For an audit request, investigate and recommend. For authorized implementation, make the changes and complete verification and cleanup. Carry prior authorization forward; a status question does not revoke it. Local ownership and operational contracts take precedence over this playbook's defaults.

## What to Preserve

- Autonomous follow-through, including inspection and repair when the task calls for them. Keep routine decisions with the agent and consequential unresolved intent with the human.
- Recoverable direct-to-main delivery in trusted solo repos unless local guidance specifies another flow. Use existing Git lifecycle automation and required checks; do not add approval or branch ceremony without a concrete need.
- Fast, deterministic, actionable checks and relevant product/service proof. Repair a failing delivery gate within scope or report the real blocker; smaller instructions do not justify weaker verification.
- Non-obvious intent, ownership, privacy, external constraints, and recovery knowledge. Cross-repo orientation belongs with its canonical owner; implementation belongs in the owning repo's source.

## What to Simplify

Inspect enough current guidance, source, and executable feedback to answer the task. Follow relevant routes rather than reading every document or skill. A requested portfolio audit needs explicit coverage; a narrow correction does not.

Keep instructions that supply useful local context or protect a real boundary. Remove obsolete recipes, duplicated rules, code inventories, and artificial checkpoints. Prefer code and existing commands over prose copies of their behavior. Do not move every removed paragraph into another reference.

Skills should have precise triggers and contain knowledge or tools worth loading for that task. Keep specialist capabilities; file count alone is not a reason to remove them. Fix recurring failures in the smallest effective layer: code, tool, check, or guidance.

Use a project tracker when work needs durable execution state, and archive it when complete. Do not introduce a universal docs layout, extra review gates, or permanent centralized audit scripts without a demonstrated need or explicit request.

## References When Needed

- Guidance placement or duplication: `references/agents-md-best-practices.md`.
- Deciding whether documentation earns its place: `references/docs-structure-and-maintenance.md`.
- Execution and recovery design: `references/best-practices.md`.
- Explicitly requested readiness scoring: `references/harness-readiness-rubric.md`.

Ground findings in current files or observed behavior. Distinguish confirmed defects from suggestions and untested assumptions. Report the outcome, relevant checks and product evidence, and remaining limitations; use scores or a formal audit format only when requested.
