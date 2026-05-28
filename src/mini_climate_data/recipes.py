from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from mini_climate_data._paths import PACKAGE, bundled_recipes_dir

SCHEMA_RESOURCE = "recipe.schema.json"


@dataclass(frozen=True)
class Recipe:
    """A validated recipe and the path it was loaded from."""

    path: Path
    data: dict[str, Any]

    @property
    def name(self) -> str:
        return str(self.data["name"])

    @property
    def artifacts(self) -> list[dict[str, Any]]:
        return list(self.data.get("artifacts", []))


def recipe_schema() -> dict[str, Any]:
    schema_path = resources.files(PACKAGE) / SCHEMA_RESOURCE
    return yaml.safe_load(schema_path.read_text(encoding="utf-8"))


def load_recipe(path: str | Path) -> Recipe:
    recipe_path = Path(path)
    data = yaml.safe_load(recipe_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Recipe must contain a mapping: {recipe_path}")
    validate_recipe_data(data)
    return Recipe(recipe_path, data)


def validate_recipe(path: str | Path) -> Recipe:
    return load_recipe(path)


def update_recipe_artifact_metadata(
    recipe: str | Path | Recipe,
    artifact_root: str | Path = "artifacts",
) -> Recipe:
    """Write artifact size and checksum fields from built artifacts back to a recipe."""
    loaded = recipe if isinstance(recipe, Recipe) else load_recipe(recipe)
    artifact_base = Path(artifact_root)

    from mini_climate_data.registry import sha256

    for artifact in loaded.artifacts:
        artifact_path = artifact_base / artifact["path"]
        if not artifact_path.exists():
            raise FileNotFoundError(f"Missing artifact for {loaded.name}: {artifact_path}")
        artifact["size"] = artifact_path.stat().st_size
        artifact["checksum"] = f"sha256:{sha256(artifact_path)}"

    loaded.path.write_text(
        yaml.safe_dump(loaded.data, sort_keys=False),
        encoding="utf-8",
    )
    return load_recipe(loaded.path)


def validate_recipe_data(data: dict[str, Any]) -> None:
    jsonschema.validate(instance=data, schema=recipe_schema())


def iter_recipes(root: str | Path | None = None) -> Iterable[Recipe]:
    recipe_root = Path(root) if root else bundled_recipes_dir()
    for path in sorted(recipe_root.rglob("*.yml")) + sorted(recipe_root.rglob("*.yaml")):
        yield load_recipe(path)
