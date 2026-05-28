from __future__ import annotations

from pathlib import Path
from typing import Any

from mini_climate_data.recipes import Recipe
from mini_climate_data.reducers.base import Reducer
from mini_climate_data.reducers.helpers import (
    DimensionSubset,
    backend_options,
    parameters,
    require_matching_artifacts,
    resolve_input_paths,
    subset_spec,
    target_path,
)


class XarraySubsetReducer(Reducer):
    """Build NetCDF subsets with xarray."""

    name = "xarray_subset"

    def build(self, recipe: Recipe, artifact_root: Path) -> list[Path]:
        try:
            import xarray as xr
        except ImportError as exc:
            raise RuntimeError("Install mini-climate-data[netcdf] to use xarray_subset") from exc

        config = parameters(recipe)
        backend = backend_options(config, "xarray")
        input_paths = resolve_input_paths(
            recipe,
            config,
            reducer_name=self.name,
            cache_root=artifact_root / "_sources",
        )
        require_matching_artifacts(recipe, input_paths, reducer_name=self.name)

        written: list[Path] = []
        open_kwargs = backend.get("open_kwargs", {})
        write_kwargs = backend.get("to_netcdf_kwargs", {})
        spec = subset_spec(config)

        for input_path, artifact in zip(input_paths, recipe.artifacts, strict=True):
            target = target_path(artifact_root, artifact, config)

            with xr.open_dataset(input_path, **open_kwargs) as dataset:
                subset = _subset_dataset(dataset, spec.variables, spec.dimensions, spec.coordinates)
                _normalize_missing_value_encoding(subset)
                subset.to_netcdf(target, **write_kwargs)
            written.append(target)

        return written


def _subset_dataset(
    dataset: Any,
    variables: list[str],
    dimensions: list[DimensionSubset],
    coordinates: dict[str, Any],
) -> Any:
    subset = dataset[variables] if variables else dataset

    isel = _isel_indexers(dimensions)
    if isel:
        subset = subset.isel(isel)

    if coordinates:
        subset = subset.sel(coordinates)

    return subset


def _isel_indexers(dimensions: list[DimensionSubset]) -> dict[str, Any]:
    indexers: dict[str, Any] = {}
    for dimension in dimensions:
        if dimension.index is not None:
            indexers[dimension.name] = int(dimension.index)
        else:
            indexers[dimension.name] = slice(dimension.start, dimension.stop, dimension.stride)
    return indexers


def _normalize_missing_value_encoding(dataset: Any) -> None:
    variables = getattr(dataset, "variables", {})
    if not hasattr(variables, "values"):
        return

    for variable in variables.values():
        encoding = getattr(variable, "encoding", {})
        if "_FillValue" in encoding and "missing_value" in encoding:
            if encoding["_FillValue"] != encoding["missing_value"]:
                encoding.pop("missing_value")


xarray_subset = XarraySubsetReducer()
