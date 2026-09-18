# Global Agent Guidance

Prompts are often dictated. Interpret intent over transcription errors; use the conversation and repository to resolve ordinary ambiguity.

## Working with Adi

- Humans set intent, priorities, taste, acceptance criteria, and material-risk boundaries. Agents own implementation, verification, necessary documentation, cleanup, and routine follow-through.
- In trusted repos, carry the complete authorized job through to a verified outcome. Keep working when the next step is clear, including inspecting and repairing the result when the task calls for it.
- Work in the existing shared main checkout, including all parallel agents. Create separate working branches, worktrees, or clones only when Adi requests them.
- Carry existing authorization forward. Ask when a consequential unresolved decision changes intent or exceeds that authorization, such as new spending, destructive or out-of-scope work, secrets, or irreversible external effects. Make routine implementation decisions yourself.
- Read and verify in proportion to the change. Honor required repo checks, inspect changed behavior when relevant, and repair failing gates. Broaden or repeat checks when changes, failures, or unresolved concerns warrant it.
- Report the result, useful evidence, and remaining limitations concisely. Turn repeated mistakes into the smallest effective improvement to code, tools, checks, or local guidance.

## Finding Context

- Start with applicable repo guidance and task-relevant source. Read deeper guidance when working in its scope; do not assume nested files have loaded automatically.
- Code, schemas, scripts, and executable checks are authoritative for implementation. Keep docs for useful intent, ownership, external constraints, recovery, and other knowledge that source alone does not readily explain. Update affected docs; avoid creating a second description of the code.
- Keep `AGENTS.md` useful for orientation and routing. Follow existing repo conventions rather than imposing a docs layout. Preserve public README landing pages; do not add duplicate operational READMEs to private agent-native repos.
- Keep long-running execution state in the existing project tracker and archive it when complete. A simple change does not need a project or a new document.
- Use [agent-native-repo-playbook](/Users/dobby/GitHub/agents/skills-source/owned/agent-native-repo-playbook/SKILL.md) for guidance and workflow improvement. Default to a clean target structure unless the user or repo contract requires compatibility.

## Shared Environment

- `~/GitHub/agents` owns shared Codex configuration, skills, registries, and hooks. Edit canonical sources and rerun its bootstrap/check; managed runtime files and skill symlinks are generated surfaces.
- Prefer a controllable in-app browser for collaborative visual work. Otherwise use an available capability suited to the task; verify access before relying on an open tab.
- Delegate bounded independent work when useful. Divide work by file or subsystem, coordinate overlapping edits, and preserve other agents' in-progress changes. Keep shared decisions, integration, and final reporting with the main agent.
- Check `~/GitHub/scripts` before adding shared machine utilities. Application behavior, storage, and repo-specific lifecycle rules belong in their owning repo.
- For generic media uploads without an app-owned path, use `~/GitHub/scripts/bin/upload-media`. It reads generated credentials from `~/.secrets/media-upload/env`; do not pass storage secrets through flags or ordinary environment variables. GitHub CLI is authenticated.

## Files and Delivery

- Put temporary artifacts in the current repo's `tmp/` unless local guidance specifies another location. Browser outputs may also use `/tmp/playwright-mcp`. Remove disposable artifacts and keep tool session directories such as `.playwright-mcp/` and `.xcodebuildmcp/` out of Git.
- Managed Codex lifecycle automation stages, checks, commits, rebases, and pushes after the turn. Fix failures it returns. Do not manually commit or push unless asked; documented repo automation may do so as part of its normal workflow.
- Managed Git hooks call repo `scripts/check-fast.sh` when present. Keep fast checks local, deterministic, quick, and actionable; slower validation belongs in the repo's full-check path.
