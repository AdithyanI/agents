# Subscription-backed agent sessions

`scripts/run-agent-session.py` is the shared execution helper for repo-owned
watchers and other unattended workflows. The owning repo supplies the prompt,
business report contract and post-run validation. This helper starts one local
native client session immediately; it does not schedule jobs, interpret business
reports, publish results or switch clients after a failure.

```bash
python3 ~/GitHub/agents/scripts/run-agent-session.py \
  --client codex \
  --cwd /absolute/owning/repo \
  --prompt-file /absolute/attempt/prompt.txt \
  --transcript /absolute/attempt/events.jsonl \
  --result-file /absolute/attempt/execution.json \
  --timeout-minutes 60 --trusted --no-input
```

`--client` is `codex` or `claude`. Omit `--model` to keep that client's configured
model; `--model` and `--effort` are explicit per-run overrides. Without `--trusted`,
Codex uses its read-only sandbox and Claude uses plan mode; neither prompts for
tool permission. `--trusted` gives broad unattended access for an already
authorized workflow. It does not authorize any task beyond the prompt and repo
instructions. `--no-input` is accepted; all invocations are noninteractive.

The runner prefers the existing Codex desktop-aware resolver and Claude
Desktop's newest installed Code engine. `CODEX_BIN` / `AGENTS_CODEX_BIN` retain
the existing Codex resolver semantics. `AGENTS_CLAUDE_BIN` selects an explicit
Claude executable. Overrides are authoritative: a missing selected client fails
instead of falling back. No client is installed or updated by this helper.

## Subscription boundary

Codex must report `Logged in using ChatGPT` before inference. The run then
forces the built-in OpenAI provider, ChatGPT login and the official ChatGPT
endpoint while retaining the configured model. Claude must report a first-party
`claude.ai` login with a Pro, Max, Team or Enterprise subscription. The same
Claude settings enforce `forceLoginMethod=claudeai`, disable `apiKeyHelper`, and
neutralize inference credential/provider environment overrides during auth and
the run. Unknown subscription status fails closed.

Inference keys and route overrides are removed from the subprocess environment,
never from the parent. Token stores are not read by the runner. Native clients
own credential loading and refresh; the runner only invokes their status command.
It never starts login, selects API billing or retries through another client.
Authentication status has a bounded 20-second timeout; `--timeout-minutes`
applies to the model process. API-account rejection happens before Codex's
forced-login override, which could otherwise clear incompatible saved auth.

## Evidence and completion

Every attempt needs fresh transcript and result paths. The helper exclusively
creates those files and `<transcript>.stderr.log` with mode `0600`; existing
evidence is never overwritten. Native client session persistence remains enabled.
Both failed and successful runs retain their output. On timeout or interruption,
cleanup sends TERM then KILL to the owned process group and observed descendants,
including detached tools. A forcibly killed runner cannot guarantee cleanup.

Stdout and `--result-file` contain the same JSON envelope:

- `schema_version: 1`, `command: "run-agent-session"`, `status: "ok" | "error"`.
- `data.completed` is true only for exit zero plus a successful terminal client
  event and a session identity. Codex requires `turn.completed`; Claude requires
  a successful `result`. It makes no claim about business-report correctness.
- `data.session_id` identifies either client session. `data.thread_id` is also
  set for Codex and is null for Claude.
- `data` includes `client`, `cwd`, `auth_method`, `trusted`, `model`, `effort`,
  `executable`, transcript/stderr/result paths, prompt SHA-256, start/end times,
  elapsed seconds, client `exit_code` and `timed_out`. Exit code is null when the
  process did not finish normally or inference never started.
- `error` is null on success, otherwise has `code`, `message`, `retryable`, `hint`.
  Preflight validation can fail before files exist; stdout still reports it.

Exit codes: `0` complete; `2` invalid inputs or occupied output paths; `3`
subscription/auth unavailable; `4` missing/failed client or missing completion;
`5` timeout/interruption. `--plain` changes only stdout to a short status line;
the saved receipt remains JSON. Keep raw evidence private because model/tool
output can contain task data. A new attempt never replaces an older successful
business report; the owning watcher decides when to promote its output.

Offline regression gate:

```bash
python3 -m unittest tests.control_plane.test_agent_session
```

The test uses synthetic clients and covers authentication rejection, environment
isolation, selection/permission flags, owning cwd, prompt delivery, session
identity, failed/missing completion, evidence preservation and detached-child
timeout cleanup. It is included in `scripts/check-fast.sh`.
