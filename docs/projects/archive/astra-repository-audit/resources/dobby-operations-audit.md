# Dobby and machine-operations repository audit

Snapshot: 2026-09-17. This is a recommendation-only audit of nine repositories.
No audited repository was edited, no service or device was contacted, and no
deployment, credential operation, personal-data command, or test suite was run.

The review applied the current agent-native playbook, its guidance/docs references,
the canonical Dobby-system skill, and the user's pasted OpenAI Astra article.
The article supports precise skill triggers, conditional context, proportionate
verification, explicit authority, and completion through proof. It does not justify
removing privacy, secret, production, or actual device boundaries.

## What is working

Most roots here are already short operational routers. Documents, home-automation,
scripts, and dobby-ios are 22–40 lines; the engine root is 62. The more substantial
problems are stale facts behind those routers, duplicated ownership explanations,
and operational history mixed with current contracts.

The Dobby separation is worth preserving: person workspaces own identity/data;
engine owns shared domain behavior; gateway and iOS consume its boundaries;
agents owns generated capabilities; scripts owns machine scheduling.
Workspace identity is deliberately loaded through a separate instruction surface.
Do not consolidate those repositories, histories, or private material into agents.

Useful mechanical contracts already exist: workspace validation, gateway import
and path checks, local production activation/rollback, fixture-based dashboard
seam checks, iOS diagnostics, and home-automation syntax/link/contract checks.
A cleanup should make those paths easier to select, rather than add another
central policy or scoring system.

## Coverage and measurement

Counts use git-tracked filenames. Docs includes nested dashboard/docs in the
engine. Active/archive columns count project Markdown files, followed by actual
tasks.md tracker counts in parentheses. Counts measure inventory, not quality.
Personal workspace memory, journals, identity contents, health data, and project
contents were not read; only operational guidance, aggregate counts, and check
scripts were inspected. Therefore no judgment is made about private project
completion or the value of those records.

| Repository | Type | Root AGENTS lines / bytes | Docs MD | Architecture / references | Active / archived project MD (trackers) | Dirty records |
|---|---|---:|---:|---:|---:|---:|
| adi | Private person workspace | 82 / 6,630 | 2 | 0 / 1 | 76 (5) / 300 (25) | 0 |
| angie | Private person workspace | 77 / 4,427 | 2 | 0 / 0 | 4 (1) / 0 (0) | 0 |
| dobby-engine | Shared CLI and dashboard | 62 / 3,085 | 27 | 3 / 6 | 0 (0) / 0 (0) | 0 |
| dobby-gateway | HTTP/runtime gateway and contracts | 93 / 5,050 | 19 | 8 / 11 | 0 (0) / 0 (0) | 0 |
| dobby-ios | SwiftUI client, maintenance scope | 40 / 2,307 | 8 | 4 / 4 | 0 (0) / 0 (0) | 0 |
| documents | Local document tooling | 25 / 1,261 | 4 | 1 / 1 | 1 (0) / 1 (0) | 0 |
| scripts | Machine bootstrap/schedulers/clients | 31 / 2,659 | 42 | 6 / 26 | 5 (2) / 5 (2) | 0 |
| platform-ops | Platform routing docs and scripts | 35 / 1,847 | 14 | 7 / 7 | 0 (0) / 0 (0) | 0 |
| home-automation | Device CLI with pending live proof | 22 / 1,847 | 8 | 1 / 3 | 4 (1) / 0 (0) | 0 |

Engine additionally has dashboard/AGENTS.md at 80 lines / 7,046 bytes.
The two Documents project Markdown files are placeholder READMEs, not projects.
Generated CLAUDE.md pointers are excluded from root-size comparisons.

