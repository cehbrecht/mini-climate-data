from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from mini_climate_data.recipes import Recipe, iter_recipes


REGISTRY_NAME = "registry.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_registry(
    recipe_root: str | Path = "recipes",
    artifact_root: str | Path = "artifacts",
    output: str | Path | None = None,
) -> dict[str, str]:
    artifact_base = Path(artifact_root)
    registry: dict[str, str] = {}

    for recipe in iter_recipes(recipe_root):
        for artifact in recipe.artifacts:
            artifact_path = artifact_base / artifact["path"]
            if not artifact_path.exists():
                raise FileNotFoundError(f"Missing artifact for {recipe.name}: {artifact_path}")
            registry[artifact["logical_name"]] = f"sha256:{sha256(artifact_path)}"

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return registry


def load_registry(path: str | Path) -> dict[str, str]:
    registry_path = Path(path)
    if registry_path.suffix in {".yml", ".yaml"}:
        data: Any = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    else:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ValueError(f"Registry must be a mapping of logical names to hashes: {registry_path}")
    return data
