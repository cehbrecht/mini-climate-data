from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree

from mini_climate_data.recipes import iter_recipes
from mini_climate_data.reducers import build_recipe
from mini_climate_data.registry import REGISTRY_NAME, build_registry
from mini_climate_data.validation import validate_artifacts

DEFAULT_DATA_BRANCH = "data"
DEFAULT_DATA_WORKTREE = ".worktrees/data"


@dataclass(frozen=True)
class DataStoreConfig:
    """Local git-backed generated data store settings."""

    branch: str = DEFAULT_DATA_BRANCH
    worktree: Path = Path(DEFAULT_DATA_WORKTREE)
    recipe_root: Path = Path("recipes")

    @property
    def registry_path(self) -> Path:
        return self.worktree / REGISTRY_NAME


def run_git(args: list[str], cwd: str | Path = ".") -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def init_data_worktree(config: DataStoreConfig, *, orphan: bool = False) -> Path:
    """Create the local worktree for a generated data branch."""
    if config.worktree.exists():
        return config.worktree

    config.worktree.parent.mkdir(parents=True, exist_ok=True)
    if orphan:
        run_git(["worktree", "add", "--orphan", "-b", config.branch, str(config.worktree)])
    else:
        run_git(["worktree", "add", str(config.worktree), config.branch])
    return config.worktree


def build_data_recipe(recipe: str | Path, config: DataStoreConfig) -> list[Path]:
    """Build one recipe into the data worktree."""
    return build_recipe(recipe, config.worktree)


def build_all_data(config: DataStoreConfig) -> list[Path]:
    """Build all recipes into the data worktree."""
    built: list[Path] = []
    for recipe in iter_recipes(config.recipe_root):
        built.extend(build_recipe(recipe, config.worktree))
    return built


def validate_data(config: DataStoreConfig) -> list[Path]:
    """Validate all generated artifacts declared below the configured recipe root."""
    checked: list[Path] = []
    for recipe in iter_recipes(config.recipe_root):
        checked.extend(validate_artifacts(recipe, config.worktree))
    return checked


def write_data_registry(config: DataStoreConfig) -> dict[str, str]:
    """Write registry.json into the data worktree."""
    return build_registry(config.recipe_root, config.worktree, config.registry_path)


def clean_data(config: DataStoreConfig) -> list[Path]:
    """Remove declared generated artifacts and registry.json from the data worktree."""
    removed: list[Path] = []
    for recipe in iter_recipes(config.recipe_root):
        for artifact in recipe.artifacts:
            path = config.worktree / artifact["path"]
            if path.is_dir():
                rmtree(path)
                removed.append(path)
            elif path.exists():
                path.unlink()
                removed.append(path)

    if config.registry_path.exists():
        config.registry_path.unlink()
        removed.append(config.registry_path)

    _prune_empty_dirs(config.worktree)
    return removed


def _prune_empty_dirs(root: Path) -> None:
    if not root.exists():
        return
    for path in sorted((item for item in root.rglob("*") if item.is_dir()), reverse=True):
        try:
            path.rmdir()
        except OSError:
            pass


def data_status(config: DataStoreConfig) -> str:
    """Return porcelain status for the data worktree."""
    return run_git(["status", "--short"], cwd=config.worktree)


def publish_data(config: DataStoreConfig, *, message: str, remote: str = "origin") -> None:
    """Commit and push generated data from the data worktree."""
    run_git(["add", "."], cwd=config.worktree)
    if data_status(config):
        run_git(["commit", "-m", message], cwd=config.worktree)
    run_git(["push", remote, f"HEAD:{config.branch}"], cwd=config.worktree)
