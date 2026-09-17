---
name: agent-native-repo-playbook
description: Audit or improve a repository's agent guidance, documentation, execution checks, and completion workflow. Use for an explicit repository harness or agent-readiness review.
---

# Agent-Native Repo Playbook

Humans own intent, priorities, acceptance criteria, taste, and material risk.
Agents own implementation, verification, docs, cleanup, and routine follow-through.
Help a cold agent complete the requested job with little human coordination.

For audit/review requests, recommend changes. For implementation requests, carry
the authorized changes through verification and cleanup. Respect repo-local
contracts and the user's existing authorization.

## Choose the relevant review

- Guidance routing and duplication: `references/agents-md-best-practices.md`.
- Documentation ownership, placement, or freshness: `references/docs-structure-and-maintenance.md`.
- Explicit readiness scoring: `references/harness-readiness-rubric.md`.
- Broader operating-model design: `references/best-practices.md`.

Read the applicable repo guidance and enough source, commands, or product
evidence to answer the request. A small change needs a small investigation;
a portfolio audit needs explicit coverage. Avoid reading unrelated docs merely
because they exist.

## Review criteria

- Can an agent find the relevant source of truth and executable feedback?
- Do instructions add local knowledge or enforce a real boundary? Keep these;
  consolidate duplicates and remove obsolete recipes or generic reminders.
- Are skill descriptions precise, and do detailed references load only for
  the workflow that needs them?
- Can authorized work continue through the requested outcome without artificial
  checkpoints? Preserve decisions that truly require human judgment.
- Do important invariants have usable checks, recovery, or rerun paths?
- Are current contracts distinct from project plans and historical evidence?

Prefer improvements to existing code, tools, and docs over new policy layers.
Keep cross-repo orientation in its canonical skill and implementation facts
in the owning repo. Use the project skill for work needing durable execution
state; archive completed trackers according to the repo contract.

## Completion and evidence

For an audit, report what works, the most consequential gaps, concrete
Keep/Move/Delete recommendations where guidance is in scope, and next actions.
Ground major findings in files or observed behavior. Distinguish confirmed
defects, consolidation candidates, and unverified assumptions. Use the rubric
only when a score is requested; file counts alone are not a quality score.

For implementation, finish the scoped change, run relevant repo checks, inspect
changed behavior where practical, repair failures caused by the work, and report
compact evidence plus remaining limitations. Scale proof to risk and stop when
the requested outcome is established.

Preserve recoverable high-permission workflows and explicit operational
boundaries. Add approvals, branch process, or extra documentation only when
the task or demonstrated need calls for them. Do not introduce permanent
centralized audit scripts unless the user explicitly requests them.
