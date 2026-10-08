## Claude Code Runtime

- Repository `AGENTS.md` files are canonical and load through Claude Code's native AGENTS support. Keep that support enabled; inspect `/context` when verifying instruction discovery.
- Use the shared control plane's explicitly compatible skills from `~/.claude/skills` and the current repository's `.claude/skills`. Native Codex plugins and tools are available only in Codex.
- The shared Stop hook checks, commits, rebases, and pushes every repository the session touched after each turn, as it does for Codex. Fix failures it returns instead of committing manually.
