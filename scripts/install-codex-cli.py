#!/usr/bin/env python3
"""Link the native desktop Codex CLI and its adjacent code-mode companion."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

DESKTOP_RESOURCES = Path("/Applications/ChatGPT.app/Contents/Resources")


def codex_command_targets(home: Path, resources: Path = DESKTOP_RESOURCES) -> dict[Path, Path]:
    # Keep the code-mode companion beside the invoked command. Current macOS
    # packages expose a shell launcher in bin; executing that launcher through
    # ~/bin can exceed the desktop SSH timeout, so prefer its native app binary.
    layouts = (resources / "codex-cli/bin", resources)
    desktop_bin = next((directory for directory in layouts if all(
        (directory / name).is_file() for name in ("codex", "codex-code-mode-host")
    )), layouts[0])
    codex_target = desktop_bin / "codex"
    native_codex = resources / "codex-cli/CodexCLI.app/Contents/MacOS/codex"
    if desktop_bin == layouts[0] and native_codex.is_file():
        codex_target = native_codex
    return {
        home / "bin/codex": codex_target,
        # Codex resolves this companion relative to argv[0], so a terminal
        # symlink for `codex` must bring the host along with it.
        home / "bin/codex-code-mode-host": desktop_bin / "codex-code-mode-host",
    }



def link_owned(path: Path, helper: Path) -> bool:
    return path.is_symlink() and path.resolve() == helper.resolve()


def codex_link_owned(path: Path, target: Path, resources: Path = DESKTOP_RESOURCES) -> bool:
    if link_owned(path, target):
        return True
    return path.name in {"codex", "codex-code-mode-host"} and any(
        link_owned(path, directory / path.name)
        for directory in (resources, resources / "codex-cli/bin",
                          resources / "codex-cli/CodexCLI.app/Contents/MacOS")
    )



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-input", action="store_true", help="Never prompts")
    args = parser.parse_args()
    targets = codex_command_targets(Path.home())
    for command, target in targets.items():
        if not target.is_file() or not os.access(target, os.X_OK):
            parser.error(f"required native command is unavailable: {target}")
        if (command.exists() or command.is_symlink()) and not codex_link_owned(command, target):
            parser.error(f"unrelated terminal command exists: {command}")
    for command, target in targets.items():
        if link_owned(command, target):
            print(f"Unchanged: {command}")
            continue
        if args.apply:
            command.parent.mkdir(parents=True, exist_ok=True)
            command.unlink(missing_ok=True)
            command.symlink_to(target)
        print(f"{'Linked' if args.apply else 'Would link'}: {command} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
