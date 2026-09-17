# Codex provider switch

The **Codex Provider** menu bar app selects **Azure credits** or **Codex
subscription** independently on each Mac. The selected provider applies to new
ordinary `codex` terminal sessions and newly started local desktop runtimes.
Finish active work, reopen Codex, and start a new task after switching. Existing
tasks can retain their original provider; the menu reports the configured
default, not the billing provider of every running task.

## Usage and install

```bash
codex-provider status --plain
codex-provider azure --apply
codex-provider subscription --apply

# From the canonical agents checkout on each Mac:
python3 scripts/install-codex-provider-menu.py --apply --no-input
```

The installer builds a small native AppKit application using the local Swift
compiler, installs `~/Applications/Codex Provider.app`, and starts its per-user
`io.adithyan.codex-provider` LaunchAgent at login. It links `~/bin/codex-provider`
to `scripts/codex-provider.py`. No Xcode project or downloaded UI dependencies
are needed. The installer never restarts Codex itself.

It also links `~/bin/codex` to the installed desktop engine and installs the
existing `codex-azure` / `codex-openai` launchers from the scripts repo. Managed
login/interactive shells already put `~/bin` first. This avoids the MacBook's
older Homebrew CLI, which rejects Astra. Open a new terminal tab (or run `rehash`
in zsh) if an existing shell cached the old executable. These ordinary terminal
links remain when uninstalling the menu, so subscription sessions keep using a
compatible engine. Explicit `/opt/homebrew/bin/codex` calls still select Homebrew.

Source updates travel through the normal Git workflow. Run the installer again
on each Mac when the native app changes. It records the local Python executable
and canonical repository path in the app bundle; rerun it after moving either.

## Ownership and sync

- Shared in Git: provider definitions, `azure-astra.config.toml`,
  `chatgpt.config.toml`, skills, plugins, hooks, and common settings.
- Machine-local choice: `~/.local/state/codex-control-plane/provider`, containing
  exactly `azure` or `subscription`. It is outside Git and Syncthing.
- Applied output: `~/.codex/config.toml`, still generated through the existing
  shared renderer. Do not hand-edit it to switch providers.
- Implementation: `codex/scripts/provider_selection.py`; public command:
  `scripts/codex-provider.py`; native source: `codex/menu-bar/CodexProvider.swift`.

The first successful sync remembers the existing runtime provider, so installing
this feature does not switch an Azure machine to subscription. A fresh machine
without a provider default starts on subscription. Invalid preferences fail with
an actionable error rather than silently changing the provider. An explicit
provider selection repairs the preference.

The renderer merges only provider, matching model catalog, authentication method,
and standalone-search settings from the selected shared profile. Azure also pins
its deployment model. Subscription preserves the client's existing model choice.
The menu does not copy the Azure CLI profile's reasoning effort into the desktop
default. Explicit `codex-azure` / `codex-openai` terminal launchers retain their
per-process behavior regardless of the menu selection.

The switch, shared config apply, and trusted-project config apply use the same
local lock. Provider writes are atomic and preserve unrelated config. Preference
is written before config so a later sync can repair an interrupted write; normal
write failures restore the previous preference. Existing credential distribution
and Azure catalog generation remain intact. The switch checks readiness before
changing files and never rewrites login credentials or conversation history.

This affects local execution on the selected Mac. Opening a remote task on the
Mac mini does not make the MacBook's menu control the mini's runtime.

## Command contract

`scripts/codex-provider.py [status|azure|subscription]` emits one JSON object with
`schema_version`, `command`, `status`, `data`, `error`, and `meta`. `--plain` is
the operator view; `--json` is accepted; `--no-input` never prompts. Selection
commands default to a read-only dry-run and require `--apply` to mutate.

Successful data includes `selected`, `effective_provider`, `persisted`,
`config_in_sync`, `applied`, `restart_required`, `scope`, `state_file`, and
`config_file`. `restart_required` describes desktop activation requirements; it
does not claim to detect which provider a running desktop process has loaded.

Exit codes: 0 success; 2 validation; 3 missing authentication; 4 missing local
dependency; 5 lock timeout/interruption. `--timeout` controls lock acquisition,
defaults to 60 seconds, and accepts values above zero through 300 seconds.
No network/model call is made by the menu or switch command. No secrets are
accepted through flags or printed in output. Behavior does not depend on TTY.

## End of temporary Azure use

On each Mac, select Subscription and reopen Codex before starting new work.
Then remove the utility when it is no longer useful:

```bash
python3 scripts/install-codex-provider-menu.py --uninstall --apply --no-input
```

Uninstall removes only the menu app, its login agent, and its owned terminal
link/logs. It retains the subscription preference so later shared sync cannot
undo the choice. Azure definitions and shared credentials can remain available
for their other consumers. There is no automatic expiry or billing fallback.

## Validation

`tests/control_plane/test_codex_provider.py` covers opposite per-machine choices
surviving repeated real renderer runs, first-sync migration, round-trip settings,
credential preservation, failures/rollback, lock contention, and the CLI contract.
`codex/scripts/check-codex-control-plane.sh` also checks the effective provider
bundle against the local choice. The native bundle's `--inspect-menu` mode reads
the real helper and reports menu titles/checkmarks without switching providers.
