---
name: client-interface-guidelines
description: Design or review command-line interfaces used by agents, including machine output, errors, non-interactive operation, retries, credentials, and delivery-route reporting.
---

# Client Interface Guidelines

Design for callers that need to identify state, act without prompts, inspect the result, and recover from failure. Honor the owning repo's existing interface contract; do not redesign an established CLI simply to match this skill's examples.

Keep machine output deterministic and separate from diagnostics. Use stable failure codes, secure secret input, and explicit retry/timeout semantics. Normal operations must run without interactive prompts. Support operator inspection when useful without changing the semantic contract based on TTY detection.

## References by Decision

- New machine contract or envelope: `references/09-agent-first-contract.md`.
- Help and discovery: `references/02-basics-help-docs.md`.
- Output and errors: `references/03-output-errors.md`.
- Arguments and interaction: `references/04-arguments-interactivity-subcommands.md`.
- Retries, interruption, compatibility: `references/05-robustness-future-signals.md`.
- Configuration and secrets: `references/06-configuration-environment.md`.
- Packaging and naming: `references/07-naming-distribution-analytics.md`.
- Choosing among local/remote/cloud delivery paths: `references/12-delivery-route-selection.md`.

Use existing contract tests for affected behavior. `references/11-agent-test-matrix-template.md` supplies examples when designing coverage, not a mandatory suite. Report consequential gaps and evidence in the format the task needs.
