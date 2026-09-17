# Astra and Agent-Native Repository Audit

Completed assessment: 17 September 2026. The recommended approach is to preserve
the agent-native operating model and make the instructions supporting it more
selective, current, and easier to follow.

**The main problem is competing or stale authority, plus mandatory process hidden
inside references and skills.** Most small repos already have short root guidance.
Large documentation inventories often contain useful project evidence, public
content, or release history. A blanket reduction in files or skills would miss
the strongest issues and could remove useful knowledge.

## Coverage

- Individually reviewed all **28 primary repositories** under `~/GitHub`.
- Inspected the empty project under `~/Documents/ChatGPT/New project` and all
  eight surviving `whos-in-your-head` worktrees outside the primary folder.
- Classified **91 Git locations**: 81 with resolvable Git metadata, eight
  unresolved worktrees, and two empty cache `.git` directories. This includes
  20 bare SwiftPM caches, package sources, client/vendor checkouts, and app state.
- Traversed accessible local storage, including both external data volumes.
  Protected OS directories produced 227 access/traversal errors; no error was
  under `/Users/dobby`. System/virtual/network exclusions and exact discoveries
  are recorded in the [machine audit](resources/machine-discovery-and-secondary-audit.md).

This is an instruction, documentation, skill, and execution-harness assessment.
It does not certify production health or application correctness. The audit
made no live changes to application repos, canonical guidance, skill scope,
runtime configuration, services, or data. Its outputs are the report, evidence,
and prepared proposals in this project directory.

**Closeout repair:** The subsequent Stop hook retry exposed a harness bug: four
read-only discoveries were treated as repositories requiring publication even
though their Git metadata was absent and no changes or commits were attributed
to them. A focused fix in the canonical Stop hook now skips only those proven
inert candidates, preserves all surviving files, and still blocks uncertain
failures or recorded work. It also prevents an invalid nested Git marker from
redirecting publication into an enclosing repository. The shared guidance
proposals remain unapplied. Follow-up checks are recorded in
[validation](resources/validation.json).

## Findings That Matter Most

1. **Some instructions directly cause early stopping.** AIP's integration guide
   requires a user checkpoint between core logic and UI implementation and
   includes team-approval language. These conflict with the intended authorized
   end-to-end workflow. Preserve the actual API/job/DTO contract; remove the
   artificial stage gate when the full feature is already authorized.
2. **Several roots route to missing or obsolete authorities.** Examples include
   the absent `aip-company` skill, retired Remotion skill name, missing migration
   trackers, stale Angie state authority, and iOS references left behind by the
   gateway split. Repair these before shortening prose.
3. **Short roots can still impose long reading itineraries.** Remotion has a
   ten-item read order; several Astro/design roots require broad start sequences.
   Replace these with routes based on the requested change.
4. **Skill inventory and runtime state do not fully agree.** Two tracked local
   skills are missing from the registry, a chart skill exists only in the global
   runtime directory, and Gateway lacks four assigned repo skill links. The
   global browser fallback names a dormant skill. These are concrete distribution
   and routing problems, separate from whether 10 registered global skills is
   too many.
5. **Some skill entry points contain much more than routing.** The SwiftUI 27
   description is 2,696 parsed characters and fails the existing 1,024-character
   validator. WIN's client-invoicing root also includes extensive history and
   client-specific detail. Preserve domain safeguards and load specialized detail
   only when relevant.
6. **A few proof claims exceed their actual checks.** Gateway's affected-check
   routing misses Claude-client-only tests; the engine full-check description
   overstates workspace coverage; a static-site sanitizer claim exceeds its
   visible patterns. These need focused implementation verification, not stronger
   reminder text.

## Repository-by-Repository Decision

“First” means a concrete correction belongs in the first scoped cleanup, not an
emergency or permission to deploy. “Selective” means preserve the current shape
and simplify only the named overlap. Every row has detailed file/line evidence
and a validation recommendation in its linked group report.

