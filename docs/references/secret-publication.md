# Local secret-publication checks

The shared Git hooks and Codex/Claude Stop finalizer use the official
[Gitleaks 8.30.1 release](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1).
`hooks/config/gitleaks-release.json` pins both the downloaded archive and extracted
binary SHA-256 for supported Mac/Linux architectures. No root install or cloud
scanner is involved.

## Commands and recovery

```bash
python3 scripts/install-secret-scanner.py --apply
python3 scripts/install-secret-scanner.py --check
python3 hooks/scripts/git_secret_guard.py check-index --repo ~/GitHub/win
python3 hooks/scripts/git_secret_guard.py audit-tree --repo ~/GitHub/win
```

Machine bootstrap installs the dependency before configuring shared hooks.
Checks never download tools. A missing, changed, or failing scanner blocks
publication and gives the installer command; working files and staged changes
remain intact. The verified binary lives under
`~/.local/share/agents-control-plane/tools/gitleaks/<version>/gitleaks`.
`AGENTS_GITLEAKS_BIN` can select that same pinned binary when tests isolate HOME;
its hash must still match.

## Boundaries

- Ordinary commits scan the changed index blobs before repo fast checks.
- Codex and Claude Stop explicitly scan each staged tree during preflight,
  including repos without a fast-check script. Their later `--no-verify` commit
  cannot substitute for this check; the existing tree-stability loop covers
  changes arriving during validation.
- Pre-push scans changed blobs from every outgoing commit, including a secret
  added and then deleted before push. New remote refs exclude history only when
  the actual push destination currently advertises it. Stale local tracking refs
  are not proof. An advertised previous commit missing locally requires a fetch.
- Idle publication and automatic Git sync use these same ordinary Git hooks.
  Already-created unpublished commits still pass the pre-push boundary.

Snapshots contain exact Git objects, not mutable working-tree files. Symlink
blobs are text, not followed links. Snapshots and fully redacted intermediate
reports use private temporary directories removed after each scan. Hook output
contains only paths, rules, and line numbers; no matched content or tool stderr
is forwarded. The baseline audit adds nonsecret content hashes for review.

## False positives and limits

The central `hooks/config/gitleaks.toml` extends Gitleaks' built-in rules and
allowlists. Repo-local configurations, `.gitleaksignore`, environment overrides,
and inline `gitleaks:allow` comments do not disable this publication policy.

`hooks/config/secret-fixtures.json` records reviewed false positives by enrolled
repo ID, exact path, rule, and SHA-256 of the original matching source lines.
Moving unchanged lines or editing unrelated lines does not invalidate an
exception; changed matching content does. Encoded/archive findings require an
explicit exact-blob hash because their line numbers can address decoded content.
Each entry needs a concrete reason. Do not baseline real credentials merely
because they already exist in Git, or exempt whole test/document directories.

This is a standard pattern scanner, not proof that a repository contains no
secrets. Built-in allowlists skip some generated formats (including package lock
files and SVGs), and unknown credential formats can be missed. Ignored local
files are not publication payloads. Deliberately bypassing local hooks remains
possible for the repository owner; server enforcement and history rewriting are
separate decisions. Credential exposure still requires provider-side rotation,
not just deleting a file or accepting a scanner result.
