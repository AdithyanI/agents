#!/usr/bin/env python3
"""Scan exact Git blobs before commits and outgoing revisions before pushes.

Gitleaks runs offline with the centrally pinned rules, full redaction, and no
repo-local ignore files. Only paths, rule names and line numbers leave the scan.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import sys
import tempfile

CONTROL_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = CONTROL_ROOT / "hooks/config"
PIN = json.loads((CONFIG_ROOT / "gitleaks-release.json").read_text())
OID = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")


class ScanError(RuntimeError):
    pass


def platform_key() -> str:
    machine = {"aarch64": "arm64", "x86_64": "x64"}.get(platform.machine(), platform.machine())
    key = f"{platform.system().lower()}_{machine}"
    if key not in PIN["assets"]:
        raise ScanError("Unsupported Gitleaks platform; publication stopped.")
    return key


def installed_path() -> Path:
    return Path.home() / ".local/share/agents-control-plane/tools/gitleaks" / PIN["version"] / "gitleaks"


def scanner_path() -> Path:
    # A test runner may retain the same verified tool when it creates an isolated
    # HOME. An override never relaxes the pinned binary hash.
    path = Path(os.environ.get("AGENTS_GITLEAKS_BIN") or installed_path())
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        valid = digest == PIN["assets"][platform_key()]["binary_sha256"] and os.access(path, os.X_OK)
    except OSError:
        valid = False
    if not valid:
        raise ScanError("Pinned Gitleaks is missing or changed. Run "
                        "~/GitHub/agents/scripts/install-secret-scanner.py --apply; then retry. "
                        "No files were removed or published.")
    return path.resolve()


def git(root: str, *args: str, data: bytes | None = None) -> bytes:
    result = subprocess.run(["git", "--literal-pathspecs", "-C", root, *args],
                            input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    if result.returncode:
        # Git's diagnostics may quote repository content (for example invalid
        # configuration). Never forward raw subprocess output to hook logs.
        raise ScanError("Cannot inspect Git objects for secret scanning; publication stopped.")
    return result.stdout


def parse_raw(raw: bytes) -> set[tuple[str, str]]:
    fields = raw.split(b"\0")
    result: set[tuple[str, str]] = set()
    for index in range(0, len(fields) - 1, 2):
        header = fields[index].strip().split()
        if len(header) != 5:
            raise ScanError("Cannot inspect changed Git objects.")
        if header[1] == b"160000":
            continue  # Submodules have their own publication boundary.
        oid = header[3].decode("ascii")
        if not OID.fullmatch(oid):
            raise ScanError("Invalid Git blob identity.")
        result.add((os.fsdecode(fields[index + 1]), oid))
    return result


def index_blobs(root: str) -> set[tuple[str, str]]:
    return parse_raw(git(root, "diff", "--cached", "--raw", "--no-abbrev", "--no-renames",
                         "--diff-filter=ACMRT", "-z"))


def tree_blobs(root: str, revision: str) -> set[tuple[str, str]]:
    result = set()
    for row in git(root, "ls-tree", "-rz", "--full-tree", revision).split(b"\0"):
        if not row:
            continue
        metadata, name = row.split(b"\t", 1)
        _mode, kind, oid = metadata.split()
        if kind == b"blob":
            result.add((os.fsdecode(name), oid.decode("ascii")))
    return result


def outgoing_blobs(root: str, remote: str, updates: str) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    revisions: set[str] = set()
    for line in updates.splitlines():
        parts = line.split()
        if len(parts) != 4 or not OID.fullmatch(parts[1]) or not OID.fullmatch(parts[3]):
            raise ScanError("Invalid pre-push ref update; publication stopped.")
        local, previous = parts[1], parts[3]
        if set(local) == {"0"}:
            continue  # Deleting a ref publishes no new objects.
        args = ["rev-list", local]
        if set(previous) != {"0"}:
            # The remote's advertised tip is authoritative. If it is absent
            # locally, require a fetch rather than guessing an unsafe range.
            args.append("^" + previous)
        else:
            # Only the actual destination's current advertisement proves
            # history is already published there. Local tracking refs can be
            # stale after a remote URL change and must not exempt content.
            advertised = git(root, "ls-remote", "--refs", "--", remote)
            for row in advertised.splitlines():
                candidate = row.split(b"\t", 1)[0].decode("ascii")
                if not OID.fullmatch(candidate):
                    raise ScanError("Invalid remote object advertisement.")
                present = subprocess.run(["git", "-C", root, "rev-parse", "--verify",
                                          candidate + "^{commit}"], stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, timeout=30)
                if present.returncode == 0:
                    args.append("^" + present.stdout.decode().strip())
        revisions.update(git(root, *args).decode().splitlines())
    for revision in sorted(revisions):
        result.update(parse_raw(git(root, "diff-tree", "-r", "-m", "--root", "--no-commit-id",
                                    "--raw", "--no-abbrev", "--no-renames", "--diff-filter=ACMRT", "-z", revision)))
    return result


def repository_id(root: str) -> str:
    registry = json.loads((CONTROL_ROOT / "repos/registry.json").read_text())
    canonical = Path(root).resolve()
    for item in registry["repos"]:
        if Path(item["path"]).expanduser().resolve() == canonical:
            return item["id"]
    return ""  # Unknown repositories never inherit another repo's fixture exceptions.


def approved_fixtures(root: str) -> set[tuple[str, str, str, str]]:
    repo_id = repository_id(root)
    policy = json.loads((CONFIG_ROOT / "secret-fixtures.json").read_text())
    if policy.get("version") != 1:
        raise ScanError("Unsupported fixture policy.")
    result = set()
    for row in policy["fixtures"]:
        if row["repo"] != repo_id or not row.get("reason"):
            continue
        result.add(("lines", row["path"], row["source_lines_sha256"], row["rule"]))
        if row.get("encoded_blob_sha256"):
            result.add(("encoded-blob", row["path"], row["encoded_blob_sha256"], row["rule"]))
    return result


def scan_blobs(root: str, blobs: set[tuple[str, str]]) -> list[dict]:
    if not blobs:
        return []
    executable = scanner_path()
    # Temp files are exact Git objects, never checked-out working-tree files.
    # Symlink blobs are plain text here and cannot escape the snapshot.
    with tempfile.TemporaryDirectory(prefix="git-secret-scan-") as temporary:
        base = Path(temporary)
        base.chmod(0o700)
        source = base / "payload"
        source.mkdir(mode=0o700)
        mapping: dict[str, tuple[str, str]] = {}
        for number, (name, oid) in enumerate(sorted(blobs)):
            parts = PurePosixPath(name).parts
            if not parts or PurePosixPath(name).is_absolute() or ".." in parts:
                raise ScanError("Unsafe Git path in publication snapshot.")
            target = source / str(number) / name
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            contents = git(root, "cat-file", "blob", oid)
            target.write_bytes(contents)
            target.chmod(0o600)
            mapping[str(target)] = (name, hashlib.sha256(contents).hexdigest())
        empty_ignore = base / "ignore"
        empty_ignore.write_text("")
        environment = {key: value for key, value in os.environ.items() if not key.startswith("GITLEAKS_")}
        command = [str(executable), "dir", str(source), "--config", str(CONFIG_ROOT / "gitleaks.toml"),
                   "--gitleaks-ignore-path", str(empty_ignore), "--ignore-gitleaks-allow", "--redact=100",
                   "--no-banner", "--no-color", "--log-level", "error", "--report-format", "json",
                   "--report-path", str(base / "redacted-report.json"), "--max-target-megabytes", "0",
                   "--max-archive-depth", "2", "--max-decode-depth", "2", "--exit-code", "23"]
        completed = subprocess.run(command, cwd=base, env=environment,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        if completed.returncode not in (0, 23):
            raise ScanError("Gitleaks could not complete; publication stopped (tool output withheld).")
        try:
            findings = json.loads((base / "redacted-report.json").read_bytes())
        except (ValueError, UnicodeDecodeError):
            raise ScanError("Gitleaks returned an invalid report; publication stopped.") from None
        if not isinstance(findings, list) or bool(findings) != (completed.returncode == 23):
            raise ScanError("Gitleaks report/exit status mismatch; publication stopped.")
        approved = approved_fixtures(root)
        result = []
        for item in findings:
            path = item.get("File")
            embedded = path not in mapping or bool(item.get("Tags"))
            if path not in mapping:
                # Embedded archive findings still belong to their exact blob.
                candidates = [key for key in mapping if isinstance(path, str) and path.startswith(key + "!")]
                if len(candidates) != 1:
                    raise ScanError("Gitleaks reported an unmapped file; publication stopped.")
                path = candidates[0]
            name, digest = mapping[path]
            rule, line = item.get("RuleID"), item.get("StartLine")
            if not isinstance(rule, str) or not re.fullmatch(r"[a-z0-9_-]+", rule) or not isinstance(line, int):
                raise ScanError("Gitleaks returned invalid finding metadata.")
            source_lines = Path(path).read_bytes().splitlines(keepends=True)
            end_line = item.get("EndLine")
            line_digest = ""
            if isinstance(end_line, int) and 1 <= line <= end_line <= len(source_lines):
                line_digest = hashlib.sha256(b"".join(source_lines[line - 1:end_line])).hexdigest()
            if embedded:
                allowed = ("encoded-blob", name, digest, rule) in approved
            else:
                allowed = bool(line_digest) and ("lines", name, line_digest, rule) in approved
            if allowed:
                continue
            result.append({"path": name, "rule": rule, "line": line, "blob_sha256": digest, "source_lines_sha256": line_digest})
        return result


def check_index(root: str) -> None:
    require_clean(scan_blobs(root, index_blobs(root)))


def require_clean(findings: list[dict]) -> None:
    if findings:
        details = "; ".join(f"{row['path']!r}:{row['line']} ({row['rule']})" for row in findings[:20])
        raise ScanError(f"Possible secrets in {len(findings)} finding(s): {details}. "
                        "Remove credentials and use generated secret files. Values are withheld; "
                        "review synthetic fixtures in the central policy rather than bypassing the check.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check-index", "check-push", "audit-tree", "check-tool"))
    parser.add_argument("--repo", default=".")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--revision", default="HEAD")
    args = parser.parse_args()
    try:
        if args.action == "check-tool":
            scanner_path()
        elif args.action == "check-index":
            check_index(args.repo)
        elif args.action == "check-push":
            require_clean(scan_blobs(args.repo, outgoing_blobs(args.repo, args.remote, sys.stdin.read())))
        else:
            findings = scan_blobs(args.repo, tree_blobs(args.repo, args.revision))
            print(json.dumps({"repo": repository_id(args.repo), "findings": findings}, sort_keys=True))
            return bool(findings)
    except (ScanError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        message = str(exc) if isinstance(exc, ScanError) else "Scanner dependency or metadata failure; publication stopped."
        print(f"git-secret-guard: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
