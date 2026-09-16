# Azure web-search enablement learnings

- Provider capabilities must be tested at the right layer. Azure Responses
  `web_search` succeeded while Codex's separate `/alpha/search` returned 404.
  A 2025 issue or an exposed tool name was not enough to determine current support.
- A model-catalog flag is a protocol compatibility override, not a free upgrade
  or a smaller/larger model selection. Keep it scoped to the user's chosen
  scope and preserve all other metadata when generating the local catalog.
- Public source comments can lag deployed behavior: Codex's standard-Responses
  comment said `current_turn`, but both live Azure Astra probes returned
  `all_turns`. Record observed behavior with its date and model.
- Use the saved profile in the final smoke, without repeating its protocol
  settings as command-line overrides; otherwise a passing probe can hide a
  broken profile or relative-path resolution.
- `codex debug models` is available in CLI 0.154.0 for catalog inspection;
  `--bundled` avoids refresh. Do not dump full catalogs into chat or git: they
  contain large model instructions. Extract only the metadata needed.
- Preserve the original cache and account-provider behavior. Validate
  generated output structurally during health checks; normal cache updates
  alone should not be treated as configuration drift.

- A global catalog override reaches subscription profiles unless explicitly
  overridden there. The `chatgpt` profile therefore restores normal cache metadata
  and standalone search. This also pins its model metadata: refresh via an
  authenticated `codex exec --ignore-user-config` invocation and reapply sync.
- Desktop activation needs global settings, a process restart, and a new task.
  Verify the bundled engine without repeating provider/protocol overrides.
- A completed search event and a plausible URL are insufficient retrieval proof.
  Require actual source snippets and citation annotations from the direct API,
  then source text from Codex. Preserve failed attempts alongside successful
  retries, and distinguish search from page opening. The later September 16
  recheck recovered search without changing configuration, while page opening
  remained empty; no root cause was established.
