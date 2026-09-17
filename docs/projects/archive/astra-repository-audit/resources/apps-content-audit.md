# Apps and content repositories: Astra / agent-native audit

Read-only snapshot: 17 September 2026. Coverage: all 11 assigned primary repositories.
The factual inventory is in [apps-content-coverage.json](apps-content-coverage.json).

## Conclusion

Most of these repositories already have compact root guidance and useful local validation.
The best cleanup is **repairing conflicting or missing sources of truth and making reading
conditional**, not imposing a smaller document count everywhere. The most concrete skill
problems are stale FLI workflows, an absent company-context skill, and a roughly 2,700-character
SwiftUI skill description. Small sites often need one or two corrections, not restructuring.

This applies the user-supplied Astra article and the agent-native playbook: retain ownership,
material boundaries, working commands, and completion proof; move detailed procedures behind
task-specific routes; remove duplicated prescriptions and superseded facts after preserving
unique knowledge. No target repository was edited. No application, deployment, collection,
recording, model-provider, customer-data, or live-service checks were run.

## Inventory and interpretation

All 11 working trees were clean at inspection. HEAD and dirty counts are recorded below;
no dirty filenames or private input contents are included. The inventory is a point-in-time
snapshot, not a claim about future working-tree state.

| Repository | Purpose / type | HEAD | Dirty |
| --- | --- | --- | ---: |
| `.github` | Organization profile and GitHub ownership boundary | `48051729fde5e5d2ebab2b7a1e0808676b5f64af` | 0 |
| `adi-design` | Canonical design tokens/specimens and static showroom | `039e8c723eb3bb4ebd290d557f52da56eef74f5e` | 0 |
| `aipodcasting-website` | Public Astro marketing site | `0d3979417860bf03fec27c7f9ea0d385a3fee278` | 0 |
| `blog-personal` | Astro blog, local authoring studio, static serving | `a28cefc409fb8890f5c32f81cbfd865fb3a932e8` | 0 |
| `focus` | Local DNS / app focus policy and enforcement tooling | `c7799a80a609f2ea56e25a38fb1d16a0a5a1bf74` | 0 |
| `frontier-lab-intelligence` | Parked research / intelligence application | `2b404080a6edb87fbf0a4446f17fa00527f82c6b` | 0 |
| `litellm` | Owned LiteLLM deployment/configuration repository, not the upstream codebase | `ab36a2af7fdea47330654f07f1a62a217e6675d1` | 0 |
| `meeting-capture` | Local SwiftUI audio-capture app with future transcript contracts | `434e63d626dbe13ce70e657beb6d9fe413ec1895` | 0 |
| `stadia-macos-controller` | Swift input bridge and read-only mapping guide | `32b7a0820f659b74c57d74b0b259375b394b194b` | 0 |
| `thoughtforms-life` | Static Astro podcast site, published through WIN | `996ec0a458c13d7aa0c2cf2332d4e5f158d5742d` | 0 |
| `trenopoulospraxis` | Flask public site with protected forms and local production delivery | `da065b8f7856e6a13ffbd07706052e2960ac89ae` | 0 |

Counts below cover tracked `.md`, `.mdx`, and `.rst` files. `Refs` excludes archive subtrees.
`Other` is inside `docs/`; root product files and published content appear only in `All text`.
Every repo also has a generated `.claude/CLAUDE.md` importer: 1 line / 14 bytes, containing
`@../AGENTS.md`. These importers are not independent instruction manuals. No authored nested
`AGENTS.md` appeared in the tracked inventory.

| Repository | Root AGENTS lines / bytes | All text | docs total | Architecture | Refs | Active project docs | Archive | Changelog | Other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `.github` | 17 / 746 | 4 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| `adi-design` | 73 / 3,565 | 18 | 2 | 1 | 1 | 0 | 0 | 0 | 0 |
| `aipodcasting-website` | 77 / 3,569 | 12 | 7 | 1 | 6 | 0 | 0 | 0 | 0 |
| `blog-personal` | 82 / 4,189 | 80 | 8 | 1 | 7 | 0 | 0 | 0 | 0 |
| `focus` | 52 / 2,581 | 23 | 17 | 3 | 14 | 0 | 0 | 0 | 0 |
| `frontier-lab-intelligence` | 80 / 3,956 | 42 | 32 | 2 | 24 | 0 | 5 | 0 | 1 |
| `litellm` | 31 / 1,361 | 34 | 31 | 1 | 3 | 0 | 0 | 27 | 0 |
| `meeting-capture` | 32 / 2,026 | 6 | 3 | 1 | 2 | 0 | 0 | 0 | 0 |
| `stadia-macos-controller` | 44 / 2,337 | 15 | 11 | 3 | 6 | 1 | 1 | 0 | 0 |
| `thoughtforms-life` | 26 / 1,610 | 5 | 2 | 1 | 1 | 0 | 0 | 0 | 0 |
| `trenopoulospraxis` | 36 / 1,831 | 5 | 3 | 1 | 2 | 0 | 0 | 0 | 0 |

