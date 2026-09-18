---
name: find-skills
description: Find an existing skill when the user explicitly asks to discover, compare, or install agent skills. Use for capability discovery, not ordinary requests to perform a task.
---

# Find Skills

First check the current skill catalog and canonical `skills/registry.json` in `~/GitHub/agents`. A useful capability may already exist but be scoped to another repo or dormant. Ordinary tasks should proceed with available tools and reasoning; do not turn them into skill-installation searches.

If external discovery is needed, search a relevant upstream or skills.sh and inspect the actual skill, its tools, provenance, and fit. Popularity alone does not establish quality. Recommend a skill only when it adds useful knowledge or capability beyond what is already available.

Use the control plane for an authorized installation:

```bash
~/GitHub/agents/scripts/bootstrap-skill.sh <skills.sh-url-or-upstream-ref> --repo <repo>
```

Use `skill-creator` for adoption, custom sources, or scope changes. Keep repo-specific capabilities scoped to their owner and distribution reproducible; do not bypass the registry with a direct global package installation.

For discovery-only requests, report the useful options and tradeoffs. If nothing suitable exists, say so and continue any independently authorized work with existing capabilities. Do not create or install a new skill merely because the search found none.
