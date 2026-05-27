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


def resolve_intake_url(source: SourceSpec | dict[str, Any]) -> str:
    """Resolve a URL from an intake table using a recipe's row-selection fields."""
    data = source.data if isinstance(source, SourceSpec) else source
    if "ds_id" not in data:
        raise ValueError("Intake URL resolution requires source.ds_id")

    table_source = open_intake_source(data)
    table = table_source.read()
    return select_table_url(
        table,
        ds_id=data["ds_id"],
        ds_id_column=data.get("ds_id_column", "ds_id"),
        url_column=data.get("url_column", "url"),
    )


def select_table_url(table: Any, *, ds_id: str, ds_id_column: str = "ds_id", url_column: str = "url") -> str:
    """Select one URL from a pandas-like table or iterable of row mappings."""
    if hasattr(table, "loc") and hasattr(table, "iloc"):
        matches = table.loc[table[ds_id_column] == ds_id]
        if len(matches) != 1:
            raise ValueError(f"Expected one row for {ds_id_column}={ds_id!r}, found {len(matches)}")
        return str(matches.iloc[0][url_column])

    if hasattr(table, "to_dict"):
        rows = table.to_dict("records")
    else:
        rows = list(table)

    matches = [row for row in rows if row[ds_id_column] == ds_id]
    if len(matches) != 1:
        raise ValueError(f"Expected one row for {ds_id_column}={ds_id!r}, found {len(matches)}")
    return str(matches[0][url_column])
