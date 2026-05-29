from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_URL = "https://raw.githubusercontent.com/macpingu/mini-climate-data/"
DEFAULT_DATA_BRANCH = "data"
DEFAULT_DATA_WORKTREE = ".worktrees/data"
DEFAULT_RECIPE_ROOT = "recipes"
DEFAULT_SOURCE_CACHE = ".cache/mini-climate-data/sources"

ENV_BASE_URL = "MINI_CLIMATE_DATA_BASE_URL"
ENV_DATA_VERSION = "MINI_CLIMATE_DATA_VERSION"

REGISTRY_NAME = "registry.json"


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
    return version or os.environ.get(ENV_DATA_VERSION, DEFAULT_DATA_BRANCH)


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
