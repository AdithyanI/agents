---
name: ai-podcasting
description: Submit TCR episodes or update existing episode copy, intros, titles, and thumbnails through the scoped AI Podcasting client API. Use for client episode operations, access checks, and local source uploads.
---

# AI Podcasting

Run `scripts/ai_podcasting_client.py` relative to this skill directory, not the repository root. The CLI calls the scoped WIN client API directly at `https://api.aipodcast.ing/client/v1`; do not route these operations through the frontend or browser UI. It is fixed to the TCR show, and the server enforces the customer's operation grants.

## Choose the Operation

| Intent | Command | Payload example |
| --- | --- | --- |
| Check credential and grants | `doctor` | None |
| Find an episode | `list-episodes` | None; use publication/date filters as relevant |
| Create a new episode | `submit-episode --payload-file <file>` | `references/submit-episode.example.json` |
| Update intro/title/thumbnail assets of an unpublished episode | `update-intro-copy --source-id <id> --payload-file <file>` | `references/update-intro-copy-tcr.example.json` |
| Update existing show notes, supporting assets, or guests | `update-episode-copy --source-id <id> --payload-file <file>` | `references/update-episode-copy.example.json` |

Use CLI `--help` and the relevant example for exact inputs. JSON is the default result; `--plain` and `--human` are inspection views. Put global flags such as `--request-id` before the subcommand.

Reuse the conversation's intent, values, and selected episode. If the target is missing, list episodes with the available context; intro targets must be unpublished. Ask only when the operation or target remains ambiguous or a required value is missing. Do not impose a fixed multi-message questionnaire or ask for optional fields the user did not request.

## Source and Patch Boundaries

- Prefer an actual Descript web URL for TCR main and intro sources when available. Do not fabricate IDs or export/upload an MP4 merely to create a source link. Other recording/video URLs and local files are fallbacks; main-source MP3 is rejected.
- Use `mainSourceUrl` for submission and `introSourceUrl` for intro patches. The client normalizes the backend shape; do not supply raw backend source fields such as `raw`, `recordingLink`, or `introFile`.
- File-like fields accept URLs or local paths. The client resolves local paths through purpose-scoped temporary uploads. `scripts/aip_local_upload_helper.py --help` is available when a separate upload is needed; resulting `cache/` URLs are transport references, not permanent inventory.
- Patch only the requested fields. `showNotes`, `assetUrls`, and `guests` belong in `update-episode-copy`, not the intro command. Empty strings/null clear show notes; empty arrays/null clear assets or guests. Omit unspecified fields rather than guessing or clearing them.
- `customNewsletterDraftUrl` is a public HTTP/HTTPS Ghost draft/preview/editor/slug URL, not a local upload field. Storing it does not publish or replace the generated newsletter.
- Intro patches target unpublished episodes. Unknown fields are rejected; a successful response is not evidence that an undocumented field was accepted.

## Credentials, Setup, and Retry

Credentials come from `~/.secrets/aipodcasting/env` or the file selected by `AIPODCASTING_CLIENT_API_KEY_FILE`. Never put the key in flags, ordinary environment variables, payloads, prompts, or chat. The override variable contains only a file path.

For customer installation, upgrade, or rotation, read `references/client-setup.md` and verify `doctor` before mutation. That reference also covers credential and idempotency failures.

`submit-episode` uses the request ID as its idempotency key. Preserve the returned `meta.request_id` after an uncertain result and retry with `--request-id <same-id>` and the original payload. Use a new ID only for an intentionally separate episode. A requested preview can use `--dry-run`; it is not a mandatory intermediate checkpoint for an already authorized operation.
