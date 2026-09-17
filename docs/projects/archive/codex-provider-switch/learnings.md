# Provider switch learnings

- A shared renderer can retain shared capability policy while reading a single
  machine-local provider choice. Reusing an allowlist from existing profiles
  avoids a second set of provider/catalog/auth settings and avoids accidentally
  copying CLI reasoning defaults into the desktop app.
- Config writers need one shared lock: provider selection, ordinary shared
  apply, and trusted-project apply all read/replace the same runtime file.
- Different CLI versions share models_cache.json. An older CLI can remove Astra
  from that source cache even while a working Azure snapshot exists. Keep that
  validated snapshot when only Astra is absent; retain strict errors for broken
  input or missing/invalid saved output.
- The installed app-server does not accept --profile. Probe desktop behavior by
  changing the real machine-local default and starting an ephemeral task; use
  runtime terminal commands to verify explicit profile launchers.
- Direct swiftc needs an explicit macOS SDK path when run from the installer.
- The existing Stop reader used an older terminal binary that could not parse
  completed-subagent items. Scheduled Git auto-sync published the tested source;
  the final installer also links ~/bin/codex to the desktop engine because the
  old terminal CLI rejected real Astra requests. That fixed normal terminal
  inference and the existing Stop reader without changing task history or hook
  policy. Explicit OpenAI and Azure terminal smokes then passed.
- Native menu inspection and live helper/engine checks gave usable UI proof
  while screenshots were black from sleeping/locked displays. GUI installation
  did not need a privacy grant or a restart of the user's active Codex app.
