# Agent-Native Multi-Client Control Plane

## Goal

Re-establish `~/GitHub/agents` as a client-neutral, cross-repository control
plane that can bootstrap Codex and Claude Code side by side without duplicating
canonical guidance or capability sources.

The result should make Claude Code a first-class client, not a compatibility
afterthought, while preserving the current Codex behavior. Neither client is
architecturally primary. A machine or repository may enable either or both.

## Why This Project Exists

The repository previously supported this model twice: first as sibling
`codex/` and `claude/` control planes, then as a lighter shared-core design with
client-specific renderers. Claude support was removed on September 18, 2026 as
an explicitly authorized product simplification, not because the shared model
was shown to be unsound.

That decision has changed. Claude Code is active again and is expected to carry
an increasing share of development work. The control plane therefore needs to
restore portable agent capabilities without reviving stale runtime assumptions.

The detailed audit and proposed shape are in
[`resources/architecture-audit.md`](resources/architecture-audit.md).

## Definition Of Agent-Native

A managed repository is agent-native when a fresh supported client can:

- discover the right global, root, and nested instructions without prior chat
  context;
- discover only the skills, tools, and MCP servers intended for that repository;
- run the relevant build, test, preview, and delivery workflows non-interactively;
- receive deterministic lifecycle feedback and recover from failures;
- preserve user-owned settings, credentials, sessions, and unrelated runtime
  state;
- explain which source owns every generated surface and how to regenerate it;
- verify that bootstrap is complete and idempotent; and
- work in a sparse checkout or on another enrolled machine without treating the
  current `~/GitHub` directory listing as canonical truth.

## Current State

- `~/GitHub/agents` at `ad4702e4` is the documented canonical source checkout.
- `~/.agents` is still a separate clean Git checkout at `6accc7ca`, with a
  different remote and pre-retirement multi-client code. Its old scripts and
  configs remain runnable even though current docs describe `~/.agents` as only
  a runtime skill-link surface. This split authority must be resolved safely.
- Claude Code `2.1.220` is installed and has active runtime/session state.
- Current Claude Code has no managed global guidance or skill links, and the
  locally present Git repositories have no managed `CLAUDE.md` or
  `.claude/skills` surfaces.
- The current root bootstrap and check run `scripts/retire-agent-clients.py`.
  Its dry run currently plans to update `~/.claude.json` and remove
  `~/GitHub/adi/.claude/settings.local.json`, which contains a current local
  permission. Restored Claude configuration would be pruned again until this
  retirement path is changed.
- The neutral spine still exists: `config/global.agents.md`,
  `skills/registry.json`, `mcp/config/presets.json`, `hooks/registry.json`,
  `dev-servers/registry.json`, shared Git hooks, and the root bootstrap/check
  entrypoints.
- `codex/config/repo-bootstrap.json` currently mixes the shared repository
  inventory with Codex-only settings. It declares 31 repositories; 19 are
  present Git repositories on this machine, 12 are sparse/absent, and
  `modal_functions` is intentionally excluded. The filesystem is evidence for
  drift, not enrollment authority.

## Target Principles

- Share intent and source content; render native client artifacts.
- Keep one canonical repository identity and capability-assignment model.
- Give repositories stable IDs; treat checkout paths as deployment locations.
- Make client enablement explicit and symmetric. Do not make Codex mandatory or
  silently enable every future client.
- Keep models, effort, provider choice, authentication, sessions, and private
  local overrides owned by their client/runtime.
- Merge only fields the control plane owns. Never replace complete mutable
  settings or state files.
- Keep client-native plugin ecosystems separate. Promote a capability to the
  shared layer only when it has a real standalone skill or MCP representation.
- Do not force false parity. Hooks, subagents, previews, and session finalizers
  may share intent while retaining different implementations.
- Prefer a clean forward reconstruction over reverting either historical Claude
  implementation wholesale.

## Completion Criteria

- One neutral repo registry drives both clients, using stable repo IDs and
  explicit client enablement.
- Existing Codex global and repository outputs remain behaviorally equivalent;
  migration tests prove expected files are unchanged where their contract did
  not change.
