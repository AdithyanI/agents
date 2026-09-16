# Azure Astra in Codex

## Configuration and ownership

Azure Astra is the global default, as requested on 2026-09-16, for newly loaded
local Codex runtimes including the macOS app. Quit and reopen the app after
syncing configuration. Use `codex-openai` (or `codex --profile chatgpt`) for an
explicit subscription session. No desktop provider-picker integration is assumed.

- Subscription: Microsoft Azure Sponsorship.
- Existing resource: `aipodcasting-openai`, resource group `aipodcasting`,
  region `swedencentral`.
- Endpoint: `https://aipodcasting-openai.openai.azure.com/openai/v1`.
- Existing deployment: `gpt-6-astra`, model version `2026-09-03`,
  `GlobalStandard`. This setup does not create or change Azure deployments.
- Provider definition: `codex/config/global.config.toml`.
- Optional profile: `codex/config/azure-astra.config.toml`, rendered to
  `~/.codex/azure-astra.config.toml`.

Azure model requests bill the Azure resource's subscription. Sponsorship credit
eligibility and remaining balance must be checked in Azure billing; successful
inference alone does not prove that credits covered a request.

## Native credential materialization

The existing shared canonical secret `litellm--azure-openai-api-key` is the key
for this Azure resource. Reuse it without copying its value into a second
canonical family. The primary secret owner stays unchanged.

`codex/config/secrets.env.map` maps that secret to `AZURE_OPENAI_API_KEY` in
Codex's native `~/.codex/.env`. This generated file is owner-only (`0600`) and
works for GUI launches without shell environment inheritance. It contains
credentials and must never be printed, committed, or hand-maintained.

Materialize on each machine that will use Azure, and again after key rotation:

```bash
~/GitHub/scripts/sync/materialize_machine_env.py \
  --secret-scope shared \
  --mapping-file ~/GitHub/agents/codex/config/secrets.env.map \
  --output-file ~/.codex/.env \
  --apply
~/GitHub/agents/codex/scripts/sync-config.sh --apply
```

The materializer owns the complete `.env` file. Add future native Codex secret
mappings to the same map; don't overwrite unrelated manually maintained values
without migrating their ownership first. Normal configuration sync does not
materialize secrets or require Azure credentials when using the subscription.

## Choosing Azure

For an explicit terminal session, use `codex-azure`, the thin launcher at
`~/GitHub/scripts/bin/codex-azure` linked into `~/bin/codex-azure`. It runs
`codex --profile azure-astra` with all additional arguments forwarded:

```bash
codex-azure
codex-azure "Review this project"
codex-azure exec "Summarize the current changes"
```

The Azure selection applies only to that invocation. It does not edit global
configuration, restart the desktop app, or change the normal `codex` command.
Codex owns interactive output, `exec --json`, error handling, and exit codes;
the launcher adds no separate output protocol or credential handling.

Inside the terminal session, run `/status` and verify `Model provider: azure`.
The model name `gpt-6-astra` alone does not establish which provider handles
requests. Normal `codex` sessions now also use the global Azure default. The launcher
was verified with a real Astra response and an `exec` header reporting
`provider: azure`; the user also confirmed the interactive `/status` display.

On another machine, after syncing both repos and configuring Azure credentials,
install the command with `ln -s ~/GitHub/scripts/bin/codex-azure ~/bin/codex-azure`.

## Choosing the Codex subscription in the terminal

Use `codex-openai`, the matching launcher at
`~/GitHub/scripts/bin/codex-openai` linked into `~/bin/codex-openai`:

```bash
codex-openai
codex-openai "Review this project"
codex-openai exec "Summarize the current changes"
```

It runs `codex --profile chatgpt` and forwards the remaining arguments. The
canonical `codex/config/chatgpt.config.toml` selects `model_provider = "openai"`
and `forced_login_method = "chatgpt"`, requiring the saved ChatGPT subscription
login. It does not use the Azure key or select OpenAI Platform API-key billing.
Model and reasoning choices remain available through Codex's normal controls.

Both launchers can run at the same time. Each selects its own process's profile;
ordinary `codex` and newly loaded desktop runtimes keep the global Azure default.
For a new subscription session, verify `/status` reports provider `openai` and
the ChatGPT account. For authentication administration use `codex login status`
or `codex login` directly: the installed CLI does not accept `--profile` for
login commands. A mismatched login method causes Codex to log out and exit;
sign in with ChatGPT again rather than placing an API key in the login store.

On another machine, sync both repos, apply the managed Codex profiles, and run:

```bash
ln -s ~/GitHub/scripts/bin/codex-openai ~/bin/codex-openai
```

## Selecting the desktop default

For the macOS app, the global Azure selection was applied on 2026-09-16:

1. Set top-level `model_provider = "azure"` and `model = "gpt-6-astra"` in
   canonical `codex/config/global.config.toml`, then run the config sync and
   control-plane checks. These global defaults also affect ordinary CLI runs.
2. Have the user finish active work, quit and reopen the desktop app, then
   start a new local task. Do not terminate the app from an active agent task.
