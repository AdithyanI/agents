# Modal Credential Delivery

Use `$secret-management` when adding or changing a runtime secret. The
logical shared DobbySecrets store owns enrolled stable values across the Mac Mini,
MacBook and ASUS peers. Modal Secrets and local credential files are generated
deliveries. Follow shared-policy activation/readiness evidence before assuming a
peer can supply the complete payload. Existing Modal resources keep their names.
Scoped deployment credentials and manifest-selected values are generated onto
ASUS from its ready local peer store during provisioning or rotation. The existing ASUS queue deploys Modal
directly from those private files; it does not call the Mac at release time.

## Stable Runtime Secrets

1. Identify the existing local scope/key with `~/GitHub/scripts/bin/local-secrets`.
   Do not print values or treat generated `.env` files as another source of truth.
2. Add or update the payload mapping in WIN's
   `scripts/modal/secrets/modal_secrets_manifest.json` and ensure its backing
   canonical value exists before release.
3. Update the owning runtime/config documentation when expected keys change and
   refresh the scoped ASUS delivery using shared `scripts` provisioning tooling.
   The complete manifest must resolve from that generated delivery before release.
4. Validate the mapping and sync helper locally. During an authorized release,
   the ASUS queue runs WIN's `scripts/modal/deploy.py` in Docker using Python 3.13
   and the shared lock. It consumes the generated credentials and synchronizes
   Modal Secrets after release checks pass and before code deployment. Verify
   the structured result and deployed target revision; a Git publication is not
   proof of secret or code activation.

For deliberate adoption of an older Modal-only secret, use the canonical
`local-secrets set` flow once. Preserve separately owned, ephemeral or externally
rotated secrets as explicit exceptions instead of overwriting their owner.

The sync helper is
`win/scripts/modal/secrets/sync_local_to_modal_secrets.py`. Inspect its current
CLI and the runtime reference before invoking it; syncing mutates Modal's
runtime credentials. Do not make live changes for a documentation-only task.

## Recovery

- A missing canonical value stops provisioning; a missing generated value or
  failed sync stops release before code deployment. Fix the canonical source
  and refresh its delivery instead of hand-editing ASUS files.
- Do not publish secret values, generated credentials or signed URLs in logs,
  test artifacts, project evidence or Git.
- Keep old deployment recovery available during migration, but route ongoing
  credential updates through the one active WIN manifest and publisher after
  cutover. Never run competing secret publishers for the same Modal app.
