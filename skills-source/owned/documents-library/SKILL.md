---
name: documents-library
description: Search, retrieve, cite, and copy-import files in Adi's Documents library through the packaged HTTPS CLI. Use for finding personal records and answering questions from their originals, or configuring the Documents client; not for authoring Google Docs or changing corpus maintenance policy.
---

# Documents Library

The Documents repository owns the corpus, catalog, API, and packaged `documents`
client. The configured HTTPS address is `https://documents.adithyan.io`. Normal
agents use the client without SSH, a Documents checkout, or a mounted corpus.
This skill supplies usage guidance; access still requires an explicitly configured
endpoint and credential file for the current person/workspace.

## Client setup and readiness

Use the installed private `documents` package, version 0.2.0 or newer. For a fresh
machine, install a wheel built from accepted private source, pin its version and
SHA-256, and follow the owning bootstrap's executable path. Installation and
client/API details live in `~/GitHub/documents/docs/references/http-client.md`;
do not invent another wrapper, package, or credential store.

On an enrolled development peer, Scripts materializes the canonical
`documents--api-key` into `~/.secrets/documents/api-key`:

```bash
python3 ~/GitHub/scripts/setup/asus/materialize-documents-api-key.py --apply --json --no-input
export DOCUMENTS_ENDPOINT=https://documents.adithyan.io
export DOCUMENTS_API_KEY_FILE="$HOME/.secrets/documents/api-key"
documents status --no-input
```

The generated credential file is private and user-owned. Pass only its path;
never print the key or put its value in flags, URLs, ordinary environment
variables, or source. A machine missing enrollment needs its authorized secret
setup; installing or linking this skill does not grant access. Do not distribute
Adi's credentials to Angie or another unconfigured workspace.

Inspect `data.ready`, runtime identity, and `meta.endpoint`/`meta.transport`.
Installed/configured software does not establish successful deployment or
completed data migration. Follow the current project tracker when operating
the service, and retain the actual failure code when readiness is unavailable.

Within a Dobby workspace, prefer its `./bin/dobby documents` interface when
configured. It requires workspace-owned `DOBBY_DOCUMENTS_ENDPOINT`,
`DOBBY_DOCUMENTS_API_KEY_FILE`, and the installed client path in
`DOBBY_DOCUMENTS_CLI`. Generic machine `DOCUMENTS_*` settings do not select a
Dobby person's corpus. See `~/GitHub/dobby-engine/docs/references/documents.md`.

## Find, retrieve, and cite

```bash
documents search --query "residence permit" --limit 10
documents search --query "income statement" --year 2025 --bucket work --ext pdf
documents get --document-id <id-from-search> --output tmp/document.pdf
```

Search accepts exact names/identifiers plus `--year`, `--bucket`, `--ext`,
`--person`, and `--type`. Limits are 1–100. Broaden a missed query with
`--mode any` or the source language's terms; current keyword search does not
guarantee semantic or cross-language matches.

Keep `document_id` and `content_hash`/`version_hash` from results. Prefer retrieval
by ID; root-relative `--path` remains available. Downloads return verified byte
count and SHA-256, preserve existing outputs, and remove ordinary partial
transfers. Use a new destination unless replacement with `--overwrite` is intended.

Results can contain metadata matches, extracted page citations, and an explicit
text-extraction status. Cite the original document, its version hash, and the
1-based page number when available. A metadata match is not page evidence, and
a model-derived confidence/evidence field is not a verified fact. Retrieve the
original and inspect the relevant page before relying on dates, amounts, or
contract terms. If no page evidence is available, say so rather than inventing it.

The requesting agent owns task-specific interpretation and extraction from
downloaded originals. Use appropriate local PDF/Office/OCR tooling for scanned,
encrypted, or unsupported files, retaining provenance and uncertainty. Keep
downloads in the working repo's `tmp/` unless the user chose a destination;
keep personal contents out of Git and general logs. Do not start collection-wide
processing or a new provider service merely because a search missed a document.

## Copy-only import and failures

```bash
documents ingest --source ~/Downloads/statement.pdf
```

HTTPS ingest accepts one regular file per call and preserves its source. It
deduplicates by content hash, so retrying the same file after a lost response is
safe. Directory batches, extraction jobs, rebuilds, moving, and deletion remain
deliberate owner-repo operations; do not substitute filesystem access for an
unsupported HTTP operation.

Read the JSON envelope's `status`, `error.code`, and `error.retryable`. Auth
configuration failures require the correct generated file; network/timeouts may
be retried within the task. Never silently switch to a local corpus, another
person's credentials, or a different endpoint after failure. API/client recovery
details belong in the owning references, not in a second skill implementation.
