# Astra and Agent-Native Simplification

Status: completed and archived on September 18, 2026.

## Outcome and Scope

Simplified shared guidance, skills, and documentation across all 28 primary repositories from the [machine-wide audit](../astra-repository-audit/report.md). Changed 26 repositories; deliberately kept `documents` and `home-automation` as-is. All repositories remain present. Cached dependencies, vendor copies, and secondary worktrees were classified in the earlier audit rather than treated as independent projects.

Adi's operating model is preserved: humans set intent, priorities, taste, and material-risk boundaries; agents make routine decisions and complete authorized work. Dictated prompts are interpreted by intent. Code, schemas, scripts, and checks define implementation; docs retain useful ownership, rationale, recovery, and external constraints. No universal documentation layout, mandatory reading sequence, or new management framework was introduced.

The user authorized implementation across the repositories, including global and personal workflow guidance. The [OpenAI Astra article](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) and supplied Ryan Lopopolo quotation informed the direction. The earlier [Codex-only cleanup](../codex-only-control-plane/evidence.md) remains intact. Application support for Claude is distinct from retired Claude development setup.

## Completed Work

- [x] Simplify shared instructions while preserving autonomy, existing authorization, required checks, generated-file ownership, privacy, and recovery boundaries.
- [x] Narrow skill triggers, make supporting references conditional, and reconcile canonical sources, registry entries, and runtime links.
- [x] Record a corrected, consolidated, or deliberately unchanged outcome for every primary repository.
- [x] Repair confirmed stale routes and duplicate authorities without deleting unique domain knowledge or personal/public content.
- [x] Validate affected changes and independently review important navigation and behavioral contracts.
- [x] Archive the complete project directory and verify its final links and active-path removal.

## Shared Changes

- Global guidance now states Adi's workflow directly, including transcription tolerance, autonomous follow-through, concise evidence, and necessary rather than automatic documentation. Removed the mandatory route to the dormant browser skill.
- The agent-native playbook and project skill now support task-sized discovery and validation. Scoring, templates, and deeper references are optional tools. Removed compulsory project paperwork and repeated reading/checklists from CLI guidance.
- Shortened Dobby, podcasting, PDF, design, skill-authoring, and FLI review guidance while preserving their useful contracts: person/workspace isolation, Shelf serving-host authority, provider/auth/idempotency details, design tokens and taste, and parked runtime behavior.
- Adopted `find-skills`, `swiftui-whats-new-27`, and `figma-use` into owned sources before personalizing them. Fixed invalid legacy Figma frontmatter and missing companion references; refreshed affected UI metadata without dropping invocation policies.
- Registered the real repo-local `omni-flash-video` and `fli-daily-intelligence` skills. Preserved the unregistered chart helper as a dormant canonical source. The global default remains 10 skills; useful specialist capabilities remain available in their intended scope.
- Consolidated overlapping Codex architecture/configuration/flow pages and routed lifecycle details to their existing owner. Kept the already-useful agents root source map and its conditional validation requirements.
- The only behavior change outside the shared control plane is a gateway validation repair: affected Claude-client changes now select that package's tests and dependent gateway tests. Three regression cases cover selection, failure propagation, and the docs-only skip. MeetingCapture also received a source-comment correction.

## Repository Outcomes

Every changed document group received diff and local-link review. Gate summaries below distinguish actual checks from staged-only skips.

