#!/usr/bin/env python3
"""Install the pinned official Gitleaks release without root or package scripts."""
from __future__ import annotations

import argparse
import hashlib
import io
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hooks.scripts import git_secret_guard as guard


def install() -> None:
    platform = guard.platform_key()
    version = guard.PIN["version"]
    asset = guard.PIN["assets"][platform]
    name = f"gitleaks_{version}_{platform}.tar.gz"
    url = f"https://github.com/gitleaks/gitleaks/releases/download/v{version}/{name}"
    with urllib.request.urlopen(url, timeout=60) as response:
        archive = response.read(64 * 1024 * 1024 + 1)
    if hashlib.sha256(archive).hexdigest() != asset["archive_sha256"]:
        raise guard.ScanError("Official release archive checksum mismatch; nothing installed.")
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as package:
        member = package.getmember("gitleaks")
        if not member.isfile() or member.size > 64 * 1024 * 1024:
            raise guard.ScanError("Invalid Gitleaks release member.")
        payload = package.extractfile(member).read()
    if hashlib.sha256(payload).hexdigest() != asset["binary_sha256"]:
        raise guard.ScanError("Gitleaks binary checksum mismatch; nothing installed.")
    target = guard.installed_path()
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".gitleaks-", delete=False) as stream:
        staged = Path(stream.name)
        try:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
            staged.chmod(0o700)
            os.replace(staged, target)
        finally:
            staged.unlink(missing_ok=True)
    print(f"Installed verified Gitleaks {version} ({platform}).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--apply", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        guard.scanner_path()
        print(f"OK: verified Gitleaks {guard.PIN['version']}.")
    except guard.ScanError:
        if args.check:
            print("Gitleaks missing or changed; run scripts/install-secret-scanner.py --apply.", file=sys.stderr)
            return 1
        if not args.apply:
            print(f"WOULD INSTALL: verified Gitleaks {guard.PIN['version']} ({guard.platform_key()}).")
            return 0
        try:
            install()
        except Exception:
            print("Gitleaks installation failed; existing binary preserved. Retry the installer.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
