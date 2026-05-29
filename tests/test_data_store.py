from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from git import Repo

from mini_climate_data.cli import main
from mini_climate_data.config import (
    DEFAULT_DATA_BRANCH,
    DEFAULT_DATA_WORKTREE,
    DEFAULT_SOURCE_CACHE,
    REGISTRY_NAME,
    DataStoreConfig,
)
from mini_climate_data.data_store import (
    build_all_data,
    build_recipe_with_source_cache,
    clean_data,
    init_data_worktree,
    validate_data,
    write_data_registry,
)
from mini_climate_data.recipes import Recipe


def test_data_store_defaults() -> None:
    config = DataStoreConfig()

    assert config.branch == DEFAULT_DATA_BRANCH
    assert config.worktree == Path(DEFAULT_DATA_WORKTREE)
    assert config.source_cache == Path(DEFAULT_SOURCE_CACHE)
    assert config.registry_path == Path(DEFAULT_DATA_WORKTREE) / REGISTRY_NAME


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


def test_init_data_worktree_uses_gitpython(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    repo = Repo.init(source)
    with repo.config_writer() as config:
        config.set_value("user", "email", "test@example.test")
        config.set_value("user", "name", "Test User")
    (source / "README.md").write_text("source\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")
    repo.create_head("data")
    monkeypatch.chdir(source)

    worktree = init_data_worktree(
        DataStoreConfig(branch="data", worktree=tmp_path / "data-worktree")
    )

    assert worktree == tmp_path / "data-worktree"
    assert Repo(worktree).active_branch.name == "data"


def test_init_external_data_store_clones_repo(tmp_path: Path) -> None:
    remote = tmp_path / "remote"
    remote.mkdir()
    repo = Repo.init(remote)
    with repo.config_writer() as config:
        config.set_value("user", "email", "test@example.test")
        config.set_value("user", "name", "Test User")
    (remote / "README.md").write_text("external data\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")
    repo.create_head("data")

    worktree = tmp_path / "external-data"
    initialized = init_data_worktree(
        DataStoreConfig(
            name="external",
            repo=str(remote),
            branch="data",
            worktree=worktree,
        )
    )

    assert initialized == worktree
    assert Repo(worktree).active_branch.name == "data"
    assert (worktree / "README.md").read_text(encoding="utf-8") == "external data\n"


def test_data_build_injects_source_cache(tmp_path: Path, monkeypatch) -> None:
    seen_source_cache: list[str] = []
    recipe = Recipe(
        path=tmp_path / "recipe.yml",
        data={
            "name": "example/cache",
            "source": {
                "kind": "direct_url",
                "description": "Source",
                "url": "file:///tmp/source.nc",
            },
            "reducer": {"name": "xarray_subset", "parameters": {"variable": "tas"}},
            "artifacts": [{"path": "example/cache.nc", "logical_name": "example/cache.nc"}],
            "validation": {"openable": False},
        },
    )
    config = DataStoreConfig(
        branch="data-test",
        worktree=tmp_path / "data",
        source_cache=tmp_path / "sources",
    )

    def fake_build_recipe(patched: Recipe, artifact_root: Path) -> list[Path]:
        seen_source_cache.append(patched.data["reducer"]["parameters"]["source_cache"])
        return [artifact_root / "example/cache.nc"]

    monkeypatch.setattr("mini_climate_data.data_store.build_recipe", fake_build_recipe)

    assert build_recipe_with_source_cache(recipe, config) == [tmp_path / "data/example/cache.nc"]
    assert seen_source_cache == [str(tmp_path / "sources")]


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


def test_data_cli_uses_config_file_defaults(tmp_path: Path) -> None:
    runner = CliRunner()
    worktree = tmp_path / "configured-data"
    source_cache = tmp_path / "configured-sources"
    config_path = tmp_path / "mcd.toml"
    config_path.write_text(
        f"""
[data_store]
branch = "data-from-config"
worktree = "{worktree}"
recipe_root = "recipes/example"
source_cache = "{source_cache}"

[registry]
name = "configured-registry.json"
""",
        encoding="utf-8",
    )

    build_result = runner.invoke(main, ["--config", str(config_path), "data", "build-all"])
    registry_result = runner.invoke(main, ["--config", str(config_path), "data", "registry"])

    assert build_result.exit_code == 0
    assert "wrote" in build_result.output
    assert registry_result.exit_code == 0
    assert f"{worktree}/configured-registry.json" in registry_result.output
    assert (worktree / "example/hello-climate.txt").exists()
    assert (worktree / "configured-registry.json").exists()


def test_data_cli_can_select_named_store(tmp_path: Path) -> None:
    runner = CliRunner()
    worktree = tmp_path / "atlas-data"
    config_path = tmp_path / "stores.toml"
    config_path.write_text(
        f"""
[stores.atlas]
base_url = "https://example.test/atlas"
branch = "atlas-data"
worktree = "{worktree}"
recipe_root = "recipes/example"
source_cache = "{tmp_path / "atlas-sources"}"
registry = "atlas-registry.json"
""",
        encoding="utf-8",
    )

    build_result = runner.invoke(
        main,
        ["--config", str(config_path), "data", "build-all", "--store", "atlas"],
    )
    registry_result = runner.invoke(
        main,
        ["--config", str(config_path), "data", "registry", "--store", "atlas"],
    )

    assert build_result.exit_code == 0
    assert registry_result.exit_code == 0
    assert (worktree / "example/hello-climate.txt").exists()
    assert (worktree / "atlas-registry.json").exists()