3. Verify the new task uses Azure. Existing tasks may retain their provider;
   don't infer their billing from the model label alone.

To return to the subscription, remove those top-level model/provider defaults
from the canonical template, sync/check, and restart before creating a task.
Retain the `azure` provider table and optional profile. The ChatGPT login is
independent of the Azure key and should not be overwritten with an Azure key.

The named CLI profile is not a verified desktop profile selector. Do not claim
that Azure and subscription entries coexist in the desktop model dropdown.

## Priority processing

Verified against Azure on 2026-09-16: this deployment's `gpt-6-astra` model
version `2026-09-03` does not support Priority Processing. An authorized
`az rest --method put` attempt using management API `2026-05-15-preview` and
`properties.serviceTier = "Priority"` returned HTTP 400,
`InvalidResourceProperties`:

> The model 'gpt-6-astra' version '2026-09-03' does not support Priority service tier.

A subsequent management API read confirmed the deployment remained `Running`
with provisioning state `Succeeded`, unchanged model, SKU/capacity, safety
policy, upgrade policy, and no configured service tier. No Codex settings were
changed. Do not enable a Codex Fast preference as a workaround for this
deployment's unsupported service tier.

For a supported model, Azure can select priority at the deployment level or
through the Responses API's `service_tier = "priority"`. These are different
field names and casing: the current [ARM deployment schema](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts/deployments)
uses `properties.serviceTier = "Priority"`. Verify the saved deployment and
the response's actual `service_tier` before claiming priority is active;
requests can fall back to standard processing. See [Azure Priority Processing](https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/priority-processing)
for supported model versions, pricing, and fallback conditions.

## Web search in the Azure profile

Enabled by explicit request on 2026-09-16, only in the existing `azure-astra`
profile. The user wanted Azure search while retaining an easy comparison and
rollback path. This is a tested Codex compatibility workaround, not a standard
Azure portal switch.

### Why the override exists

The current Astra catalog selects `use_responses_lite = true`. Codex's Lite
request path omits hosted Responses tools and relies on a separate search
endpoint. Enabling `supports_standalone_web_search` on our Azure provider exposed
the tool but its `/openai/v1/alpha/search` request returned 404. Setting
`web_search = "live"` alone did not make search available.

