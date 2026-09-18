# Arguments and Interaction

Use the existing repo contract and parser conventions. Prefer explicit long flags for options, simple positional arguments for natural operands, and consistent names across subcommands. Keep required inputs discoverable through help and actionable validation errors. Support stdin/stdout file markers when useful.

## Agent Execution

Missing required input produces a stable error explaining how to supply it. Normal execution must not prompt, even when stdin is a TTY. `--no-input` must disable every interactive path; TTY presence alone does not select operator mode.

Interactive prompts belong only in an explicitly selected operator workflow. Such a workflow must still have a non-interactive equivalent. Keep cancellation responsive and never echo password input.

Make consequential mutations and their target explicit. A dry-run or target-confirmation flag can protect against accidental destructive actions while remaining scriptable. Carry existing user authorization forward; do not require another conversational approval for an already authorized operation. Ask only when the intended target or authority remains unresolved.

Never accept secret values through flags. Use supported credential files, stdin, or secret-manager integration; a file-selection flag carries a path, not the secret itself.

## Command Shape

Choose consistent noun/verb naming and avoid ambiguous synonyms. Reuse flags for the same meaning. Where the parser supports it, avoid surprising ordering restrictions; otherwise make valid placement clear in help and examples. Do not add compatibility aliases or a second command surface without an actual consumer need.