| Repository | Inspected HEAD |
|---|---|
| adi | e1e29b5ae2d6fab7a0185f31d44c535231f60920 |
| angie | 22d7a9c0ffa78a5815ee5b75677f40e6b8720a21 |
| dobby-engine | 31df2ab6bedd20d77060fc1ccae0af03f63b10e5 |
| dobby-gateway | efce84f213f3241275523e7b12377e0d7ca64241 |
| dobby-ios | 14674ad27656eb3a08bf587f5a00c9fcd7851604 |
| documents | 8b2b9fef89b4e137cf7cf7590680496c73a1b17c |
| scripts | ab7c24fe428cc138bb67eb3fa4951adc1b9724fb |
| platform-ops | a93c745c71d5fd9cac330f09f95e381fbb70cd8b |
| home-automation | 9be03d9afa545d5bb041bd207ddcfb267b3a125b |

Machine-readable metadata: [dobby-operations-coverage.json](dobby-operations-coverage.json).
The snapshot records actual runtime links separately from the registry.

## Skill exposure

These are repo-local .agents/skills entries in addition to the shared global kit.
Claude mirrors pointing at the same canonical sources do not constitute duplicate
skill ownership. Installed plugin catalogs and the global kit are audited by the
parent task.

| Repository | Observed repo skill links | Assessment |
|---|---|---|
| adi | adi-writing, codex-agent-loop, codex-app-server, cv-creator, dobby-system, media-toolkit, social-media-publishing | Mixed personal-work and engineering use is plausible. Technical loop/App Server skills are candidates for usage-based review, not demonstrated waste. Codex-only client scope matches root guidance. |
| angie | cv-creator, dobby-system, media-toolkit | Plausible workspace scope; no removal recommended from inventory alone. |
| dobby-engine | dobby-system | Focused. |
| dobby-gateway | None observed | Registry assigns codex-agent-loop, codex-app-server, dobby-system, media-toolkit. Treat as runtime-distribution mismatch to investigate separately from content cleanup. |
| dobby-ios | dobby-system, media-toolkit, and nine iOS/SwiftUI plugin-derived skills | Most are directly relevant specialists. For a maintenance-only app, rare app-intents/performance tools may be candidates for narrower routing after usage evidence. Do not delete useful debugging tooling by count. |
| documents | None | Shared global capabilities plus local CLI/docs appear sufficient. |
| scripts | media-storage-lifecycle, media-toolkit | Relevant to shared media clients and storage ownership. |
| platform-ops | None | Local docs/scripts appear sufficient. |
| home-automation | None | Root conditionally routes to global project, client-interface-guidelines, and secret-management. Appropriate. |

The canonical Dobby-system skill is 160 lines / 13,338 bytes.
Its [description](/Users/dobby/GitHub/agents/skills-source/owned/dobby-system/SKILL.md) (line 3)
enumerates many repos and topics; [line 12](/Users/dobby/GitHub/agents/skills-source/owned/dobby-system/SKILL.md)
says any Dobby-system change should check it first.
Most repo roots instead route to it for ownership/boundary/cross-repo changes.
Align the skill to that narrower trigger. Keep ownership/privacy and a short
decision router; move feature-level artifact export details at
[line 142](/Users/dobby/GitHub/agents/skills-source/owned/dobby-system/SKILL.md)
behind the already-linked engine contract. Preserve the actual privacy and writer
boundaries. This is a content proposal, distinct from the Gateway link mismatch.

## Repository findings

### adi

**Keep.** The identity-versus-operations split is explicit in
[AGENTS.md:3](/Users/dobby/GitHub/adi/AGENTS.md:3).
The root conditionally routes cross-repo work to Dobby-system and ordinary memory
placement to the body map, instead of loading the complete private corpus.
The workspace shim, owner-host constraints for live state, generated config
ownership, and local checks are meaningful controls.

**Move/consolidate, near-term.** The trigger table at
[AGENTS.md:39](/Users/dobby/GitHub/adi/AGENTS.md:39) has grown from a routing table
into detailed domain recipes. Retain recognizable intent-to-command routes and
explicit standing authorization; put shared procedures in the engine command
docs and person-specific behavior in the existing person-owned instruction
surface. Do not erase per-person exceptions or copy their contents into agents.
The ownership/hook narrative at
[AGENTS.md:69](/Users/dobby/GitHub/adi/AGENTS.md:69) can be a short pointer once its
canonical contract is clear.

