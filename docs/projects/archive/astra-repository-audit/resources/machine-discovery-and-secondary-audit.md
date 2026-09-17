# Machine Discovery and Secondary Git Locations

The scan traversed `/` using directory metadata without following symlinks. It
visited 336,292 directories in 257 seconds and found 71 `.git` directory/file
markers plus 20 bare-repository candidates. Git metadata verified all 20 bare
repositories and 61 of the 71 working-tree markers. The remaining markers are
eight unresolved worktrees and two empty pre-commit `.git` directories.

This is coverage of accessible local storage, not a claim that protected system
areas were inspectable. `/System` was excluded (immutable OS and duplicate
firmlinked data volume), along with virtual `/dev` and network automount
`/Network`. There were 227 traversal errors, mostly protected `/private/var`
and system-service directories. None was under `/Users/dobby`. The inventory
records grouped errors, exact discovered roots, and explicit exclusions.

Machine inventory: [repository-inventory.json](repository-inventory.json).
Primary metadata: [primary-repository-snapshot.json](primary-repository-snapshot.json).

## Complete Disposition

| Category | Locations | Audit disposition |
| --- | ---: | --- |
| Primary working repos in `~/GitHub` | 28 | Individually reviewed across the three group reports plus shared/control-plane review. |
| Empty unmanaged project | 1 | `~/Documents/ChatGPT/New project`: initialized Git, no HEAD, tracked files, docs, or working content. No guidance/framework needed; optionally remove only when its app/project ownership is settled. |
| Valid linked worktree | 1 | `~/.codex/worktrees/951d/agents`: same Git common directory as primary agents, clean at inspection. Apply future policy at canonical source; no independent rewrite or pruning. |
| Unresolved linked worktrees | 8 | Surviving `whos-in-your-head` checkouts; missing original Git metadata. Preserve until recovery/ownership is resolved. Reviewed separately below. |
| App runtime data | 1 | `~/.codex/memories`: retain as Codex runtime storage; inspected only Git metadata, counts, and absence of root guidance. No memory contents copied. |
| Client/vendor checkouts | 6 | Codex marketplace/plugin staging, vendor-imported OpenAI skills, and Copilot marketplaces. Preserve upstream ownership and client lifecycle. `codex/AGENTS.md` explicitly protects the nested vendor-import checkout. |
| Pre-commit cache remnants | 2 | Both `.git` directories are empty and Git cannot resolve them. Cache cleanup candidates via the owning tool; not missing personal repo guidance. |
| SwiftPM/Xcode dependency storage | 36 | 16 package checkouts plus 20 bare caches for four packages across local/derived-data stores. Preserve upstream docs; use owning build/cache lifecycle for disk cleanup. |
| Homebrew/package sources | 7 | Homebrew itself, five taps, and the Newsreader font checkout. Preserve upstream instructions. Font checkout has two tracked changes; no cleanup or discard was attempted. |
| Temporary upstream source | 1 | `scripts/tmp/iphone-update/idevicerestore-src`: clean vendor source for device-update work. Confirm the owning recovery/update task no longer needs it before removal. |

These categories account for all 91 discovered Git locations. The managed repo
registry additionally names `~/GitHub/codexclaw`, which is absent on this machine.
Missing local checkout is compatible with sparse-machine distribution and is not
by itself evidence that its canonical registry entry should be deleted.

## Unresolved Who's In Your Head Worktrees

All eight `.git` files point under the absent
`~/GitHub/whos-in-your-head/.git/worktrees/` tree. Their root `AGENTS.md`,
README, and package manifest hashes match across the eight copies. That does
**not** prove their source trees or uncommitted work are equivalent.

Each has a 49-line root, seven Markdown docs, and a Next.js app with explicit
lint, typecheck, test, and build commands. The inspected fast gate starts with
`git rev-parse`, so it cannot run normally while Git metadata is unresolved.
All eight have broken repo skill links, including the root-mandated
`azure-webapp-deploy` route. Exact per-worktree checks are recorded in
[secondary-worktree-coverage.json](secondary-worktree-coverage.json).

Keep the server-only credentials boundary, structured model-output validation,
explicit game-state contract, and local test/build routes. The branch-first
workflow is a deliberate repo exception intended to protect deployable `main`;
do not erase it simply to homogenize the portfolio. The global default permits
local exceptions.

Recommended sequence: establish whether the product was retired, preserve any
unique files, restore or deliberately retire the Git/worktree relationship,
then replace the absent deployment skill with the current verified owner route.
No deploy, provider call, package installation, or source deletion is necessary
for this audit. No generic docs rewrite is justified before ownership recovery.

## Boundaries of This Audit

External vendor and dependency checkouts are classified individually in JSON and
reviewed as ownership categories, rather than treated as personal projects to
rewrite. Public READMEs, package documentation, bare caches, and app-owned memory
are not an instruction-consolidation target. Disk reclamation is a separate
decision from improving agent guidance.
