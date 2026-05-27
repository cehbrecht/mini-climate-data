from __future__ import annotations

from mini_climate_data.recipes import validate_recipe_data
from mini_climate_data.sources import (
    load_catalog_aliases,
    load_source_spec,
    resolve_catalog_url,
    select_table_url,
)


def test_load_source_spec_from_example_recipe() -> None:
    source = load_source_spec("recipes/example/hello-climate.yml")

    assert source.kind == "synthetic"


def test_intake_source_shape_is_valid() -> None:
    validate_recipe_data(
        {
            "name": "copernicus/example",
            "source": {
                "kind": "intake",
                "description": "Copernicus Climate Data Store via cp4cds intake manifest.",
                "license": "Copernicus C3S data license",
                "catalog": "c3s",
                "entry": "c3s-cica-atlas",
                "ds_id": "cica-atlas-v025",
                "url_param": "url",
                "parameters": {"variable": "tas"},
            },
            "reducer": {"script": "reducers/example.py"},
            "artifacts": [
                {
                    "path": "copernicus/example.nc",
                    "logical_name": "copernicus/example.nc",
                    "max_size": 100000,
                }
            ],
            "validation": {"openable": True, "engine": "netcdf"},
        }
    )


def test_select_table_url_from_records() -> None:
    table = [
        {"ds_id": "other", "url": "https://example.test/other.nc"},
        {"ds_id": "cica-atlas-v025", "url": "https://example.test/cica-atlas-v025.nc"},
    ]

    assert (
        select_table_url(table, ds_id="cica-atlas-v025")
        == "https://example.test/cica-atlas-v025.nc"
    )


def test_select_table_url_rejects_missing_match() -> None:
    table = [{"ds_id": "other", "url": "https://example.test/other.nc"}]

    try:
        select_table_url(table, ds_id="cica-atlas-v025")
    except ValueError as exc:
        assert "Expected one row" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_catalog_alias_resolves_c3s_url() -> None:
    aliases = load_catalog_aliases()

    assert (
        aliases["c3s"]
        == "https://raw.githubusercontent.com/cp4cds/c3s_34g_manifests/master/intake/catalogs/c3s.yaml"
    )
    assert resolve_catalog_url({"catalog": "c3s"}) == aliases["c3s"]


def test_url_param_can_select_non_default_column() -> None:
    table = [
        {"ds_id": "cica-atlas-v025", "download_url": "https://example.test/cica-atlas-v025.nc"},
    ]

    assert (
        select_table_url(table, ds_id="cica-atlas-v025", url_param="download_url")
        == "https://example.test/cica-atlas-v025.nc"
    )


def test_direct_url_source_shape_is_valid() -> None:
    validate_recipe_data(
        {
            "name": "direct/example",
            "source": {
                "kind": "direct_url",
                "description": "Stable upstream test file.",
                "url": "https://example.test/data.nc",
            },
            "reducer": {"script": "reducers/example.py"},
            "artifacts": [
                {
                    "path": "direct/example.nc",
                    "logical_name": "direct/example.nc",
                    "max_size": 100000,
                }
            ],
            "validation": {"openable": True, "engine": "netcdf"},
        }
    )
