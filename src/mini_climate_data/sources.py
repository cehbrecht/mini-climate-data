from __future__ import annotations

import csv
import gzip
from dataclasses import dataclass
from importlib import resources
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import urlopen

import yaml

from mini_climate_data._paths import PACKAGE
from mini_climate_data.recipes import Recipe, load_recipe

CATALOGS_RESOURCE = "catalogs.yml"


@dataclass(frozen=True)
class SourceSpec:
    """Original-data source metadata from a recipe."""

    kind: str
    data: dict[str, Any]


def load_source_spec(recipe: str | Path | Recipe) -> SourceSpec:
    loaded = recipe if isinstance(recipe, Recipe) else load_recipe(recipe)
    source = loaded.data["source"]
    return SourceSpec(kind=source["kind"], data=source)


def load_catalog_aliases() -> dict[str, str]:
    """Load built-in intake/STAC catalog aliases."""
    catalog_path = resources.files(PACKAGE) / CATALOGS_RESOURCE
    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Catalog alias registry must be a mapping: {catalog_path}")
    catalogs = data.get("catalogs", {})
    if not isinstance(catalogs, dict):
        raise ValueError(f"Catalog alias registry must contain a catalogs mapping: {catalog_path}")
    return {str(name): str(config["url"]) for name, config in catalogs.items()}


def resolve_catalog_url(source: SourceSpec | dict[str, Any]) -> str:
    """Resolve a catalog URL from either an explicit URL or a named catalog alias."""
    data = source.data if isinstance(source, SourceSpec) else source
    if "catalog_url" in data:
        return str(data["catalog_url"])
    if "catalog" not in data:
        raise ValueError("Source must define either catalog_url or catalog")

    aliases = load_catalog_aliases()
    catalog_name = data["catalog"]
    try:
        return aliases[catalog_name]
    except KeyError as exc:
        known = ", ".join(sorted(aliases))
        raise ValueError(f"Unknown catalog alias {catalog_name!r}. Known aliases: {known}") from exc


def open_intake_source(source: SourceSpec | dict[str, Any]):
    """Open an intake catalog entry described by a recipe source block."""
    data = source.data if isinstance(source, SourceSpec) else source
    if data["kind"] != "intake":
        raise ValueError(f"Expected an intake source, got {data['kind']!r}")

    try:
        import intake
    except ImportError as exc:
        raise RuntimeError("Install mini-climate-data[intake] to open intake sources") from exc

    catalog = intake.open_catalog(resolve_catalog_url(data), **data.get("intake_kwargs", {}))
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
    try:
        table = table_source.read()
    except TypeError as exc:
        if "csv_kwargs" not in str(exc):
            raise
        table = read_intake_csv_manifest(data)
    return select_table_url(
        table,
        ds_id=data["ds_id"],
        ds_id_column=data.get("ds_id_column", "ds_id"),
        url_param=data.get("url_param", data.get("url_column", "url")),
    )


def read_intake_csv_manifest(source: SourceSpec | dict[str, Any]) -> list[dict[str, str]]:
    """Read an intake CSV manifest directly when intake's CSV driver is incompatible."""
    data = source.data if isinstance(source, SourceSpec) else source
    catalog_url = resolve_catalog_url(data)
    catalog = yaml.safe_load(_read_url_text(catalog_url))
    entry = catalog["sources"][data["entry"]]
    catalog_dir = catalog_url.rsplit("/", 1)[0]
    urlpath = str(entry["args"]["urlpath"]).replace("{{ CATALOG_DIR }}", catalog_dir)
    urlpath = urljoin(catalog_url, urlpath)

    payload = urlopen(urlpath).read()
    compression = entry["args"].get("csv_kwargs", {}).get("compression")
    if compression == "gzip" or urlpath.endswith(".gz"):
        payload = gzip.decompress(payload)

    return list(csv.DictReader(StringIO(payload.decode("utf-8"))))


def _read_url_text(url: str) -> str:
    return urlopen(url).read().decode("utf-8")


def select_table_url(
    table: Any,
    *,
    ds_id: str,
    ds_id_column: str = "ds_id",
    url_param: str = "url",
) -> str:
    """Select one URL from a pandas-like table or iterable of row mappings."""
    if hasattr(table, "loc") and hasattr(table, "iloc"):
        matches = table.loc[table[ds_id_column] == ds_id]
        if len(matches) != 1:
            raise ValueError(f"Expected one row for {ds_id_column}={ds_id!r}, found {len(matches)}")
        return str(matches.iloc[0][url_param])

    if hasattr(table, "to_dict"):
        rows = table.to_dict("records")
    else:
        rows = list(table)

    matches = [row for row in rows if row[ds_id_column] == ds_id]
    if len(matches) != 1:
        raise ValueError(f"Expected one row for {ds_id_column}={ds_id!r}, found {len(matches)}")
    return str(matches[0][url_param])
