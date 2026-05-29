from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from mini_climate_data.cli import main
from mini_climate_data.data_store import (
    DEFAULT_DATA_BRANCH,
    DEFAULT_DATA_WORKTREE,
    DataStoreConfig,
    build_all_data,
    clean_data,
    validate_data,
    write_data_registry,
)


def test_data_store_defaults() -> None:
    config = DataStoreConfig()

    assert config.branch == DEFAULT_DATA_BRANCH
    assert config.worktree == Path(DEFAULT_DATA_WORKTREE)
    assert config.registry_path == Path(DEFAULT_DATA_WORKTREE) / "registry.json"


def test_build_validate_and_registry_for_data_worktree(tmp_path: Path) -> None:
    config = DataStoreConfig(
        branch="data-test",
        worktree=tmp_path / "data",
        recipe_root=Path("recipes/example"),
    )

    built = build_all_data(config)
    checked = validate_data(config)
    registry = write_data_registry(config)

    assert built == [tmp_path / "data/example/hello-climate.txt"]
    assert checked == [tmp_path / "data/example/hello-climate.txt"]
    assert registry["example/hello-climate.txt"].startswith("sha256:")
    assert (tmp_path / "data/registry.json").exists()

    removed = clean_data(config)

    assert tmp_path / "data/example/hello-climate.txt" in removed
    assert tmp_path / "data/registry.json" in removed
    assert not (tmp_path / "data/example/hello-climate.txt").exists()


def test_data_cli_build_validate_and_registry(tmp_path: Path) -> None:
    runner = CliRunner()
    worktree = tmp_path / "data"

    build_result = runner.invoke(
        main,
        [
            "data",
            "build-all",
            "--branch",
            "data-test",
            "--worktree",
            str(worktree),
            "--recipes",
            "recipes/example",
        ],
    )
    validate_result = runner.invoke(
        main,
        [
            "data",
            "validate",
            "--branch",
            "data-test",
            "--worktree",
            str(worktree),
            "--recipes",
            "recipes/example",
        ],
    )
    registry_result = runner.invoke(
        main,
        [
            "data",
            "registry",
            "--branch",
            "data-test",
            "--worktree",
            str(worktree),
            "--recipes",
            "recipes/example",
        ],
    )

    assert build_result.exit_code == 0
    assert "wrote" in build_result.output
    assert validate_result.exit_code == 0
    assert "ok" in validate_result.output
    assert registry_result.exit_code == 0
    assert "registry.json" in registry_result.output