There are **244 tracked text files but only 117 under `docs/`**. Published blog content,
design component specifications, historical changelogs, and archived contracts are not
equivalent to always-loaded instructions. Stadia's two project documents are empty-state
README indexes, not projects: **none of these 11 repositories has an active tracked
`docs/projects/**/tasks.md`**. Missing tracker references below therefore cannot be treated
as live execution state.

The shared registry currently supplies 10 global standalone skills. This table records
additional repo-level skills only; native plugin skill exposure was not inspected here.
Claude links to the same canonical skills do not create additional authored copies.

| Repository | Managed repo skills | Repo-owned skills | Fit / action |
| --- | --- | --- | --- |
| `.github` | None | None | Appropriate for a tiny configuration repository. |
| `adi-design` | None | None | Global `adi-design` provides the identity workflow; no extra local skill needed. |
| `aipodcasting-website` | None | None | Root requires absent `aip-company`; repair the authority route. |
| `blog-personal` | `adi-writing` | `blog-posting` | Sensible separation of voice and repository mechanics; keep task-specific activation. |
| `focus` | None | None | Commands/references are sufficient. |
| `frontier-lab-intelligence` | `adi-writing`, `fli-review`, `openai-docs` | `fli-daily-intelligence` | Reasonable specialization, but review/daily skills are stale; local skill is unregistered. |
| `litellm` | None | None with a `SKILL.md` | A residual `litellm-security-unlock/` directory has `agents/` and `scripts/`, but no entry skill. Do not count it as loaded. |
| `meeting-capture` | `swiftui-specialist`, `swiftui-whats-new-27` | None | Both fit the platform; shorten SDK skill metadata, preserve conditional technical references. |
| `stadia-macos-controller` | None | None | Existing config and checked clients are sufficient. |
| `thoughtforms-life` | None | None | Appropriate. Avoid applying personal-brand skills to an intentionally distinct site without a matching request. |
| `trenopoulospraxis` | None | None | Appropriate. Repository-specific contracts are more useful than additional generic skills. |

## Repository findings

### 1. `.github` — one stale public link; otherwise leave small

**Working:** [AGENTS.md:6](/Users/dobby/GitHub/.github/AGENTS.md:6) states a concrete
ownership boundary in 17 lines. The [boundary reference:3](/Users/dobby/GitHub/.github/docs/github-actions-boundary.md:3)
is only 11 lines. There is no reason to impose a full architecture/reference/project tree.

**Confirmed:** [README.md:7](/Users/dobby/GitHub/.github/README.md:7) points to
`docs/github-actions-retirement.md`, which is absent. The current document is
`docs/github-actions-boundary.md`. Root routing already uses the correct path.

**Keep / Move / Delete:** Keep the public README and ownership constraint. Fix that one
link; no moves or deletions are justified. If the repeated boundary text later diverges,
keep the detail in the existing reference and a short public summary in README.

**Check/proof route inspected:** [check-fast.sh:6](/Users/dobby/GitHub/.github/scripts/check-fast.sh:6)
checks staged conflict/whitespace issues and optional workflow lint;
[check-full.sh:14](/Users/dobby/GitHub/.github/scripts/check-full.sh:14) supports an empty workflow
directory. A link existence check and diff inspection are enough for this edit. Running or
adding hosted workflows would be unrelated.

**Priority:** Immediate, tiny repair.

### 2. `adi-design` — keep the canon; reduce repeated operational routing

**Working:** Root guidance identifies the single design canon and generated consumer
boundary ([AGENTS.md:25](/Users/dobby/GitHub/adi-design/AGENTS.md:25)). Component prompts and
`system/INTEGRATION.md` are product specifications, not stray operational docs. The two
documents under `docs/` have distinct architecture and delivery purposes.

**Candidate:** [AGENTS.md:19](/Users/dobby/GitHub/adi-design/AGENTS.md:19) gives an unconditional
three-document start sequence. Root hosting details at
[AGENTS.md:59](/Users/dobby/GitHub/adi-design/AGENTS.md:59) repeat
[deploy-and-sync.md:14](/Users/dobby/GitHub/adi-design/docs/references/deploy-and-sync.md:14).
For a specimen edit, deployment and integration reading are unnecessary. Make these
routes conditional: canon changes → integration; showroom changes → architecture;
production work → deploy reference.

