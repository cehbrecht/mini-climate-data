from __future__ import annotations

import glob
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mini_climate_data.recipes import Recipe, load_recipe

Reducer = Callable[[Recipe, Path], list[Path]]


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


def write_text(recipe: Recipe, artifact_root: Path) -> list[Path]:
    """Write tiny synthetic text artifacts for workflow smoke tests."""
    parameters: dict[str, Any] = recipe.data.get("reducer", {}).get("parameters", {})
    message = parameters.get("message", "")
    written: list[Path] = []

    for artifact in recipe.artifacts:
        target = artifact_root / artifact["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(message, encoding="utf-8")
        written.append(target)

    return written


def ncks_subset(recipe: Recipe, artifact_root: Path) -> list[Path]:
    """Build NetCDF subsets with NCO's ncks command.

    This reducer intentionally keeps dataset-specific choices in the recipe:
    inputs, variables, dimension selectors, compression, and format conversion.
    """
    parameters: dict[str, Any] = recipe.data.get("reducer", {}).get("parameters", {})
    input_paths = _resolve_input_paths(recipe, parameters)

    if len(input_paths) != len(recipe.artifacts):
        raise ValueError(
            f"ncks_subset needs one declared artifact per input file; "
            f"found {len(input_paths)} input(s) and {len(recipe.artifacts)} artifact(s)"
        )

    written: list[Path] = []
    for input_path, artifact in zip(input_paths, recipe.artifacts, strict=True):
        target = artifact_root / artifact["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and parameters.get("overwrite", True):
            target.unlink()

        _run_ncks(input_path, target, parameters)
        written.append(target)

    return written


def _resolve_input_paths(recipe: Recipe, parameters: dict[str, Any]) -> list[Path]:
    if "input_glob" in parameters:
        paths = sorted(Path(path) for path in glob.glob(str(parameters["input_glob"])))
    else:
        value = parameters.get("input") or recipe.data["source"].get("url")
        if not value:
            raise ValueError("ncks_subset requires reducer.parameters.input or source.url")
        paths = [Path(_strip_file_url(str(value)))]

    if not paths:
        raise FileNotFoundError("ncks_subset input_glob did not match any files")

    missing = [path for path in paths if not path.is_file()]
    if missing:
        formatted = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"ncks_subset input file(s) do not exist: {formatted}")

    number = parameters.get("number")
    if number is not None and int(number) > 0:
        paths = paths[: int(number)]

    return paths


def _strip_file_url(value: str) -> str:
    return value.removeprefix("file://")


def _run_ncks(input_path: Path, output_path: Path, parameters: dict[str, Any]) -> None:
    command = [str(parameters.get("ncks_command", "ncks"))]

    if parameters.get("netcdf4_classic", False):
        command.append("-7")

    if "compression_level" in parameters:
        level = int(parameters["compression_level"])
        if not 0 <= level <= 9:
            raise ValueError("ncks_subset compression_level must be between 0 and 9")
        command.extend(["-L", str(level)])

    for selector in parameters.get("selectors", []):
        command.extend(["-d", _format_selector(selector)])

    variables = _variables(parameters)
    if variables:
        command.extend(["--variable", ",".join(variables)])

    command.extend([str(input_path), str(output_path)])
    subprocess.run(command, check=True)


def _variables(parameters: dict[str, Any]) -> list[str]:
    if "variables" in parameters:
        variables = parameters["variables"]
        if isinstance(variables, str):
            return [variables]
        return [str(variable) for variable in variables]

    if "variable" in parameters:
        return [str(parameters["variable"])]

    return []


def _format_selector(selector: dict[str, Any]) -> str:
    dimension = selector["dimension"]
    values = [
        selector.get("start", ""),
        selector.get("stop", ""),
        selector.get("stride", ""),
    ]
    while values and values[-1] == "":
        values.pop()
    return ",".join([str(dimension), *(str(value) for value in values)])


REDUCERS: dict[str, Reducer] = {
    "ncks_subset": ncks_subset,
    "write_text": write_text,
}
