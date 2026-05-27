from __future__ import annotations

from pathlib import Path

from mini_climate_data.recipes import Recipe, load_recipe
from mini_climate_data.reducers.base import Reducer
from mini_climate_data.reducers.nco import ncks_subset
from mini_climate_data.reducers.synthetic import write_text
from mini_climate_data.reducers.xarray import xarray_subset


def build_recipe(
    recipe: str | Path | Recipe,
    artifact_root: str | Path = "artifacts",
) -> list[Path]:
    """Build artifacts for a recipe using a packaged reducer."""
    loaded = recipe if isinstance(recipe, Recipe) else load_recipe(recipe)
    reducer_name = loaded.data["reducer"]["name"]
    try:
        reducer = REDUCERS[reducer_name]
    except KeyError as exc:
        known = ", ".join(sorted(REDUCERS))
        raise ValueError(f"Unknown reducer {reducer_name!r}. Known reducers: {known}") from exc
    return reducer(loaded, Path(artifact_root))


REDUCERS: dict[str, Reducer] = {
    "ncks_subset": ncks_subset,
    "write_text": write_text,
    "xarray_subset": xarray_subset,
}
