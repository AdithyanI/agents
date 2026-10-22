---
name: media-storage-lifecycle
description: Use when adding, changing, reviewing, or cleaning media or object storage, including published website media, downloads, private conversation and recovery archives. Covers S3 cache/share/permanent lifetimes separately from public/private access, Modal artifacts and caches, browser uploads, provider-owned handoffs, ownership, expiry, reacquisition, replacement/deletion cleanup, and storage audits.
---

# Media Storage Lifecycle

## Purpose

Choose the shortest-lived storage boundary that satisfies the next real
consumer, and make ownership, expiry, replacement, and deletion explicit. This
skill is the cross-repo routing contract; implementation details remain in each
owning repository's docs.

The shared S3 provider is native Versity on ASUS. Public media uses bucket
`assets`, with public base `https://storage.aipodcast.ing/assets`; private
archives use their explicitly configured private bucket and scoped credentials.
Read `scripts/docs/references/asus-storage-services.md` for service ownership,
filesystem locations and recovery. Existing R2 originals are retained only for
deliberate recovery, not a runtime fallback. Verify the active cleanup
implementation instead of assuming the former R2 lifecycle rules still run on
native storage.

Unless Adi explicitly says otherwise, every S3 object key starts with one of
the existing lifetime prefixes: `cache/`, `share/`, or `permanent/`. Put the
person/product namespace beneath that prefix, not beside it. This applies to
private archives and recovery data as well as public media; do not invent a
parallel top-level storage scheme. Retention and access are independent:
`permanent/` means retained bytes, not public access. Retained conversations and
Git recovery belong under `permanent/<person>/...` in the configured private
store, never the public media uploader.

## Required Workflow

1. Read the active repo's `AGENTS.md` and the relevant storage references listed
   in [references/decision-guide.md](references/decision-guide.md).
2. Name the next consumer before choosing storage:
   - same process/container;
   - another Modal container;
   - WIN or another background job;
   - browser or HTTP-only provider;
   - user-facing deliverable;
   - durable product inventory; or
   - external provider that becomes authoritative.
3. Choose the first target in the decision table that satisfies that consumer.
4. Define an owner, stable key family and access policy for every S3 object.
   A lifecycle prefix alone establishes neither ownership nor public access.
5. Define what happens when the object expires, is replaced, or its owner is
   deleted.
6. Add focused proof for the selected boundary and update the owning repo's
   durable docs when behavior changes.

## Storage Decision Table

| Boundary | Use when | Required behavior |
| --- | --- | --- |
| Container-local file | Producer and consumer run in the same container invocation | Delete in `finally`; never serialize or return the path remotely |
| Modal internal artifact | Another Modal container or bounded retry needs the bytes | Use typed `MediaArtifactRef`; validate capability/manifest; let the 72-hour artifact lifecycle or exact run cleanup remove it |
| S3 `cache/` | A browser, independent caller, background job, or HTTP-only consumer needs a temporary handoff | Persist provenance; validate before reuse and reacquire or regenerate when missing; expose publicly only if the consumer requires it |
| S3 `share/` | A deliberately time-bounded, user-facing or cross-machine deliverable must outlive ordinary cache | Require a named product owner and documented expiry; never use as an unowned processing default |
| S3 `permanent/` | Canonical inventory, retained product assets, conversations, or recovery evidence | Use an owner-stable key and authoritative reference; preserve intended private access; define deliberate replacement/deletion rather than cache expiry |
| Provider-owned storage | Ghost, YouTube, Transistor, Frame.io, or another destination accepts and owns the final bytes | Upload directly where possible; persist the provider identity needed by the product; do not retain a duplicate S3 final without a separate consumer |

Use local or Modal-internal storage for every intermediate in an all-Modal
subgraph. Materialize publicly only at the first consumer that genuinely needs
an HTTP URL.

WIN orchestration and asynchronous job boundaries can pass persisted artifact
references without reading the bytes. They do not alone justify publication.
Keep Source identity/provenance separate from temporary location; link through
the existing artifact cache rather than storing Modal URIs in HTTP URL fields.
Background uploads still transfer the same bytes: select retained outputs
explicitly. Native S3 is still an outbound destination for Modal regardless of
whether the Mac or ASUS hosts it.
Read WIN's `docs/references/modal/media-transfer-policy.md` for dated billing facts
and WIN's `docs/architecture/media-source-identity-and-storage.md` for Source
identity and acquisition contracts. Use the owning repo docs and current
deployment evidence to determine rollout status.

## Ownership And Cleanup Rules

- Site-owned public media collections and downloadable files use the existing
  ASUS-hosted S3 `assets` bucket under `permanent/`, with stable URLs in site
  source. New site-owned keys use `permanent/sites/<hostname>/<purpose>/...`;
  preserve established permanent keys when they already serve the consumer.
  The site owns retention, replacement and deletion. Functional UI assets such
  as icons, fonts and component specimens may stay with the site source.
- Static hosting and media storage are separate choices. A move to Cloudflare
  Pages keeps published media in S3 rather than copying it into Git or Pages
  build output. Record the accepted dependency: Pages can serve the site during
  a home outage while linked ASUS media remains dependent on home connectivity.
- Generic public uploads default to `cache/`; `share/` and `permanent/` require
  an explicit owning workflow. Internal consumers use internal artifacts.
- Lifetime prefixes apply within private buckets too. Never publish private
  bytes merely to reuse a public helper, or skip the lifetime prefix because
  the bucket is private.
- Browser APIs expose purpose/upload intents, not raw lifecycle-folder choice.
- Every durable key should identify its owner, for example
  `permanent/ads/<source_id>/...` or
  `permanent/channel-assets/<channel>/...`.
- Replace safely: commit the new authoritative reference first, then delete the
  previous exact managed object only when no other record shares it.
- Delete completely: remove dependent records/configuration and the exact owned
  object; missing media is an idempotent no-op.
- If post-commit cleanup fails, keep the new reference valid, log the orphan,
  and let inventory reporting detect it. Do not roll back to a dead URL.
- A `cache/` or `share/` URL stored in Mongo is never durable merely because the
  string remains. Active work must validate it and reacquire, regenerate, or
  fail with a clear re-upload requirement.
- Preserve original provider/source provenance whenever temporary storage may
  expire.
- Never bulk-delete from a prefix without resolving its exact candidate set and
  protected references first. Record before/after counts and bytes for approved
  destructive cleanup.

## Repo Routing

- For Modal entrypoints or artifact contracts, also use `$modal-function-sync`.
- For WIN public job or generated frontend contracts, read WIN's
  `docs/references/api-endpoint-implementation.md`.
- Keep cross-repo decisions here; keep exact functions, schemas, paths,
  retention configuration, and commands in the owning repo docs linked from
  the decision guide.
- Put deterministic inventory, orphan detection, and lifecycle validation in
  the owning repository's scripts/checks. A skill teaches the workflow; it is
  not the enforcement mechanism.

## Validation Checklist

- The selected target matches the next consumer and no earlier public boundary
  remains.
- No new function or browser upload defaults to `share/` or `permanent/`.
- Expiring references have validation and recovery behavior.
- Replacement and deletion tests prove ordering and shared-reference safety.
- Provider uploads prove that no unnecessary S3 final copy is created.
- Scheduled cleanup covers new Modal cache namespaces and abandoned multipart
  uploads when applicable.
- Storage behavior is recorded in durable architecture/reference docs, not only
  an active project tracker.
