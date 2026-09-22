"""Small machine-local provider layer shared by sync, validation, and the menu CLI."""
from __future__ import annotations

import contextlib
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import tomllib

PROFILES = {"azure": "azure-astra.config.toml", "subscription": "chatgpt.config.toml"}
AZURE_MODELS = ("gpt-6-astra", "gpt-6-sol", "gpt-6-luna")
AZURE_CATALOG = "model-catalogs/azure-gpt6.json"
# Subscription removes the Azure catalog; the retired search override stays owned.
OWNED = ("model_provider", "model_catalog_json", "forced_login_method", "features.standalone_web_search")


def state_path() -> Path:
    return Path.home() / ".local/state/codex-control-plane/provider"


def load(path: Path) -> dict:
    return tomllib.loads(path.read_text()) if path.is_file() else {}


def selected(config: Path) -> str:
    state = state_path()
    if state.exists():
        value = state.read_text().strip()
        if value not in PROFILES:
            raise ValueError(f"Invalid provider preference in {state}; select azure or subscription.")
        return value
    provider = load(config).get("model_provider", "openai")
    if provider not in ("azure", "openai"):
        raise ValueError(f"Unrecognized current provider {provider!r}; explicitly select azure or subscription.")
    return "azure" if provider == "azure" else "subscription"


def supported(canonical: Path) -> bool:
    return all((canonical / name).is_file() for name in PROFILES.values())


def values(canonical: Path, choice: str, config: Path | None = None) -> dict:
    profile = load(canonical / PROFILES[choice])
    if profile.get("model_provider") != ("azure" if choice == "azure" else "openai"):
        raise ValueError(f"Invalid or missing {PROFILES[choice]}")
    result = {k: profile.get(k) for k in OWNED if not k.startswith("features.")}
    result["features.standalone_web_search"] = profile.get("features", {}).get("standalone_web_search")
    if choice == "azure":
        result["model"] = profile.get("model")
        if not result["model"]:
            raise ValueError("Azure profile is missing its deployment model.")
        if config is not None and load(config).get("model") in AZURE_MODELS:
            result["model"] = load(config)["model"]
    return result


