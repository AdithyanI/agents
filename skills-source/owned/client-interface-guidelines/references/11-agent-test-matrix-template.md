# CLI Contract Test Examples

Select cases that exercise the changed contract and use the tool's actual schema and exit codes. Reuse existing tests; do not add every case to every CLI or create an interface just to satisfy this table.

| Relevant behavior | Useful evidence |
| --- | --- |
| Structured output | Success and failure parse correctly; diagnostics do not corrupt stdout |
| Non-interactive execution | Missing required input fails promptly rather than prompting |
| Remote operation | Timeout and dependency/auth failures have stable codes and actionable results |
| Retry or resume | An uncertain result can be reconciled without duplicating a mutation |
| Secret handling | Credentials do not appear in output; supported file/stdin/manager input works |
| Interruption | The operation reports or preserves recoverable state |
| Existing consumers | A contract change respects the actual migration requirements |
| Multiple delivery routes | Explicit route selection/failure and any automatic fallback are observable; asynchronous completion is not claimed prematurely |

For risky mutations, verify a dry-run or equivalent inspection path where the tool provides one. Avoid live spending or deployment merely to exercise an unrelated documentation change.
