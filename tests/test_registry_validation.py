from __future__ import annotations

from pathlib import Path
from shutil import copyfile

from mini_climate_data.recipes import update_recipe_artifact_metadata
from mini_climate_data.reducers import build_recipe
from mini_climate_data.registry import build_registry
from mini_climate_data.validation import validate_artifacts


def test_reduce_validate_and_build_registry(tmp_path: Path) -> None:
    recipe = Path("recipes/example/hello-climate.yml")
    artifact_root = tmp_path / "artifacts"

    build_recipe(recipe, artifact_root)
    checked = validate_artifacts(recipe, artifact_root)
    registry = build_registry("recipes/example", artifact_root)

    assert checked == [artifact_root / "example/hello-climate.txt"]
    assert registry["example/hello-climate.txt"].startswith("sha256:")


def test_update_recipe_artifact_metadata(tmp_path: Path) -> None:
    recipe = tmp_path / "hello-climate.yml"
    artifact_root = tmp_path / "artifacts"
    copyfile("recipes/example/hello-climate.yml", recipe)

    build_recipe(recipe, artifact_root)
    updated = update_recipe_artifact_metadata(recipe, artifact_root)

    artifact = updated.artifacts[0]
    assert artifact["size"] == (artifact_root / artifact["path"]).stat().st_size
    assert artifact["checksum"].startswith("sha256:")
    assert "checksum:" in recipe.read_text(encoding="utf-8")