def get(data: dict, key: str):
    value = data
    for part in key.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def overlay(text: str, settings: dict) -> str:
    """Replace only our scalar keys, preserving unrelated config and comments."""
    lines = []
    section = ""
    for line in text.splitlines(keepends=True):
        header = re.match(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$", line.rstrip())
        if header:
            section = header[1]
        elif line.lstrip().startswith("[["):
            section = "__array__"
        assignment = re.match(r"^\s*([A-Za-z_][A-Za-z_0-9.]*)\s*=", line)
        path = f"{section}.{assignment[1]}" if section and assignment else assignment[1] if assignment else None
        if path not in settings:
            lines.append(line)
    body = "".join(lines)
    top = "".join(f"{key} = {json.dumps(value)}\n" for key, value in settings.items()
                  if "." not in key and value is not None)
    feature = settings.get("features.standalone_web_search")
    if feature is not None:
        entry = f"standalone_web_search = {json.dumps(feature)}\n"
        match = re.search(r"(?m)^\s*\[features\]\s*(?:#[^\n]*)?\n", body)
        if match:
            body = body[:match.end()] + entry + body[match.end():]
        else:
            body = body.rstrip() + "\n\n[features]\n" + entry
    result = top + body
    parsed = tomllib.loads(result)
    if any(get(parsed, k) != v for k, v in settings.items()):
        raise ValueError("Provider settings could not be rendered; config was left unchanged.")
    return result


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=".provider-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777 if path.exists() else 0o600)
        os.replace(temporary, path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def azure_catalog(data: dict) -> dict:
    """Select complete upstream entries, including their prompts and protocol metadata."""
    models = data.get("models") if isinstance(data, dict) else None
    if not isinstance(models, list) or not all(isinstance(model, dict) for model in models):
        raise ValueError("Model catalog must contain a models array.")
    selected_models = [model for model in models if model.get("slug") in AZURE_MODELS]
    by_slug = {model["slug"]: model for model in selected_models}
    if len(selected_models) != len(AZURE_MODELS) or set(by_slug) != set(AZURE_MODELS):
        raise ValueError("Model catalog must contain Astra, Sol, and Luna exactly once.")
    return {"models": [by_slug[slug] for slug in AZURE_MODELS]}


def read_catalog(path: Path) -> dict | None:
    try:
        return azure_catalog(json.loads(path.read_text()))
    except (OSError, ValueError):
        return None


def catalog_ready(config: Path) -> bool:
    path = config.parent / AZURE_CATALOG
    try:
        data = json.loads(path.read_text())
        return data == azure_catalog(data)
    except (OSError, ValueError):
        return False


def prepare_catalog(canonical: Path, config: Path, *, apply: bool = False, refresh: bool = False) -> dict | None:
    """Materialize an Azure-only runtime snapshot without pinning the shared cache."""
    if load(canonical / PROFILES["azure"]).get("model_catalog_json") != AZURE_CATALOG:
        return None
    target = config.parent / AZURE_CATALOG
    data = read_catalog(config.parent / "models_cache.json") or read_catalog(target)
    if data is None and refresh and not load(config).get("model_catalog_json"):
        # Initial setup on another Mac may still have a pre-launch cache. Native
        # OpenAI discovery refreshes metadata only; it makes no inference request.
        binary = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
        if binary.is_file():
            try:
                result = subprocess.run(
                    [str(binary), "-c", 'model_provider="openai"', "debug", "models"],
                    cwd=config.parent, stdin=subprocess.DEVNULL, capture_output=True,
                    text=True, timeout=30, check=False,
                )
                if result.returncode == 0:
                    data = read_catalog(config.parent / "models_cache.json") or azure_catalog(json.loads(result.stdout))
            except (OSError, ValueError, subprocess.TimeoutExpired):
                pass
    if data is None:
        raise ValueError(
            "Azure GPT-6 model metadata is missing. Select subscription, run "
            "`codex debug models` to refresh native discovery, then rerun shared bootstrap. "
            "Existing config and model catalogs were left unchanged."
        )
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if apply and (not target.is_file() or target.read_text() != rendered):
        atomic_write(target, rendered)
    return data


@contextlib.contextmanager
def config_lock(config: Path, timeout: float = 60):
    config.parent.mkdir(parents=True, exist_ok=True)
    with (config.parent / ".control-plane-config.lock").open("a") as stream:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Codex configuration is busy; retry the provider switch.")
                time.sleep(0.1)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def status(config: Path, canonical: Path) -> dict:
    choice = selected(config)
    expected = values(canonical, choice, config)
    data = load(config)
    in_sync = all(get(data, k) == v for k, v in expected.items())
    if expected.get("model_catalog_json") == AZURE_CATALOG:
        in_sync = in_sync and catalog_ready(config)
    return {"selected": choice, "effective_provider": data.get("model_provider", "openai"),
            "persisted": state_path().is_file(), "config_in_sync": in_sync,
            "applied": False, "restart_required": True, "scope": "this_machine",
            "state_file": str(state_path()), "config_file": str(config)}


def preflight(config: Path, canonical: Path, choice: str) -> None:
    values(canonical, choice, config)
    if choice == "azure":
        provider = load(config).get("model_providers", {}).get("azure", {})
        if not provider.get("base_url") or not provider.get("env_key"):
            raise ValueError("Azure provider is not installed; run the shared bootstrap.")
        env = config.parent / ".env"
        key = provider["env_key"]
        if not env.is_file() or not re.search(rf"(?m)^(?:export\s+)?{re.escape(key)}\s*=\s*\S+", env.read_text()):
            raise PermissionError("Azure credentials are not ready; run the shared bootstrap.")
        prepare_catalog(canonical, config)
    else:
        # File-based ChatGPT auth is this control plane's existing contract.
        auth = config.parent / "auth.json"
        data = json.loads(auth.read_text()) if auth.is_file() else {}
        if data.get("auth_mode") not in (None, "chatgpt") or not data.get("tokens", {}).get("access_token"):
            raise PermissionError("Codex subscription login is missing; sign in with ChatGPT first.")


def switch(config: Path, canonical: Path, choice: str, apply: bool, timeout: float) -> dict:
    preflight(config, canonical, choice)
    if not apply:
        result = status(config, canonical)
        result["requested"] = choice
        return result
    with config_lock(config, timeout):
        preflight(config, canonical, choice)
        if choice == "azure":
            prepare_catalog(canonical, config, apply=True)
        before = config.read_text()
        after = overlay(before, values(canonical, choice, config))
        preference = state_path()
        old_preference = preference.read_text() if preference.is_file() else None
        # Preference first: a subsequent sync repairs a crash between the two writes.
        atomic_write(preference, choice + "\n")
        try:
            if config.read_text() != before:
                raise ValueError("Codex config changed during the switch; retry.")
            if after != before:
                atomic_write(config, after)
        except Exception:
            if old_preference is None:
                preference.unlink(missing_ok=True)
            else:
                atomic_write(preference, old_preference)
            raise
        result = status(config, canonical)
        result["applied"] = True
        return result


def main() -> int:
    action = sys.argv[1]
    if action == "lock":
        config = Path(sys.argv[2])
        with config_lock(config):
            return subprocess.call(sys.argv[3:], env={**os.environ, "CODEX_CONFIG_LOCK_HELD": str(config)})
    canonical, config = map(Path, sys.argv[2:4])
    if not supported(canonical):
        return 0
    choice = selected(config)
    if action == "catalog":
        apply = "--apply" in sys.argv[4:]
        prepare_catalog(canonical, config, apply=apply, refresh=apply)
    elif action == "render":
        target = Path(sys.argv[4])
        settings = values(canonical, choice, config)
        # Subscription model choice remains client-owned when shared sync runs.
        if choice == "subscription" and "model" in load(config):
            settings["model"] = load(config)["model"]
        target.write_text(overlay(target.read_text(), settings))
    elif action == "remember":
        if not state_path().exists():
            atomic_write(state_path(), choice + "\n")
    elif action == "check":
        if not status(config, canonical)["config_in_sync"]:
            raise ValueError("Codex provider settings disagree with this Mac's preference; run sync-config.sh --apply.")
    else:
        raise ValueError(f"Unknown action: {action}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TimeoutError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
