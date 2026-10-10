## Claude Code Runtime

- Repository `AGENTS.md` files are canonical and load through Claude Code's native AGENTS support. Keep that support enabled; inspect `/context` when verifying instruction discovery.
- Use the shared control plane's explicitly compatible skills from `~/.claude/skills` and the current repository's `.claude/skills`. Native Codex plugins and tools are available only in Codex.
- The shared Stop hook checks, commits, rebases, and pushes every repository the session touched after each turn, as it does for Codex. Fix failures it returns instead of committing manually.
- Adi runs Claude Code in `bypassPermissions` mode; that user-owned setting already lives in `~/.claude/settings.json`. Bypass still stops on shell scripts it cannot analyze, such as `bash -c '…'`/`sh -c` wrappers or long inline `python3 -c` programs. Write multi-step or quoted logic to a script file in the scratchpad or `tmp/` and run it directly, so trusted work does not wait on a prompt.
