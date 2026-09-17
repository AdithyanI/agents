# Agents Control Plane

This repo owns shared agent skills, client configuration, hooks, and their
reproducible distribution across MacBook and Mac Mini.

## Sources and routing

| Change | Canonical source | Detail |
| --- | --- | --- |
| Standalone skill content and scope | `skills-source/`, `skills/registry.json` | `skill-creator` skill; `docs/references/skills-registry.md` |
| Native Codex plugins | `plugins/registry.json` | `docs/references/plugins-registry.md` |
| MCP definitions and repo/client targets | `mcp/config/presets.json` | `mcp/AGENTS.md` |
| Lifecycle and Git hooks | `hooks/registry.json`, `hooks/scripts/`, `hooks/git/` | `docs/references/repo-lifecycle-hook-adapter.md` |
| Managed repos and identity propagation | `codex/config/repo-bootstrap.json` | `docs/references/codex-control-plane-operations.md` |
| Global guidance | `config/global.agents.md` | This repo owns the source; client guidance is generated. |
| Codex machine configuration | `codex/` | `codex/AGENTS.md` |
| Claude, Copilot, and VS Code overlays | `config/claude-settings.json`, `config/copilot-settings.json`, `config/vscode-agent-defaults.json` | `docs/references/agent-control-plane-operations.md`, `docs/references/copilot-control-plane-operations.md` |
| Agent-preview launch commands | `dev-servers/registry.json` | `docs/references/agent-control-plane-operations.md` |
| Read-only dashboard | `dashboard-app/`, `scripts/control-plane-dashboard.py` | `dashboard-app/AGENTS.md`, `docs/references/control-plane-dashboard.md` |

For Dobby ownership or cross-repo boundaries, use
`skills-source/owned/dobby-system/SKILL.md`. Keep implementation facts in the
owning repo. For architecture orientation use `docs/architecture/architecture-map.md`;
for docs placement use `docs/AGENTS.md`.

## Distribution boundaries

- Edit canonical sources, not generated client config or skill symlink destinations.
  Standalone skills are link-first; native plugins remain plugin entries.
- Keep global capability scope small and intentional. Native Codex plugin
  enablement is global/manual for this setup; use a standalone MCP target when
  one repo needs reliable MCP coverage without the whole plugin.
- Keep repo-local skills/plugins registered in their existing unmanaged lists.
  Existing local repos must contain the registered skill file. Do not create
  additional mapping manifests or copy skills into Copilot-specific skill folders.
- For a supplied upstream skill reference, use `scripts/bootstrap-skill.sh`.
  Refresh external skills deliberately; edit owned skills at canonical paths.
- `enabled_clients` controls generated surfaces; Codex is mandatory.
  `model_instructions_clients` narrows identity propagation and includes Codex.
  Keep model, reasoning, profile, and service-tier selection client-owned.
- Preview commands use `{repo_root}` to follow active checkouts. Machine service
  ports, launchd scheduling, and generic machine bootstrap belong in `~/GitHub/scripts`.
- Dashboard production serves a versioned external release. Preserve the
  source/build/runtime boundary and use its documented deployment command.
- Classify newly discovered bundled Codex skills in
  `codex/config/bundled-skills-policy.json`; do not leave runtime policy drift.

## Apply and verify

Use the shared wrapper for changes affecting multiple client surfaces:

```sh
./scripts/bootstrap-machine-agent-control-planes.sh --apply --repo /absolute/repo/path
./scripts/check-agent-control-planes.sh --repo /absolute/repo/path
```

Repo filters require exact paths. Omit the filter for changes that truly affect
all managed repos. Component scripts are for intentional single-surface work.

| Changed input | Required verification |
| --- | --- |
| Skill/plugin registries | Matching sync and check in the same change |
| MCP definitions or targets | Shared bootstrap/check; inspect every selected client surface |
| Hook registry/scripts, Git hooks, managed-hook sync | Shared bootstrap/check plus `scripts/test-control-plane.sh` |
| Codex global config or repo bootstrap | Codex control-plane validation; shared bootstrap for affected clients |
| VS Code defaults or renderer | `scripts/sync-vscode-agent-defaults.sh --check` and `scripts/test-control-plane.sh`; keep the scripts repo's reconcile caller aligned if CLI changes |
| Claude/Copilot overlays or preview registry | Re-render affected clients and check their resulting surfaces |

Fast local verification is `scripts/check-fast.sh`; keep that gate deterministic,
local, quick, and actionable. Broader verification is `scripts/check-full.sh`.
New agent-facing clients follow
`docs/references/cli-interface-contract.md`. Repo-specific lifecycle logic uses
the optional repo-owned Python hooks described in the lifecycle reference.

Keep detailed renderer behavior and recovery in the existing operations docs.
Update the owning contract when behavior changes; avoid repeating it across
global guidance, this router, and client references.
