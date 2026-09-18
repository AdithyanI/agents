# Documentation That Earns Its Place

Code, schemas, configuration, and runnable commands are the authority for implementation. Documentation is useful when it supplies information those sources do not readily explain: intent, design tradeoffs, ownership across systems, external constraints, or recovery and operational knowledge.

## Keep, Consolidate, or Remove

- Keep unique information that prevents a plausible mistake or expensive rediscovery. Preserve public documentation, personal records, and historical evidence according to their purpose.
- Consolidate repeated knowledge into its actual owner. Prefer a link to existing source or documentation over another summary that can drift.
- Remove obsolete instructions and descriptions that only narrate discoverable code. Do not preserve every deleted paragraph in an archive or new reference.
- Distinguish active execution state from current contracts and historical records. A dated past decision is not automatically stale guidance.

Follow the repo's existing organization. Where new documentation is justified and no convention exists, use the smallest fitting location: `AGENTS.md` for orientation, `docs/architecture/` for design intent, or `docs/references/` for operational lookup. Do not create empty folders or apply a mandatory document template. Use a diagram only when it explains something more clearly.

Update affected useful docs alongside a behavior or ownership change. Check incoming links after moves and removals. Add a mechanical freshness check only for a repeated mismatch that the check can actually detect.

Use the existing project tracker for long-running work; archive the completed project according to local convention. Routine edits do not need a tracker, handoff document, or separate learnings file.
