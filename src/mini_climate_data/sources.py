from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mini_climate_data.recipes import Recipe, load_recipe


@dataclass(frozen=True)
class SourceSpec:
    """Original-data source metadata from a recipe."""

    kind: str
    data: dict[str, Any]


def load_source_spec(recipe: str | Path | Recipe) -> SourceSpec:
    loaded = recipe if isinstance(recipe, Recipe) else load_recipe(recipe)
    source = loaded.data["source"]
    return SourceSpec(kind=source["kind"], data=source)


def open_intake_source(source: SourceSpec | dict[str, Any]):
    """Open an intake catalog entry described by a recipe source block."""
    data = source.data if isinstance(source, SourceSpec) else source
    if data["kind"] != "intake":
        raise ValueError(f"Expected an intake source, got {data['kind']!r}")

    try:
        import intake
    except ImportError as exc:
        raise RuntimeError("Install mini-climate-data[intake] to open intake sources") from exc

    catalog = intake.open_catalog(data["catalog_url"], **data.get("intake_kwargs", {}))
    entry = data["entry"]
    source_entry = catalog[entry]

    parameters = data.get("parameters", {})
    if parameters:
        source_entry = source_entry(**parameters)

    return source_entry
