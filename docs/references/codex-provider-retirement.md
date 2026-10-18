# Native Codex provider ownership

Codex uses its native account login and model discovery. Shared bootstrap manages
guidance, skills, hooks and capabilities; it preserves the client's provider,
model, reasoning, profile, Fast preferences and native notification callbacks. The Azure provider menu and its
catalog generator are retired. The explicit `chatgpt` and automation `autofix`
profiles remain available without changing the global default.

After updating both `agents` and `scripts` through Git, run on each Mac:

```sh
python3 ~/GitHub/agents/scripts/retire-codex-provider.py --dry-run --no-input
python3 ~/GitHub/agents/scripts/retire-codex-provider.py --apply --no-input
python3 ~/GitHub/agents/scripts/install-codex-cli.py --apply --no-input
python3 ~/GitHub/agents/scripts/retire-codex-provider.py --dry-run --no-input
```

The retirement command removes only the owned provider menu and login agent,
its launcher/preference, the Azure launcher, Azure profile/catalogs/provider
definition, recognized generated selection/context overrides, and
`AZURE_OPENAI_API_KEY` from Codex's generated `.env`. Other environment entries,
ChatGPT authentication, conversations, model cache, native CLI links and shared
Azure credentials remain with their existing owners. It reports paths rather
than credential contents. The pre-migration config is retained under
`~/.local/state/codex-control-plane/backups/retired-provider/` with private access.
Rerunning the command is safe and reports no changes after retirement.
No full bootstrap is needed for this migration. Normal bootstrap and runtime
checks continue through the existing shared control-plane commands.

The native CLI installer links `~/bin/codex` to the bundled native executable
and keeps `codex-code-mode-host` adjacent. It avoids the previously slow shell
wrapper and installs no background service or provider switcher. An unrelated
existing executable is left untouched with an actionable error.

Existing sessions retain their original runtime configuration. Restart Codex
when active work is finished if those sessions need to adopt the cleanup; the
migration does not restart Codex or its shared remote app-server.