**Candidate consistency clarification:**
[INTEGRATION.md:15](/Users/dobby/GitHub/adi-design/system/INTEGRATION.md:15) calls the
components reference specifications rather than shipping code, while
[architecture:51](/Users/dobby/GitHub/adi-design/docs/architecture/how-adi-design-works.md:51)
explains the showroom imports the actual component sources. This can be clarified as
“showroom uses these implementations; consumers may import or port them” without moving
specifications or inventing a packaging system.

**Keep / Move / Delete:** Keep one-way token ownership, versioning, generated boundaries,
commands, and the cross-repo ownership route. Move root hosting specifics to the existing
reference; consolidate repeated explanations of where authoring happens. Delete no
component prompts or canon resources based on file count.

**Check/proof route inspected:** [check-fast.sh:11](/Users/dobby/GitHub/adi-design/scripts/check-fast.sh:11)
includes shell/Node and delivery-contract tests, with Astro validation selected by staged
paths; [check-full.sh:21](/Users/dobby/GitHub/adi-design/scripts/check-full.sh:21) prepares
specimens, checks Astro, and builds. Existing tests establish release mechanics; future
visual changes still need preview inspection. Documentation-only routing needs links and
diffs, not a deployment.

**Priority:** Near-term, after the shared guidance pilot; low need for structural change.

### 3. `aipodcasting-website` — repair missing company authority and distinguish fallback proof

**Working:** The site is clearly static, content is typed and located in data modules, and
the current public deployment is documented as Cloudflare Pages. The
[production contract:42](/Users/dobby/GitHub/aipodcasting-website/docs/references/production-contract.md:42)
explicitly describes local checks that do not publish. Preserve the short public README.

**Confirmed missing source:** [AGENTS.md:43](/Users/dobby/GitHub/aipodcasting-website/AGENTS.md:43)
and [content-model.md:35](/Users/dobby/GitHub/aipodcasting-website/docs/references/content-model.md:35)
require the managed `aip-company` skill for factual authority. That skill has no registry
entry, no global runtime directory, no canonical owned source, and no repo-local skill.
Choose the present canonical company source and route there; do not recreate a skill merely
to satisfy an obsolete name. Existing company claims must not be reauthored by inference.

**Confirmed ambiguous command naming:**
[package.json:16](/Users/dobby/GitHub/aipodcasting-website/package.json:16) exposes
`deploy:mac-mini` and `verify:production`, but the latter builds and probes the local
fallback, as [production-contract.md:16](/Users/dobby/GitHub/aipodcasting-website/docs/references/production-contract.md:16)
acknowledges. An agent following the command table can finish with a healthy fallback
without evidence about public Pages. Label the fallback commands consistently and route
public-release verification to Pages status / public route proof. This is a semantics
cleanup, not evidence that the deployment is broken.

**Candidate:** Replace the seven-item
[docs read order:62](/Users/dobby/GitHub/aipodcasting-website/AGENTS.md:62) with task routes.
The design reference [calls the skill canon:3](/Users/dobby/GitHub/aipodcasting-website/docs/references/design-system.md:3)
and then copies its generic rules; the shared skill itself identifies `adi-design/system/`
as canon. Keep local HSL/Tailwind integration facts and point to the actual canon for design
values, avoiding a third editable rules copy.

**Keep / Move / Delete:** Keep static-site scope, data ownership, company-truth boundary,
content and contact contracts. Move fallback-only operational detail out of default reading.
Delete the stale skill name only after replacing the authority route. Consolidate copied
design principles while retaining local conversions and layout constraints.

**Check/proof route inspected:** `pnpm check:fast` selects staged Astro/config and formatting
checks; `pnpm check:full` builds and checks the local capabilities/public-site contract.
For docs changes, validate routes. For command renaming later, validate package scripts and
their callers; for a site change, run the local full gate and inspect the affected preview.
No public deploy or production probe was performed in this audit.

**Priority:** First cleanup pass for the absent authority and command semantics.

### 4. `blog-personal` — selective reading and one content contract

