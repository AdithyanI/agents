# Audit Learnings

## What Helped

- Three reviewers owned disjoint repository groups; parent retained discovery,
  shared contracts, privacy boundaries, and synthesis. All 27 delegated repos
  received a concrete review, and a second pass caught four semantic losses in
  the shared drafts before delivery.
- Git-tracked inventories separated docs from build caches and provided stable
  HEAD evidence. A metadata-only filesystem pass found repositories outside the
  usual folder without reading personal documents or credentials.
- Existing repo checks and skill validation supplied useful evidence. A registry
  check passing did not imply correct skill content or complete runtime links.

## Findings About the Workflow

- Short AGENTS files can route into extensive mandatory recipes; root length
  alone is a weak measure. Wrong authority and automatic intermediate stopping
  were more consequential than raw file count.
- Archived evidence, published content, product specifications, and changelogs
  need a different retention decision from current agent instructions.
- A broad machine inventory must distinguish primary repos, valid worktrees,
  unresolved worktree pointers, bare dependency caches, package sources, and
  app-owned state. Eight broken worktree relationships were not safe deletion
  candidates merely because their root guidance matched.
- Skill description measurements should parse YAML; quoting/escapes made raw
  source-scalar counts differ from the validator's 2,696-character value.

## Harness Gaps Exposed

- The existing repo Markdown checker treats a local `file:line` link as a
  literal filename. Audit-internal links were adapted to plain file targets
  with visible line labels; the canonical checker was not changed as part of
  this audit. A future checker change can support the app's line-link syntax.
- Current registry validation does not by itself catch unregistered local skill
  directories, a global copied skill, oversized skill content metadata, or
  missing applied Gateway links. Strengthen the relevant existing check only
  where that invariant is intended; no new fleet-wide service is needed.
- Link validation catches missing paths, but current-versus-historical and
  command-versus-implementation contradictions still require focused reading.
- A read-only audit can select broken Git markers for Stop-hook finalization.
  The closeout retry exposed this on two empty pre-commit caches and two orphan
  worktrees. The canonical hook was repaired to skip only candidates with
  positively absent metadata and no recorded work, including saved retries.
  Root-identity checking prevents Git from falling through to an enclosing repo;
  malformed or uncertain metadata still blocks publication. Integration tests
  verify file preservation and the retained failure behavior.

## Follow-through

Use the report's staged pilot and preservation map. Start with confirmed wrong
instructions and ownership routes; test the proposed shorter shared guidance on
representative tasks before scaling. Keep all audit evidence in this archived
project, outside routine startup context. Disposable inventory helpers are
removed at closeout; this audit adds no permanent policy or monitoring layer.
