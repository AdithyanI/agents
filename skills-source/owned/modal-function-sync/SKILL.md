---
name: modal-function-sync
description: Implement or update WIN's Modal functions, registry, generated client, and release integration. Use for new Modal functions or pipelines, caller contract changes, or maintenance of the consolidated WIN/Modal runtime.
---

# WIN Modal Integration

WIN owns both the backend and the Modal runtime. Use the official `$modal` skill
for platform APIs and patterns; this skill owns repository integration and
delivery. Keep current processing behavior, model choices, remote names and
storage contracts unless the task explicitly changes them.

## Start Here

Read WIN's `AGENTS.md`, `docs/references/modal-runtime.md`, the affected function
and its tests. Source is under `win/modal_runtime/`; the sibling
`modal_functions` checkout retains pre-consolidation history and recovery code.
Do new implementation in WIN. The
[archived migration](../../../../win/docs/projects/archive/modal-consolidation/tasks.md)
records the verified ASUS-to-Modal release and recovery evidence.

## Implement and Sync

- Keep one canonical implementation under `modal_runtime/functions/` or the
  existing runtime domain. Shared runtime helpers live in `modal_runtime/common/`.
- Add deployed symbols to `modal_runtime/deploy.py` and exposed caller contracts
  to `modal_runtime/registry.py`. Preserve the `aip-processor` app and existing
  function, class, Volume and Secret identities across source moves.
- Keep imports safe during local deployment and inside containers. Model/GPU
  dependencies belong in their image or function lifecycle, not backend imports.
- Generate `services/modal/client_generated.py` with
  `scripts/modal/sync-client.sh`; never edit generated output directly.
  `scripts/modal/check-client.sh` checks drift without changing it.
- Backend I/O, caching, retries and ergonomic wrappers remain in
  `services/modal/client.py`. Workflow decisions remain in `core/`.
- A source move does not authorize changing workflow placement or concurrency.
  For intended execution changes, explicitly model parallel inputs, retry
  ownership, persisted outcomes and cancellation instead of adding an implicit
  scheduler.

## Credentials

Use `$secret-management` and [references/modal-secrets.md](references/modal-secrets.md)
when credential delivery changes. Stable runtime secrets belong in the
logical shared `DobbySecrets` store and WIN's
`scripts/modal/secrets/modal_secrets_manifest.json`. Modal Secrets are generated
runtime copies. Preserve existing names and avoid unmanaged manual updates.
Provisioning and rotation generate only the selected runtime values and Modal
deployment credentials from the ready ASUS peer's store. Stable source values
follow the three-peer writable policy; release uses generated delivery directly
and no Mac call occurs during a Modal release. Runtime OAuth/session state is separate.

## Validation and Delivery

Use `scripts/local/bootstrap_python.sh` to create WIN's shared `venv`; use
`venv/bin/python` for both backend and Modal tooling.
Run registry validation, client drift checks and affected tests. The existing
root `scripts/check-fast.sh` and `scripts/check-full.sh` own integrated gates;
run these on the development Mac and keep full suites proportional to the change.
ASUS deployment runs source/credential preflight and provider proof, never the
test suite, linter or type checker.

Develop on the MacBook or Mini and publish WIN. The existing ASUS queue deploys
both targets directly. Its `~/GitHub/scripts/setup/asus/deploy-modal.py` wrapper
uses the queue's immutable WIN checkout and runs `scripts/modal/deploy.py` in a
small Python 3.13 submission container constrained by the shared lock. It validates the exact revision
and generated credentials, synchronizes Modal Secrets, deploys and records
target-specific evidence.
Do not infer activation from a Git push alone or bypass the coordinator with
bare `python -m modal_runtime.deploy`. Do not run both legacy and consolidated
publishers for the same app. Respect another task's storage maintenance lock.

See [references/paths.md](references/paths.md) for the small set of integration
entrypoints; the owning source and runtime reference remain authoritative.