**Working:** The local [blog-posting skill:8](/Users/dobby/GitHub/blog-personal/.agents/skills/blog-posting/SKILL.md:8)
has a narrow mechanical purpose and only 29 lines. `adi-writing` is independently scoped to
voice. Published posts are product content, so the 80-text-file count is not documentation
overload. [check-full.sh:18](/Users/dobby/GitHub/blog-personal/scripts/check-full.sh:18)
builds and probes an isolated loopback artifact, providing a concrete autonomous completion
path without altering the active release.

**Confirmed small fact drift:** Root's “required frontmatter” list
([AGENTS.md:26](/Users/dobby/GitHub/blog-personal/AGENTS.md:26)) and
[content-verification.md:38](/Users/dobby/GitHub/blog-personal/docs/references/content-verification.md:38)
call `tags` required, while [content.config.ts:21](/Users/dobby/GitHub/blog-personal/src/content.config.ts:21)
defaults missing tags to an empty string. The duplicated schema prose has already drifted.
Keep the schema authoritative and explain only the author-facing rules that need prose.

**Candidate reading overhead:** The
[root read order:59](/Users/dobby/GitHub/blog-personal/AGENTS.md:59) routes ordinary work through
architecture, design, verification, hosting, production, secrets, and a prior cleanup audit.
Use content/design/deployment-specific routes. The historical cleanup-candidate document
already [says it is evidence:3](/Users/dobby/GitHub/blog-personal/docs/references/post-cloud-simplification-audit.md:3),
not a reason to mix unrelated cleanup into delivery; it should not be default startup reading.

**Keep / Move / Delete:** Keep content ownership, slug/visibility semantics, exact check and
preview entrypoints, and immutable release ownership. Move root schema detail into the
existing content reference. Delete duplicate default-gate wording and the blanket read
sequence. Preserve posts, studio documentation, and unique migration evidence.

**Check/proof route inspected:** [check-fast.sh:35](/Users/dobby/GitHub/blog-personal/scripts/check-fast.sh:35)
uses the staged set for frontmatter and Astro checks; before staging it still runs contract
tests and the storage-URL scan but can skip the changed content. State this explicitly in
command guidance so an unstaged invocation is not mistaken for full content proof. For
real content/layout work use the relevant direct check or isolated full gate and inspect
the changed page. No new test needed merely to shorten routing prose.

**Priority:** Near-term pilot for conditional routing and a single content authority.

### 5. `focus` — historical status is masquerading as current guidance

**Working:** The repo keeps focus policy separate from providers and generated state.
Its [default check:11](/Users/dobby/GitHub/focus/automation/check-fast.sh:11) describes the
absence of live provider mutation and network refresh; the implementation exercises policy
tests, local compilation, and dry-run provider/install paths. The
[commit adapter:35](/Users/dobby/GitHub/focus/scripts/check-fast.sh:35) selects that check
for relevant staged changes. Dry-run defaults and emergency recovery are meaningful
boundaries, not overcautious generic instructions.

**Confirmed stale state:** [current-state.md:100](/Users/dobby/GitHub/focus/docs/references/current-state.md:100)
says `docs/projects/repo-hardening/tasks.md` “now holds” active state and routes to it again
at line 114. That file is absent. The
[April audit:11](/Users/dobby/GitHub/focus/docs/references/agent-native-audit.md:11) repeatedly
treats it as current and still recommends future closeout. A historical audit and present
status now reinforce the same dead route.

**Confirmed duplication / candidate consolidation:**
[agent-workflow.md:5](/Users/dobby/GitHub/focus/docs/references/agent-workflow.md:5),
[docs-contract.md:5](/Users/dobby/GitHub/focus/docs/references/docs-contract.md:5), and root
guidance repeat the global operating model, docs placement, tracker rules, and baseline
validation. The workflow's five-document startup list allows narrower tasks, which is
better than an absolute requirement, but still makes generic policy the default route.

**Keep / Move / Delete:** Keep policy ownership, generated-state boundary, dry-run/recovery,
and the concrete fast-check route. Put current shipped behavior first in current-state;
move dated audit findings to an archival location or mark them clearly superseded.
Consolidate generic workflow/docs-contract prose into the shared playbook or a few local
exceptions, then remove redundant files only after preserving unique facts and updating
links. Remove the missing tracker assertion rather than recreating an empty active project.

**Check/proof route inspected:** `scripts/check-fast.sh` is the staged hook adapter;
`automation/check-fast.sh` is the complete local baseline. `scripts/check-full.sh` currently
just invokes the same baseline. Explain that relationship rather than assuming “full”
provides live enforcement proof. Runtime enforcement changes require the relevant provider
dry run and controlled proof; a docs cleanup does not justify changing DNS, installing a
filter, or testing emergency unlock.

