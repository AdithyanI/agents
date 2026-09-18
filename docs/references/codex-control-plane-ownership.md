# Codex Control Plane Ownership

The [architecture overview](../architecture/codex-control-plane.md) explains the source/runtime split; [root guidance](../../AGENTS.md) maps canonical inputs. This reference records exceptions that matter when syncing or cleaning state.

| Location | Ownership |
| --- | --- |
| `~/GitHub/agents` | Shared Codex source, registries, templates, skills, hooks, and dashboard source |
| `~/.agents/skills` | Generated user-scope skill links; do not put a full checkout here |
| `~/.codex` | Applied config plus runtime-owned auth, conversations, snapshots, databases, vendor imports, and caches |
| repo `.codex/`, managed `.agents/skills/` | Generated behavior and links; real repo-local skills remain owned by that repo |
| `~/GitHub/scripts` | Generic machine bootstrap, shell glue, scheduling, SSH, and public service wiring |
| `~/.local/state/codex-control-plane/` | Machine-local provider selection, backups, reconcile and maintenance state |

## Boundaries Sync Must Preserve

- `~/.codex/vendor_imports/skills` is an app-managed nested Git checkout. Do not flatten it, move it into the canonical skill registry, or delete it as repository clutter.
- Authentication and session/runtime state stay out of this repository. `~/.codex` itself should not become a source-control home.
- Shared provider profiles are canonical, but each Mac's active Azure/subscription choice lives in `~/.local/state/codex-control-plane/provider`. Use the [provider switch](codex-provider-switch.md); do not commit the active choice as the shared default.
- For standalone profile files, only `tui.model_availability_nux` is runtime-owned model-picker onboarding state. Sync preserves it and drift checks exclude it; other profile settings remain managed.
- `config/global.agents.md` supplies global guidance. Global hooks render to `~/.codex/hooks.json`; assigned repo hooks render to `.codex/hooks.json`.
- Development preview ports come from `dev-servers/registry.json`. Public Cloudflare/LaunchAgent services remain owned by `scripts` and their applications.
- Dashboard source is tracked here; production serves a versioned release outside the checkout. A source change alone is not a deployment.

Use [shared operations](agent-control-plane-operations.md) for apply/check commands and [Codex operations](codex-control-plane-operations.md) for runtime recovery.
