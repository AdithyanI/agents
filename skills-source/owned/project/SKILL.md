---
name: project
description: Create, resume, replan, or close a long-running project with durable scope, progress, evidence, and a clear resume point. Use when the user requests project tracking or work spans sessions; routine edits do not need a tracker.
---

# Project

Keep one tracker as the durable resume point for long-running work. Follow the repo's existing tracker home: for example, Dobby workspaces use `projects/<project>/tasks.md`; otherwise prefer `docs/projects/<project>/tasks.md`.

## Working State

Read the current tracker and verify it against current source and results. Replan in place when scope or reality changes. Preserve the user's intended outcome and existing authorization; a stale plan is evidence to update, not a reason to stop.

Record only what another agent needs to continue: goal and completion criteria, relevant constraints and decisions, work remaining or in progress, useful evidence, and actual blockers. Use milestones or a current-batch table when they help. Omit empty sections and generic execution rules. `references/tasks-template.md` is an optional starting point, not a required schema.

Continue through implementation, proportionate verification, repair, and cleanup. Ask only for missing decisions that materially affect the outcome and cannot be resolved from available context. Update the tracker after meaningful changes or before handoff; do not copy routine tool output into it.

For parallel work, keep the tracker single-writer and assign clear ownership. The parent integrates results and records the durable outcome. See `references/subagent-conventions.md` if coordination itself needs design.

## Completion and Archive

Prove the completion criteria against current state, resolve remaining work, and record validation and any meaningful limitation. Keep useful lessons in the tracker or improve their actual owning source; a separate learnings document is optional.

Archive the complete project directory under the same tracker home's `archive/` path. The bundled helper moves the complete directory, including resources:

```bash
python3 /Users/dobby/GitHub/agents/skills-source/owned/project/scripts/archive_project.py --source <active-project-dir> --destination <tracker-home>/archive/<project> --no-input
```

Use `--dry-run` when an inspection pass is useful. Require `source_removed: true`, verify the active directory is gone, repair relative links affected by the move, and run the relevant repo hygiene check. Do not leave a completed project or empty placeholder in the active folder. If work is still incomplete, keep it active and name the remaining work; do not archive merely to finish a turn.

`references/tracker-operating-rules.md` covers continuity and closeout edge cases. Report the outcome, relevant validation, and archived tracker path when complete.
