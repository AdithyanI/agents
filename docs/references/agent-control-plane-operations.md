# Agent Control-Plane Operations

This repo manages shared guidance, skills, MCPs, lifecycle hooks, and native client configuration. Canonical source lives in `~/GitHub/agents`; `~/.agents/skills`, `~/.codex`, and `~/.claude` are runtime locations. `repos/registry.json` gives repositories stable IDs and explicitly enables each client. New enrollments enable both Codex and Claude; Claude management defaults on when the optional client is installed and respects each machine's explicit opt-out.

## Apply and validate

```bash
cd ~/GitHub/agents
./scripts/bootstrap-machine-agent-control-planes.sh --dry-run
./scripts/bootstrap-machine-agent-control-planes.sh --apply
./scripts/check-agent-control-planes.sh
./scripts/test-control-plane.sh
```

Bootstrap reconciles skill links, native plugins, Codex previews, local Git hooks, and enabled client outputs. Check validates these outputs, repository hygiene, runtime drift, and hermetic regressions. Historical client retirement is excluded from both commands.

For one repository, use an exact path with shared bootstrap/check:

```bash
./scripts/bootstrap-machine-agent-control-planes.sh --apply --repo ~/GitHub/agents
./scripts/check-agent-control-planes.sh --repo ~/GitHub/agents
```

Sparse machines are normal. Registry entries absent locally are skipped; existing non-Git folders at managed paths warn because they may be broken placeholders. Machine-enrollment checks use `~/GitHub/agents` by default; override with `AGENTS_MANAGED_REPO_CHECK_ROOT` for another canonical checkout.

`repos/registry.json` declares exact `auto_enrollment_exclusions`
for retired repository paths and retained recovery checkouts. The Git sync enrollment step preserves these
directories and their history without adding them back to `repos`; it does not
remove an existing enrollment. Skill-link sync also never prunes links inside
excluded checkouts, because a retired checkout can share its remote with the
enrolled repo (`dobby-engine` is now `dobby`) and a pruned link would be
committed and pushed there. List retired repos (`dobby-engine`, `documents`,
`photo-search`) here and remove their `repos` entries. `~/GitHub/modal_functions` is excluded because
WIN owns its active implementation and release; its historical GitHub repository
is archived and no retained local checkout is required. `~/GitHub/aipodcasting` is retired
after its frontend moved into `win/frontend/`; WIN owns its skills, Figma MCP
assignment, and frontend preview. Its exclusion prevents a restored historical
checkout from becoming active again. Bootstrap leaves any retained checkout's
existing generated files and source untouched.

`platform-ops` is absorbed into `scripts`, which owns the Cloudflare API and docs
MCP assignments. `futureoflife-podcast` and `thoughtforms-life` are absorbed into
the `aipodcasting-website` workspace. All three retired paths remain excluded
from enrollment, including when a historical checkout is restored for recovery.

Codex trusts only exact enrolled paths with `clients.codex.config.codex_trust: true`.
The default is false. Reconciliation removes stale GitHub grants and broad ancestor
grants such as `/`, the home directory and `~/GitHub`; unrelated specific user
workspaces remain intact. `--root` selects cleanup scope and never bypasses the
registry. Review a new repo's origin and executable instructions before explicit
enrollment; normal work inside existing owned repos remains autonomous.

Each repo may also declare `envrc_sha256` with reviewed relative `.envrc` paths.
Scripts' [shell environment reconciler](../../../scripts/docs/references/direnv-auto-trust.md)
applies these hashes on each machine; Git sync never accepts changed content.

## Entry points and ownership

| Command or source | Contract |
| --- | --- |
| `scripts/auto-apply-agent-control-planes.sh --apply` | Reconcile runtime-relevant changes since a machine-local Git revision stamp; use full bootstrap for first sync or shared-input changes |
| `scripts/enroll-managed-repos.sh --apply --repo <name-or-path>` | Enroll an explicitly reviewed direct child repo and enable both clients; without `--repo`, discovery only reports candidates |
| `scripts/sync-skills-registry.sh` | Render global and repo skill links from `skills/registry.json` |
| `scripts/sync-plugins-registry.sh` | Validate native plugin entries; Codex config sync renders their runtime state |
| `scripts/sync-codex-plugin-installs.py` | Install enabled missing native plugin packages |
| `scripts/sync-codex-previews.py` | Render preview environments from `dev-servers/registry.json` |
| `scripts/sync-managed-git-hooks.sh --apply` | Set managed repo `core.hooksPath` to this repo's `hooks/git` |
| `codex/scripts/bootstrap-machine-codex.sh --apply` | Apply Codex config, global guidance, repo MCPs/hooks, terminal integration, and thread maintenance |
| `claude/scripts/sync-claude.py --apply` | Reconcile owned Claude guidance, portable skills, project MCP, and selected hooks; `--check` reports drift and default is `--dry-run` |
| `scripts/audit-agent-runtime-drift.py --plain` | Read-only machine-health report for plugin and Codex runtime drift |

