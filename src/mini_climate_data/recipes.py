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


def validate_recipe_data(data: dict[str, Any]) -> None:
    jsonschema.validate(instance=data, schema=recipe_schema())


def iter_recipes(root: str | Path | None = None) -> Iterable[Recipe]:
    recipe_root = Path(root) if root else bundled_recipes_dir()
    for path in sorted(recipe_root.rglob("*.yml")) + sorted(recipe_root.rglob("*.yaml")):
        yield load_recipe(path)
