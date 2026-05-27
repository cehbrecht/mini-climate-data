from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from mini_climate_data.recipes import Recipe


class Reducer(ABC):
    """Base class for all packaged artifact reducers."""

    name: str

    def __call__(self, recipe: Recipe, artifact_root: Path) -> list[Path]:
        return self.build(recipe, artifact_root)

    @abstractmethod
    def build(self, recipe: Recipe, artifact_root: Path) -> list[Path]:
        """Build artifacts for a validated recipe."""