**Priority:** First cleanup pass for stale status; near-term for generic prose consolidation.

### 6. `frontier-lab-intelligence` — skills have not followed the current architecture or parked state

**Working:** The root leads with an explicit parked state
([AGENTS.md:7](/Users/dobby/GitHub/frontier-lab-intelligence/AGENTS.md:7)); the
[service lifecycle:74](/Users/dobby/GitHub/frontier-lab-intelligence/docs/references/service-lifecycle.md:74)
provides a dependency-free maintenance mode and a distinct runtime-required gate. The
[implementation contract index:55](/Users/dobby/GitHub/frontier-lab-intelligence/docs/references/implementation-contracts.md:55)
already moved a 1,200-line catch-all into an archive and labels it historical. Preserve that
successful split. The 24 current references cover real pipeline boundaries; count alone
does not justify combining them back into one manual.

**Confirmed stale managed review skill:**
[fli-review:21](/Users/dobby/GitHub/agents/skills-source/owned/fli-review/SKILL.md) references
absent `docs/references/context.md`; its [line 37](/Users/dobby/GitHub/agents/skills-source/owned/fli-review/SKILL.md)
references retired `docs/references/build-log.jsonl`, which the current fast check
[explicitly forbids:42](/Users/dobby/GitHub/frontier-lab-intelligence/scripts/check-fast.sh:42).
Its prescribed startup loads trackers and assumes running data/product surfaces. The
root now makes trackers opt-in and the service intentionally unavailable. Route reviews
through current status, the task-specific contract, and parked-state limits; derive the
current objective from the session instead of forcing a stale interview-deadline gate.

**Confirmed stale repo skill:**
[fli-daily-intelligence:8](/Users/dobby/GitHub/frontier-lab-intelligence/.agents/skills/fli-daily-intelligence/SKILL.md:8)
says one Investment path produces every Insight, and
[line 141](/Users/dobby/GitHub/frontier-lab-intelligence/.agents/skills/fli-daily-intelligence/SKILL.md:141)
says Engineering has no run. Current
[insight-refresh.md:7](/Users/dobby/GitHub/frontier-lab-intelligence/docs/references/insight-refresh.md:7)
documents independent Investment and Engineering generators, and the Engineering generator
exists at [engineering_agent.py:1](/Users/dobby/GitHub/frontier-lab-intelligence/src/fli/insights/engineering_agent.py:1).
The skill also assumes an [always-on app:111](/Users/dobby/GitHub/frontier-lab-intelligence/.agents/skills/fli-daily-intelligence/SKILL.md:111).
It duplicates implementation fields and workflow recipes already maintained in the
reference and live CLI contract. Reduce it to a daily-brief task router with current
audience selection, publication boundary, and completion proof; retain historical outputs.

**Confirmed registry gap:** The tracked local `fli-daily-intelligence` skill is not listed in
`skills/registry.json`'s `unmanaged_repo_local_skills`, whereas blog's local skill is
([registry:411](/Users/dobby/GitHub/agents/skills/registry.json)). Reconcile registration
in the control plane when retaining this skill. Do not hand-edit runtime symlinks.

**Candidate guidance improvements:** Root
[start sequence:16](/Users/dobby/GitHub/frontier-lab-intelligence/AGENTS.md:16) requires broad
context even for small maintenance. Root
[precedence wording:23](/Users/dobby/GitHub/frontier-lab-intelligence/AGENTS.md:23) says to
follow the preserved external prompt when chat conflicts; clarify that it is the default
scope when intent is ambiguous and that current explicit user decisions supersede it.
Keep actual publication/contact boundaries and the parked-state prohibition.

**Keep / Move / Delete:** Keep lifecycle/data ownership, provenance, provider routing,
atomic publication, and explicit external-delivery boundaries. Move implementation detail
from the daily skill into its existing owning references. Delete obsolete routes, old
audience assertions, and forced broad reads. Archive no research data and resume no service
as part of this cleanup. Generated build-log history can retain historical paths; do not
rewrite generated history merely because paths later changed. Two current references also
link absent archival proof files (artifact-library:271 and registry-curation:88); repair
those citations or label the evidence unavailable, without inventing proof.

**Check/proof route inspected:** `scripts/check-fast.sh` is not a pure read: it may render
and stage a build-log artifact ([line 103](/Users/dobby/GitHub/frontier-lab-intelligence/scripts/check-fast.sh:103))
and, with dependencies restored, runs broader tests/builds and stages SPA output. This audit
did not invoke it. After an authorized docs/skill change use the parked maintenance gate
and inspect any generated diff. Use `--require-runtime` only for actual resumed runtime
work. Neither mode licenses collection or external delivery.

