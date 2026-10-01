# Azure web research

`mcp/config/presets.json` assigns `azure-web-research` to every managed repository.
The stdio server uses the existing `aipodcasting-openai` Azure OpenAI Responses API
and Bing web search. No Foundry project, hosting service, or third-party search
account is needed. `mcp/config/azure-web-research.json` owns the endpoint and helper
deployments; it does not change the model selected for the calling Codex chat.

- `web_search`: quick lookup through `gpt-6-luna`, low reasoning.
- `web_research`: multiple-source investigation through `gpt-6.1-sol`, high reasoning.
  This is a research workflow, not the dedicated `o3-deep-research` deployment.
- Both accept a public `query`, optional `domains`, result `limit`, and `timeout`.
  Results contain a cited answer, sources/snippets, token usage, and the provider's
  `tool_usage.web_search.num_requests` billing count. Snippet limits do not limit
  billed Bing requests. Partial responses preserve output and usage.

Only the supplied query and filters are sent; repository files and chat history
are not added. Credentials come from generated, owner-only `~/.codex/.env` using
the existing secret mapping. Never put keys in MCP arguments, config, or logs.
The client makes no automatic retries: timeouts can leave provider completion
and charges uncertain.

Azure documents indexed/cached content for this API, with no guaranteed live page
retrieval. Fetch primary sources directly when their current text matters. Model
text is synthesis; citations and returned source snippets are the evidence.
Bing tool charges are separate from inference. Sponsorship coverage requires
billing confirmation; a successful request alone does not prove coverage.

Apply and check through the shared control-plane commands. Reopen Codex or start
a fresh runtime to load newly configured MCP tools; existing chats may retain
their original tool list. The CLI works immediately:

```bash
python3 ~/GitHub/agents/mcp/azure_web_research.py search \
  'AVFoundation composition editing documentation' --domain developer.apple.com --plain --no-input
python3 ~/GitHub/agents/mcp/azure_web_research.py research \
  'Compare native transcript selection options for a macOS video editor' --timeout 180 --no-input
```

CLI output defaults to the shared JSON envelope; `--plain` prints the answer and
usage. Request timeouts default to 50 seconds for search and 180 for research,
with a maximum of 300. MCP's outer timeout is 300 seconds.

Verification on October 1, 2026: the existing Luna deployment returned Apple
AVFoundation sources and citations in 6.7 seconds, reporting four Bing requests.
Run focused contract tests with `python3 -m unittest tests.control_plane.test_azure_web_research`.

Sources: [Azure OpenAI web search](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/web-search)
and [Foundry web-search tools](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/web-search).
