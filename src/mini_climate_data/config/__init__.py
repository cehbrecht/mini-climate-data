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
DEFAULT_STORE = "default"

ENV_BASE_URL = "MINI_CLIMATE_DATA_BASE_URL"
ENV_CONFIG = "MINI_CLIMATE_DATA_CONFIG"
ENV_DATA_VERSION = "MINI_CLIMATE_DATA_VERSION"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load packaged defaults and merge optional user TOML overrides."""
    config = _read_toml(Path(__file__).with_name(DEFAULT_CONFIG_RESOURCE))
    user_config = _user_config_path(path)
    if user_config and user_config.exists():
        config = _merge(config, _read_toml(user_config))
    return _normalize_config(config)


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


def _normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy/default configuration into named stores."""
    normalized = dict(config)
    stores = dict(normalized.get("stores", {}))
    default_store = dict(stores.get(DEFAULT_STORE, {}))

    if "data_store" in normalized:
        default_store = _merge(default_store, normalized["data_store"])
    if "fetch" in normalized:
        fetch = normalized["fetch"]
        if "base_url" in fetch:
            default_store["base_url"] = fetch["base_url"]
        if "version" in fetch:
            default_store["branch"] = fetch["version"]
    if "registry" in normalized and "name" in normalized["registry"]:
        default_store["registry"] = normalized["registry"]["name"]

    stores[DEFAULT_STORE] = default_store
    for name, store in list(stores.items()):
        if name != DEFAULT_STORE:
            stores[name] = _merge(default_store, store)
    normalized["stores"] = stores
    return normalized


CONFIG = load_config()

DEFAULT_STORE_CONFIG = CONFIG["stores"][DEFAULT_STORE]
DEFAULT_BASE_URL = str(DEFAULT_STORE_CONFIG["base_url"])
DEFAULT_DATA_BRANCH = str(DEFAULT_STORE_CONFIG["branch"])
DEFAULT_DATA_WORKTREE = str(DEFAULT_STORE_CONFIG["worktree"])
DEFAULT_RECIPE_ROOT = str(DEFAULT_STORE_CONFIG["recipe_root"])
DEFAULT_SOURCE_CACHE = str(DEFAULT_STORE_CONFIG["source_cache"])
REGISTRY_NAME = str(DEFAULT_STORE_CONFIG["registry"])


@dataclass(frozen=True)
class StoreSettings:
    """Resolved settings for one generated data store."""

    name: str
    data: dict[str, Any]

    @property
    def repo(self) -> str | None:
        value = self.data.get("repo")
        return str(value) if value else None

    @property
    def base_url(self) -> str:
        return str(self.data["base_url"])

    @property
    def branch(self) -> str:
        return str(self.data["branch"])

    @property
    def worktree(self) -> str:
        return str(self.data["worktree"])

    @property
    def recipe_root(self) -> str:
        return str(self.data["recipe_root"])

    @property
    def source_cache(self) -> str:
        return str(self.data["source_cache"])

    @property
    def registry_name(self) -> str:
        return str(self.data["registry"])


@dataclass(frozen=True)
class Settings:
    """Resolved package settings loaded from TOML."""

    data: dict[str, Any]

    @classmethod
    def load(cls, path: str | Path | None = None) -> Settings:
        return cls(load_config(path))

    @property
    def default_store(self) -> str:
        return str(self.data.get("default_store", DEFAULT_STORE))

    @property
    def stores(self) -> dict[str, Any]:
        return dict(self.data["stores"])

    def store(self, name: str | None = None) -> StoreSettings:
        store_name = name or self.default_store
        try:
            data = self.stores[store_name]
        except KeyError as exc:
            known = ", ".join(sorted(self.stores))
            raise ValueError(f"Unknown data store {store_name!r}. Known stores: {known}") from exc
        return StoreSettings(store_name, dict(data))

    @property
    def data_branch(self) -> str:
        return self.store().branch

    @property
    def data_worktree(self) -> str:
        return self.store().worktree

    @property
    def recipe_root(self) -> str:
        return self.store().recipe_root

    @property
    def source_cache(self) -> str:
        return self.store().source_cache

    @property
    def registry_name(self) -> str:
        return self.store().registry_name

    @property
    def fetch_base_url(self) -> str:
        return self.store().base_url

    @property
    def fetch_version(self) -> str:
        return self.store().branch

    def data_store_config(
        self,
        *,
        store: str | None = None,
        branch: str | None = None,
        worktree: str | Path | None = None,
        recipe_root: str | Path | None = None,
        source_cache: str | Path | None = None,
    ) -> DataStoreConfig:
        store_settings = self.store(store)
        return DataStoreConfig(
            name=store_settings.name,
            repo=store_settings.repo,
            base_url=store_settings.base_url,
            branch=branch or store_settings.branch,
            worktree=Path(worktree or store_settings.worktree),
            recipe_root=Path(recipe_root or store_settings.recipe_root),
            source_cache=Path(source_cache or store_settings.source_cache),
            registry_name=store_settings.registry_name,
        )


@dataclass(frozen=True)
class DataStoreConfig:
    """Local git-backed generated data store settings."""

    name: str = DEFAULT_STORE
    repo: str | None = None
    base_url: str = DEFAULT_BASE_URL
    branch: str = DEFAULT_DATA_BRANCH
    worktree: Path = Path(DEFAULT_DATA_WORKTREE)
    recipe_root: Path = Path(DEFAULT_RECIPE_ROOT)
    source_cache: Path = Path(DEFAULT_SOURCE_CACHE)
    registry_name: str = REGISTRY_NAME

    @property
    def registry_path(self) -> Path:
        return self.worktree / self.registry_name


def configured_base_url(
    base_url: str | None = None,
    *,
    store: str | None = None,
    settings: Settings | None = None,
) -> str:
    """Return the configured data-store base URL with one trailing slash."""
    configured = (settings or Settings(CONFIG)).store(store).base_url
    base = base_url or os.environ.get(ENV_BASE_URL, configured)
    return base if base.endswith("/") else f"{base}/"


def configured_data_version(
    version: str | None = None,
    *,
    store: str | None = None,
    settings: Settings | None = None,
) -> str:
    """Return the configured generated-data branch or version."""
    configured = (settings or Settings(CONFIG)).store(store).branch
    return version or os.environ.get(ENV_DATA_VERSION, configured)


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
