from __future__ import annotations

import click

from mini_climate_data.recipes import iter_recipes, validate_recipe
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
        "Publishing is intentionally CI-owned for now. Use the data-branch workflow "
        "or add an explicit deployment implementation before invoking this command."
    )


if __name__ == "__main__":
    main()