| Repository | Recommendation | First useful change | Detail |
| --- | --- | --- | --- |
| `.github` | Tiny correction | Fix the public README's missing boundary-reference link; retain the small layout. | [Apps](resources/apps-content-audit.md) |
| `adi` | First, operational docs | Align boot-context description with current engine behavior; preserve private identity, standing authorization, and workspace boundaries. | [Dobby](resources/dobby-operations-audit.md) |
| `adi-design` | Selective | Make initial reading conditional and keep token authoring/consumer ownership explicit. | [Apps](resources/apps-content-audit.md) |
| `adithyan-ai-videos` | First | Replace fixed read order, correct Remotion skill route, register the local Omni skill; preserve render/storage/cost boundaries. | [Media](resources/product-media-audit.md) |
| `agents` | First, shared pilot | Apply reviewed concise guidance, repair capability inventory/routing, and consolidate repeated operational detail. | [Shared](resources/shared-guidance-audit.md) |
| `aip-cognitive-revolution` | Mostly keep | Remove one repeated root rule when next touched; retain packaging and generated-asset checks. | [Media](resources/product-media-audit.md) |
| `aipodcasting` | First | Remove forced intermediate checkpoint and obsolete Python/feature-README prescriptions; retain frontend/backend contracts. | [Media](resources/product-media-audit.md) |
| `aipodcasting-website` | First | Replace absent company-authority skill and broad read order with verified routes. | [Apps](resources/apps-content-audit.md) |
| `angie` | First | Correct stale live-state and boot-context routing; preserve non-Codex and person-specific behavior. | [Dobby](resources/dobby-operations-audit.md) |
| `blog-personal` | Selective | Make reading conditional and consolidate authoring/runtime instructions; retain public posts and local publishing workflow. | [Apps](resources/apps-content-audit.md) |
| `dobby-engine` | First, selected paths | Align full-check claims with its script and remove whole-dashboard inspection requirements for small UI changes. | [Dobby](resources/dobby-operations-audit.md) |
| `dobby-gateway` | First | Reconcile missing skill links and duplicated/stale ownership docs; separately repair Claude-client test routing. | [Dobby](resources/dobby-operations-audit.md) |
| `dobby-ios` | First | Repair post-split cross-repo routes and stale model-picker/setup facts; retain maintenance and device boundaries. | [Dobby](resources/dobby-operations-audit.md) |
| `documents` | Mostly keep | Preserve the compact tooling/ownership contract; no broad relocation of docs or corpus material. | [Dobby](resources/dobby-operations-audit.md) |
| `focus` | Selective | Consolidate repeated workflow prose; preserve actual policy/enforcement and recovery contracts. | [Apps](resources/apps-content-audit.md) |
| `frontier-lab-intelligence` | First, offline | Reconcile stale skills/architecture with parked status and register the local skill appropriately. | [Apps](resources/apps-content-audit.md) |
| `futureoflife-podcast` | First | Correct sibling-template promises and missing tracker route; separately test the sanitizer guarantee. | [Media](resources/product-media-audit.md) |
| `home-automation` | Mostly keep | Preserve its conditional router, local checks, and explicit pending real-device acceptance. | [Dobby](resources/dobby-operations-audit.md) |
| `litellm` | Mostly keep | Preserve deployment/recovery docs and useful changelogs; do not count its empty skill folder as a loaded skill. | [Apps](resources/apps-content-audit.md) |
| `local-transcription` | Mostly keep | Retain isolated test routes and live-job-state boundary; no new framework or skills needed. | [Media](resources/product-media-audit.md) |
| `meeting-capture` | Targeted skill correction | Shorten SwiftUI SDK metadata while preserving platform-specific references and recording boundaries. | [Apps](resources/apps-content-audit.md) |
| `modal_functions` | First | Make the root production command match the canonical secret-sync/check deployment wrapper. | [Media](resources/product-media-audit.md) |
| `platform-ops` | First, documentation | Repair the missing tracker route and distinguish current storage contracts from historical trial/proof. | [Dobby](resources/dobby-operations-audit.md) |
| `scripts` | Selective consolidation | Keep the 31-line root; clarify one owner per operational topic across large scheduler/index references. | [Dobby](resources/dobby-operations-audit.md) |
| `stadia-macos-controller` | Selective | Consolidate repeated guide/operator recipes while retaining app-versus-guide delivery boundaries. | [Apps](resources/apps-content-audit.md) |
| `thoughtforms-life` | First, paired with sibling | Correct false template parity and missing migration route; preserve intentional identity differences. | [Apps](resources/apps-content-audit.md) |
| `trenopoulospraxis` | First, documentation | Put protected current behavior ahead of superseded incident history and fix the absent tracker citation. | [Apps](resources/apps-content-audit.md) |
| `win` | First, selected references | Replace blanket testing recipes with real validation routes; repair evidence links and split invoicing history from its entry point. | [Media](resources/product-media-audit.md) |

