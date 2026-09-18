# Agents Control-Plane Repo

Personal Codex configuration, skills, plugins, MCPs, previews, and lifecycle hooks, reproduced across MacBook and Mac Mini.

## Orientation

For changes affecting Dobby ownership, engine/workspace boundaries, dashboard/gateway flow, or more than one Dobby repo, read `skills-source/owned/dobby-system/SKILL.md`. Keep cross-repo orientation there and control-plane contracts in this repo's docs.

## Canonical Sources

| Source | Owns |
| --- | --- |
| `config/global.agents.md` | Machine-wide guidance rendered to `~/.codex/AGENTS.md` |
| `codex/config/` | Personal Codex config, bundled-skill policy, and shared repo inventory in `repo-bootstrap.json` |
| `skills/registry.json` | Standalone skill ownership and distribution |
| `skills-source/owned/`, `skills-source/external/` | Canonical managed skill content |
| `plugins/registry.json` | Native Codex plugin enablement and installation |
| `mcp/config/presets.json` | MCP definitions and repository scopes |
| `hooks/registry.json`, `hooks/scripts/` | Codex lifecycle hook configuration and implementations |
| `hooks/git/` | Shared local Git hooks |
| `dev-servers/registry.json` | Opt-in local previews rendered to `.codex/environments/environment.toml` |
| `dashboard-app/` | Read-only control-plane dashboard |

Edit these inputs and rerun bootstrap; do not hand-edit generated `.codex/config.toml`, `.codex/hooks.json`, preview environments, or managed skill symlink destinations.

## Entry Points

- Apply: `./scripts/bootstrap-machine-agent-control-planes.sh --apply`
- Reconcile after Git sync: `./scripts/auto-apply-agent-control-planes.sh --apply`
- Validate runtime and regressions: `./scripts/check-agent-control-planes.sh`
- Hermetic tests: `./scripts/test-control-plane.sh`
- Machine-health audit: `./scripts/audit-agent-runtime-drift.py --plain`
- Install a standalone skill: `./scripts/bootstrap-skill.sh <skills.sh-url-or-upstream-ref> --repo <repo>`
- Install a native plugin: `./scripts/bootstrap-plugin.sh <plugin-name-or-id> [--scope global|repo|dormant] [--repo <repo>]`

Shared bootstrap/check support exact repository paths, such as `--repo ~/GitHub/agents`. Prefer shared bootstrap for registry changes so related outputs stay consistent. Use component commands for intentional single-surface troubleshooting.

## Contracts

- Codex is the sole supported development client. Retired-client cleanup is a removal migration, not an optional runtime framework.
- Repo bootstrap entries define behavior such as `personality`, `model_instructions_file`, `developer_instructions`, `project_root_markers`, and `features`. Model, reasoning effort, profile, and Fast/service tier remain client-owned.
- A repo's identity prompt is declared once as `model_instructions_file`; it reaches Codex through the generated repo config.
- MCP schema version 3 assigns each definition to `repos: "all"` or an explicit array of managed repository paths. Empty arrays leave a definition unassigned. Output lives only in repo `.codex/config.toml`.
- Standalone skills use symlinks at `~/.agents/skills/<skill>` or repo `.agents/skills/<skill>`. Keep repo-local skills in their owning repos unless explicitly promoted.
- Keep `unmanaged_repo_local_skills` and `unmanaged_repo_local_plugins` in their existing registries. An existing repo must contain every declared local skill; fix stale entries rather than hiding errors. Do not add mapping manifests.
- Keep global skills/plugins a minimal default kit. Native plugins use global/manual enablement; their repo scope is not reliable. If a bundled MCP needs one-repo scope, promote that MCP into the standalone MCP registry.
- Do not decompose native plugins into standalone skills/MCPs without an explicit need. A rendered plugin entry is distinct from an installed package: bootstrap installs missing enabled packages, and runtime drift checks verify availability.
- Classify new OpenAI-bundled skills in `codex/config/bundled-skills-policy.json` as allowed or disabled.
- New agent-facing CLI clients follow `docs/references/cli-interface-contract.md`.
- Preview commands use `{repo_root}` to follow the active checkout. Public Cloudflare/LaunchAgent services and ports belong in `~/GitHub/scripts`, outside the preview registry.
- Dashboard production serves an exact versioned build from `~/.local/share/agents-control-plane-dashboard/current`; source edits are not a production deployment.

## Hooks and Validation

- Optional repo lifecycle scripts live at `scripts/hooks/session_start.py`, `scripts/hooks/user_prompt_submit.py`, and `scripts/hooks/finalize_codex_thread.py`. Follow `docs/references/repo-lifecycle-hook-adapter.md` for their contracts.
- Managed repos use `core.hooksPath` pointing at this repo's `hooks/git/`. Commit-time validation delegates to repo `scripts/check-fast.sh` when present. Keep it local, deterministic, and quick; slower checks belong in `scripts/check-full.sh`.
- Skill/plugin registry changes require their sync/check in the same change.
- MCP, bootstrap, or preview registry changes require shared bootstrap/check and inspection of affected Codex output.
- Hook registry, lifecycle scripts, shared Git hooks, or Git-hook installer changes require shared bootstrap/check and hermetic regression tests.
- Global Codex config or repo-bootstrap changes require Codex control-plane validation.

Detailed commands and ownership live in `docs/references/agent-control-plane-operations.md`, `codex-control-plane-operations.md`, and `codex-control-plane-ownership.md`.
