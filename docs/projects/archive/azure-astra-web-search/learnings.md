# Azure web-search enablement learnings

- Provider capabilities must be tested at the right layer. Azure Responses
  `web_search` succeeded while Codex's separate `/alpha/search` returned 404.
  A 2025 issue or an exposed tool name was not enough to determine current support.
- A model-catalog flag is a protocol compatibility override, not a free upgrade
  or a smaller/larger model selection. Keep it scoped to the user's chosen
  profile and preserve all other metadata when generating the local catalog.
- Public source comments can lag deployed behavior: Codex's standard-Responses
  comment said `current_turn`, but both live Azure Astra probes returned
  `all_turns`. Record observed behavior with its date and model.
- Use the saved profile in the final smoke, without repeating its protocol
  settings as command-line overrides; otherwise a passing probe can hide a
  broken profile or relative-path resolution.
- `codex debug models` is available in CLI 0.154.0 for catalog inspection;
  `--bundled` avoids refresh. Do not dump full catalogs into chat or git: they
  contain large model instructions. Extract only the metadata needed.
- Preserve the original cache and global/subscription configuration. Validate
  generated output structurally during health checks; normal cache updates
  alone should not be treated as configuration drift.
