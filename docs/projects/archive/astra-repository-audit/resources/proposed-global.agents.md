# Global Agent Guidance

> Prompts may be dictated; interpret intent over transcription errors.

## Operating model

- Humans set intent, priorities, acceptance criteria, and material risk boundaries. Agents own implementation, relevant verification, documentation, cleanup, and routine follow-through.
- In trusted repos, continue through the authorized work until the requested outcome is complete. A first implementation is not completion when the task includes running, inspecting, or fixing it.
- Ask when an unresolved decision materially changes intent or authorization: destructive or out-of-scope work, new spending, secrets, or irreversible external effects. Carry existing authorization forward and use judgment for routine implementation choices.
- Match discovery and verification to the change. Use the affected repo's documented checks and inspect changed behavior when relevant; rerun or broaden checks when failures, new changes, or unresolved risk justify it.
- Report what changed, the evidence establishing it, and any relevant validation limitation.

## Knowledge and guidance

- Repo-local guidance and docs own local structure and workflow. Read the relevant routes as the task requires.
- When work moves into a deeper subtree, inspect applicable local guidance; do not assume the client loaded it dynamically.
- For repo harness or guidance audits, use the `agent-native-repo-playbook` skill.
- Keep durable knowledge in its existing canonical doc. Update that doc when behavior changes; add a new document only for a distinct topic that needs an owner.
- Keep root guidance as a short router. Detailed architecture and implementation facts belong in repo docs according to the local contract. Archive completed project trackers before final handoff, or state the concrete blocker.
- Repeated mistakes are evidence for the smallest useful fix: clearer code/errors, a check, a script, or a precise local instruction.
- Preserve an explicit public/human README where it serves the repo. In private agent-native repos, use AGENTS and the existing docs structure for operational knowledge.
- Default to a clean target structure unless repo guidance or the user explicitly require compatibility. Do not add dual reads, legacy fallbacks, or compatibility shims by default.

## Managed capabilities

- `~/GitHub/agents` owns shared skills, hooks, registries, and generated client configuration. Edit canonical sources and use its documented bootstrap/check workflow; do not hand-edit generated runtime files or skill symlink destinations.
- Temporary generated-file edits are available for troubleshooting. Put the durable fix in the canonical source and re-render it.
- For shared machine utilities, check `~/GitHub/scripts` before adding a cross-repo helper. Application behavior and storage belong to the owning app.
- Prefer a controllable in-app browser for collaborative visual work. For automation or unavailable in-app control, use an available browser capability suited to the task; verify access before relying on it.
- Delegate bounded independent work when useful; keep shared decisions and final integration with the main agent.

## Files and Git

- Keep scratch files under the current repo's `tmp/` unless local guidance specifies another location. Browser traces/screenshots may also use `/tmp/playwright-mcp`. Remove disposable artifacts; keep tool session folders out of Git.
- Managed lifecycle automation stages, checks, commits, rebases, and pushes after the turn. Fix check failures it returns. Do not manually commit or push unless asked; documented repo automation may do so as part of its normal workflow.
- GitHub CLI is authenticated. For generic media uploads without an app-owned storage path, use `~/GitHub/scripts/bin/upload-media`, which reads generated credentials from `~/.secrets/media-upload/env`; never pass storage secrets in flags or ordinary environment variables.
