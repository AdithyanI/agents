# Modal Credential Delivery

Use `$secret-management` when adding or changing a runtime secret. The
machine-local canonical store remains the authority; Modal Secrets and local
credential files are generated deliveries. Consolidating source does not move
canonical secret ownership or require renaming existing Modal resources.

## Stable Runtime Secrets

1. Identify the existing local scope/key with `~/GitHub/scripts/bin/local-secrets`.
   Do not print values or treat generated `.env` files as another source of truth.
2. Add or update the payload mapping in WIN's
   `scripts/modal/secrets/modal_secrets_manifest.json` and ensure its backing
   canonical value exists before release.
3. Update the owning runtime/config documentation when expected keys change.
4. Validate the mapping and sync helper locally. During an authorized release,
   WIN's `scripts/modal/deploy.py` performs managed sync after release checks
   pass and before code deployment. Verify the structured result and deployed
   target revision; a Git publication is not proof of secret or code activation.

For deliberate adoption of an older Modal-only secret, use the canonical
`local-secrets set` flow once. Preserve separately owned, ephemeral or externally
rotated secrets as explicit exceptions instead of overwriting their owner.

The sync helper is
`win/scripts/modal/secrets/sync_local_to_modal_secrets.py`. Inspect its current
CLI and the runtime reference before invoking it; syncing mutates Modal's
runtime credentials. Do not make live changes for a documentation-only task.

## Recovery

- A missing canonical value or failed sync stops release before code deployment.
- Do not publish secret values, generated credentials or signed URLs in logs,
  test artifacts, project evidence or Git.
- Keep old deployment recovery available during migration, but route ongoing
  credential updates through the one active WIN manifest and publisher after
  cutover. Never run competing secret publishers for the same Modal app.
