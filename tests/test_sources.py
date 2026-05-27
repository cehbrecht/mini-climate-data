from __future__ import annotations

from mini_climate_data.recipes import validate_recipe_data
from mini_climate_data.sources import load_source_spec


def test_load_source_spec_from_example_recipe() -> None:
    source = load_source_spec("recipes/example/hello-climate.yml")

    assert source.kind == "synthetic"


def test_intake_source_shape_is_valid() -> None:
    validate_recipe_data(
        {
            "name": "copernicus/example",
            "source": {
                "kind": "intake",
                "provenance": "Copernicus Climate Data Store via cp4cds intake manifest.",
                "license": "Copernicus C3S data license",
                "catalog_url": "https://raw.githubusercontent.com/cp4cds/c3s_34g_manifests/master/intake/catalogs/c3s.yaml",
                "entry": "example_entry",
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


def test_direct_url_source_shape_is_valid() -> None:
    validate_recipe_data(
        {
            "name": "direct/example",
            "source": {
                "kind": "direct_url",
                "provenance": "Stable upstream test file.",
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