**Correct, immediate.** The operational body map's
[session boot description](/Users/dobby/GitHub/adi/docs/body-map.md:133)
says newest full session summaries are boot-loaded. The engine's current
[Codex boot contract](/Users/dobby/GitHub/dobby-engine/docs/lifecycle-hooks.md:59)
loads bounded recent tldrs; full records are on demand. Express client-specific
behavior once in the engine and link it. This audit did not read session records.

**Delete.** Only duplicated operational explanations after their unique
authorization/context has been preserved. No recommendation to delete personal
records, archives, or identity text.

**Execution and verification.** The entry point is workspace-local bin/dobby.
[scripts/check-fast.sh](/Users/dobby/GitHub/adi/scripts/check-fast.sh:6) includes a
workspace-binding check plus local integrity validators and staged workspace
validation. [check-full](/Users/dobby/GitHub/adi/scripts/check-full.sh:31) validates
the full workspace. For a routing-only correction, inspect the doc paths and diff;
run required owner checks during implementation without copying their private
output into this report. A boot behavior change additionally needs engine tests
and bounded, private workspace proof.

### angie

**Keep.** Root
[identity separation](/Users/dobby/GitHub/angie/AGENTS.md:3),
[workspace-local entry point](/Users/dobby/GitHub/angie/AGENTS.md:25),
and engine ownership are sound. Its three repo skills are not evidence of excess.

**Correct, immediate — confirmed stale state authority.**
[AGENTS.md:47](/Users/dobby/GitHub/angie/AGENTS.md:47) and
[line 59](/Users/dobby/GitHub/angie/AGENTS.md:59), plus
[body-map.md:42](/Users/dobby/GitHub/angie/docs/body-map.md:42) and
[line 67](/Users/dobby/GitHub/angie/docs/body-map.md:67), still describe workspace
JSON as live Shelf state. The canonical
[engine storage contract](/Users/dobby/GitHub/dobby-engine/docs/shelf.md:24)
says live state is engine-owned, person-bound SQLite; workspace JSON is only
one-time import/audit/backup material. This is a real competing authority, not
cosmetic verbosity. Replace the stale routing with the CLI/owner contract,
including its per-host semantics.

**Correct, immediate.**
[AGENTS.md:52](/Users/dobby/GitHub/angie/AGENTS.md:52) says the body map is injected
at boot without distinguishing client. Current
[lifecycle docs](/Users/dobby/GitHub/dobby-engine/docs/lifecycle-hooks.md:67)
make it on demand for Codex and preserve a legacy packet for other runtimes.
The body's session-summary description at
[line 125](/Users/dobby/GitHub/angie/docs/body-map.md:125) needs the same
client-aware clarification. Preserve actual non-Codex behavior rather than
blindly copying Adi's Codex-only wording.

**Move/delete, later.** Move root migration lineage at
[AGENTS.md:21](/Users/dobby/GitHub/angie/AGENTS.md:21) to existing history if still
useful. Do not homogenize identity or archive private projects based on counts.

**Execution and verification.** bin/dobby pins the workspace;
[check-fast](/Users/dobby/GitHub/angie/scripts/check-fast.sh:6) verifies that binding
and staged schemas; check-full performs full workspace syntax/schema validation.
Correcting docs does not require a live Shelf mutation. Test storage/binding changes
in engine fixtures, then perform a separately authorized private smoke if needed.

### dobby-engine

**Keep.** The root's
[no-person-data boundary](/Users/dobby/GitHub/dobby-engine/AGENTS.md:3),
workspace binding, and command contracts are essential. The current
[write-recipes index](/Users/dobby/GitHub/dobby-engine/docs/agent-write-recipes.md:3)
is good progressive disclosure: use the live CLI schema/help for exact fields.
The existing mixed docs layout is deliberate and small enough that a mass
rename into architecture/references would add migration work without demonstrated
benefit.

