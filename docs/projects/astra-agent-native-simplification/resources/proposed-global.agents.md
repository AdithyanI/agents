# Global Agent Guidance

> Proposal for `config/global.agents.md`; not active guidance.

> Prompts may be dictated; interpret intent over transcription errors.

## Operating Model

- Humans set intent, priorities, acceptance criteria, and material-risk boundaries. Agents own implementation, verification, documentation, cleanup, and routine follow-through.
- In trusted repos, continue through the complete authorized outcome. When the task includes running, inspecting, or repairing the result, finish those steps before handing it back.
- Carry existing authorization forward. Ask when an unresolved decision materially changes intent or exceeds that authorization, such as new spending, destructive or out-of-scope work, secrets, or irreversible external effects. Use judgment for routine implementation and repair.
- Match discovery and verification to the change. Run the affected repo's required checks and inspect changed behavior when relevant. Rerun or broaden checks when changes, failures, or unresolved concerns justify it; do not waive a required failing gate.
- Report the result, evidence, and any remaining validation limitation. Turn repeated mistakes into the smallest useful improvement to code, tools, checks, or local guidance.

## Knowledge and Guidance

- Repo-local guidance owns structure and workflow. Read the applicable instructions and task-relevant sources; inspect deeper guidance when working in that subtree rather than assuming it loaded dynamically.
- Use `agent-native-repo-playbook` for repo guidance, documentation, or execution-workflow audits and improvements.
- Keep durable knowledge in its owning repo document and update it when durable behavior changes. Add a document only for a distinct topic that needs one.
- Follow the repo's docs contract. Otherwise use `AGENTS.md` for routing, `docs/architecture/` for system shape, `docs/references/` for exact facts, and project trackers for active execution. Archive completed trackers before handoff or state the concrete blocker.
- Preserve README files that serve an explicit public/human landing page. In private agent-native repos, keep operational knowledge in AGENTS and the existing docs structure.
- Default to a clean target structure unless the user or repo contract requires compatibility; do not add legacy fallbacks or dual structures by default.

## Managed Capabilities

- `~/GitHub/agents` owns shared Codex configuration, skill distribution, registries, and hooks. Edit canonical sources and use its bootstrap/check workflow; managed runtime files and skill symlinks are generated surfaces. Temporary troubleshooting edits must be followed by a canonical fix and re-render.
- Prefer a controllable in-app browser for collaborative visual work. For automation or unavailable in-app control, use an available browser capability suited to the task; verify access before relying on it.
- Delegate bounded independent work when useful. Keep shared decisions, integration, and final reporting with the main agent.
- Check `~/GitHub/scripts` before adding shared machine utilities. Keep application behavior, storage, and repo-specific lifecycle rules with their owning repo.

## Files and Git

- Put temporary artifacts under the current repo's `tmp/` unless local guidance specifies another location. Browser screenshots/traces may also use `/tmp/playwright-mcp`. Remove disposable artifacts and keep tool session folders such as `.playwright-mcp/` and `.xcodebuildmcp/` out of Git.
- Managed Codex lifecycle automation stages, checks, commits, rebases, and pushes after the turn. Fix failures it returns. Do not manually commit or push unless asked; documented repo automation may do so as part of its normal workflow.
- Managed Git hooks call repo `scripts/check-fast.sh` when present. Keep fast checks local, deterministic, quick, and actionable; put slower validation in the repo's full-check path.
- GitHub CLI is authenticated. For generic media uploads without an app-owned storage path, use `~/GitHub/scripts/bin/upload-media`, which reads generated credentials from `~/.secrets/media-upload/env`; do not pass storage secrets through flags or ordinary environment variables.
