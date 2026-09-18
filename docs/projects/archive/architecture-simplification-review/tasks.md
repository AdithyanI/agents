# Architecture Simplification Review

Status: assessment complete and archived, September 18, 2026. Recommendations below are not implemented migrations.

## Goal

Assess the 28 primary repositories for useful consolidation, unnecessary runtime or storage layers, and cloud transfer overhead. Recommend changes that fit Adi's workflow: shared main, overlapping parallel agents, autonomous execution, minimal documentation, and automatic deployment on main commits.

This is an assessment. Repository moves, database migrations, service shutdowns, and production deployment are not part of this review. Preserve personal/customer data and useful platform or security boundaries. Distinguish repository organization from deployable processes and real network hops.

## Recommendation

Consolidate tightly coupled product source selectively. First repair delivery and checks that resist an actively edited shared main. Most important request paths already use loopback, stdio, or local databases, so repository mergers mainly reduce coordination and duplicated implementation; runtime savings need separate evidence.

First product candidate: `win` + `aipodcasting`. Next: `dobby-engine` + `dobby-gateway`. Keep independent deployable processes where their resource, platform, or recovery needs differ. Avoid a portfolio-wide monorepo or a new universal orchestration framework.

## Coverage and Repository Decisions

All 28 primary repositories are represented below. This is a targeted source/configuration assessment, not an exhaustive code audit. Earlier inventory distinguishes these from caches, vendor copies, and secondary checkouts.

| Repositories | Recommendation and reason |
| --- | --- |
| `win`, `aipodcasting` | Strong merge candidate: one product with coupled generated UI/API contracts and sibling-checkout synchronization. Keep Next, API, and worker processes. |
| `modal_functions` | Could join the AIP product repository after the first merge. Keep Modal deployment, images, Linux dependencies, and burst/GPU compute. |
| `dobby-engine`, `dobby-gateway` | Strong second code-merger candidate. First fix engine revision/trigger coupling; combining Git history alone does not make releases coherent. |
| `futureoflife-podcast`, `thoughtforms-life` | Combine their Astro implementation with separate show data, branding, domains, and build targets. The review found 18 identical implementation/config files and five differing files. |
| `scripts`, `platform-ops` | Fold active platform utilities/inventory into their existing machine-operations owner in `scripts`; preserve history and update callers. Lower priority than delivery correctness. |
| `agents` | Keep the portable Codex control plane separate from machine services and applications. |
| `adi`, `angie` | Keep separate personal workspaces and data histories. They are identity boundaries. |
| `documents`, `home-automation` | Keep independent domain workflows. Documents has rebuildable search state; home automation already uses a one-shot local device CLI. |
| `dobby-ios` | Keep separate for now; current guidance describes a deprecation path. Avoid investing in a merge before its future is settled. |
| `local-transcription`, `litellm` | Keep shared services: multiple callers, provider credentials/routing, caching and recovery behavior earn these boundaries. |
| `adithyan-ai-videos` | Keep the composition workspace for now. It supplies a Git revision to a shared renderer, rather than owning WIN application state. |
| `aipodcasting-website`, `blog-personal`, `adi-design` | Keep distinct products/content ownership. Share genuinely duplicated release code; these static outputs are not a microservice request chain. |
| `aip-cognitive-revolution` | Keep the Ghost theme separate from the Astro podcast implementation. |
| `meeting-capture`, `stadia-macos-controller`, `focus` | Keep separate native/device responsibilities and permission/recovery boundaries. |
| `frontier-lab-intelligence`, `trenopoulospraxis`, `.github` | Keep: respectively parked research, an independent application with sensitive state, and an organization-profile repository. |

Supporting evidence: [WIN contract generator](/Users/dobby/GitHub/win/scripts/local/sync_aip_contracts.sh), [Modal client generator](/Users/dobby/GitHub/modal_functions/scripts/local/sync_win_modal_client.sh), [channel-specific publishing paths](/Users/dobby/GitHub/win/services/database/models/channel_model.py), [platform ownership split](/Users/dobby/GitHub/platform-ops/docs/architecture/home-object-storage-routing.md), and [iOS current direction](/Users/dobby/GitHub/dobby-ios/AGENTS.md).

