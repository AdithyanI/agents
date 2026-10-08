## Claude Code Runtime

- Repository `AGENTS.md` files are canonical and load through Claude Code's native AGENTS support. Keep that support enabled; inspect `/context` when verifying instruction discovery.
- Use the shared control plane's explicitly compatible skills from `~/.claude/skills` and the current repository's `.claude/skills`. Native Codex plugins and tools are available only in Codex.
- Claude sessions do not run the Codex publication hook. Complete implementation and required local checks, then report the changed files and validation. Commit or push only when Adi requests it or the repository's existing delivery contract explicitly authorizes it.
