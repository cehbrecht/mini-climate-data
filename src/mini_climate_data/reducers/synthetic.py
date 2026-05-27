from __future__ import annotations

from pathlib import Path
from typing import Any

from mini_climate_data.recipes import Recipe


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
