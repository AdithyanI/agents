# Agent-Native Multi-Client Control Plane

## Goal

Re-establish `~/GitHub/agents` as a client-neutral, cross-repository control
plane that can bootstrap Codex and Claude Code side by side without duplicating
canonical guidance or capability sources.

The result should make Claude Code a first-class client, not a compatibility
afterthought, while preserving the current Codex behavior. Neither client is
architecturally primary. A machine or repository may enable either or both.
The clients do not need to use the same agent definition, persona, prompt stack,
or runtime features. They need equivalent ability to understand, change,
validate, and finish work in the repository.

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
- run a fast, deterministic, actionable repository gate before delivery, with
  slower verification kept in the repository's full-check path;
- receive deterministic lifecycle feedback and recover from failures;
- preserve user-owned settings, credentials, sessions, and unrelated runtime
  state;
- explain which source owns every generated surface and how to regenerate it;
- verify that bootstrap is complete and idempotent; and
- work in a sparse checkout or on another enrolled machine without treating the
  current `~/GitHub` directory listing as canonical truth.

## Audited Baseline — October 7, 2026

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
- Target operational parity, not agent-identity parity. Native agents, models,
  prompts, roles, and orchestration may differ between clients.
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
- Every managed repo exposes a quick local `scripts/check-fast.sh` or an explicit
  equivalent, and the shared Git hook plus both client workflows use that same
  repo-owned gate rather than duplicating validation logic.
- Native lifecycle events pass through client adapters into shared normalized
  repo-hook contracts, with actionable feedback returned in the form each client
  supports.
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
   - Make the existing fast-check contract directly discoverable and callable
     from both clients while preserving the shared pre-commit path.
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
7. **Harness improvement loop**
   - Use real Codex and Claude work to identify where agents lose context, stop
     early, run the wrong check, or cannot recover.
   - Fix each repeated failure in the smallest effective layer: source, tool,
     fast check, lifecycle adapter, skill, or guidance.
   - Keep useful cross-client improvements in the neutral core and leave
     client-native advantages in their owning adapters.

## Current Batch

| Status | Work | Evidence |
| --- | --- | --- |
| complete | Recover both historical coexistence designs and the retirement rationale | Git history through `d216ee40`, `a9bb8c7c`, and `bad2bb6b` |
| complete | Audit current canonical sources and live Codex/Claude runtime state | `resources/architecture-audit.md` |
| complete | Check current official Claude Code surfaces relevant to the design | Official docs links in the audit |
| complete | Receive implementation authorization | October 8: Adi asked Codex to do the shared work and leave native acceptance for a Claude Code session |
| complete | Stop automatic retirement of Claude setup | Normal bootstrap/check no longer invoke the explicit historical removal migration; preservation regressions pass |
| complete | Resolve the duplicate source checkout on this Mac | Archived to `~/.local/state/agents-control-plane/legacy-source/20261008T093508Z`; `~/.agents` now contains runtime skill links only; launcher/link references and three cleaner LaunchAgents reconciled |
| complete | Establish native AGENTS.md version floor | `claude/config/policy.json` requires 2.1.281; this Mac upgraded to 2.1.286 |
| complete | Introduce neutral repository identity and client selection | `repos/registry.json`; Codex projection exactly equals previous source; Claude enabled only for `agents` |
| complete | Add safe Claude context-hook adapters | SessionStart/UserPromptSubmit tests pass; Claude Stop rejected; no unnecessary live hooks enabled |
| complete | Render and apply the agents pilot | Eight outputs: global guidance, four global skills, two repo skills, and project MCP; check passes and second apply makes zero changes |
| complete | Integrate machine selection and operations | Claude requires local opt-in; absent Codex is skipped by shared orchestration; bootstrap, check, reconciliation and runtime audit support both clients |
| complete | Finish integrated source validation | `scripts/check-full.sh` passes, including 384 hermetic regressions; shared runtime checks, dashboard data and dashboard build pass |
| complete | Native Claude acceptance in `agents` | Claude Code 2.1.286 desktop session: global guidance and root `AGENTS.md` loaded; nested `docs/AGENTS.md` discovered on file access; four global and two repo skills listed; `openaiDeveloperDocs` MCP search returned results |
| complete | Confirm Claude skill discovery surface | Probe: a skill only in `.agents/skills` is not discovered; the same skill linked into `.claude/skills` is. Keep the `.claude/skills` renderer |
| complete | Claude turn finalization | `hooks/scripts/claude_tool_use.py` (PostToolUse) registers touched repositories per session; shared `stop.py --runtime claude` finalizes them plus the starting repo. Hooks are repo-scoped `*` and render only into Claude-enabled repos. Live session registration observed, including a subagent Bash call under the parent session_id. `test_claude_stop.py` is in the fast gate; full suite 389 OK |
| complete | Remove machine-specific absolute paths | About 90 `/Users/dobby` doc links became repo-relative; guidance and skills use `~/GitHub` or skill names; the fal-seedance mapping path resolves per machine |
| pending | First live Claude Stop publication | Expect `runtime=claude ok turn-repo-pushed` in `~/.local/state/agents-control-plane/log/hooks-stop.log` after the acceptance session's turn |
| pending | Wider rollout | `adi`, then the second machine; see Next Steps |

