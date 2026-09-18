---
name: skill-creator
description: Create, edit, import, adopt, scope, or distribute agent skills through the agents control plane. Use for SKILL.md and UI metadata changes, registry ownership, upstream refreshes, and reproducible runtime links.
---

# Skill Creator

`~/GitHub/agents` owns managed skill sources and distribution. Follow its repo guidance, edit canonical source rather than runtime symlinks, and keep `skills/registry.json` as the only mapping manifest. Carry the user's existing authorization across repo boundaries when the work requires it.

## Placement and Content

- Keep a one-repo skill in that repo's `.agents/skills/<name>` and declare it in `unmanaged_repo_local_skills`.
- Use `skills-source/owned/<name>` for locally maintained shared sources. Use `external` for upstream sources that remain refreshable; adopt intentional local drift into `owned` and set `upstream_ref` to `-`.
- Choose the narrowest useful scope: repo targets, `dormant` for retained but unlinked capabilities, or `global` for the small default kit. Align repo skill targets with any required MCP scope.
- Preserve the name unless a rename is requested. For authored skills, frontmatter needs `name` and a concise, specific `description`; put specialized detail in the body or an existing relevant reference.
- Add knowledge or tools that improve execution. Remove generic instructions, duplicate code descriptions, and fixed conversation recipes. Do not create a skill, reference, README, or template just to fill out a structure.

For content design decisions, see `references/skill_design.md`. For registry entries, adoption, imports, and exact sync commands, use `references/control_plane_lifecycle.md`. UI metadata fields and invocation policy are in `references/openai_yaml.md`.

## Entry Points

Use `scripts/bootstrap-skill.sh <skills.sh-url-or-upstream-ref> --repo <repo>` from the control-plane root for a normal external import. For a new owned skill, the optional `scripts/init_skill.py` beside this skill scaffolds only the resources requested; remove unused placeholders.

Validate an edited skill with the bundled helper:

```bash
python3 /Users/dobby/GitHub/agents/skills-source/owned/skill-creator/scripts/quick_validate.py <skill-dir>
```

Update `agents/openai.yaml` when user-facing behavior or scope changes. Quote the default prompt so the shell preserves the skill name:

```bash
python3 /Users/dobby/GitHub/agents/skills-source/owned/skill-creator/scripts/generate_openai_yaml.py <skill-dir> --interface 'display_name=Example Skill' --interface 'short_description=Describe the specific capability clearly.' --interface 'default_prompt=Use $example-skill to complete this task.'
```

The Python helpers require PyYAML. Test added or changed executable helpers against their actual behavior; wording-only edits need parsing and route checks.

Registry/distribution changes require shared bootstrap and checks in the same change: `~/GitHub/agents/scripts/bootstrap-machine-agent-control-planes.sh --apply`, then `~/GitHub/agents/scripts/check-fast.sh` and applicable control-plane validation. Scoped bootstrap/check takes an exact `--repo <repo-root>`. Keep generated repo links with their canonical registry/source change; do not include unrelated work in manual staging.
