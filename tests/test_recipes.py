from __future__ import annotations

from pathlib import Path

from mini_climate_data.recipes import iter_recipes, load_recipe


def test_example_recipe_is_valid() -> None:
    recipe = load_recipe(Path("recipes/example/hello-climate.yml"))

    assert recipe.name == "example/hello-climate"
    assert recipe.artifacts[0]["logical_name"] == "example/hello-climate.txt"


def test_iter_recipes_finds_example_recipe() -> None:
    names = {recipe.name for recipe in iter_recipes("recipes")}

    assert "example/hello-climate" in names