**Correct, immediate — validation overclaim.**
[AGENTS.md:49](/Users/dobby/GitHub/dobby-engine/AGENTS.md:49) promises extra
workspace validation in check-full.
[scripts/check-full.sh:20](/Users/dobby/GitHub/dobby-engine/scripts/check-full.sh:20)
through its end performs syntax checks and the Python test suite only.
Align the description with what runs, and separately name workspace validation
when a workspace-shape change needs it. Do not silently add private workspace
access to a generic check just to satisfy stale prose.

**Correct, immediate — stale boot statement.**
The engine's default [body map:124](/Users/dobby/GitHub/dobby-engine/docs/body-map.md:124)
also repeats the older full-session boot description while
[lifecycle-hooks.md:59](/Users/dobby/GitHub/dobby-engine/docs/lifecycle-hooks.md:59)
describes the bounded Codex packet. Keep one client-aware boot authority.

**Move/delete, near-term — dashboard router.**
[dashboard/AGENTS.md:31](/Users/dobby/GitHub/dobby-engine/dashboard/AGENTS.md:31)
keeps a completed-project narrative and links a tracker absent from the current
checkout and tracked filenames. Remove the dead pointer after checking whether
unique decisions already live in its architecture docs.
The detailed page catalogue and interaction descriptions at
[line 46](/Users/dobby/GitHub/dobby-engine/dashboard/AGENTS.md:46) and
[line 71](/Users/dobby/GitHub/dobby-engine/dashboard/AGENTS.md:71) belong in the
existing product/UI references; keep private-data, writer, secret, and deployment
boundaries in scoped guidance.

**Make conditional, near-term.**
[dashboard/AGENTS.md:79](/Users/dobby/GitHub/dobby-engine/dashboard/AGENTS.md:79)
directs every UI change to capture every page and Architecture state.
Preserve visual inspection, but select changed routes/states and expand to the
whole app for shared theme/navigation/system changes. The adjacent check-full
rule already uses that proportional pattern.

**Execution and verification.** bin/dobby is the stdlib CLI; engine
[check-fast](/Users/dobby/GitHub/dobby-engine/scripts/check-fast.sh:35) runs its
unittest suite. Dashboard npm check-fast includes fixture-based backend seam
proof; npm shots accepts route/width flags; local deployment uses a versioned
release. These are available proof paths, not tests executed by this audit.
A doc-only cleanup needs path/diff checks and required owner checks, not dashboard
production activation or personal-data reads.

### dobby-gateway

**Keep.** Root
[ownership and runtime-native boundaries](/Users/dobby/GitHub/dobby-gateway/AGENTS.md:79),
canonical contracts, clean-release production delivery, and the explicit split
between local validation and live assistant turns are valuable.
The [live smoke policy](/Users/dobby/GitHub/dobby-gateway/docs/references/quality/live-smoke-policy.md:18)
has concrete grounds: real usage, conversation mutations, and possible approval
effects. Keep that boundary; do not treat it as obsolete hesitation.

**Make conditional, near-term.**
[AGENTS.md:8](/Users/dobby/GitHub/dobby-gateway/AGENTS.md:8) presents three documents
as unconditional Start Here reading. Route each by question: ownership, runtime
flow, contract change. It already has a contextual second list.

**Consolidate/correct, immediate to near-term.**
The two workspace architecture pages overlap in handoff diagrams and boundary
rules:
[system-context.md:128](/Users/dobby/GitHub/dobby-gateway/docs/architecture/workspaces/dobby-workspace-system-context.md:128)
and
[personal-agent-workspace.md:19](/Users/dobby/GitHub/dobby-gateway/docs/architecture/workspaces/personal-agent-workspace.md:19).
Keep one short gateway-to-workspace contract and point broader orientation to
Dobby-system. This is confirmed drift as well as overlap: the first page says
Codex is the assistant runtime at
[line 50](/Users/dobby/GitHub/dobby-gateway/docs/architecture/workspaces/dobby-workspace-system-context.md:50)
and Gateway owns the iPhone surface at
[line 97](/Users/dobby/GitHub/dobby-gateway/docs/architecture/workspaces/dobby-workspace-system-context.md:97),
while the current root defines two runtimes and a separate iOS owner.
The second page's config ownership wording at
[line 46](/Users/dobby/GitHub/dobby-gateway/docs/architecture/workspaces/personal-agent-workspace.md:46)
should distinguish workspace inputs from agents-generated runtime config.

