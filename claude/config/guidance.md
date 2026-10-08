## Claude Code Runtime

- Repository `AGENTS.md` files are canonical and load through Claude Code's native AGENTS support. Keep that support enabled; inspect `/context` when verifying instruction discovery.
- Use the shared control plane's explicitly compatible skills from `~/.claude/skills` and the current repository's `.claude/skills`. Native Codex plugins and tools are available only in Codex.
- In Claude-enabled managed repositories, the shared Stop hook checks, commits, rebases, and pushes the session's work after each turn, as it does for Codex. Fix failures it returns instead of committing manually. In other repositories, complete the work and required checks, then report the changed files and validation; commit or push only when Adi asks or the repository's delivery contract authorizes it.
