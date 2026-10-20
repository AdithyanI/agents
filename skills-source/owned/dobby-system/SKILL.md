---
name: dobby-system
description: Orient Dobby changes that cross repository boundaries or affect person-workspace identity, private data, memory placement, engine/gateway ownership, host authority, or machine operations. Use when deciding which Dobby layer owns a change.
---

# Dobby System

This is the canonical cross-repo orientation for Dobby. Use it when ownership or routing matters; local implementation facts belong in the owning repo's source and relevant docs.

## Ownership

| Repo | Owns |
| --- | --- |
| `~/GitHub/adi`, `~/GitHub/angie` | Separate person workspaces: constitution, memory, journal, person prompts, workspace hooks, and `./bin/dobby` shim |
| `~/GitHub/dobby` | Shared CLI/engine, dashboard source, shared behavior, storage contracts, and default prompts |
| `~/GitHub/dobby/services/documents` | Document corpus, catalog, extraction, authenticated API and packaged client; ASUS owns the canonical corpus at `/srv/storage/documents`, and raw documents stay outside Git |
| `~/GitHub/dobby/services/photo-search` | Authenticated photo/video search API, indexed annotations and agent client on ASUS; Immich owns originals, metadata and asset authorization |
| `~/GitHub/dobby-gateway` | HTTP front door, assistant runtime routing, bearer auth, shared client contracts, and gateway service behavior |
| `~/GitHub/dobby-ios` | iOS app, SwiftUI, and iOS build/deploy/TestFlight tooling |
| `~/GitHub/agents` | Shared Codex configuration, skills, MCP/plugin registries, and lifecycle distribution |
| `~/GitHub/scripts` | Machine bootstrap, launchd/scheduler wiring, and thin wrappers around owner-repo entrypoints |

## Person and Runtime Boundaries

- Folder identity matters: an agent in `adi` operates in Adi's workspace; one in `angie` operates in Angie's. Keep their repositories, private data, and writer histories separate.
- Workspaces hold identity and data, with `./bin/dobby` pinning the workspace and calling the shared engine. Do not copy engine implementation into workspaces or hardcode person paths in shared code; resolve `DOBBY_WORKSPACE` or the workspace marker.
- Gateway and product clients consume workspace-bound CLI/API contracts. Do not read private memory, SQLite, or legacy JSON directly from another product.
- Private corpus, memory, and artifact content stays in the person's workspace or its explicitly configured data store, not in engine, gateway, iOS, agents, or public/content repos.
- Session summaries, metadata and small readable dialogue stay in the person workspace. Full runtime transcripts may live in its configured private S3 archive, referenced by integrity-checked records in Git. The engine owns capture and authenticated retrieval; scripts owns storage provisioning, credential delivery and backup. Do not route conversations through the public media uploader or put archive logic in the agents dispatcher.
- Apply the existing [object-storage lifetime policy](../media-storage-lifecycle/SKILL.md) to private data too: retained transcripts and Git recovery use `permanent/<person>/...` within the configured private store. Lifetime prefixes do not grant public access; keep person isolation and authentication separate from retention.
- Documents and photos are explicit domain bridges. The engine exposes `dobby documents` and `dobby photos`, delegating to the domain-owned clients rather than duplicating API, authentication or indexing behavior. Each workspace selects its endpoint and generated credential-file path; photos also require an explicit library. Do not infer a person's corpus from machine-wide credentials or another workspace.
- Original and generated documents belong in the existing Documents library, outside workspace Git. Keep context plus stable document IDs and SHA-256 references in the person workspace; retrieve originals through its configured Documents client. Functional UI assets and source code are not document originals or exports.
- Routine document/photo/video lookup uses the authenticated APIs from any configured agent machine; it does not require SSH to ASUS, mounted storage or local indexes. Scripts owns client provisioning and generated credential delivery from the shared secret store. Missing setup or failed API access must not silently fall back to another person, host or corpus. Exact command and configuration contracts live in engine `docs/references/documents.md` and `docs/references/photos.md`.
- Health uses engine-owned SQLite at `~/Library/Application Support/Dobby/health/health.sqlite`, with `person_id` isolation. Access it through workspace-bound Dobby commands or gateway responses. Workspace health JSON is import/audit/backup material.
- Shelf and cinema watch lists use the engine-owned authenticated live-state service on ASUS. Configured workspaces, jobs and dashboards read and write the same person-isolated authority through `DOBBY_STATE_ENDPOINT`; service or token failures must not fall back to retired local state. Local SQLite remains only an explicit local/development mode, and workspace `state/shelf.json` is legacy import/audit material.
- Live launchd plists are machine-local runtime state. `scripts` owns installers and scheduling wrappers; real domain behavior stays with its owner.

## Workspace Context When Needed

For workspace shape or person-data placement, read that workspace's `docs/body-map.md`. For memory writes, use `~/GitHub/dobby/docs/agent-write-recipes.md`: CLI-owned journal, Shelf, sessions, dreams, calendar, and mail writes go through `./bin/dobby`; direct files are limited to documented shapes.

The constitution at `dobby/constitution.md` supplies identity and behavior. It is declared once as `model_instructions_file` in the shared repo registry and loaded through generated Codex config. Session-start cards are separate bounded orientation, not another constitution source; lifecycle details belong in the engine docs.

Area `canon.md` holds durable conclusions; declared area data directories hold normalized source material. Raw exports remain inputs/backups, reflections go in `journal/`, and personal open loops go in Shelf. Area `log.jsonl` files are retired.

Visible artifacts belong under `memory/areas/<area>/artifacts/<slug>/`. Dashboard `index.html` and optional `book.json` are independently authored expressions; do not derive one from the other. The engine owns the book toolkit and `dobby artifact export`; use its `docs/artifacts.md` for the contract and the workspace body map for placement.

## Changing a Boundary

Change each owning layer directly. Update this skill only when cross-repo ownership, routing, privacy, or host authority changes; do not duplicate feature-level docs here. Keep repo guidance useful for local routing and avoid duplicate operational READMEs.

Run affected owner-repo checks according to local guidance. Shared engine behavior also needs a real workspace smoke when relevant. A docs-only change does not require running every Dobby repository's suite.