Root docs rules at
[AGENTS.md:42](/Users/dobby/GitHub/dobby-gateway/AGENTS.md:42)
are repeated in [repo-contracts.md:16](/Users/dobby/GitHub/dobby-gateway/docs/references/repo-contracts.md:16).
Keep one authoritative rule set and a pointer.
The Claude runtime reference still names the absent
[~/.agents/hooks registry](/Users/dobby/GitHub/dobby-gateway/docs/references/claude-runtime.md:102);
the canonical registry is in the tracked agents repo.

**Investigate separately, immediate.** The registry assigns four repo skills,
including codex-app-server required by
[AGENTS.md:70](/Users/dobby/GitHub/dobby-gateway/AGENTS.md:70), but .agents/skills
and .claude/skills were absent. Repo bootstrap still registers this repo.
The audit proves the filesystem/registry mismatch, not its cause. Reconcile
through canonical control-plane tools in an implementation pass; do not hand-create
runtime links.

**Repair the mechanical gap, near-term.**
The new shared Claude client has its own
[test command](/Users/dobby/GitHub/dobby-gateway/shared/claude-client/package.json:10),
but [check-affected.sh:20](/Users/dobby/GitHub/dobby-gateway/scripts/check-affected.sh:20)
has no shared/claude-client case, and
[ci-check.sh:18](/Users/dobby/GitHub/dobby-gateway/scripts/ci-check.sh:18)
does not run that package's tests. The mobile-gateway test builds the Claude client
but runs only its own test directory. A Claude-client-only change can therefore
select no affected tests. Add the owned package to affected/full validation with
its dependent gateway checks, rather than compensating with another prose reminder.
This is source-confirmed wiring, not a claim that its tests fail.

**Execution and verification.** npm check:fast performs staged formatting, path/
tracker/import guardrails and local-production contract tests; npm check:affected
is separate; scripts/ci-check.sh is full validation.
[repo-validation.md:20](/Users/dobby/GitHub/dobby-gateway/docs/references/setup/repo-validation.md:20)
clearly states that distinction. A docs cleanup should use its existing path
checker plus owner fast checks. Runtime changes need affected tests and relevant
health/proof; live turns should use the documented opt-in and disposable scope.

### dobby-ios

**Keep.** Root guidance is concise and appropriately limits the
[maintenance scope](/Users/dobby/GitHub/dobby-ios/AGENTS.md:5).
Keep bundle/key identity, untracked credentials, thin-client ownership,
contract-fixture parity, device interaction proof, and explicit blocked/skipped
reporting. Eleven repo skill links are mostly relevant iOS specialists; count
alone does not justify removal.

**Correct, immediate — split left broken routes.** Current docs still refer to
gateway-owned pages as if they lived here. Confirmed missing local destinations
include:
[iphone-chat-loop.md:108](/Users/dobby/GitHub/dobby-ios/docs/architecture/mobile/iphone-chat-loop.md:108),
[iphone-turn-recovery.md:137](/Users/dobby/GitHub/dobby-ios/docs/architecture/mobile/iphone-turn-recovery.md:137),
[offline-capture-and-sync.md:191](/Users/dobby/GitHub/dobby-ios/docs/architecture/mobile/offline-capture-and-sync.md:191),
[ios-chat-behavior.md:276](/Users/dobby/GitHub/dobby-ios/docs/references/ios-chat-behavior.md:276),
[ios-development.md:3](/Users/dobby/GitHub/dobby-ios/docs/references/setup/ios-development.md:3),
[line 267](/Users/dobby/GitHub/dobby-ios/docs/references/setup/ios-development.md:267),
and [testflight-release.md:193](/Users/dobby/GitHub/dobby-ios/docs/references/setup/testflight-release.md:193).
Point to the actual owning gateway document rather than recreating copies.

