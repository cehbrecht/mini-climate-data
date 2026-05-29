from __future__ import annotations

from pathlib import Path

import click

from mini_climate_data.data_store import (
    DEFAULT_DATA_BRANCH,
    DEFAULT_DATA_WORKTREE,
    DataStoreConfig,
    build_all_data,
    build_data_recipe,
    clean_data,
    data_status,
    init_data_worktree,
    validate_data,
    write_data_registry,
)
from mini_climate_data.data_store import (
    publish_data as publish_data_store,
)
from mini_climate_data.recipes import iter_recipes, update_recipe_artifact_metadata, validate_recipe
from mini_climate_data.reducers import build_recipe
from mini_climate_data.registry import build_registry
from mini_climate_data.validation import validate_artifacts


@click.group()
def main() -> None:
    """Build, validate, publish, and fetch tiny climate datasets."""


@main.command("list")
@click.option(
    "--recipes",
    "recipe_root",
    default="recipes",
    show_default=True,
    type=click.Path(exists=True),
)
def list_recipes(recipe_root: str) -> None:
    """List available recipes."""
    for recipe in iter_recipes(recipe_root):
        click.echo(recipe.name)


@main.command()
@click.argument("recipe", type=click.Path(exists=True))
@click.option("--artifact-root", default="artifacts", show_default=True, type=click.Path())
def build(recipe: str, artifact_root: str) -> None:
    """Run the reducer declared by a recipe."""
    validate_recipe(recipe)
    for path in build_recipe(recipe, artifact_root):
        click.echo(f"wrote {path}")


@main.command()
@click.argument("target", type=click.Path(exists=True))
@click.option(
    "--artifact-root",
    default="artifacts",
    show_default=True,
    type=click.Path(exists=True),
)
def validate(target: str, artifact_root: str) -> None:
    """Validate a recipe's generated artifacts."""
    checked = validate_artifacts(target, artifact_root)
    for path in checked:
        click.echo(f"ok {path}")


@main.command("update-checksums")
@click.argument("recipe", type=click.Path(exists=True))
@click.option(
    "--artifact-root",
    default="artifacts",
    show_default=True,
    type=click.Path(exists=True),
)
def update_checksums(recipe: str, artifact_root: str) -> None:
    """Write built artifact sizes and checksums back to a recipe."""
    updated = update_recipe_artifact_metadata(recipe, artifact_root)
    for artifact in updated.artifacts:
        click.echo(f"updated {artifact['path']} {artifact['checksum']}")


@main.command("build-registry")
@click.option(
    "--recipes",
    "recipe_root",
    default="recipes",
    show_default=True,
    type=click.Path(exists=True),
)
@click.option(
    "--artifact-root",
    default="artifacts",
    show_default=True,
    type=click.Path(exists=True),
)
@click.option("--output", default="artifacts/registry.json", show_default=True, type=click.Path())
def build_registry_command(recipe_root: str, artifact_root: str, output: str) -> None:
    """Generate the pooch registry from built artifacts."""
    registry = build_registry(recipe_root, artifact_root, output)
    click.echo(f"wrote {len(registry)} entries to {output}")


@main.command("publish-data")
def publish_data() -> None:
    """Explain the deployment boundary for generated data."""
    raise click.ClickException(
        "Use the `mcd data publish` command to publish locally generated artifacts."
    )


@main.group()
def data() -> None:
    """Manage the local git-backed generated data store."""


def _data_config(branch: str, worktree: str, recipes: str = "recipes") -> DataStoreConfig:
    return DataStoreConfig(branch=branch, worktree=Path(worktree), recipe_root=Path(recipes))


@data.command("init")
@click.option("--branch", default=DEFAULT_DATA_BRANCH, show_default=True)
@click.option("--worktree", default=DEFAULT_DATA_WORKTREE, show_default=True, type=click.Path())
@click.option(
    "--orphan",
    is_flag=True,
    help="Create a new orphan data branch if the branch does not exist yet.",
)
def data_init(branch: str, worktree: str, orphan: bool) -> None:
    """Create or reuse the local data branch worktree."""
    config = _data_config(branch, worktree)
    path = init_data_worktree(config, orphan=orphan)
    click.echo(f"data worktree ready at {path}")


