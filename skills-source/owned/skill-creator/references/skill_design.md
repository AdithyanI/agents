# Skill Content Design

A skill should supply useful context, a capability, or a fragile local contract that a capable agent would otherwise need to rediscover. It need not prescribe a workflow. Start from the gap it closes; do not install a skill because a task happens to have a familiar name.

## Routing and Structure

For locally authored skills, frontmatter contains `name` and `description`. Use a lowercase hyphenated name under 64 characters. Keep the description under 1024 characters, without XML tags, and make its trigger precise. The body loads after selection; descriptions should identify the task rather than contain the whole procedure.

Use the body for orientation, non-obvious constraints, tool entrypoints, and conditional routes. Do not repeat generic coding advice, require a fixed reading order, or dictate conversation scripts. Leave implementation details in source where they are readily discoverable.

Add resources only when they earn their place:

- `scripts/`: repeated or fragile operations worth making executable.
- `references/`: specialized knowledge needed for a particular task or decision.
- `assets/`: material used in deliverables, such as fonts or templates.
- `agents/openai.yaml`: UI metadata and invocation policy.

Link useful references directly. Removing prose is preferable to relocating a redundant description into another file. Do not add empty resource folders, auxiliary manuals, or a mandatory document template.

## Constraints and Evaluation

Preserve real ownership, privacy, external-effect, and recovery boundaries. Give freedom where several approaches work. Prefer executable helpers for deterministic operations, and make it clear whether the agent should run or inspect them.

For a new or materially changed fragile capability, use representative tasks to verify that it closes its intended gap. Run changed executable helpers and inspect their result. A trigger wording change needs parsing and routing review, not an invented benchmark or product feature.

When use reveals a failure, fix its cause in the appropriate source, tool, or instruction. Unexpected navigation is not itself an error; change routing when it led to missing context or an incorrect result. Avoid expanding a skill to prevent every hypothetical mistake.
