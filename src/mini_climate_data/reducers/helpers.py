from __future__ import annotations

import glob
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from mini_climate_data.recipes import Recipe
from mini_climate_data.sources import resolve_intake_url


@dataclass(frozen=True)
class DimensionSubset:
    """Reducer-neutral subset instructions for one dimension."""

    name: str
    index: int | None = None
    start: Any = None
    stop: Any = None
    stride: int | None = None


@dataclass(frozen=True)
class SubsetSpec:
    """Reducer-neutral description of a common NetCDF subset."""

    variables: list[str]
    dimensions: list[DimensionSubset]
    coordinates: dict[str, Any]


def parameters(recipe: Recipe) -> dict[str, Any]:
    return recipe.data.get("reducer", {}).get("parameters", {})


def backend_options(config: dict[str, Any], backend_name: str) -> dict[str, Any]:
    options = config.get("backend_options", {})
    if not isinstance(options, dict):
        raise ValueError("reducer.parameters.backend_options must be a mapping")
    backend_specific = options.get(backend_name, {})
    if backend_specific:
        return dict(backend_specific)
    return dict(options)


def resolve_input_paths(
    recipe: Recipe,
    config: dict[str, Any],
    *,
    reducer_name: str,
    cache_root: Path | None = None,
) -> list[Path]:
    if "input_glob" in config:
        paths = sorted(Path(path) for path in glob.glob(str(config["input_glob"])))
    else:
        value = config.get("input") or _source_url(recipe)
        if not value:
            raise ValueError(f"{reducer_name} requires reducer.parameters.input or source.url")
        paths = [_local_input_path(str(value), cache_root, reducer_name=reducer_name)]

    if not paths:
        raise FileNotFoundError(f"{reducer_name} input_glob did not match any files")

    missing = [path for path in paths if not path.is_file()]
    if missing:
        formatted = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"{reducer_name} input file(s) do not exist: {formatted}")

    number = config.get("number")
    if number is not None and int(number) > 0:
        paths = paths[: int(number)]

    return paths


def _source_url(recipe: Recipe) -> str | None:
    source = recipe.data["source"]
    if source["kind"] == "intake":
        return resolve_intake_url(source)
    return source.get("url")


def _local_input_path(value: str, cache_root: Path | None, *, reducer_name: str) -> Path:
    if is_remote_url(value):
        if cache_root is None:
            raise ValueError(f"{reducer_name} requires a cache root to download remote inputs")
        return download_source(value, cache_root)
    return Path(strip_file_url(value))


def is_remote_url(value: str) -> bool:
    scheme = urlparse(value).scheme
    return scheme in {"http", "https"}


def download_source(url: str, cache_root: Path) -> Path:
    """Download a remote original file into a local source cache."""
    try:
        import pooch
    except ImportError as exc:
        raise RuntimeError("Install mini-climate-data[fetch] to cache remote sources") from exc

    cache_root.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(url)
    filename = Path(parsed.path).name or "source"
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return Path(
        pooch.retrieve(
            url,
            known_hash=None,
            fname=f"{digest}-{filename}",
            path=cache_root,
            progressbar=True,
        )
    )


def strip_file_url(value: str) -> str:
    return value.removeprefix("file://")


def require_matching_artifacts(
    recipe: Recipe,
    input_paths: list[Path],
    *,
    reducer_name: str,
) -> None:
    if len(input_paths) != len(recipe.artifacts):
        raise ValueError(
            f"{reducer_name} needs one declared artifact per input file; "
            f"found {len(input_paths)} input(s) and {len(recipe.artifacts)} artifact(s)"
        )


def target_path(artifact_root: Path, artifact: dict[str, Any], config: dict[str, Any]) -> Path:
    target = artifact_root / artifact["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and config.get("overwrite", True):
        target.unlink()
    return target


def subset_spec(config: dict[str, Any]) -> SubsetSpec:
    return SubsetSpec(
        variables=_variables(config),
        dimensions=_dimensions(config),
        coordinates=dict(config.get("coordinates", config.get("sel", {}))),
    )


def _variables(config: dict[str, Any]) -> list[str]:
    if "variables" in config:
        variables = config["variables"]
        if isinstance(variables, str):
            return [variables]
        return [str(variable) for variable in variables]

    if "variable" in config:
        return [str(config["variable"])]

    return []


def _dimensions(config: dict[str, Any]) -> list[DimensionSubset]:
    if "dimensions" in config:
        dimensions = config["dimensions"]
        if not isinstance(dimensions, dict):
            raise ValueError("reducer.parameters.dimensions must be a mapping")
        return [_dimension_from_config(name, value) for name, value in dimensions.items()]

    if "isel" in config:
        return [_dimension_from_legacy_isel(name, value) for name, value in config["isel"].items()]

    if "selectors" in config:
        return [_dimension_from_nco_selector(selector) for selector in config["selectors"]]

    return []


def _dimension_from_config(name: str, value: Any) -> DimensionSubset:
    if isinstance(value, int):
        return DimensionSubset(name=name, index=value)
    if value is None:
        return DimensionSubset(name=name)
    if not isinstance(value, dict):
        raise ValueError(f"Dimension {name!r} must be an integer, null, or mapping")
    return DimensionSubset(
        name=name,
        index=value.get("index"),
        start=value.get("start"),
        stop=value.get("stop"),
        stride=value.get("stride"),
    )


def _dimension_from_legacy_isel(name: str, value: Any) -> DimensionSubset:
    if isinstance(value, dict):
        return DimensionSubset(
            name=name,
            start=value.get("start"),
            stop=value.get("stop"),
            stride=value.get("stride"),
        )
    return DimensionSubset(name=name, index=int(value))


def _dimension_from_nco_selector(selector: dict[str, Any]) -> DimensionSubset:
    return DimensionSubset(
        name=selector["dimension"],
        start=selector.get("start"),
        stop=selector.get("stop"),
        stride=selector.get("stride"),
    )
