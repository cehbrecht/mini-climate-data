from __future__ import annotations

import click

from mini_climate_data.config import DEFAULT_USER_CONFIG, Settings
from mini_climate_data.data_store import (
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
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False),
    help=f"Read configuration overrides from TOML. Defaults to {DEFAULT_USER_CONFIG} if present.",
)
@click.pass_context
def main(ctx: click.Context, config_path: str | None) -> None:
    """Build, validate, publish, and fetch tiny climate datasets."""
    ctx.obj = Settings.load(config_path)


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


def _data_config(
    ctx: click.Context,
    branch: str | None,
    worktree: str | None,
    recipes: str | None = None,
    source_cache: str | None = None,
):
    settings: Settings = ctx.find_root().obj
    return settings.data_store_config(
        branch=branch,
        worktree=worktree,
        recipe_root=recipes,
        source_cache=source_cache,
    )


@data.command("init")
@click.option("--branch", default=None, help="Data branch name.")
@click.option("--worktree", default=None, type=click.Path(), help="Data branch worktree path.")
@click.option(
    "--orphan",
    is_flag=True,
    help="Create a new orphan data branch if the branch does not exist yet.",
)
@click.pass_context
def data_init(ctx: click.Context, branch: str | None, worktree: str | None, orphan: bool) -> None:
    """Create or reuse the local data branch worktree."""
    config = _data_config(ctx, branch, worktree)
    path = init_data_worktree(config, orphan=orphan)
    click.echo(f"data worktree ready at {path}")


@data.command("build")
@click.argument("recipe", type=click.Path(exists=True))
@click.option("--branch", default=None, help="Data branch name.")
@click.option("--worktree", default=None, type=click.Path(), help="Data branch worktree path.")
@click.option("--source-cache", default=None, type=click.Path(), help="Original-source cache path.")
@click.pass_context
def data_build(
    ctx: click.Context,
    recipe: str,
    branch: str | None,
    worktree: str | None,
    source_cache: str | None,
) -> None:
    """Build one recipe into the data worktree."""
    config = _data_config(ctx, branch, worktree, source_cache=source_cache)
    for path in build_data_recipe(recipe, config):
        click.echo(f"wrote {path}")


@data.command("build-all")
@click.option("--branch", default=None, help="Data branch name.")
@click.option("--worktree", default=None, type=click.Path(), help="Data branch worktree path.")
@click.option("--source-cache", default=None, type=click.Path(), help="Original-source cache path.")
@click.option(
    "--recipes",
    "recipe_root",
    default=None,
    type=click.Path(exists=True),
    help="Recipe root to build.",
)
@click.pass_context
def data_build_all(
    ctx: click.Context,
    branch: str | None,
    worktree: str | None,
    source_cache: str | None,
    recipe_root: str | None,
) -> None:
    """Build all recipes into the data worktree."""
    config = _data_config(ctx, branch, worktree, recipe_root, source_cache)
    for path in build_all_data(config):
        click.echo(f"wrote {path}")


@data.command("validate")
@click.option("--branch", default=None, help="Data branch name.")
@click.option("--worktree", default=None, type=click.Path(exists=True), help="Data worktree path.")
@click.option(
    "--recipes",
    "recipe_root",
    default=None,
    type=click.Path(exists=True),
    help="Recipe root to validate.",
)
@click.pass_context
def data_validate(
    ctx: click.Context,
    branch: str | None,
    worktree: str | None,
    recipe_root: str | None,
) -> None:
    """Validate generated data in the data worktree."""
    config = _data_config(ctx, branch, worktree, recipe_root)
    for path in validate_data(config):
        click.echo(f"ok {path}")


@data.command("registry")
@click.option("--branch", default=None, help="Data branch name.")
@click.option("--worktree", default=None, type=click.Path(exists=True), help="Data worktree path.")
@click.option(
    "--recipes",
    "recipe_root",
    default=None,
    type=click.Path(exists=True),
    help="Recipe root for registry entries.",
)
@click.pass_context
def data_registry(
    ctx: click.Context,
    branch: str | None,
    worktree: str | None,
    recipe_root: str | None,
) -> None:
    """Write registry.json into the data worktree."""
    config = _data_config(ctx, branch, worktree, recipe_root)
    registry = write_data_registry(config)
    click.echo(f"wrote {len(registry)} entries to {config.registry_path}")


@data.command("clean")
@click.option("--branch", default=None, help="Data branch name.")
@click.option("--worktree", default=None, type=click.Path(exists=True), help="Data worktree path.")
@click.option(
    "--recipes",
    "recipe_root",
    default=None,
    type=click.Path(exists=True),
    help="Recipe root whose artifacts should be removed.",
)
@click.option("--yes", is_flag=True, help="Confirm removal of generated data files.")
@click.pass_context
def data_clean(
    ctx: click.Context,
    branch: str | None,
    worktree: str | None,
    recipe_root: str | None,
    yes: bool,
) -> None:
    """Remove declared generated artifacts and registry.json from the data worktree."""
    if not yes:
        raise click.ClickException("Refusing to clean without --yes")
    config = _data_config(ctx, branch, worktree, recipe_root)
    removed = clean_data(config)
    for path in removed:
        click.echo(f"removed {path}")
    if not removed:
        click.echo("nothing to remove")


@data.command("status")
@click.option("--branch", default=None, help="Data branch name.")
@click.option("--worktree", default=None, type=click.Path(exists=True), help="Data worktree path.")
@click.pass_context
def data_store_status(ctx: click.Context, branch: str | None, worktree: str | None) -> None:
    """Show git status for the data worktree."""
    config = _data_config(ctx, branch, worktree)
    click.echo(data_status(config) or "clean")


@data.command("publish")
@click.option("--branch", default=None, help="Data branch name.")
@click.option("--worktree", default=None, type=click.Path(exists=True), help="Data worktree path.")
@click.option("--remote", default="origin", show_default=True)
@click.option("--message", default="Update generated climate artifacts", show_default=True)
@click.pass_context
def data_publish(
    ctx: click.Context,
    branch: str | None,
    worktree: str | None,
    remote: str,
    message: str,
) -> None:
    """Commit and push generated data from the data worktree."""
    config = _data_config(ctx, branch, worktree)
    publish_data_store(config, message=message, remote=remote)
    click.echo(f"pushed {branch} to {remote}")


if __name__ == "__main__":
    main()
