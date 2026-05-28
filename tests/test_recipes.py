from __future__ import annotations

from pathlib import Path

from mini_climate_data.recipes import iter_recipes, load_recipe


def test_example_recipe_is_valid() -> None:
    recipe = load_recipe(Path("recipes/example/hello-climate.yml"))

    assert recipe.name == "example/hello-climate"
    assert recipe.artifacts[0]["logical_name"] == "example/hello-climate.txt"


def test_cica_atlas_era5_recipe_is_valid() -> None:
    recipe = load_recipe(Path("recipes/c3s-cica-atlas/era5-psl.yml"))

    assert recipe.name == "c3s-cica-atlas/era5-psl"
    assert recipe.data["source"]["entry"] == "c3s-cica-atlas"
    assert recipe.data["source"]["ds_id"] == "c3s-cica-atlas.psl.ERA5.mon.v25"
    assert recipe.artifacts[0]["logical_name"].endswith("psl_ERA5_mon_194001-202512_v025-small.nc")


def test_iter_recipes_finds_example_recipe() -> None:
    names = {recipe.name for recipe in iter_recipes("recipes")}

    assert "example/hello-climate" in names
    assert "c3s-cica-atlas/era5-psl" in names
