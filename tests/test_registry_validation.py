from __future__ import annotations

from pathlib import Path

from mini_climate_data.reducers import build_recipe
from mini_climate_data.registry import build_registry
from mini_climate_data.validation import validate_artifacts


def test_reduce_validate_and_build_registry(tmp_path: Path) -> None:
    recipe = Path("recipes/example/hello-climate.yml")
    artifact_root = tmp_path / "artifacts"

    build_recipe(recipe, artifact_root)
    checked = validate_artifacts(recipe, artifact_root)
    registry = build_registry("recipes", artifact_root)

    assert checked == [artifact_root / "example/hello-climate.txt"]
    assert registry["example/hello-climate.txt"].startswith("sha256:")
