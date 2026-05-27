from __future__ import annotations

import os
from pathlib import Path


DEFAULT_BASE_URL = "https://raw.githubusercontent.com/macpingu/mini-climate-data/"
DEFAULT_VERSION = "data"


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
        raise RuntimeError("Install pooch or mini-climate-data with its runtime dependencies to fetch data") from exc

    version = version or os.environ.get("MINI_CLIMATE_DATA_VERSION", DEFAULT_VERSION)
    base = base_url or os.environ.get("MINI_CLIMATE_DATA_BASE_URL", DEFAULT_BASE_URL)
    if not base.endswith("/"):
        base = f"{base}/"

    downloader = pooch.create(
        path=path or pooch.os_cache("mini-climate-data"),
        base_url=f"{base}{version}/",
        registry=registry or {},
    )
    return downloader.fetch(name)
