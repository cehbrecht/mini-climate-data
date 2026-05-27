from __future__ import annotations

from importlib import resources
from pathlib import Path


PACKAGE = "mini_climate_data"


def bundled_recipes_dir() -> Path:
    """Return a filesystem path to bundled recipe files."""
    return Path(str(resources.files(PACKAGE) / "_recipes"))


def repo_root(start: Path | None = None) -> Path:
    """Find the repository root from a path inside the working tree."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "recipes").exists():
            return candidate
    return current
