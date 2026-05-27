from __future__ import annotations

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


REDUCERS: dict[str, Reducer] = {
    "write_text": write_text,
}
