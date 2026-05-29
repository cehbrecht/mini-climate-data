from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import urlopen

DEFAULT_BASE_URL = "https://raw.githubusercontent.com/macpingu/mini-climate-data/"
DEFAULT_VERSION = "data"
REGISTRY_NAME = "registry.json"


def registry_url(base_url: str | None = None, version: str | None = None) -> str:
    """Return the registry URL for a generated data branch or version."""
    version = version or os.environ.get("MINI_CLIMATE_DATA_VERSION", DEFAULT_VERSION)
    base = base_url or os.environ.get("MINI_CLIMATE_DATA_BASE_URL", DEFAULT_BASE_URL)
    if not base.endswith("/"):
        base = f"{base}/"
    return f"{base}{version}/{REGISTRY_NAME}"


def load_remote_registry(base_url: str | None = None, version: str | None = None) -> dict[str, str]:
    """Load registry.json from the configured generated data store."""
    with urlopen(registry_url(base_url, version)) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in data.items()
    ):
        raise ValueError("Remote registry must be a mapping of logical names to hashes")
    return data


def fetch(
    name: str,
    *,
    registry: dict[str, str] | None = None,
    base_url: str | None = None,
    version: str | None = None,
    path: str | Path | None = None,
) -> str:
    """Fetch a generated artifact by stable logical name."""
    try:
        import pooch
    except ImportError as exc:
        raise RuntimeError("Install mini-climate-data[fetch] to fetch data") from exc

    version = version or os.environ.get("MINI_CLIMATE_DATA_VERSION", DEFAULT_VERSION)
    base = base_url or os.environ.get("MINI_CLIMATE_DATA_BASE_URL", DEFAULT_BASE_URL)
    if not base.endswith("/"):
        base = f"{base}/"

    downloader = pooch.create(
        path=path or pooch.os_cache("mini-climate-data"),
        base_url=f"{base}{version}/",
        registry=registry if registry is not None else load_remote_registry(base, version),
    )
    return downloader.fetch(name)