The setup reference names missing ~/.agents control-plane sources and the wrong
MCP source file at
[lines 11–16](/Users/dobby/GitHub/dobby-ios/docs/references/setup/ios-development.md:11).
The current canonical MCP registry is agents/mcp/config/presets.json.
Its [line 277](/Users/dobby/GitHub/dobby-ios/docs/references/setup/ios-development.md:277)
claims npm check:affected invokes the iOS tests; this repo has no package.json,
and Gateway's current check:affected excludes iOS. Remove that stale monorepo
claim and retain the actual script path.

**Correct, immediate — stale product description.**
[iphone-codex-controls.md:18](/Users/dobby/GitHub/dobby-ios/docs/architecture/mobile/iphone-codex-controls.md:18)
and [line 32](/Users/dobby/GitHub/dobby-ios/docs/architecture/mobile/iphone-codex-controls.md:32)
say no model picker/model field. Current
[ModelChoice.swift](/Users/dobby/GitHub/dobby-ios/Dobby/Models/ModelChoice.swift:3)
and [SettingsView.swift:55](/Users/dobby/GitHub/dobby-ios/Dobby/Views/Settings/SettingsView.swift:55)
implement a selectable model and runtime routing wire value. Update the doc from
current source; this is not a recommendation to change models or expand the app.

**Move/consolidate, near-term.** The 458-line/45.8 KB
[ios-design-language.md](/Users/dobby/GitHub/dobby-ios/docs/references/ios-design-language.md:415)
combines current design rules with a long fixed-bug history.
Preserve reproducible platform limitations and the responder-chain lesson; move
dated implementation narratives out of the current design contract when their
unique facts have another durable home. Some behavior overlaps with
ios-chat-behavior.md; decide one owner per topic before deleting anything.

**Execution and verification.** check-ios-fast runs simulator tests and has
explicit no-Xcode/no-simulator skip branches at
[script line 147](/Users/dobby/GitHub/dobby-ios/scripts/check-ios-fast.sh:147).
A zero exit can mean skipped, so report which occurred.
Machine/route preflights, the phone deploy wrapper, the markdown gallery, and
interactive/XCUITest proof are documented. Keep the
[focus/gesture proof rule](/Users/dobby/GitHub/dobby-ios/docs/references/setup/ios-development.md:77);
it is tied to an actual escaped defect. Correcting links and prose does not require
a phone install. An app behavior change still uses the existing device gate.

### documents

**Keep; no structural rewrite recommended.** This is a small owner repo with a
25-line root, one architecture document and one command reference.
[AGENTS.md:7](/Users/dobby/GitHub/documents/AGENTS.md:7) keeps documents out of git
and distinguishes copy-only ingest from destructive cleanup.
[commands.md:11](/Users/dobby/GitHub/documents/docs/references/commands.md:11)
defines stable machine output; catalog/manifests provide recovery evidence.
Those boundaries serve actual source-data risk and should survive simplification.

**Move/delete, optional later.** The two tiny project-folder README placeholders
are not active trackers and need not trigger an archive project. Remove only if
the repo chooses to stop maintaining placeholder pages. No material duplication
or broken operational Markdown links was confirmed in the selected sources.

**Execution and verification.** python3 -m documents.cli is the development
front door. [check-fast](/Users/dobby/GitHub/documents/scripts/check-fast.sh:37)
performs shell/Python syntax and pytest; check-full currently delegates to it.
Documentation already describes the fast suite accurately. Do not run imports,
extraction, cleanup or catalog searches simply to validate docs edits; those can
touch private corpora or billable providers. Fixture-based tests are the suitable
implementation proof before any specifically authorized source-data operation.

### scripts

**Keep.** The root is an effective conditional router:
[AGENTS.md:9](/Users/dobby/GitHub/scripts/AGENTS.md:9).
Preserve machine/app ownership, canonical secret materialization, source-based
propagation, idempotent tooling, and human-only OS permission boundaries.
The architecture explicitly
[keeps domain implementations with their owners](/Users/dobby/GitHub/scripts/docs/architecture/repo-architecture.md:80).
These are useful constraints, not generic coding instruction.

