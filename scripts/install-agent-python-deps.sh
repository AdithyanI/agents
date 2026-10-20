#!/usr/bin/env bash
set -euo pipefail

# Ensure Python modules that shared agent tooling imports at runtime:
#   requests -> media-toolkit WIN API client
#   yaml     -> control-plane dashboard skill metadata (PyYAML)
# Installs into the pinned interpreter's user site, like the PDF skill deps.

APPLY=0
PYTHON_BIN="${PYTHON_BIN:-python3}"
MODULES=(requests yaml)
PACKAGES=(requests PyYAML)

usage() {
  cat <<USAGE
Usage: $(basename "$0") [options]

Ensure Python modules required by shared agent tooling (media-toolkit, dashboard).

Default mode is dry-run. Use --apply to install missing modules.

Options:
  --apply            Install missing modules
  --dry-run          Show actions only (default)
  --python <path>    Override python3 used for import checks and pip install
  -h, --help         Show this help
USAGE
}

log() {
  printf '%s\n' "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --dry-run) APPLY=0; shift ;;
    --python) PYTHON_BIN="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
done

command -v "$PYTHON_BIN" >/dev/null 2>&1 || die "Python not found: $PYTHON_BIN"

missing=()
for index in "${!MODULES[@]}"; do
  if ! "$PYTHON_BIN" -c "import ${MODULES[$index]}" >/dev/null 2>&1; then
    missing+=("${PACKAGES[$index]}")
  fi
done

if (( ${#missing[@]} == 0 )); then
  log "OK: agent Python modules already available (${MODULES[*]})"
  exit 0
fi

if (( APPLY == 0 )); then
  log "WOULD INSTALL: ${missing[*]} via $PYTHON_BIN -m pip install --user"
  exit 0
fi

pip_args=(install --user)
if "$PYTHON_BIN" -m pip install --help 2>/dev/null | grep -q -- "--break-system-packages"; then
  pip_args+=(--break-system-packages)
fi
pip_args+=("${missing[@]}")
log "+ $PYTHON_BIN -m pip ${pip_args[*]}"
"$PYTHON_BIN" -m pip "${pip_args[@]}"
for module in "${MODULES[@]}"; do
  "$PYTHON_BIN" -c "import ${module}" || die "module still missing after install: ${module}"
done
log "OK: agent Python modules installed"
