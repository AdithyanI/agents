# Agent Control-Plane Operations

This repo manages Codex configuration, skills, plugins, MCPs, lifecycle hooks, local previews, and the read-only dashboard. Canonical source lives in `~/GitHub/agents`; `~/.agents/skills` and `~/.codex` are runtime locations.

## Apply and validate

```bash
cd ~/GitHub/agents
./scripts/bootstrap-machine-agent-control-planes.sh --dry-run
./scripts/bootstrap-machine-agent-control-planes.sh --apply
./scripts/check-agent-control-planes.sh
./scripts/test-control-plane.sh
```

Bootstrap reconciles skill links, native plugins, Codex previews, local Git hooks, and the Codex runtime. It also removes obsolete setup left by retired development clients. Check validates these outputs, repository hygiene, runtime drift, and hermetic regressions.

For one repository, use an exact path with shared bootstrap/check:

```bash
./scripts/bootstrap-machine-agent-control-planes.sh --apply --repo ~/GitHub/agents
./scripts/check-agent-control-planes.sh --repo ~/GitHub/agents
```

Sparse machines are normal. Registry entries absent locally are skipped; existing non-Git folders at managed paths warn because they may be broken placeholders. Machine-enrollment checks use `~/GitHub/agents` by default; override with `AGENTS_MANAGED_REPO_CHECK_ROOT` for another canonical checkout.

## Entry points and ownership

| Command or source | Contract |
| --- | --- |
| `scripts/auto-apply-agent-control-planes.sh --apply` | Reconcile runtime-relevant changes since a machine-local Git revision stamp; use full bootstrap for first sync or shared-input changes |
| `scripts/enroll-managed-repos.sh --apply` | Add direct child Git repos under `~/GitHub` to `codex/config/repo-bootstrap.json` |
| `scripts/sync-skills-registry.sh` | Render global and repo skill links from `skills/registry.json` |
| `scripts/sync-plugins-registry.sh` | Validate native plugin entries; Codex config sync renders their runtime state |
| `scripts/sync-codex-plugin-installs.py` | Install enabled missing native plugin packages |
| `scripts/sync-codex-previews.py` | Render preview environments from `dev-servers/registry.json` |
| `scripts/sync-managed-git-hooks.sh --apply` | Set managed repo `core.hooksPath` to this repo's `hooks/git` |
| `codex/scripts/bootstrap-machine-codex.sh --apply` | Apply Codex config, global guidance, repo MCPs/hooks, terminal integration, and thread maintenance |
| `scripts/audit-agent-runtime-drift.py --plain` | Read-only machine-health report for plugin and Codex runtime drift |

Only `skills/registry.json` is tracked in the top-level `skills/` folder. User-scope links are neither staged nor registered with Stop, even if their runtime folder is inside an old checkout. Repo-scoped generated changes are registered with the active Codex Stop transaction for checked publication.

MCP schema version 3 uses neutral definitions and a `repos` scope per server. `"all"` selects all managed repositories, an explicit array selects those paths, and `[]` leaves a definition unassigned. The only generated MCP surface is repo `.codex/config.toml`.

## Local previews and remote access

`dev-servers/registry.json` owns short-lived local previews. Public Cloudflare/LaunchAgent services such as `adithyan.io` remain owned by `~/GitHub/scripts`.

Each listed repo gets one fixed-port preview in `.codex/environments/environment.toml`. The renderer rejects `autoPort: true`. Generated commands call `scripts/run-agent-preview-server.py`, which reuses an existing listener on `127.0.0.1:<port>` instead of spawning another server. `{repo_root}` resolves to the selected checkout, including an explicitly selected worktree.

Codex remote connections use `features.remote_connections` in the global config and managed OpenSSH aliases in `~/.ssh/config`. The scripts repo owns the SSH address, user, key, and Tailscale setup.

## Retired-client migration

Claude, Copilot, their VS Code agent defaults, and the Antigravity experiment have no active renderers or optional enable flags. `scripts/retire-agent-clients.py` removes dedicated per-repo client setup and recognized historical global outputs. Bootstrap runs it so another machine cannot retain old hooks or jobs after syncing this change.

The migration supports `--dry-run`, `--apply`, and `--check`, plus exact `--repo` filters. It backs up changed regular files under `~/.local/state/agents-control-plane/retired-client-backups` before removing owned setup. It preserves application binaries, credentials, conversations, real skill source directories, unknown MCP entries, and unrelated preferences. Dedicated repo client instructions/permissions and retired editor integration preferences are removed, including manual additions. It retires owned launchers and the old Claude finalizer/archiver and Copilot pruner jobs. Recovery of tracked source is through Git history; local configuration recovery uses those private backups.

## Lifecycle and commit gate

`hooks/registry.json` renders global hooks to `~/.codex/hooks.json` and selected repo hooks to `.codex/hooks.json`. Stop is global; SessionStart and UserPromptSubmit are repo-scoped. Optional repo scripts live under `scripts/hooks/`; missing scripts are successful no-ops. See `repo-lifecycle-hook-adapter.md` for payload and ownership contracts.

Explicit thread finalization is separate from native hooks: `codex/scripts/finalize-codex-thread.py` reads thread ownership, runs optional repo `scripts/hooks/finalize_codex_thread.py`, and then archives.

Stop discovers affected repositories across the turn tree and consolidates their current staged and working-tree changes. Git invokes `hooks/git/pre-commit`, which delegates to repo `scripts/check-fast.sh` when present. Tracked branches push optimistically and rebase only when the remote is ahead; new branches establish upstream tracking. Successful `main` publication sends a bounded best-effort revision notification to Mac Mini production automation. Builds remain outside the hook; periodic reconciliation recovers failed notifications. Timing lives in `~/.local/state/agents-control-plane/log/hooks-stop.log`.