## Current Implementation Decisions

- Minimum Claude Code version: `2.1.281`, using native root/nested `AGENTS.md`
  discovery. No generated project `CLAUDE.md` bridge.
- Claude permission posture: Adi wants autonomous (bypass-permissions) agents.
  Permission mode stays a user-owned Claude setting; the control plane renders
  no permissions, provider, model, or credential changes.
- Initial rollout: `agents` only; `adi` follows once its Codex identity prompt
  (`model_instructions_file`) has a chosen Claude mapping.
- Cross-client Git attribution selects repositories; both clients then stage
  repository-wide, matching the shared-main-checkout contract. Concurrent
  sessions may publish each other's dirty files. This is accepted parity, not
  isolation.
- Native Claude plugins support project scope (`enabledPlugins` in committed
  `.claude/settings.json`, plus a per-machine install), but cloud sessions load
  neither user- nor project-enabled plugins. Not adopted: rendered skills and
  hooks already cover the need without skill-name prefixes or an install step.
  Revisit for sharing or cloud distribution.
- This Mac is opted in through `~/.local/state/agents-control-plane/claude/enabled.json`.
  Other machines remain opted out. Pilot project outputs are Git-ignored so
  source sync cannot bypass the machine gate.
- Custom subagents and native plugins are optional later extensions.
- Initial target is local Claude Code. Desktop, Cowork, and cloud-session
  behavior require separate acceptance.
- Which observed harness failures should seed the later improvement loop. Avoid
  designing a generic framework before side-by-side use supplies evidence.

## Next Steps

1. Confirm the first live Claude Stop publication in `hooks-stop.log`.
2. Enable `adi`: choose how its Codex identity prompt reaches Claude (project
   `CLAUDE.md` import, output style, or appended system prompt), confirm its
   fast gate, then enable Claude in `repos/registry.json` and reapply.
3. Second machine: install Claude Code >= 2.1.281, run
   `python3 claude/scripts/sync-claude.py --apply --enable`, then shared bootstrap.
4. Review Claude compatibility for global skills still marked Codex-only:
   `adi-design`, `find-skills`, `impeccable`, `pdf`, `secret-management`.
5. Convert remaining capability name/path assignments to stable repository IDs,
   add per-client capability presentation to the dashboard, and finish
   ownership-aware cleanup of disabled Codex outputs.
6. Cloud and Cowork sessions are deferred. They would need committed, portable
   `.claude` repo files (relative skill links, `.mcp.json`) instead of
   machine-rendered ignored outputs.
7. Keep optional native plugins/subagents and later harness improvements driven
   by real usage.

The project remains active until native acceptance and rollout criteria are met.

## Validation Evidence — October 8, 2026

- `scripts/check-full.sh` passes, including the fast source gate and all 384
  hermetic control-plane tests. Post-documentation hygiene and whitespace checks
  pass. Private local evidence is retained under
  `~/.local/state/agents-control-plane/claude/migration-evidence/20261008/`.
- Shared bootstrap applied successfully; Codex runtime validation covers 18
  present managed repositories.
- Compared 47 pre-migration Codex outputs: 29 remain byte-identical; 18 repo
  configs change only the comment pointing to `repos/registry.json`. Parsed
  configuration and guidance content are unchanged in all 47.
- Claude check passes and a second apply changes zero outputs. Machine-disabled
  and missing-client behavior, user-state preservation, conflict refusal,
  selective cleanup, and interrupted-write recovery have regression coverage.
- Runtime drift audit: zero errors and zero warnings.
- Dashboard data command and `npm run build` pass. The dashboard was built
  locally; production activation remains owned by existing delivery automation.

Native Claude acceptance (same day, Claude Code 2.1.286 desktop session):
instruction, nested AGENTS, skill and MCP discovery as recorded above; live
PostToolUse registration into the session transaction; fast gate passes;
`scripts/check-agent-control-planes.sh` passes with 389 hermetic tests and a
clean runtime drift audit.

Machine recovery evidence lives in the legacy archive's `migration-record.json`
and `karabiner-before.json`. Two skill links in the non-Git `whos-in-your-head`
remnant (`claude-api`, `azure-webapp-deploy`) were already dangling before this
migration; the archive preserves their references but contains no missing source
to recover. This does not affect the managed pilot.