| Repository | Outcome | Validation |
| --- | --- | --- |
| `.github` | Fixed the stale public ownership link; kept compact root guidance. | Fast gate returned an explicit no-stage skip; link/diff reviewed. |
| `adi` | Made owner routes and boot/context reading conditional; preserved personal authorizations and identity boundaries. | Workspace identity/corpus/network guards; staged validation had no input. |
| `adi-design` | Removed default reading order and duplicate hosting prose; clarified canonical tokens, showroom use, and synchronization. | Two source/release contract checks; 55 CSS property names and ordered values match the skill asset. |
| `adithyan-ai-videos` | Removed fixed intake/reading/storyboard checkpoints and three duplicate recipes; preserved complete authorized render/delivery and installed CLI routing. | Local skill parsed; fast gate explicitly skipped runtime checks with no staged input. |
| `agents` | Simplified global/shared skills, registry routing, and overlapping control-plane docs; retained source ownership and executable gates. | Bootstrap, fast/shared checks, 267 regression tests, 55 skill validations, 107 shared-reference targets. |
| `aip-cognitive-revolution` | Removed generic root repetition; kept substantive theme/content knowledge. | Link/diff review; fast gate explicitly skipped build/package scan with no staged input. |
| `aipodcasting` | Trimmed integration/feature/studio manuals and removed obsolete Python/LLM rules, mandatory README/barrel recipes, and artificial team approval steps. | Local production-source tests and shell checks; staged lint had no input. |
| `aipodcasting-website` | Removed missing company-skill route and duplicate schema/design descriptions; identified current claims sources and fallback-only verification. | Link/diff review; fast gate had no staged input. |
| `angie` | Corrected Shelf persistence/host authority and conditional context routes; preserved voice, writeback, and privacy boundaries. | Workspace identity guard; staged validation had no input. |
| `blog-personal` | Removed mandatory reads and a wrong duplicated frontmatter schema; simplified the local skill and corrected design/verification ownership. | 11 release-contract tests, storage URL scan, skill parse; staged Astro/content checks had no input. |
| `dobby-engine` | Shortened dashboard and body-map guidance; corrected lifecycle ownership and full-check scope. | 193 Python tests plus syntax/JSON checks. |
| `dobby-gateway` | Consolidated workspace guidance, removed source inventories, and repaired affected-test/CI coverage for the Claude client. | Three new routing tests, fast gate, full CI: 145 Node tests, builds, fixture parity, architecture checks, Biome on 94 files. |
| `dobby-ios` | Kept useful root guidance; corrected current model controls, gateway paths, MCP caveats, and mobile recovery intent. | Edited links/diffs; native/simulator/live-stack tests unnecessary for documentation-only changes. |
| `documents` | **Kept:** compact copy-only/original-preservation and index/data contracts already serve the task. | 27 tests plus syntax/conflict checks. |
| `focus` | Deleted duplicate workflow/docs manuals; routed current state to runtime owners and archived dated audit/rollout evidence. | 33 shell checks, local tests/compile/verification, provider and installer dry runs. |
| `frontier-lab-intelligence` | Preserved parked state; simplified both-audience skill routing, current PDF/delivery ownership, and mapping docs; archived research provenance. | Parked gate: 282-entry build log, 140 Python syntax checks, 64 frontend tests; skill parsed. |
| `futureoflife-podcast` | Corrected false parity claims, historical-export versus WIN publishing ownership, and sanitizer limitations. | Static build: 293 pages; links/diffs. |
| `home-automation` | **Kept:** conditional device ownership and authorization guidance already fits; unfinished Hue acceptance remains active. | 19 offline tests plus scaffold/syntax/link checks. |
| `litellm` | Removed the duplicate repo-contract manual; kept config/image ownership and useful operations. | 36 local tests; staged checks had no input. |
| `local-transcription` | Added three useful routes; kept substantive operational documentation. | 105 tests and five CLI/deploy help surfaces. |
| `meeting-capture` | Clarified current audio capture versus deferred transcription; corrected design ownership and repetitive harness prose. | Swift build passed; existing SDK deprecation/CLT path warnings remain. |
| `modal_functions` | Made function intake conditional and corrected the guarded release command while retaining caller/container contracts. | Registry and skill validation; staged Python/import checks had no input. |
| `platform-ops` | Removed retired bridge/missing migration routes and restored visibility of unfinished recovery acceptance in its existing owner document. | Links/diffs; fast gate explicitly skipped with no staged input. |
| `scripts` | Replaced source/Git-flow inventories with command and owner routes; retained actual machine runbooks and repaired recovery links. | 348 tests, 119 shell checks, local client/registry/health fixtures. |
| `stadia-macos-controller` | Consolidated install/recovery in deployment guidance and separated guide release ownership; retained signing, Accessibility, and dictation facts. | Guide/config/redaction/release checks; 40 mapping actions including 14 Codex controls. |
| `thoughtforms-life` | Corrected parity, publication ownership, and sanitizer claims while preserving distinct site identity. | Static build: 230 pages; links/diffs. |
| `trenopoulospraxis` | Removed a missing migration route; separated protected current form behavior from old containment/release history. | Python/shell syntax and diff checks. |
| `win` | Removed universal test/template requirements; simplified invoice routing while retaining financial policy and unique historical evidence. | Docs gate, invoice-reference consistency, skill parse; staged Python checks had no input. |

