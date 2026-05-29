from __future__ import annotations

import subprocess
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


class NcksSubsetReducer(Reducer):
    """Build NetCDF subsets with NCO's ncks command."""

    name = "ncks_subset"

    def build(self, recipe: Recipe, artifact_root: Path) -> list[Path]:
        config = parameters(recipe)
        backend = backend_options(config, "nco")
        input_paths = resolve_input_paths(
            recipe,
            config,
            reducer_name=self.name,
            cache_root=Path(config.get("source_cache", artifact_root / "_sources")),
        )
        require_matching_artifacts(recipe, input_paths, reducer_name=self.name)

        spec = subset_spec(config)
        if spec.coordinates:
            raise ValueError("ncks_subset does not support coordinate label selections")

        written: list[Path] = []
        for input_path, artifact in zip(input_paths, recipe.artifacts, strict=True):
            target = target_path(artifact_root, artifact, config)
            _run_ncks(input_path, target, spec.variables, spec.dimensions, backend)
            written.append(target)

        return written


def _run_ncks(
    input_path: Path,
    output_path: Path,
    variables: list[str],
    dimensions: list[DimensionSubset],
    backend: dict[str, Any],
) -> None:
    command = [str(backend.get("command", backend.get("ncks_command", "ncks")))]

    if backend.get("netcdf4_classic", False):
        command.append("-7")

    if "compression_level" in backend:
        level = int(backend["compression_level"])
        if not 0 <= level <= 9:
            raise ValueError("ncks_subset compression_level must be between 0 and 9")
        command.extend(["-L", str(level)])

    for dimension in dimensions:
        command.extend(["-d", _format_dimension(dimension)])

    if variables:
        command.extend(["--variable", ",".join(variables)])

    command.extend([str(input_path), str(output_path)])
    subprocess.run(command, check=True)


def _format_dimension(dimension: DimensionSubset) -> str:
    if dimension.index is not None:
        return f"{dimension.name},{dimension.index}"

    values = [dimension.start, dimension.stop, dimension.stride]
    while values and values[-1] is None:
        values.pop()
    formatted_values = [str(value) if value is not None else "" for value in values]
    return ",".join([dimension.name, *formatted_values])


ncks_subset = NcksSubsetReducer()
