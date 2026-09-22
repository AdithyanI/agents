#!/usr/bin/env python3
"""Bound automatic Git payloads before staging and at the commit boundary.

Read file metadata and Git object sizes, never file contents. Large generated
artifacts belong outside Git; this does not delete or unstage anything on error.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat
import subprocess
import sys

MAX_FILE_BYTES = 100 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024


class PayloadError(RuntimeError):
    pass


def git(root: str, *args: str, data: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", "--literal-pathspecs", "-C", root, *args],
        input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
    )
    if result.returncode:
        raise PayloadError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def index_sizes(root: str) -> dict[str, int]:
    fields = git(root, "diff", "--cached", "--raw", "--no-abbrev", "--no-renames",
                 "--diff-filter=ACMRT", "-z").split(b"\0")
    entries: dict[str, str] = {}
    for offset in range(0, len(fields) - 1, 2):
        header = fields[offset].split()
        if len(header) != 5:
            raise PayloadError("Cannot inspect staged Git object metadata.")
        if header[1] == b"160000":  # Submodule commit, not a file payload.
            continue
        entries[os.fsdecode(fields[offset + 1])] = header[3].decode("ascii")
    if not entries:
        return {}
    objects = sorted(set(entries.values()))
    rows = git(root, "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)",
               data=("\n".join(objects) + "\n").encode()).splitlines()
    sizes: dict[str, int] = {}
    for row in rows:
        parts = row.split()
        if len(parts) != 3 or parts[1] != b"blob":
            raise PayloadError("Cannot inspect a staged Git blob size.")
        sizes[parts[0].decode("ascii")] = int(parts[2])
    return {path: sizes[oid] for path, oid in entries.items()}


def check_sizes(sizes: dict[str, int], *, max_file: int = MAX_FILE_BYTES,
                max_total: int = MAX_TOTAL_BYTES) -> None:
    oversized = [(path, size) for path, size in sizes.items() if size > max_file]
    total = sum(sizes.values())
    if not oversized and total <= max_total:
        return
    details = [f"{path!r}: {size:,} bytes" for path, size in sorted(oversized)[:10]]
    if total > max_total:
        details.append(f"total changed content: {total:,} bytes")
    raise PayloadError(
        "Git payload limit exceeded; automatic publication stopped without deleting files. "
        f"Limits: {max_file:,} bytes per file, {max_total:,} bytes per change. "
        "Keep generated media/build artifacts outside Git and ignore their paths. "
        + "; ".join(details)
    )


def check_index(root: str, **limits: int) -> None:
    check_sizes(index_sizes(root), **limits)


def stage(root: str, **limits: int) -> None:
    candidates = sorted(set(filter(None, git(
        root, "ls-files", "--modified", "--deleted", "--others", "--exclude-standard", "-z",
    ).split(b"\0"))))
    sizes = index_sizes(root)
    for candidate in candidates:
        name = os.fsdecode(candidate)
        try:
            info = (Path(root) / name).lstat()
        except FileNotFoundError:
            sizes.pop(name, None)  # Tracked deletion.
            continue
        if stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
            sizes[name] = info.st_size
        elif not stat.S_ISDIR(info.st_mode):
            raise PayloadError(f"Cannot automatically stage special file {name!r}.")
    check_sizes(sizes, **limits)
    if candidates:
        # Stage only inspected paths: a new file arriving during validation must
        # wait for the next consolidation pass, not sneak into `git add -A`.
        git(root, "add", "-A", "--pathspec-from-file=-", "--pathspec-file-nul",
            data=b"\0".join(candidates) + b"\0")
    check_index(root, **limits)  # Also catches clean-filter or concurrent changes.


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage", "check-index"))
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    try:
        (stage if args.action == "stage" else check_index)(args.repo)
    except (PayloadError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"git-payload-guard: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