## Changes Worth Doing First

1. **Make checks tolerate unrelated parallel edits.** WIN and Modal compare the entire working-tree diff before/after formatting, despite selecting particular Python targets. In a disposable fixture, an unrelated `notes.txt` edit made each real checker exit 1 and falsely report Ruff changes; the Python target was unchanged. Scope change detection to formatter targets or use check-only output. Preserve actual lint/type/import checks. Sources: [WIN fast check, lines 64–75](/Users/dobby/GitHub/win/scripts/check-fast.sh), [Modal fast check](/Users/dobby/GitHub/modal_functions/scripts/check-fast.sh). Small change, reproduced defect.

2. **Fix Dobby's deployed engine dependency.** Dashboard production pins `DOBBY_ENGINE` to its release, while the shared deployment triggers omit engine `src/**` and `bin/**`. Gateway defaults to the mutable engine checkout. An engine-only change therefore need not refresh dashboard behavior, and gateway/dashboard can use different revisions. Add actual dependency paths and make the gateway's engine revision explicit. Sources: [service registry, lines 54–65](/Users/dobby/GitHub/scripts/sync/local-production-services.json), [dashboard runner, line 39](/Users/dobby/GitHub/dobby-engine/dashboard/scripts/run-local-production.sh), [gateway configuration, lines 96–106](/Users/dobby/GitHub/dobby-gateway/services/mobile-gateway/src/config.ts). Confirmed source mismatch; live version divergence was not measured.

3. **Deploy a captured published commit while agents continue editing main.** The shared reconciler rejects a dirty checkout before deployment, rechecks it after acquiring a lock, and reports failure if HEAD/worktree changes during deployment. Several owners also implement source/release/activation/rollback plumbing independently. Have the existing deployer consume an exact committed source snapshot, verify the built SHA, and retain app-owned health, drain, activation, and rollback behavior. Do not merely remove cleanliness guards while building from mutable source. Start with one owner, then reuse proven common primitives rather than replacing every deployer at once. Sources: [reconciler, lines 392, 462, 517](/Users/dobby/GitHub/scripts/sync/local-production-reconcile.py), [blog owner](/Users/dobby/GitHub/blog-personal/scripts/local_production.py), [design owner](/Users/dobby/GitHub/adi-design/scripts/deploy-local-production.sh). Medium/high migration cost; source-level friction, not a measured production-delay incident.

4. **Make delivery status useful to the agent.** Shared `local-production status --plain` prints an outer hardcoded `ok`, which can hide an owner's nested unavailable health. Stop-hook publication queues deployment asynchronously, so a successful Git push is not proof that a requested live change is serving. Preserve the asynchronous delivery model; expose published SHA, deployed SHA, health, and pending/failure in the existing status result. Sources: [shared status, lines 82–85 and 285–304](/Users/dobby/GitHub/scripts/bin/local-production), [blog status owner](/Users/dobby/GitHub/blog-personal/scripts/local_production.py), [Stop delivery notification](/Users/dobby/GitHub/agents/hooks/scripts/stop.py).

## Product Simplification After Those Repairs

For AIP, moving frontend and backend together removes cross-repo contract coordination. Modal source can follow if it simplifies ownership. Keep useful Python-to-TypeScript generation and independent deployment compatibility. WIN and Modal also maintain similar `MediaArtifactRef` models; colocating source may allow one small schema module. Preserve the Modal adapter's cache reuse, expiry checks, and idempotent dispatch. Evidence: [WIN model](/Users/dobby/GitHub/win/services/modal/models.py), [Modal model](/Users/dobby/GitHub/modal_functions/src/schemas/artifacts.py), [client behavior](/Users/dobby/GitHub/win/services/modal/client.py).

A smaller cleanup is already explicit in WIN: publish-workflow overrides remain solely to preserve old test monkeypatch locations. Update tests to the current owner and remove duplicate inherited behavior. Evidence: [compatibility comment at line 126](/Users/dobby/GitHub/win/core/orchestration/publishing/episode/episode_publish_workflow.py) and [base implementation at line 419](/Users/dobby/GitHub/win/core/orchestration/publishing/episode/episode_preparation_base.py).