The 28 primary repos were clean at the recorded inspection points. The
[structural snapshot](resources/primary-repository-snapshot.json) and group
inventories retain HEADs and measurement definitions. Counts differ slightly
where a group includes nested dashboard docs or public MDX/RST; they are
inventory measures, not ranked scores.

## Prepared Shared Changes

Three reviewable draft replacements and a patch are ready:

| Source | Original | Draft | Reduction |
| --- | ---: | ---: | ---: |
| Global guidance | 7,569 bytes | 3,923 bytes | 48% |
| Agent-native playbook entry point | 4,985 bytes | 3,228 bytes | 35% |
| Agents repo root | 14,946 bytes | 4,985 bytes | 67% |

Read the [proposal and preservation map](resources/guidance-proposal-review.md),
then the [global draft](resources/proposed-global.agents.md),
[playbook draft](resources/proposed-agent-native-repo-playbook.md), and
[root draft](resources/proposed-agents-root.md).
The [unified patch](resources/shared-guidance-proposal.patch) passes
`git apply --check` against the recorded originals. It is not applied.

An independent review checked for lost ownership, authorization, privacy,
validation, and completion contracts. Its four substantive findings were
incorporated. Companion reference/metadata corrections are listed before
activation. The reductions describe file bytes, not measured token savings or
proven model-performance improvement.

## Staged Rollout

1. **Shared pilot:** land the small reviewed guidance change through canonical
   sources, resolve the browser/skill inventory mismatches, update necessary
   companion references, and run the existing bootstrap/check workflow. Keep
   model choice and runtime behavior unchanged unless separately required.
2. **Concrete corrections:** fix stale authorities, wrong commands, missing
   routes, and artificial checkpoints in bounded repo groups. Start with AIP,
   WIN, Modal, and the shared control plane; coordinate Dobby and sibling-site
   ownership fixes with their real owners. Preserve unique facts before removing
   duplicate documents.
3. **Selective consolidation:** give each repeated topic one canonical current
   contract. Move experiment/incident chronology to clearly historical context.
   Keep public content, design specifications, changelogs, and useful evidence.
   Leave small good repos largely alone.
4. **Behavioral verification:** run representative tasks with the revised
   instructions. Evaluate unnecessary reads/stops, outcome correctness, and
   appropriate proof. Treat sanitizer, mutation-lock, and affected-test gaps as
   distinct code changes with focused validation. Expand rollout based on results.

Completion of a cleanup batch means the new route works, unique knowledge is
preserved, affected checks pass, obsolete references are reconciled, and the
agent completes representative authorized work. It does not mean reaching a
particular file count or replacing the portfolio with one large manual.

## Validation and Limits

- Reconciled primary inventory with all three review groups and secondary Git
  locations; validated source paths/line evidence and current proposal syntax.
- Repo hygiene and `scripts/check-fast.sh` passed, including 41 unit tests and
  the local production-source shell check. This validates the audit's home repo,
  not every app's runtime.
- The existing SwiftUI skill validator failed its description-length check;
  this is a confirmed pre-existing finding, not a failure introduced by a draft.
- App suites, provider calls, deployments, recording, publishing, financial
  operations, private memory/corpus contents, and live production data were not
  exercised. References to these are operational routing assessments only.
- Eight orphaned worktrees require recovery/retirement decisions before any
  deletion. Package-managed sources and app-owned state should use their own
  lifecycle rather than personal guidance cleanup.

The detailed reports provide exact evidence and scoped validation for each
recommendation. No permanent audit service or new fleet-wide policy framework
was introduced.
