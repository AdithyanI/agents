---
name: secret-management
description: "Manage shared stable credentials in DobbySecrets and keep rotating authentication state with its runtime owner. Use for credential naming, three-peer sharing, generated repo/runtime files, provider delivery, and validation without exposing values."
---

# Secret Management

## Overview

Use this skill to answer three questions:

1. Which lane owns this secret?
2. Which files, names, and validation steps must change?
3. How should the secret be documented so future agents do it the same way?

Read [references/decision-guide.md](references/decision-guide.md) for the concrete matrix, examples, naming rules, and file targets.

## Shared Policy

Stable enrolled credentials use one logical `DobbySecrets/scopes/shared` store
across the Mac Mini, MacBook and ASUS. The selected v2 policy makes all three
peers writable through `bin/local-secrets` with send/receive synchronization;
there is no permanent source/mirror role. Git carries code, guidance and mappings,
not values. Check the scripts repo's `docs/references/shared-api-credentials.md`
for activation evidence before assuming a peer is ready.

Mappings and explicit source sets select shared names and local consumers. Existing
Mac tool outputs remain Mac-only. Materialization requires the selected local
values and conflict-free readiness; conflicts preserve outputs and need explicit
resolution. Rotating OAuth/session credentials and Google user ADC retain their
existing runtime owners and are excluded from stable-value replication.

## Workflow

1. Identify the secret's primary consumer.
   - Running app on its declared host or external provider
   - Local development in one repo
   - Shared operator tooling across repos on one machine
   - GitHub Actions only

2. Pick one primary lane.
   - Avoid giving the same secret family multiple hand-maintained homes.
   - If the value must appear in another lane, generate it from the same local canonical value instead of inventing a second owner.

3. Apply the lane-specific changes.
   - Use the checklist in [references/decision-guide.md](references/decision-guide.md).

4. Update durable docs when the pattern is new.
   - Prefer repo docs/reference updates over ad-hoc chat-only explanations.

## Lanes

### Runtime

Use for deployed application secrets.

- Enroll stable shared values under
  `~/Documents/DobbySecrets/scopes/shared/<secret-name>` on the authorized peers.
  Keep mutable authentication state in its owning runtime lane.
- Wire the value through the owning runtime's actual materialization contract. Current Mac Mini
  services use repo mappings plus generated `.env` files and repo-owned deploy/restart commands.
- Use provider-native references or deploy-time sync only for a runtime that actually supports and
  consumes them; do not recreate retired cloud-host settings.
- If local repo development also needs the value, use the same canonical secret family in its generated
  `.env` rather than creating another owner.

### Repo-Local

Use for secrets needed in one repo's local development workflow.

- Keep the value canonical in the local store.
- Map it into the repo's local bootstrap (`secret_env_map.env` or equivalent).
- Keep `.env.example` as placeholder-only documentation.

### Machine-Local Shared

Use for credentials shared across repos on one machine for operator tooling.

- Keep the value canonical in the local store.
- Sync it to `~/.secrets/<integration>/...`.
- Source it from shell bootstrap only as a generated machine-local file.
- Do not store secret values in `~/GitHub/agents`, `~/.agents`, or tracked shell config.

### External Runtimes And GitHub CI

Use provider-owned secret storage as a generated delivery target. Stable source
values remain in the logical shared store.

- Keep GitHub Actions secrets limited to intentional cloud-runner delivery or CI-only credentials.
- Use the existing deployment owner for the workload.
- For Modal or another external runtime, use an explicit manifest. Provision scoped
  generated credentials on its release host from that peer's shared store, refresh
  them on rotation, and let that host deliver the selected provider values. WIN's ASUS
  Modal publisher consumes this delivery without a release-time Mac call.
- Do not make a cloud-vault login a bootstrap dependency for new local workflows.

## Naming Rules

- Repo-owned secret families: `repo--secret-name`
- Shared integration families: `integration--secret-name`
- Machine-local integrations: match the folder name under `~/.secrets/<integration>/`
- GitHub secret names should be explicit about purpose, not repo history

## Guardrails

- Do not add a new secret to GitHub Actions just because it is convenient.
- Do not put literal secret values in `.zshrc`, tracked YAML, or committed config files.
- Do not create a machine-local integration when repo-local bootstrap is the real fit.
- Treat file-based credentials as a separate case; they may need materialization, not `KEY=value` sync.
- Use `~/GitHub/scripts/bin/local-secrets` for reads/writes/import/status workflows; never print
  secret values in logs or agent responses.
- Keep store files untracked with `0700` directories and `0600` files. Preserve
  existing Mac Backblaze coverage; follow the ASUS backup contract for Linux.
  Synchronization is not a substitute for backup or conflict recovery.