Our existing Azure endpoint successfully accepts `tools: [{"type":"web_search"}]`
inside a standard Responses request. The Azure backend uses Grounding with Bing
Search; no new deployment, Foundry project, MCP, or service was provisioned.
The original [Codex issue #4881](https://github.com/openai/codex/issues/4881)
describes an older limitation and does not establish current Azure API support.
See [Microsoft's current web-search guide](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/web-search)
and [Codex's hosted-tool gating](https://github.com/openai/codex/blob/rust-v0.154.0/codex-rs/core/src/tools/spec_plan.rs).

### Ownership and effective settings

- Canonical settings: `codex/config/azure-astra.config.toml`.
- Runtime profile: `~/.codex/azure-astra.config.toml`.
- Generated catalog: `~/.codex/model-catalogs/azure-astra.json`, resolved relative
  to the runtime profile file by Codex.
- Generator: `codex/scripts/sync-azure-model-catalog.py`, invoked by the normal
  `codex/scripts/sync-config.sh --apply` workflow before installing profiles.
- Source: Codex's machine-local `~/.codex/models_cache.json`. The generator copies
  its model entries and changes only Astra's `use_responses_lite` to `false`.
  It preserves context limits, model instructions, tool metadata, and all other
  models. Neither catalog belongs in git; the normal cache is never modified.

The Azure profile supplies:

```toml
model_catalog_json = "model-catalogs/azure-astra.json"
web_search = "live"

[features]
standalone_web_search = false
```

`wire_api = "responses"` was already configured on the provider. The model-catalog
flag is the additional setting that selects standard rather than Lite requests.
`model_catalog_json` loads at process startup; start a new session when changing
it. This is profile isolation, not an automatic rule for every Azure request.
Do not select the subscription provider inside the Azure profile and assume the
catalog override disappears.

### Switch paths or roll back

| Command | Provider and search behavior |
| --- | --- |
| `codex-azure` | Azure Astra, standard Responses, Azure-hosted search |
| `codex-openai` | ChatGPT subscription, normal model catalog and Codex search |
| `codex --model gpt-6-astra -c 'model_provider="azure"'` | Original Azure path using the normal catalog; bypasses the Azure profile |

Ordinary `codex` also uses that original Azure path under the current global
default. The desktop's global Azure default does not select `azure-astra`:
this change does not activate search in existing desktop tasks or alter the
subscription profile. Use separate new sessions for comparisons.

For a persistent rollback, remove `model_catalog_json` and the
`features.standalone_web_search` override from the canonical Azure profile,
then run `codex/scripts/sync-config.sh --apply`. Do not hand-edit the rendered
profile: the next sync would restore the canonical version. The unused derived
catalog can remain locally; it has no effect without the profile reference.

### Refresh and diagnose

After a Codex update, or if search/tool behavior regresses:

1. Check `codex --version` and `/status` in the affected session. Confirm which
   launcher/profile and provider started it.
2. Let a normal `codex-openai` session populate the current source model catalog.
   On a new machine, do this before materializing the Azure catalog. If the
   subscription profile has not been installed yet, use
   `codex -c 'model_provider="openai"' -c 'forced_login_method="chatgpt"'` instead.
3. Run `codex/scripts/sync-config.sh --apply`, then
   `codex/scripts/check-codex-control-plane.sh`. The generator writes atomically
   and refuses invalid catalogs instead of replacing the last valid output.
4. Start a new `codex-azure` session and require an actual native `web_search`
   event. A plausible answer or a URL alone is not evidence of search.
5. If it still fails, use the original Azure command above and resume the
   [enablement project record](../projects/archive/azure-astra-web-search/tasks.md).
   Compare a direct Azure Responses search request with Codex before changing
   Azure resources. Record the exact error without logging credentials.

The normal control-plane check validates the saved catalog structurally. It
does not require byte equality with the live source cache: ordinary catalog
refreshes must not create spurious machine-health failures. Applying sync
refreshes the derived snapshot; it does not fetch remote model metadata itself.
The original Azure path can log `failed to decode models response: missing field
models` when refreshing its catalog, because Azure returns a different catalog
shape. The original-path smoke still completed successfully using fallback
metadata. Populate the source cache through the subscription path as above;
the derived-catalog profile avoids that refresh request.

### Trade-offs and evidence

- This changes the request protocol, not the model. The generated catalog keeps
  the current 272,000-token window and 95% effective budget (258,400 tokens).
  It does not enable the model's maximum advertised context length.
- Both direct Azure Astra probes returned `reasoning.context = "all_turns"`,
  with and without an explicit context value. The older Codex source comment
  assuming standard Responses defaults to `current_turn` was not true for this
  deployment. See [Azure reasoning behavior](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/reasoning).
- Native search and shell execution passed with the saved Azure profile in
  CLI 0.154.0; earlier isolated tests also passed with desktop engine
  0.154.0-alpha.6.2. The saved-profile smoke reported cached input tokens.
- Switching protocols does not duplicate every model request. Search actions
  have additional tool charges and returned content uses tokens. Credit
  coverage and comparative long-session cost were not verified.
- Microsoft currently treats `external_web_access` as `false`; the Codex
  `"live"` setting does not promise unrestricted live fetching on Azure.
- The snapshot requires refresh after relevant model/Codex changes. Long coding
  sessions, compaction, resume behavior, latency, and quality parity remain
  unbenchmarked. These are reasons to retain the original path for comparison.

The [project verification record](../projects/archive/azure-astra-web-search/resources/verification.json)
contains the synthetic smoke outcomes and configuration-isolation evidence.

## Protocol and validation

Use the Responses API (`wire_api = "responses"`) and the Azure deployment name
as `model`. The `/openai/v1` endpoint does not require an `api-version` query
parameter. Don't mix this route with the older dated-preview endpoint example.

Validate both a minimal Responses request and an isolated request through the
Codex engine bundled with the desktop app. Disable lifecycle hooks and external
integrations during the smoke test, and keep scratch work under this repo's
`tmp/`. Runtime verification is separate from desktop UI activation, which
requires a restart of the user's app after the global default changes.

Installed-build history checks on 2026-09-16 (`0.154.0-alpha.6.2`):

- A saved synthetic OpenAI task resumed without a provider override still used
  `openai`, even when the app-server default was `azure`. A default change does
  not establish that existing tasks have migrated.
- The installed server's default `thread/list` under Azure omitted the eight
  OpenAI tasks returned by the same query under OpenAI. This differs from the
  current public manual's claim that an omitted provider filter includes all
  providers. The macOS client's actual filter behavior must be checked after
  restart; do not promise that every old task stays visible in its default view.
- These checks used a disposable test conversation; existing user tasks were
  not rewritten or deleted.

Verified on 2026-09-15:

- A direct, non-stored Azure Responses request returned `AZURE_ASTRA_OK` from
  `gpt-6-astra`.
- `/Applications/ChatGPT.app/Contents/Resources/codex` version
  `0.154.0-alpha.6.2` completed a read-only `pwd` tool call and returned
  `AZURE_ASTRA_CODEX_OK` using this provider and deployment. The smoke process
  had `AZURE_OPENAI_API_KEY` removed from its inherited environment, proving
  native `.env` credential loading. User configuration, lifecycle hooks, apps,
  and web search were disabled for the isolated check.
- The live config registered `azure` while leaving the default provider unset
  (`openai`); `~/.codex/.env` had mode `0600`.
- `scripts/check-fast.sh` passed, including Codex structural/runtime validation.
- Desktop UI activation and Azure credit deduction were not tested.

Azure Astra currently lacks mid-turn steering and mid-conversation reasoning
changes supported by the OpenAI route. Availability of hosted Codex features
must be checked separately; a working model request does not prove parity.

Sources checked 2026-09-15:

- [Microsoft's Codex setup guide](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/codex)
- [Azure Astra model capabilities](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure#gpt-6)
- [Codex desktop model configuration](https://learn.chatgpt.com/docs/models#configure-your-default-local-model)