**Priority:** First cleanup pass for stale skills and registration; keep runtime parked.

### 7. `litellm` — healthy compact operational docs; history does not need blanket deletion

**Working:** This is the small owned proxy configuration/deployment repository, not an
upstream LiteLLM checkout. [AGENTS.md:8](/Users/dobby/GitHub/litellm/AGENTS.md:8) assigns
runtime versus machine-reconciler ownership. Of 31 docs, 27 are dated changelogs. Current
knowledge is one architecture document plus a small reference set. The
[operations health policy:117](/Users/dobby/GitHub/litellm/docs/references/operations.md:117)
explicitly prevents provider calls during health checks—retain it.

**Confirmed minor wording drift:** [repo-contract.md:3](/Users/dobby/GitHub/litellm/docs/references/repo-contract.md:3)
says all `CLAUDE.md` files are absent. A generated `.claude/CLAUDE.md` importer is tracked.
Express the actual constraint as no independently authored duplicate guidance. The
manual `find` instruction at line 43 is a candidate for removal if managed surface checks
already prove that contract.

**Candidate:** The global operating/docs contract is repeated between root and
[repo-contract.md:28](/Users/dobby/GitHub/litellm/docs/references/repo-contract.md:28). A small
consolidation is sufficient. The residual skill directory without `SKILL.md` can be
investigated during ordinary cleanup, but its scripts may still have callers; absence from
skill loading does not prove the directory is disposable.

**Keep / Move / Delete:** Keep exact model-route, secret materialization, storage identity,
no-provider-health, and rollback facts. Keep dated changelogs outside default reading.
Delete no historical document merely to reduce the total. Remove only redundant guidance
and false generated-file assertions.

**Check/proof route inspected:** [check-fast.sh:24](/Users/dobby/GitHub/litellm/scripts/check-fast.sh:24)
runs local Python regression tests; full adds repository checks and compilation. The
[operator contract:24](/Users/dobby/GitHub/litellm/docs/references/operations.md:24) provides
isolated candidate state, liveness/readiness, guarded activation, and recovery. A docs
cleanup needs no model request, deployment, state inspection, or cloud quota action.

**Priority:** Later / opportunistic. Strong candidate to leave structurally unchanged.

### 8. `meeting-capture` — clarify present output and shorten SDK metadata

**Working:** [Root boundaries:5](/Users/dobby/GitHub/meeting-capture/AGENTS.md:5) cleanly
separate a generic local app from downstream personal memory. The
[harness reference:39](/Users/dobby/GitHub/meeting-capture/docs/references/agent-harness.md:39)
distinguishes launch proof from permission-gated recording proof. Human OS permission is
a real limit, not an unnecessary model approval ritual. The three docs have distinct uses.

**Confirmed current/future ambiguity:** Root introduces a transcript app and says the raw
transcript is the primary artifact, but
[architecture:21](/Users/dobby/GitHub/meeting-capture/docs/architecture/overview.md:21) and
[output contract:21](/Users/dobby/GitHub/meeting-capture/docs/references/transcript-output-contract.md:21)
say audio-only is current and transcription is not wired. The output reference opens with
“writes raw transcript records” before correcting that below. Current source initializes
audio recorders ([AppState.swift:49](/Users/dobby/GitHub/meeting-capture/Sources/MeetingCapture/Stores/AppState.swift:49)).
Lead with shipped audio output and label the paired Markdown/JSON format explicitly as a
future contract. Preserve the contract; do not implement transcription during a docs audit.

**Confirmed skill metadata overload:**
[swiftui-whats-new-27:3](/Users/dobby/GitHub/agents/skills-source/external/swiftui-whats-new-27/SKILL.md)
has a roughly 2,700-character description, including API error recipes and many feature examples.
The root body already routes to topical references. Shorten metadata to SDK-27 adoption,
migration and matching errors, and leave exact pitfalls in references. Preserve the
source's technical content and the managed external-skill provenance/update mechanism.
The 20-line `swiftui-specialist` root is already a conditional reference router; the two
skills have complementary baseline versus release-specific jobs.

**Keep / Move / Delete:** Keep app/downstream ownership, user-selected local output,
macOS target, concrete build commands, and honest proof boundaries. Move prospective
output descriptions under a clearly labeled future section. Remove stale “once
implementation resumes” qualifiers from commands only after confirming whether they
describe project intent or merely leftover wording; do not infer an authorized resume.