Dobby's more consequential runtime issue is separate from repository layout: all Codex conversations share one queue and one active-turn slot. A long conversation can delay another person/conversation. Investigate sequencing per conversation while preserving steering, interruption, compaction, and recovery. Verify installed App Server concurrency before changing this contract. Sources: [runtime queue at lines 475–479 and 543–548; singleton at 1058](/Users/dobby/GitHub/dobby-gateway/services/mobile-gateway/src/codexBridge.ts). No contention-frequency measurement was taken.

## Actual Network and Storage Boundaries

Tracked defaults show:

- AIP UI → Next proxy → local WIN API → local Mongo job → worker → Modal or publisher. WIN → LiteLLM is also loopback. [AIP defaults](/Users/dobby/GitHub/aipodcasting/scripts/local/secrets/static_env_defaults.env), [WIN runtime](/Users/dobby/GitHub/win/docs/references/local-production-runtime.md).
- Dobby client → authenticated gateway → local Codex App Server over stdio. Dashboard chat uses a local gateway proxy; Shelf uses the local Python CLI and SQLite. [App Server spawn](/Users/dobby/GitHub/dobby-gateway/shared/codex-client/src/spawn.ts), [dashboard proxy](/Users/dobby/GitHub/dobby-engine/dashboard/server/chatApi.ts), [Shelf client](/Users/dobby/GitHub/dobby-gateway/services/mobile-gateway/src/shelfClient.ts).
- Media S3 is native Versity on the Mac Mini, backed by local files/xattrs. Local clients use loopback; external consumers use direct home HTTPS ingress. Cloudflare is DNS-only for this storage hostname. Older R2 objects remain recovery material. [Storage routing and recovery acceptance](/Users/dobby/GitHub/platform-ops/docs/architecture/home-object-storage-routing.md).

Keep Mongo for atomic job claims, retry checkpoints, and application records. Keep SQLite for Shelf/Health querying and concurrent CLI/dashboard/gateway access; it is already local file-backed state. Keep authored memory/documents/configuration as files. Local transcription already uses atomic job/result files for its bounded service. Removing a database name would not remove those coordination needs. Evidence: [Mongo claims](/Users/dobby/GitHub/win/services/database/job/writers.py), [SQLite configuration](/Users/dobby/GitHub/dobby-engine/src/dobby/local_store.py), [Shelf locking](/Users/dobby/GitHub/dobby-engine/src/dobby/shelf/store.py), [transcription files](/Users/dobby/GitHub/local-transcription/transcription/cloud/service.py).

One avoidable public route is confirmed in source: Dobby Withings sync hardcodes the public WIN endpoint even though WIN serves the authenticated route on its local API. Make the endpoint configurable and select loopback for a co-located caller; remote callers still need a reachable endpoint. This affects sync, not each dashboard page read. [Engine call, line 976](/Users/dobby/GitHub/dobby-engine/src/dobby/health/sync.py), [WIN route, line 147](/Users/dobby/GitHub/win/api/handlers/personal/withings_snapshot.py). No live configuration or latency was tested.

Do not replace S3 operations with direct file writes without preserving metadata, multipart/auth behavior, lifecycle ownership, and recovery. Independent backup/restore acceptance for the home object store remains unfinished in its owning record; protect retained recovery copies until that work is proven.

## Cloud Cost and Transfer Opportunities

Official Modal pages were fetched successfully on September 18, 2026:

- [Network egress billing](https://modal.com/docs/guide/network-egress-billing): charges start **October 1, 2026**; September is measurement-only, and the first bill including egress arrives **November 1, 2026**. Each billing cycle includes 1 TiB on Starter, 10 TiB on Team, or 100 TiB on Enterprise; excess is **$0.04/GiB**, once per workspace across environments. An additional 1 TiB above the allowance is $40.96. This is an illustration, not an account forecast.
- The same page excludes Modal Volume reads/writes from network egress. Uploading from Modal to the Mac, an external API/object store, or another container over a direct network connection still counts. Inbound downloads are ingress; caching dependencies primarily saves setup/runtime, not metered media egress.
- [Volume guide](https://modal.com/docs/guide/volumes) and [price card](https://modal.com/pricing): $0.09/GiB/month with 1 TiB/month included; daily storage snapshots can leave deleted data billable for up to four days. Account plan, credits, usage, and actual bill were not inspected.

Several good optimizations already exist: Modal keeps many intermediates internal; Transistor can receive final bytes directly from Modal; Deepgram fetches extracted audio rather than receiving a second upload through the local transcription service. Preserve these paths. Sources: [transfer policy](/Users/dobby/GitHub/modal_functions/docs/references/media-transfer-policy.md), [Transistor handoff](/Users/dobby/GitHub/modal_functions/src/functions/integrations/transistor/upload_audio/__init__.py), [transcription provider path](/Users/dobby/GitHub/local-transcription/transcription/cloud/service.py).

The next measured optimization candidate is Remotion cloud rendering: every invocation clones/fetches the requested revision and runs `npm ci` on a worker configured for 32 CPUs/64 GiB. Reusing lockfile-pinned dependencies or a prepared bundle may reduce repeated setup. Measure frequency, setup/render duration, and bytes before claiming savings. [Renderer, lines 18 and 90 onward](/Users/dobby/GitHub/modal_functions/src/functions/video/render_remotion_cloud/__init__.py). No paid render was run.

## Remaining Guidance and Check Cleanup

- WIN, Modal, LiteLLM, AIP frontend, gateway, and Stadia checks require a fixed docs directory skeleton. Remove directory-presence gates where no consumer needs them; keep useful docs and behavioral/link checks. Gateway's [tracker scan](/Users/dobby/GitHub/dobby-gateway/scripts/check-project-trackers.sh) also includes ignored scratch files: remove the name-placement gate or restrict it to tracked repo-owned project files.
- Globally available Impeccable still mandates some new-work confirmation, planning artifacts, and handoffs. A lighter owned workflow can preserve design craft without mandatory paperwork. [New-work recipe](/Users/dobby/GitHub/agents/skills-source/external/impeccable/reference/new-work.md).
- OpenAI Docs still contains a missing-MCP install/restart recipe despite its official-web fallback and canonical config ownership. Prefer the available fallback for a lookup; repair persistent tool configuration through its owner when required. This is a conditional instruction defect, not an observed MCP outage. [Skill source](/Users/dobby/GitHub/agents/skills-source/external/openai-docs/SKILL.md).
- Similar developer-instruction blocks exist for Adi and Angie, but private identity prompt dependencies were not inspected. Do not delete them merely because text repeats.

## Completion Evidence and Resume Point

- Three independent bounded reviews covered the product/media, Dobby, and supporting-app/operations groups. Parent review checked the major source claims and directly reproduced both formatter false failures in disposable fixtures; fixtures were removed.
- Refreshed official provider terms by direct public HTTP. No private records, credentials, live databases, health endpoints, provider jobs, deployments, or app migrations were accessed/executed. Current runtime overrides, real contention, transfer usage, and realized savings remain unknown.
- The only behavioral-guidance edit is the canonical preference for automatic deployment on main commits through existing delivery automation. Global guidance synchronization succeeded. Existing shared-main and overlapping-agent preferences remain active.
- The agents repo's required `scripts/check-fast.sh` passed: 35 Python tests, the release-source shell check, registry checks, Git-hook drift check, and Codex structural validation. Global guidance sync and local-reference/hygiene checks passed. Application suites were not run because application source did not change.
- The whole-directory archive helper returned `source_removed: true`; the active tracker directory is gone. The prior-cleanup link was updated for its archived location.

The next implementation batch should fix target-scoped formatter detection, Dobby release dependencies, and misleading delivery status; then adapt one deployed service to consume a captured published commit during ongoing edits. Prepare the AIP code merger after those delivery contracts are proven. This is a recommendation sequence, not a claim that any merger or runtime repair has occurred.

The earlier completed guidance cleanup is [archived separately](../astra-agent-native-simplification/tasks.md). Keep this assessment as one dated decision record; implementation should update the owning code and only necessary operational context.
