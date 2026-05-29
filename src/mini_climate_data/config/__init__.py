from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib

DEFAULT_CONFIG_RESOURCE = "defaults.toml"
DEFAULT_USER_CONFIG = "mini-climate-data.toml"

ENV_BASE_URL = "MINI_CLIMATE_DATA_BASE_URL"
ENV_CONFIG = "MINI_CLIMATE_DATA_CONFIG"
ENV_DATA_VERSION = "MINI_CLIMATE_DATA_VERSION"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load packaged defaults and merge optional user TOML overrides."""
    config = _read_toml(Path(__file__).with_name(DEFAULT_CONFIG_RESOURCE))
    user_config = _user_config_path(path)
    if user_config and user_config.exists():
        config = _merge(config, _read_toml(user_config))
    return config


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Configuration must be a TOML table: {path}")
    return data


def _user_config_path(path: str | Path | None) -> Path | None:
    if path is not None:
        return Path(path)
    if ENV_CONFIG in os.environ:
        return Path(os.environ[ENV_CONFIG])
    local = Path(DEFAULT_USER_CONFIG)
    return local if local.exists() else None


def _merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


CONFIG = load_config()

DEFAULT_BASE_URL = str(CONFIG["fetch"]["base_url"])
DEFAULT_DATA_BRANCH = str(CONFIG["data_store"]["branch"])
DEFAULT_DATA_WORKTREE = str(CONFIG["data_store"]["worktree"])
DEFAULT_RECIPE_ROOT = str(CONFIG["data_store"]["recipe_root"])
DEFAULT_SOURCE_CACHE = str(CONFIG["data_store"]["source_cache"])
DEFAULT_FETCH_VERSION = str(CONFIG["fetch"].get("version", DEFAULT_DATA_BRANCH))
REGISTRY_NAME = str(CONFIG["registry"]["name"])


@dataclass(frozen=True)
class DataStoreConfig:
    """Local git-backed generated data store settings."""

    branch: str = DEFAULT_DATA_BRANCH
    worktree: Path = Path(DEFAULT_DATA_WORKTREE)
    recipe_root: Path = Path(DEFAULT_RECIPE_ROOT)
    source_cache: Path = Path(DEFAULT_SOURCE_CACHE)

    @property
    def registry_path(self) -> Path:
        return self.worktree / REGISTRY_NAME


def configured_base_url(base_url: str | None = None) -> str:
    """Return the configured data-store base URL with one trailing slash."""
    base = base_url or os.environ.get(ENV_BASE_URL, DEFAULT_BASE_URL)
    return base if base.endswith("/") else f"{base}/"


def configured_data_version(version: str | None = None) -> str:
    """Return the configured generated-data branch or version."""
    return version or os.environ.get(ENV_DATA_VERSION, DEFAULT_FETCH_VERSION)


def config_value(name: str) -> str:
    """Return a string configuration value by constant name."""
    try:
        value = globals()[name]
    except KeyError as exc:
        raise ValueError(f"Unknown config value: {name}") from exc
    if not isinstance(value, str):
        raise ValueError(f"Config value is not a string: {name}")
    return value


if __name__ == "__main__":
    print(config_value(sys.argv[1]))