@data.command("build")
@click.argument("recipe", type=click.Path(exists=True))
@click.option("--branch", default=DEFAULT_DATA_BRANCH, show_default=True)
@click.option("--worktree", default=DEFAULT_DATA_WORKTREE, show_default=True, type=click.Path())
def data_build(recipe: str, branch: str, worktree: str) -> None:
    """Build one recipe into the data worktree."""
    config = _data_config(branch, worktree)
    for path in build_data_recipe(recipe, config):
        click.echo(f"wrote {path}")


@data.command("build-all")
@click.option("--branch", default=DEFAULT_DATA_BRANCH, show_default=True)
@click.option("--worktree", default=DEFAULT_DATA_WORKTREE, show_default=True, type=click.Path())
@click.option(
    "--recipes",
    "recipe_root",
    default="recipes",
    show_default=True,
    type=click.Path(exists=True),
)
def data_build_all(branch: str, worktree: str, recipe_root: str) -> None:
    """Build all recipes into the data worktree."""
    config = _data_config(branch, worktree, recipe_root)
    for path in build_all_data(config):
        click.echo(f"wrote {path}")


@data.command("validate")
@click.option("--branch", default=DEFAULT_DATA_BRANCH, show_default=True)
@click.option(
    "--worktree",
    default=DEFAULT_DATA_WORKTREE,
    show_default=True,
    type=click.Path(exists=True),
)
@click.option(
    "--recipes",
    "recipe_root",
    default="recipes",
    show_default=True,
    type=click.Path(exists=True),
)
def data_validate(branch: str, worktree: str, recipe_root: str) -> None:
    """Validate generated data in the data worktree."""
    config = _data_config(branch, worktree, recipe_root)
    for path in validate_data(config):
        click.echo(f"ok {path}")


@data.command("registry")
@click.option("--branch", default=DEFAULT_DATA_BRANCH, show_default=True)
@click.option(
    "--worktree",
    default=DEFAULT_DATA_WORKTREE,
    show_default=True,
    type=click.Path(exists=True),
)
@click.option(
    "--recipes",
    "recipe_root",
    default="recipes",
    show_default=True,
    type=click.Path(exists=True),
)
def data_registry(branch: str, worktree: str, recipe_root: str) -> None:
    """Write registry.json into the data worktree."""
    config = _data_config(branch, worktree, recipe_root)
    registry = write_data_registry(config)
    click.echo(f"wrote {len(registry)} entries to {config.registry_path}")


@data.command("clean")
@click.option("--branch", default=DEFAULT_DATA_BRANCH, show_default=True)
@click.option(
    "--worktree",
    default=DEFAULT_DATA_WORKTREE,
    show_default=True,
    type=click.Path(exists=True),
)
@click.option(
    "--recipes",
    "recipe_root",
    default="recipes",
    show_default=True,
    type=click.Path(exists=True),
)
@click.option("--yes", is_flag=True, help="Confirm removal of generated data files.")
def data_clean(branch: str, worktree: str, recipe_root: str, yes: bool) -> None:
    """Remove declared generated artifacts and registry.json from the data worktree."""
    if not yes:
        raise click.ClickException("Refusing to clean without --yes")
    config = _data_config(branch, worktree, recipe_root)
    removed = clean_data(config)
    for path in removed:
        click.echo(f"removed {path}")
    if not removed:
        click.echo("nothing to remove")


@data.command("status")
@click.option("--branch", default=DEFAULT_DATA_BRANCH, show_default=True)
@click.option(
    "--worktree",
    default=DEFAULT_DATA_WORKTREE,
    show_default=True,
    type=click.Path(exists=True),
)
def data_store_status(branch: str, worktree: str) -> None:
    """Show git status for the data worktree."""
    config = _data_config(branch, worktree)
    click.echo(data_status(config) or "clean")


@data.command("publish")
@click.option("--branch", default=DEFAULT_DATA_BRANCH, show_default=True)
@click.option(
    "--worktree",
    default=DEFAULT_DATA_WORKTREE,
    show_default=True,
    type=click.Path(exists=True),
)
@click.option("--remote", default="origin", show_default=True)
@click.option("--message", default="Update generated climate artifacts", show_default=True)
def data_publish(branch: str, worktree: str, remote: str, message: str) -> None:
    """Commit and push generated data from the data worktree."""
    config = _data_config(branch, worktree)
    publish_data_store(config, message=message, remote=remote)
    click.echo(f"pushed {branch} to {remote}")


if __name__ == "__main__":
    main()
