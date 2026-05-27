"""Tiny, reproducible climate datasets for tests and examples."""

from mini_climate_data.fetching import fetch
from mini_climate_data.registry import build_registry, load_registry
from mini_climate_data.recipes import iter_recipes, load_recipe, validate_recipe
from mini_climate_data.sources import load_catalog_aliases, load_source_spec, resolve_catalog_url, resolve_intake_url

__all__ = [
    "build_registry",
    "fetch",
    "iter_recipes",
    "load_catalog_aliases",
    "load_source_spec",
    "load_recipe",
    "load_registry",
    "resolve_catalog_url",
    "resolve_intake_url",
    "validate_recipe",
]
