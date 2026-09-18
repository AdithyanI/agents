# Execution and Recovery

Use this reference when improving how an agent runs, verifies, or delivers work. The skill entrypoint defines the human-agent boundary.

## Diagnose an Actual Failure

Trace a concrete task to the point where execution stalled or the outcome became uncertain. Was the missing element ownership, a runnable command, accessible state, actionable feedback, or recovery? Improve that element instead of adding a checklist for every future task.

Good tools expose stable exit codes, non-interactive execution, and focused failure output. Use structured data where another tool consumes it. Keep logs and relevant product state inspectable without exposing secrets.

## Proof and Delivery

- Use the repo's required gates and focused checks for the changed contract. Keep commit-time checks local and quick; slower validation belongs in the full-check path.
- Inspect changed UI, API, service, or workflow behavior when that establishes something static checks cannot. An unavailable proof path is a limitation to report, not a reason to claim success.
- Reuse documented lifecycle automation for commit, rebase, and push. Preserve rerun or rollback paths and explicit ownership of production, spending, secrets, and irreversible effects.
- Add a test, review step, or automation only when it closes a specific gap. Repeated failures warrant a durable fix; a one-off typo does not require a new policy layer.

For broad reviews, prioritize gaps that block completion or hide incorrect results. Do not infer repository quality from document count, prescribed folders, or the presence of a particular framework.
