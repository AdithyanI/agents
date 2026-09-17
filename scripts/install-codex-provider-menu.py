#!/usr/bin/env python3
"""Machine-facing installer for the local Codex provider menu (macOS only)."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import sys
import tempfile
import time


APP_NAME = "Codex Provider.app"
EXECUTABLE = "CodexProvider"
IDENTIFIER = "io.adithyan.codex-provider"


def run(arguments: list[str], *, timeout: int = 120, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, capture_output=True, text=True, timeout=timeout, check=check)


def write_plist(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        plistlib.dump(value, handle, sort_keys=True)


def app_owned(path: Path) -> bool:
    try:
        with (path / "Contents/Info.plist").open("rb") as handle:
            return plistlib.load(handle).get("CFBundleIdentifier") == IDENTIFIER
    except (OSError, plistlib.InvalidFileException):
        return False


def plist_owned(path: Path, app: Path) -> bool:
    try:
        with path.open("rb") as handle:
            value = plistlib.load(handle)
        return value.get("Label") == IDENTIFIER and value.get("ProgramArguments") == [str(app / "Contents/MacOS" / EXECUTABLE)]
    except (OSError, plistlib.InvalidFileException):
        return False


def link_owned(path: Path, helper: Path) -> bool:
    return path.is_symlink() and path.resolve() == helper.resolve()


def stop_owned_app(app: Path, domain: str) -> None:
    # launchctl addresses only this utility. Also close an instance manually
    # launched from Finder, matched by its complete executable path.
    run(["/bin/launchctl", "bootout", f"{domain}/{IDENTIFIER}"], check=False)
    executable = str(app / "Contents/MacOS" / EXECUTABLE)
    processes = run(["/bin/ps", "-axo", "pid=,comm="], check=False)
    for row in processes.stdout.splitlines():
        fields = row.strip().split(maxsplit=1)
        if len(fields) == 2 and fields[1] == executable:
            try:
                os.kill(int(fields[0]), 15)
            except ProcessLookupError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Build, install, and start the menu app at login")
    mode.add_argument("--dry-run", action="store_true", help="Describe changes without writing (default)")
    parser.add_argument("--uninstall", action="store_true", help="With --apply, remove only the menu app and its login agent")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="Canonical agents repository")
    parser.add_argument("--python", default=sys.executable, help="Python executable for the provider helper")
    parser.add_argument("--no-input", action="store_true", help="Accepted for automation; this installer never prompts")
    args = parser.parse_args()

    if sys.platform != "darwin":
        parser.error("Codex Provider requires macOS")
    home = Path.home()
    root = args.root.expanduser().resolve()
    app = home / "Applications" / APP_NAME
    plist = home / "Library/LaunchAgents" / f"{IDENTIFIER}.plist"
    helper = root / "scripts/codex-provider.py"
    launcher = home / "bin/codex-provider"
    domain = f"gui/{os.getuid()}"
    if app.exists() and not app_owned(app):
        parser.error(f"refusing to replace an unrelated application: {app}")
    if plist.exists() and not plist_owned(plist, app):
        parser.error(f"refusing to replace an unrelated login agent: {plist}")

    if args.uninstall:
        if not args.apply:
            print(f"Would unload {IDENTIFIER} and remove {app} and {plist}.")
            if link_owned(launcher, helper):
                print(f"Would remove the owned terminal command {launcher}.")
            print("The local provider selection and Codex configuration are retained.")
            return 0
        stop_owned_app(app, domain)
        plist.unlink(missing_ok=True)
        if app.exists():
            shutil.rmtree(app)
        for name in ("provider-menu.out.log", "provider-menu.err.log"):
            (home / ".local/state/codex-control-plane/log" / name).unlink(missing_ok=True)
        if link_owned(launcher, helper):
            launcher.unlink()
        print(f"Removed {app} and its login agent. Provider selection is unchanged.")
        return 0

    python = shutil.which(args.python)
    if not python:
        parser.error(f"Python executable is unavailable: {args.python}")
    python = str(Path(python).absolute())
    source = root / "codex/menu-bar/CodexProvider.swift"
    if not source.is_file() or not helper.is_file():
        parser.error(f"provider source or helper is missing under {root}")
    if (launcher.exists() or launcher.is_symlink()) and not link_owned(launcher, helper):
        parser.error(f"unrelated terminal command exists at {launcher}; move it before installing")
    swift = run(["/usr/bin/xcrun", "--find", "swiftc"]).stdout.strip()
    sdk = run(["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-path"]).stdout.strip()
    if not args.apply:
        print(f"Would compile {source} using {swift}.")
        print(f"Would install {app}, load {plist}, and start the menu on this Mac.")
        print(f"Helper: {python} {helper}")
        print(f"Would link {launcher} to {helper}.")
        print("Provider selection is unchanged. Codex itself will not be restarted.")
        return 0

    # Build before replacing the live utility. Temporary build output is kept in
    # the repository's ignored tmp directory and removed even on failure.
    temporary_root = root / "tmp"
    temporary_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="codex-provider-menu-", dir=temporary_root) as temporary:
        staged = Path(temporary) / APP_NAME
        contents = staged / "Contents"
        binary = contents / "MacOS" / EXECUTABLE
        binary.parent.mkdir(parents=True)
        resources = contents / "Resources"
        resources.mkdir()
        run([swift, "-O", "-swift-version", "5", "-sdk", sdk, "-target", f"{platform.machine()}-apple-macos13.0",
             "-framework", "AppKit", str(source), "-o", str(binary)], timeout=180)
        write_plist(contents / "Info.plist", {
            "CFBundleExecutable": EXECUTABLE,
            "CFBundleIdentifier": IDENTIFIER,
            "CFBundleName": "Codex Provider",
            "CFBundleDisplayName": "Codex Provider",
            "CFBundlePackageType": "APPL",
            "CFBundleVersion": "1",
            "CFBundleShortVersionString": "1.0",
            "LSMinimumSystemVersion": "13.0",
            "LSUIElement": True,
            "NSHighResolutionCapable": True,
        })
        (resources / "provider-menu.json").write_text(
            json.dumps({"python": python, "script": str(helper), "root": str(root)}, indent=2) + "\n",
            encoding="utf-8",
        )
        run(["/usr/bin/codesign", "--force", "--sign", "-", str(staged)])
        run(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(staged)])
        # Exercise the actual bundle/config/helper contract without changing the
        # provider, before replacing a known working installed app.
        inspection = run([str(binary), "--inspect-menu"], timeout=190)
        menu_state = json.loads(inspection.stdout)
        if menu_state.get("selected") not in ("azure", "subscription"):
            raise RuntimeError("built menu could not read the provider selection")

        stop_owned_app(app, domain)
        app.parent.mkdir(parents=True, exist_ok=True)
        if app.exists():
            shutil.rmtree(app)
        shutil.copytree(staged, app)

    launcher.parent.mkdir(parents=True, exist_ok=True)
    if not launcher.is_symlink():
        launcher.symlink_to(helper)
    log_dir = home / ".local/state/codex-control-plane/log"
    log_dir.mkdir(parents=True, exist_ok=True)
    write_plist(plist, {
        "Label": IDENTIFIER,
        "ProgramArguments": [str(app / "Contents/MacOS" / EXECUTABLE)],
        "WorkingDirectory": str(root),
        "RunAtLoad": True,
        "LimitLoadToSessionType": "Aqua",
        "EnvironmentVariables": {"HOME": str(home), "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"},
        "StandardOutPath": str(log_dir / "provider-menu.out.log"),
        "StandardErrorPath": str(log_dir / "provider-menu.err.log"),
    })
    # bootout/bootstrap can briefly race loginwindow's removal of the old job.
    for attempt in range(5):
        result = run(["/bin/launchctl", "bootstrap", domain, str(plist)], check=False)
        if result.returncode == 0:
            break
        if attempt == 4:
            raise RuntimeError(f"launchctl bootstrap failed: {result.stderr.strip()}")
        time.sleep(0.5)
    loaded = run(["/bin/launchctl", "print", f"{domain}/{IDENTIFIER}"])
    if "state = running" not in loaded.stdout:
        # The job can be loaded before the GUI process enters its run loop.
        time.sleep(0.5)
        loaded = run(["/bin/launchctl", "print", f"{domain}/{IDENTIFIER}"])
    if "state = running" not in loaded.stdout:
        raise RuntimeError(f"menu login agent is loaded but not running; inspect {log_dir}")
    print(f"Installed and started {app}")
    print(f"Login agent: {plist}")
    print(f"Terminal command: {launcher}")
    print(f"Current provider: {menu_state['selected']} (this Mac only)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        print(f"ERROR: {' '.join(error.cmd)}: {(error.stderr or error.stdout).strip()}", file=sys.stderr)
        raise SystemExit(4)
    except subprocess.TimeoutExpired as error:
        print(f"ERROR: command timed out after {error.timeout} seconds", file=sys.stderr)
        raise SystemExit(5)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