**Check/proof route inspected:** Fast is `swift build`. Full additionally bundles and
launches the app, checks minimum system version and the microphone purpose string, and
its cleanup can kill the named running process
([check-full.sh:10](/Users/dobby/GitHub/meeting-capture/scripts/check-full.sh:10)). Full is
therefore appropriate for app/permission changes, not every wording update. Use only the
required source/link checks for docs and metadata; never claim recording proof from build
success.

**Priority:** First shared skill-metadata pass; near-term for present/future doc wording.

### 9. `stadia-macos-controller` — consolidate runbooks, keep physical proof explicit

**Working:** The root names the config source and machine installer owner. The guide has
a dependency-free server and dedicated checked production client. Its full gate deliberately
does not rebuild the unrelated Swift bridge
([repo-contract.md:36](/Users/dobby/GitHub/stadia-macos-controller/docs/references/repo-contract.md:36)).
This is good proportional validation. Project README placeholders are not stale active work.

**Confirmed duplication; candidate consolidation:** Install, accessibility, hot reload,
verification and troubleshooting are repeated in
[setup.md:134](/Users/dobby/GitHub/stadia-macos-controller/docs/references/setup.md:134),
[deployment.md:18](/Users/dobby/GitHub/stadia-macos-controller/docs/references/deployment.md:18),
and [repo-contract.md:46](/Users/dobby/GitHub/stadia-macos-controller/docs/references/repo-contract.md:46).
Choose one bridge operator runbook; leave two-machine-specific signing/recovery facts
there, make setup a local-run entrypoint, and keep the root as task routing. A static guide
change should not require reading Ghostty integration or reinstalling the input bridge.

**Keep / Move / Delete:** Keep mapping ownership, canonical machine install location,
stable signed app identity, source-versus-staged-binary distinction, and genuine controller
proof. Move repeated install recipes into one existing runbook and delete duplicates
after updating links. Do not erase physical Accessibility setup or assume guide health
proves real input actions.

**Check/proof route inspected:** Fast validates guide routes/config/mappings and staged
Swift manifest changes; full adds the bridge build. Root
[validation:30](/Users/dobby/GitHub/stadia-macos-controller/AGENTS.md:30) correctly requires a
real controller action for live behavior. Future prose should distinguish “guide change,”
“mapping change,” and “bridge/runtime change” so each proof path is clear. No controller,
launchd, or live keystroke actions were exercised.

**Priority:** Near-term, modest runbook consolidation; no broad reorganization.

### 10. `thoughtforms-life` — the tiny root contains an incorrect cross-repo constraint

**Working:** Only two docs are needed. They distinguish ongoing WIN publishing from
historical Ghost bulk import. Sanitizer and permalink constraints are concrete and worth
keeping. The large tracked-file count is mostly site/media content, not guidance overhead.

**Confirmed conflicting ownership contract:**
[AGENTS.md:7](/Users/dobby/GitHub/thoughtforms-life/AGENTS.md:7) says only `src/data/` differs
from the sibling, and line 26 says design changes apply to both. Current
[architecture:35](/Users/dobby/GitHub/thoughtforms-life/docs/architecture/repo-architecture.md:35)
explicitly permits separate `src/styles/global.css` identities but claims components are
byte-identical. A read-only comparison with `futureoflife-podcast` found differences in
both `src/styles/global.css` and `src/components/Header.astro`; the header difference is
real fallback-logo markup, not merely a comment. Root instructions can therefore cause
an agent to overwrite intentional branding or incorrectly “repair” a supposed sync failure.
Define the actual shared template boundary and allowed identity differences before syncing.

**Confirmed missing route:** [AGENTS.md:12](/Users/dobby/GitHub/thoughtforms-life/AGENTS.md:12)
points to `~/GitHub/scripts/docs/projects/ghost-static-migration/tasks.md`, absent at that
path and at the corresponding archive path. Replace startup routing with the existing
durable content-pipeline owner; retain historical links only if an actual destination is found.

**Candidate:** The [historical export instructions:38](/Users/dobby/GitHub/thoughtforms-life/docs/references/content-pipeline.md:38)
still describe starting an old hosted Ghost service. This audit did not verify whether
that retired/paused cloud source is recoverable. Label it historical and verify availability
only when a real backfill requires it; do not restart it to satisfy documentation cleanup.

**Keep / Move / Delete:** Keep static scope, stable URLs, sanitizer boundary and WIN
publishing ownership. Remove the false “only data differs”/“byte-identical” promises and
dead active-tracker link. No additional skill or new documentation tree is warranted.