## Claude machine enablement

Normal bootstrap manages Claude when Desktop or the Code CLI is installed; a missing
`enabled.json` means enabled. No machine preference file is needed for this default.
An explicit `python3 claude/scripts/sync-claude.py --apply --disable` removes only
renderer-owned outputs and keys, retains user data, and persists the opt-out.
`--apply --enable` re-enables that machine. These preferences and output ownership
records live under `~/.local/state/agents-control-plane/claude/` and do not sync
between machines. If neither client is installed, bootstrap skips Claude without
creating outputs.
The renderer excludes each repo's `.claude/skills`, `.claude/settings.json`, and
`.mcp.json` outputs through that clone's `.git/info/exclude`, so repository sync
cannot bypass machine selection. It refuses to overwrite tracked configuration;
do not untrack a hand-written shared configuration as part of rollout.

Shared orchestration skips Codex-only materialization and runtime checks when
the Codex executable is absent, while continuing shared validation and Claude.
Installed Codex still runs its normal checks. After installing a previously
absent client, rerun bootstrap; post-sync reconciliation tracks source revisions,
not application installation events.

Claude Desktop's **local Code sessions** and the CLI use the same guidance,
skills, hooks and project MCP configuration; a standalone CLI is not required.
This setup does not upload account skills or configure Cowork/cloud sessions.
See [Desktop shared configuration](https://code.claude.com/docs/en/desktop#shared-configuration).

When a CLI is available, the renderer checks that it is at least `2.1.281` for
native root and nested `AGENTS.md` discovery. Without a standalone CLI, it validates
the installed macOS Desktop bundle and discovers the newest complete Code engine
already cached under `~/Library/Application Support/Claude/claude-code/`.
It invokes that exact binary with `--version` and applies the same minimum.
Version/build directories are discovered dynamically; no binary is copied,
installed or linked onto PATH. Existing Code sessions are not interrupted.

If Desktop has not downloaded its Code engine yet, the renderer can still prepare
shared configuration and reports only the Desktop app version, explicitly noting
that the embedded engine version was not CLI-probed. The app version is never
compared with the Code minimum. Use an up-to-date Desktop and a fresh local Code
session, then verify `/context`, `/skills` and `/mcp`.
No project instruction mirror is generated; the renderer preserves native
instruction-selection preferences, permissions, authentication and model choices.
See [Claude instruction discovery](https://code.claude.com/docs/en/memory#agentsmd).

Only standalone skills explicitly including `claude` in their registry `clients`
are shared; omitted `clients` keeps existing Codex scope. Native plugins retain
their native owner. Conflicting handwritten outputs or edited managed entries
stop reconciliation before writes. Output updates use a lock, recovery journal,
and private backups. No credentials, sessions, or `settings.local.json` are managed.

Only `skills/registry.json` is tracked in the top-level `skills/` folder. User-scope links are neither staged nor registered with Stop, even if their runtime folder is inside an old checkout. Repo-scoped generated changes are registered with the active Codex Stop transaction for checked publication.

MCP schema version 3 uses neutral definitions and a `repos` scope per server. `"all"` selects all managed repositories, an explicit array selects those paths, and `[]` leaves a definition unassigned. Each enabled client renders the assignment: Codex uses repo `.codex/config.toml`; Claude uses project `.mcp.json` while preserving unrelated server entries.

The `xcode` preset scopes Apple's native `/usr/bin/xcrun mcpbridge` to Snipwit.
It follows the developer directory selected by `xcode-select`, so upgrading Xcode
does not require changing a pinned application path. Xcode must be running, with
the project open and **Settings > Intelligence > Allow external agents to use
Xcode tools** enabled by the user. Xcode also asks permission when a new external
client first calls a tool. Approve the native Codex client rather than a disposable
verification process. See Apple's [external agent setup](https://developer.apple.com/documentation/xcode/giving-external-agents-access-to-xcode).
Verify `xcrun --find mcpbridge` and the MCP `initialize` / `tools/list` handshake
after an Xcode update. Tool availability comes from that running Xcode instance;
the registry installs no third-party bridge or credentials. Xcode's
`xcrun mcpbridge run-agent skills export --output-dir <path>` can export its
current Apple-provided skill bundles for inspection before a canonical import.

### Claude session finalization

Claude has no App Server or archive step, so `claude/scripts/finalize-stale-claude-sessions.py`
finalizes idle Claude Code sessions for repos that ship
`scripts/hooks/finalize_claude_session.py`. The macOS bootstrap installs it as the
hourly `com.<user>.claude-session-finalizer` LaunchAgent (6-hour idle cutoff, at most
four sessions per run). A busy or recently idle `~/.claude/sessions/<pid>.json`
handshake protects live work; the ledger
`~/.local/state/claude-control-plane/finalized-claude-sessions.json` makes each session
finalize once. Use `--dry-run` to inspect candidates and `--mark-only` to absorb a
backlog. Repo policy (Dobby's remember and transcript capture) stays in the repo hook;
see the engine's `docs/lifecycle-hooks.md`.

## Local previews and remote access

`dev-servers/registry.json` owns short-lived local previews and native Run actions.
Public Cloudflare/LaunchAgent services such as `adithyan.io` remain owned by
`~/GitHub/scripts`. A repository defines one `servers` entry for a fixed-port
preview or one `actions` entry with `name`, `runtimeExecutable`, and
`runtimeArgs` for a native build/run command. Native commands run directly,
without a server port or listener reuse check. Snipwit's Run action invokes its
own `scripts/build-and-run.sh`; `{repo_root}` follows the active checkout.

Each listed repo gets one Run action in `.codex/environments/environment.toml`.
For preview servers, the renderer rejects `autoPort: true` and wraps commands
with `scripts/run-agent-preview-server.py`, which reuses an existing listener on
`127.0.0.1:<port>` instead of spawning another server. `{repo_root}` resolves to
the selected checkout, including an explicitly selected worktree.

The `aipodcasting-website` Run action opens its marketing site from
`sites/aipodcasting` on port 4322. Podcast previews run from the same workspace:
`pnpm --filter @aipodcasting/thoughtforms dev` uses port 4330, and
`pnpm --filter @aipodcasting/futureoflife dev` uses port 4331. The retired
standalone checkouts no longer receive preview configuration.

Managed OpenSSH aliases live in `~/.ssh/config`. The scripts repo owns the SSH address, user, key, and Tailscale setup.

## Retired-client migration

`scripts/retire-agent-clients.py` retains the historical Codex-only removal migration for deliberate recovery work. It is never called by bootstrap, reconciliation, or health checks. Its `--apply` removes matching Claude setup, including restored setup and project-local permissions; do not use it on a coexistence installation.

The migration supports `--dry-run`, `--apply`, and `--check`, plus exact `--repo` filters. It backs up changed regular files under `~/.local/state/agents-control-plane/retired-client-backups` before removing owned setup. It preserves application binaries, credentials, conversations, real skill source directories, unknown MCP entries, and unrelated preferences. Dedicated repo client instructions/permissions and retired editor integration preferences are removed, including manual additions. It retires owned launchers and the old Claude finalizer/archiver and Copilot pruner jobs. Recovery of tracked source is through Git history; local configuration recovery uses those private backups.

## Lifecycle and commit gate

`hooks/registry.json` renders global hooks to `~/.codex/hooks.json` and selected repo hooks to `.codex/hooks.json`. Stop is global; SessionStart and UserPromptSubmit are repo-scoped. Optional repo scripts live under `scripts/hooks/`; missing scripts are successful no-ops. See `repo-lifecycle-hook-adapter.md` for payload and ownership contracts.

Explicit thread finalization is separate from native hooks: `codex/scripts/finalize-codex-thread.py` reads thread ownership, runs optional repo `scripts/hooks/finalize_codex_thread.py`, and then archives.

Stop discovers affected repositories across the turn tree and consolidates their current staged and working-tree changes. It explicitly runs the shared secret scanner and repo `scripts/check-fast.sh` when present before committing the validated tree. Ordinary commits use `hooks/git/pre-commit`; all ordinary pushes use `hooks/git/pre-push`. See [secret-publication.md](secret-publication.md) for the pinned scanner, false-positive policy and recovery. Tracked branches push optimistically and rebase only when the remote is ahead; new branches establish upstream tracking. Successful `main` publication sends a bounded best-effort revision notification to Mac Mini production automation. Builds remain outside the hook; periodic reconciliation recovers failed notifications. Timing lives in `~/.local/state/agents-control-plane/log/hooks-stop.log`.
