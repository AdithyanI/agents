# WIN Integration Paths

These paths are relative to `~/GitHub/win`.

| Responsibility | Entry point |
| --- | --- |
| Orientation and runtime contract | `AGENTS.md`, `docs/references/modal-runtime.md` |
| Active consolidation and cutover evidence | `docs/projects/modal-consolidation/tasks.md` |
| Functions and shared runtime helpers | `modal_runtime/functions/`, `modal_runtime/common/` |
| Exposed caller contracts | `modal_runtime/registry.py` |
| Modal deployment registration | `modal_runtime/deploy.py` |
| Registry validation and client generation | `tools/modal/validate_registry.py`, `tools/modal/generate_modal_client.py` |
| Same-repo generated client | `services/modal/client_generated.py` (generated; do not edit) |
| Backend transport, cache and retry integration | `services/modal/client.py` |
| Client sync and drift check | `scripts/modal/sync-client.sh`, `scripts/modal/check-client.sh` |
| Shared local Python environment | `scripts/local/bootstrap_python.sh`, `venv/bin/python` |
| Exact-revision release and status | `scripts/modal/deploy.py` |
| Runtime credential manifest and sync | `scripts/modal/secrets/modal_secrets_manifest.json`, `scripts/modal/secrets/sync_local_to_modal_secrets.py` |
| Runtime regression tests | `tests/modal_runtime/`, `pytest-modal.ini` |
| Backend client tests | `tests/services/modal/test_client.py` |

The canonical secret store and machine/queue delivery tooling remain owned by
`~/GitHub/scripts`; use its `bin/local-secrets` interface and deployment
references. The `modal_functions` checkout is retained for history and recovery,
not as a second implementation location. Do not delete it or deploy from it
without accounting for the active cutover and recovery contract.