**Check/proof route inspected:** [check-fast.sh:6](/Users/dobby/GitHub/thoughtforms-life/scripts/check-fast.sh:6)
always builds the site. It does not test template parity or prove sanitizer behavior.
For the docs correction, inspect the shared paths and update both owners' contracts in
a coordinated pass. Future sanitizer changes warrant fixture-based verification; future
visual changes need both affected previews. Do not add a shared package or parity check
until the intentional boundary is settled.

**Priority:** First cleanup pass coordinated with the sibling site's audit.

### 11. `trenopoulospraxis` — separate current protected behavior from superseded incident history

**Working:** The root separates app/runtime ownership, synthetic local validation, and
production authorization. Keep the restriction against reading submitted private records.
The [full check:17](/Users/dobby/GitHub/trenopoulospraxis/scripts/check-full.sh:17) builds a
disposable image, runs synthetic tests, sets mail suppression, then probes a loopback
container. This is an excellent explicit autonomous validation boundary for future work.

**Confirmed missing route:** [AGENTS.md:13](/Users/dobby/GitHub/trenopoulospraxis/AGENTS.md:13)
points to absent `docs/projects/archive/mac-mini-migration/tasks.md`. The short architecture
and migration reference already preserve current ownership. Repair the historical citation
or remove it from mandatory sources; do not recreate an active migration project.

**Confirmed contradictory current/old facts:**
[local-production.md:45](/Users/dobby/GitHub/trenopoulospraxis/docs/references/local-production.md:45)
describes legacy recipient behavior. Later
[line 95](/Users/dobby/GitHub/trenopoulospraxis/docs/references/local-production.md:95) describes
the protected replacement behavior, and
[line 113](/Users/dobby/GitHub/trenopoulospraxis/docs/references/local-production.md:113)
says the emergency patch was superseded. The same reference interleaves current delivery,
an emergency disabled-state snapshot, and the replacement's operational contract. A cold
agent must read to the end to discover which facts govern.

**Keep / Move / Delete:** Lead the current reference with the protected implementation,
fail-closed configuration and rollback policy. Move the superseded incident chronology to
a clearly historical subsection or archive, preserving unique recovery evidence. Delete
the obsolete behavior assertion from the current contract. Keep meaningful production
authorization and private-data limits; Astra guidance is not a reason to weaken them.

**Check/proof route inspected:** Fast parses Python/shell and checks whitespace; full runs
the synthetic container tests and HTTP smoke. For a documentation-only correction, compare
the current handler/tests with the reference and inspect links; do not submit forms,
send email, redeploy or read production records. When real behavior changes, complete the
local synthetic gate and report its evidence before a separate production action.

**Priority:** First cleanup pass, documentation only; preserve the protected runtime.

## Recommended rollout

1. **Immediate — fix demonstrable wrong instructions.** Correct `.github`'s public link,
   the absent marketing-company authority, FLI stale skill routes/architecture/registration,
   the thoughtforms sibling contract, stale tracker links, and the protected-site current
   versus historical statements. These are concrete repairs, not speculative deletion.
2. **Near-term — apply the shared prompt policy selectively.** Convert numbered read orders
   into task routes in the three Astro sites and FLI. Consolidate focus's generic workflow
   prose and Stadia's repeated operator recipes. Shorten SDK skill metadata through the
   managed skill source workflow. Preserve relevant external technical references.
3. **Later — evaluate in actual tasks.** Use an ordinary post edit, a site visual change,
   a guide mapping change, and a parked-repo maintenance task to check whether a cold agent
   reaches the correct source, runs appropriate proof, and stops at the intended boundary.
   Add a mechanical guardrail only for a demonstrated repeated error. Do not create a
   new fleet-wide audit service or a uniform documentation skeleton for every small repo.

Success means fewer wrong routes and unnecessary reads while preserving correct autonomous
completion—not the smallest possible count of Markdown files or skills.

## Evidence and audit limits

Inspection used `git rev-parse HEAD`, `git status --porcelain=v1`, `git ls-files`, file
size/line counts, direct numbered reads, `rg`, path-existence checks, and a read-only sibling
template comparison. Root guidance, actual key references, skill entries, package command
maps, and fast/full check implementations were inspected for every repository. The report
distinguishes confirmed text/code/path mismatches from consolidation candidates.

No application/deploy/recording/network-effect suites were executed. This audit establishes
instruction and discovery issues; it does not certify application correctness, current
production health, historical output quality, or external resource availability. Runtime
and customer data were not inspected. Only this report and its coverage JSON were written.
