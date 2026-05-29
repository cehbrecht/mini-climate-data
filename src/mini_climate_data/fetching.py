from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen

from mini_climate_data.config import (
    CONFIG,
    Settings,
    configured_base_url,
    configured_data_version,
)


def registry_url(
    base_url: str | None = None,
    version: str | None = None,
    *,
    store: str | None = None,
    settings: Settings | None = None,
) -> str:
    """Return the registry URL for a generated data branch or version."""
    resolved = settings or Settings(CONFIG)
    registry_name = resolved.store(store).registry_name
    return (
        f"{configured_base_url(base_url, store=store, settings=resolved)}"
        f"{configured_data_version(version, store=store, settings=resolved)}/{registry_name}"
    )


def load_remote_registry(
    base_url: str | None = None,
    version: str | None = None,
    *,
    store: str | None = None,
    settings: Settings | None = None,
) -> dict[str, str]:
    """Load registry.json from the configured generated data store."""
    with urlopen(registry_url(base_url, version, store=store, settings=settings)) as response:
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
    store: str | None = None,
    path: str | Path | None = None,
) -> str:
    """Fetch a generated artifact by stable logical name."""
    try:
        import pooch
    except ImportError as exc:
        raise RuntimeError("Install mini-climate-data[fetch] to fetch data") from exc

    settings = Settings(CONFIG)
    version = configured_data_version(version, store=store, settings=settings)
    base = configured_base_url(base_url, store=store, settings=settings)

    downloader = pooch.create(
        path=path or pooch.os_cache("mini-climate-data"),
        base_url=f"{base}{version}/",
        registry=registry
        if registry is not None
        else load_remote_registry(base, version, store=store, settings=settings),
    )
    return downloader.fetch(name)