## Evidence and Limits

Shared bootstrap and `scripts/check-agent-control-planes.sh` passed: all 28 managed repo configurations validate, hook drift is zero, and runtime plugin auditing reports zero errors/warnings. The separately registered but absent `codexclaw` checkout was skipped by the hook enrollment check; it is not one of the 28 primary repos. No retired-client cleanup remains pending.

The shared gate passed 267 hermetic regression tests. `scripts/check-fast.sh` also passed. All 55 active/plugin/repo-local or newly registered skill sources checked by the skill validator passed. A focused scan of 107 local links and literal resource routes in the changed shared skill trees passed after broken companion references were repaired. The rendered global guidance matches its canonical source; adopted skill links resolve, and the chart helper is absent from global runtime.

Independent review confirmed that the shortened guidance retains autonomous completion, carried authorization, noninteractive clients, personal preferences, and operational boundaries. Review findings about legacy CLI prompts, design deployment ownership, and missing companion routes were fixed. Repository workers checked changed incoming links as well as deletions. Coverage verification matched all 28 primary Git roots.

No production deployment, live assistant turn, paid render, customer publication/invoice, private corpus operation, recording, or device/phone action was used as proof. FLI's gate deliberately omits runtime/data checks while parked and without dependencies. Staged-only gate success is not claimed as application validation. No model-performance improvement was measured. Private identity/journal/state files and public/customer content were preserved; unrelated concurrent edits were excluded from this project's change accounting.

## Separate Existing Follow-ups

These are application or operational acceptance issues, not unfinished guidance cleanup. Their limitations are recorded in the owning repository rather than hidden by corrected prose:

- Gateway Claude persona loading still reads legacy JSON while personal workspaces use Markdown: `dobby-gateway/docs/references/claude-runtime.md`.
- The phone's Opus label/wire value is currently aliased to Sonnet by the gateway: `dobby-ios/docs/architecture/mobile/iphone-codex-controls.md`.
- Full-service backup/restore and real reboot/missing/full-disk acceptance remain unproved: `platform-ops/docs/architecture/home-object-storage-routing.md`, recovery acceptance section. The old migration tracker was deleted before this batch (commit `a93c745`, September 17); its unresolved acceptance was recovered from history and made visible again. Abandoned multipart cleanup is separate.
- Hue physical pairing/device acceptance remains in `home-automation/docs/projects/hue-cli/tasks.md`.
- The two podcast sites' legacy regex cleanup is not a general untrusted-HTML sanitizer; accepting arbitrary untrusted exports needs separate hardening. Their `docs/references/content-pipeline.md` files state this boundary.

## Lessons and Closeout

Shorter entrypoints alone are insufficient when companion references reintroduce mandatory reading, redundant documentation, or permission prompts. Correct the whole active route and keep existing authorization explicit. Code-first guidance still needs non-obvious ownership, recovery, privacy, and product intent; those were retained. Already-useful repositories do not need edits to satisfy a cleanup target.

The earlier inactive proposals and analysis were superseded by this implementation and removed after their useful decisions and review results were incorporated here; Git retains their history. Disposable worker reports and raw check logs were removed after their outcomes were integrated here. No new audit framework or standing documentation obligation was added.

The whole-directory archive helper returned `source_removed: true`; the active project path is absent. Archive-relative links and final repository hygiene/whitespace checks passed. This archived record is the completion receipt; subsequent work should use current owning guidance rather than reopen the superseded proposals.
