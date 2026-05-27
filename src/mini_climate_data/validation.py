from __future__ import annotations

from pathlib import Path

from mini_climate_data.recipes import Recipe, load_recipe
from mini_climate_data.registry import sha256


def validate_artifacts(
    recipe: str | Path | Recipe,
    artifact_root: str | Path = "artifacts",
) -> list[Path]:
    loaded = recipe if isinstance(recipe, Recipe) else load_recipe(recipe)
    artifact_base = Path(artifact_root)
    checked: list[Path] = []

    for artifact in loaded.artifacts:
        path = artifact_base / artifact["path"]
        if not path.exists():
            raise FileNotFoundError(f"Missing artifact: {path}")

        size = path.stat().st_size
        max_size = int(artifact["max_size"])
        if size > max_size:
            raise ValueError(f"{path} is {size} bytes, exceeding recipe limit of {max_size} bytes")

        checksum = artifact.get("checksum")
        if checksum and checksum != f"sha256:{sha256(path)}":
            raise ValueError(f"{path} checksum does not match recipe")

        if loaded.data["validation"].get("openable", False):
            _validate_openable(path, loaded.data["validation"].get("engine", "bytes"))

        checked.append(path)

    return checked


def _validate_openable(path: Path, engine: str) -> None:
    if engine == "bytes":
        with path.open("rb") as handle:
            handle.read(1)
        return

    if engine == "netcdf":
        try:
            import xarray as xr
        except ImportError as exc:
            raise RuntimeError(
                "Install mini-climate-data[netcdf] to validate NetCDF artifacts"
            ) from exc
        with xr.open_dataset(path):
            return

    if engine == "zarr":
        try:
            import xarray as xr
        except ImportError as exc:
            raise RuntimeError(
                "Install mini-climate-data[netcdf] to validate Zarr artifacts"
            ) from exc
        xr.open_zarr(path)
        return

    raise ValueError(f"Unsupported validation engine: {engine}")