- Claude receives the canonical global guidance, repository `AGENTS.md`
  hierarchy, scoped standalone skills, assigned MCP servers, and approved
  lifecycle hooks through current native surfaces.
- Root bootstrap, post-sync reconcile, checks, drift audit, and dashboard all
  understand both clients and work when one client is intentionally absent.
- Bootstrap never modifies client credentials, conversation history, runtime
  databases, `settings.local.json`, or unknown settings.
- Apply is idempotent and ownership-aware; disabling a client removes only
  outputs previously owned by its renderer and preserves recoverable backups for
  material migrations.
- Side-by-side Codex and Claude sessions cannot accidentally finalize or commit
  each other's unowned changes.
- One pilot repository passes source validation plus real Codex and Claude
  startup/capability smoke tests before wider rollout.
- The stale `~/.agents` source checkout is either retired or deliberately
  redefined, leaving exactly one canonical control-plane checkout.

## Milestones

1. **Safety and authority**
   - Stop the active retirement migration from pruning supported Claude state.
   - Resolve the `~/GitHub/agents` versus `~/.agents` source split.
   - Freeze current Codex rendered outputs as a regression baseline.
   - Set and verify the minimum supported Claude Code version.
2. **Neutral repository and capability model**
   - Move shared repository identity out of the Codex subtree.
   - Add stable repo IDs and explicit client enablement.
   - Update skill, MCP, hook, Git-hook, preview, dashboard, and drift consumers
     to resolve the same identities.
3. **Minimal Claude adapter**
   - Render global guidance without overwriting mutable Claude state.
   - Materialize the shared skill registry into Claude's native skill paths.
   - Render assigned MCP definitions into Claude's native project/user scopes.
   - Merge a narrowly owned Claude settings overlay while preserving user keys.
   - Pilot in `agents`; expand only after direct inspection.
4. **Lifecycle integration**
   - Restore normalized Claude payload adapters for safe shared repo hooks.
   - Start with `SessionStart` and `UserPromptSubmit` where useful.
   - Design and prove Claude Stop/finalization attribution separately before
     enabling automatic Git delivery.
5. **Operations and rollout**
   - Wire Claude into root bootstrap, auto-apply, checks, and drift audit.
   - Show effective per-repo/per-client capabilities in the dashboard.
   - Roll out to selected repositories, then both machines.
6. **Optional native extensions**
   - Add shared role intent with native Codex/Claude subagent definitions only
     for roles that are repeatedly useful.
   - Evaluate Claude plugins, preview launch surfaces, session maintenance, and
     cloud/Cowork distribution independently rather than assuming parity.

## Current Batch

| Status | Work | Evidence |
| --- | --- | --- |
| complete | Recover both historical coexistence designs and the retirement rationale | Git history through `d216ee40`, `a9bb8c7c`, and `bad2bb6b` |
| complete | Audit current canonical sources and live Codex/Claude runtime state | `resources/architecture-audit.md` |
| complete | Check current official Claude Code surfaces relevant to the design | Official docs links in the audit |
| in_progress | Review the target architecture and implementation boundaries with Adi | This tracker |
| pending | Implement Milestone 1 safety and authority changes | Not yet authorized in this documentation pass |

## Decisions To Review Before Implementation

- Minimum Claude Code version: upgrade to at least `2.1.277` and use native
  `AGENTS.md` discovery, or maintain a temporary generated `CLAUDE.md` import
  bridge for older installations. The clean target is the version floor.
- Claude permission posture: preserve normal client defaults or restore a
  managed permissive/bypass profile. This is client policy, not shared intent.
- Initial rollout: `agents` only is the recommended pilot; `adi` should follow
  after identity-prompt behavior and cross-client Git attribution are proven.
- Whether custom subagents belong in the first restoration. They are useful but
  not required for guidance/skills/MCP parity.
- Whether any Claude Desktop, Cowork, or cloud-session behavior belongs in this
  project. The initial target should be local Claude Code unless expanded.

## Resume Point

Review the architecture audit and the decisions above. Once accepted, begin
Milestone 1 only: remove Claude from the active retirement path, resolve the
duplicate source checkout, establish version policy, and capture a byte-for-byte
Codex baseline before adding new Claude outputs.