**Consolidate, near-term — confirmed repeated operational facts.**
The script index is 264 lines / 40,566 bytes; setup/scheduler reference is
595 lines / 61,493 bytes. Length is not itself a defect, but both maintain the
same lock/recovery and materialization policy:
[script-index.md:214](/Users/dobby/GitHub/scripts/docs/references/script-index.md:214)
versus
[setup-and-scheduler-reference.md:384](/Users/dobby/GitHub/scripts/docs/references/setup-and-scheduler-reference.md:384),
and
[index:236](/Users/dobby/GitHub/scripts/docs/references/script-index.md:236)
versus
[setup reference:419](/Users/dobby/GitHub/scripts/docs/references/setup-and-scheduler-reference.md:419).
Keep the index as one-line command/owner routing, with detailed facts in the
specific existing subsystem references or one current scheduler reference.
Do not split each paragraph into a new document; reduce competing owners.

**Correct, near-term.**
The index describes ops/check-fast differently at
[line 25](/Users/dobby/GitHub/scripts/docs/references/script-index.md:25)
and [line 137](/Users/dobby/GitHub/scripts/docs/references/script-index.md:137);
the [script](/Users/dobby/GitHub/scripts/ops/check-fast.sh:87) now runs many local
contract suites. Keep one accurate summary and link the executable for exact
coverage. No check-duration measurement was taken, so the audit does not call
the suite slow or recommend removing tests.

**Delete.** Repeated detailed inventories after updating incoming routes.
No blanket deletion of dated incidents, recovery evidence, or active trackers.
Several apparent missing paths in a naive link scan were actually explicitly
owned by other repos; they are not reported as confirmed broken links.

**Execution and verification.** ops/check-fast is the root fast gate;
scripts/check-full adds all tracked Python syntax and unittest discovery.
ops/health-check.sh and scheduler/client status commands inspect machine state,
but some setup/repair flows mutate services or send notifications. For docs-only
work, use static path/diff checks and the local required gate. For scheduler or
repair changes, test bounded fixture contracts first, then prove the exact
background process and rollback/hold behavior when that runtime change is in scope.
Do not run generic health/repair automation merely to complete this audit.

### platform-ops

**Keep.** The 35-line root has a clear routing/domain owner and concrete
[before/after snapshot rules](/Users/dobby/GitHub/platform-ops/AGENTS.md:26)
for real DNS/edge changes. Those are proportionate recovery controls.
Docs-only validation at
[AGENTS.md:34](/Users/dobby/GitHub/platform-ops/AGENTS.md:34) is already local.

**Correct, immediate — missing execution authority.**
Current storage docs link an absent active migration tracker:
[home-object-storage-routing.md:54](/Users/dobby/GitHub/platform-ops/docs/architecture/home-object-storage-routing.md:54),
[mac-mini-public-storage-feasibility.md:9](/Users/dobby/GitHub/platform-ops/docs/references/mac-mini-public-storage-feasibility.md:9),
and
[s3-upload-elimination-audit.md:7](/Users/dobby/GitHub/platform-ops/docs/references/s3-upload-elimination-audit.md:7).
No project tracker is in the current tracked tree. Resolve the pointer against
actual history/current work before declaring the project complete. Recovery
acceptance remains explicitly outstanding in current docs, so deleting its
references alone would lose an operational obligation.

**Move/consolidate, near-term — current versus historical facts.**
The feasibility reference marks an
[earlier public trial](/Users/dobby/GitHub/platform-ops/docs/references/mac-mini-public-storage-feasibility.md:65),
then has an unqualified
[Remaining Proof](/Users/dobby/GitHub/platform-ops/docs/references/mac-mini-public-storage-feasibility.md:131)
that still asks to finish Modal deployment. Current
[routing docs](/Users/dobby/GitHub/platform-ops/docs/architecture/home-object-storage-routing.md:57)
and the [consumer audit](/Users/dobby/GitHub/platform-ops/docs/references/storage-consumer-migration-audit.md:61)
say deployment/retention work passed while backup/restore remains.
Make the present acceptance state authoritative in one place, date historical
proof, and point the architecture at current routing plus the scripts-owned
operator runbook. Preserve past evidence rather than rewrite old results as if
newly verified.

