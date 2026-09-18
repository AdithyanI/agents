# Learnings

- Extract live shared behavior before deleting an integration. Codex preview generation lived inside the Claude renderer; the replacement preserves all eight generated environments byte for byte.
- Deleting source does not retire installed launchers, hooks, settings, or scheduled jobs. A removal migration is needed on each machine, with private backups and repeatable checks. It is not a client enable/disable framework.
- Keep the cleanup boundary explicit: dedicated development-client setup is removable, while application provider code, credentials, conversation history, real skill sources, and unrelated editor preferences have separate owners.
- Runtime files can be JSONC and custom hook paths can resemble managed ones. Test comment/trailing-comma parsing and exact command-path boundaries before treating a setting as owned.
- Machine auto-sync may publish and apply source while a task is still running. Preserve a baseline, attribute generated repository changes to Stop, and verify the final installed state rather than assuming only explicit tool invocations changed it.