**Simplify, later.**
The docs contract
[requires one architecture page and one reference page for each hosting exception](/Users/dobby/GitHub/platform-ops/docs/references/docs-contract.md:16).
Allow one document when it fully captures a small exception; split only when
shape and operator facts warrant it. This is a specific doc-proliferation rule,
not a reason to merge unrelated domains.

**Execution and verification.** scripts/check-fast validates staged text,
shell syntax and inventory shape; check-full checks all tracked scripts/inventory.
No runtime product exists to launch. A documentation cleanup needs local checks
and corrected links; DNS, ingress and registrar changes retain their documented
snapshots and scoped remote proof. This audit did not inspect credentials,
domain records, or live service health.

### home-automation

**Keep; no broad cleanup recommended.** The 22-line root routes by question,
separates machine scheduling from device logic, and conditionally uses three
global skills. Its small architecture, CLI contract and runbook have distinct
purposes. Local doc links resolved in the audited files.

**Preserve active status.**
The [tracker acceptance criteria](/Users/dobby/GitHub/home-automation/docs/projects/hue-cli/tasks.md:20)
distinguish implemented offline behavior from pending real-device acceptance.
Its [handoff state](/Users/dobby/GitHub/home-automation/docs/projects/hue-cli/tasks.md:48)
explicitly records external prerequisites and withheld live proof. This is
appropriate unfinished work, not archive clutter. Do not mark it complete or
auto-pair/control hardware during a docs audit.

**Move/delete.** None required now. On eventual completion, consolidate unique
research facts into the current provider reference and archive the project
according to its existing contract; preserve any unresolved device limitations.

**Execution and verification.** bin/home-auto is the machine-facing CLI.
[check-fast](/Users/dobby/GitHub/home-automation/scripts/check-fast.sh:4)
runs shell syntax, a source/link checker and unittest discovery.
[check-scaffold.py](/Users/dobby/GitHub/home-automation/scripts/check-scaffold.py:16)
already mechanically checks relative doc links.
The runbook names read-only discovery, deliberate pairing, targeted mutations,
observed outcomes and restoration. Keep that separation. No device discovery,
pairing, credential access or light mutation was attempted by this audit.

## Recommended sequence

1. **Immediate: repair facts and routes.** Angie state routing; shared boot
   descriptions; engine full-check claim; iOS split/model/control-plane drift;
   Gateway old runtime/owner references; platform missing-tracker authority.
   Reconcile Gateway skill-link drift through the control plane as a separate
   operation. These are concrete errors independent of a new house style.
2. **Near-term: reduce recurring context.** Make Gateway startup reading
   conditional; shorten dashboard guidance and select visual proof by change;
   consolidate the two Gateway workspace docs; turn the scripts index back into
   routing; separate iOS fixed-bug history and platform trial evidence from
   current contracts. Preserve unique facts and repair inbound links first.
3. **Later: evaluate behavior on ordinary tasks.** Compare correct completion,
   irrelevant reads, avoidable pauses, and proof accuracy before broad rollout.
   Revisit specialist skill exposure using actual tasks. Leave small good repos
   alone. Private workspace project cleanup requires a review inside each
   workspace, not copying its contents into the control-plane report.

For each implementation batch, use the owning repo's existing local checks;
broaden proof only for a changed runtime boundary or unresolved failure.
No new central audit script, docs taxonomy, scoring rubric, approval queue, or
mass skill deletion is needed to implement these findings.

## Evidence limitations

All claimed defects above come from current file contents, existing/missing paths,
tracked filenames, and check-script inspection. Source inspections establish
what a script says it does; they do not establish successful execution or live
service health. No timings, model-context traces, skill-use frequency, or product
smokes were measured. Private content was intentionally outside scope.

The audit's local-link scan was advisory: Markdown links plus selected explicit
path literals were checked against file-relative and repo-relative locations.
Candidates were reviewed in context before being called defects. Cross-repo
paths with an explicit owner were not counted as broken merely because absent
locally. No new scan script was installed.
