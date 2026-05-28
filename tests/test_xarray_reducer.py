from __future__ import annotations

import builtins
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from mini_climate_data.recipes import Recipe
from mini_climate_data.reducers import build_recipe, helpers


class FakeDataset:
    def __init__(self, source: Path) -> None:
        self.source = source
        self.variables: list[str] | None = None
        self.isel_indexers: dict[str, Any] | None = None
        self.sel_indexers: dict[str, Any] | None = None
        self.written: tuple[Path, dict[str, Any]] | None = None

    def __enter__(self) -> FakeDataset:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def __getitem__(self, variables: list[str]) -> FakeDataset:
        self.variables = variables
        return self

    def isel(self, indexers: dict[str, Any]) -> FakeDataset:
        self.isel_indexers = indexers
        return self

    def sel(self, indexers: dict[str, Any]) -> FakeDataset:
        self.sel_indexers = indexers
        return self

    def to_netcdf(self, target: Path, **kwargs: Any) -> None:
        target.write_bytes(b"reduced")
        self.written = (target, kwargs)


def test_xarray_subset_selects_variables_and_indexers(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "tas_input.nc"
    source.write_bytes(b"netcdf")
    opened: list[tuple[Path, dict[str, Any], FakeDataset]] = []

    def open_dataset(path: Path, **kwargs: Any) -> FakeDataset:
        dataset = FakeDataset(path)
        opened.append((path, kwargs, dataset))
        return dataset

    monkeypatch.setitem(sys.modules, "xarray", SimpleNamespace(open_dataset=open_dataset))
    recipe_path = tmp_path / "recipe.yml"
    recipe_path.write_text(
        f"""
name: example/tas-xarray
source:
  kind: direct_url
  description: Local source file for xarray reducer construction.
  url: file://{source}
reducer:
  name: xarray_subset
  parameters:
    variables: [tas]
    dimensions:
      time:
        index: 0
      lat:
        stride: 10
      lon:
        stride: 10
    coordinates:
      member_id: r1i1p1f1
    backend_options:
      open_kwargs:
        decode_times: false
      to_netcdf_kwargs:
        engine: h5netcdf
artifacts:
  - path: example/tas-small.nc
    logical_name: example/tas-small.nc
    max_size: 1024
validation:
  openable: false
""",
        encoding="utf-8",
    )

    written = build_recipe(recipe_path, tmp_path / "artifacts")

    assert written == [tmp_path / "artifacts/example/tas-small.nc"]
    assert opened[0][0] == source
    assert opened[0][1] == {"decode_times": False}
    dataset = opened[0][2]
    assert dataset.variables == ["tas"]
    assert dataset.isel_indexers == {
        "time": 0,
        "lat": slice(None, None, 10),
        "lon": slice(None, None, 10),
    }
    assert dataset.sel_indexers == {"member_id": "r1i1p1f1"}
    assert dataset.written == (tmp_path / "artifacts/example/tas-small.nc", {"engine": "h5netcdf"})


def test_xarray_subset_matches_input_glob_to_declared_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    first = tmp_path / "a.nc"
    second = tmp_path / "b.nc"
    first.write_bytes(b"a")
    second.write_bytes(b"b")
    opened: list[Path] = []

    def open_dataset(path: Path, **kwargs: Any) -> FakeDataset:
        opened.append(path)
        return FakeDataset(path)

    monkeypatch.setitem(sys.modules, "xarray", SimpleNamespace(open_dataset=open_dataset))
    recipe = Recipe(
        path=tmp_path / "recipe.yml",
        data={
            "name": "example/xarray-glob",
            "source": {"kind": "direct_url", "description": "unused", "url": str(first)},
            "reducer": {
                "name": "xarray_subset",
                "parameters": {"input_glob": str(tmp_path / "*.nc"), "variable": "tas"},
            },
            "artifacts": [
                {"path": "example/a.nc", "logical_name": "example/a.nc", "max_size": 1024},
                {"path": "example/b.nc", "logical_name": "example/b.nc", "max_size": 1024},
            ],
            "validation": {"openable": False},
        },
    )

    written = build_recipe(recipe, tmp_path / "artifacts")

    assert written == [tmp_path / "artifacts/example/a.nc", tmp_path / "artifacts/example/b.nc"]
    assert opened == [first, second]


def test_xarray_subset_caches_remote_intake_source(tmp_path: Path, monkeypatch) -> None:
    opened: list[Path] = []

    def open_dataset(path: Path, **kwargs: Any) -> FakeDataset:
        opened.append(path)
        return FakeDataset(path)

    class FakeResponse:
        def __init__(self) -> None:
            self.remaining = b"netcdf"

        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self, size: int = -1) -> bytes:
            chunk = self.remaining
            self.remaining = b""
            return chunk

    monkeypatch.setitem(sys.modules, "xarray", SimpleNamespace(open_dataset=open_dataset))
    monkeypatch.setattr(
        helpers,
        "resolve_intake_url",
        lambda source: "https://example.test/data/psl_ERA5_mon_194001-202512_v025.nc",
    )
    monkeypatch.setattr(helpers, "urlopen", lambda url: FakeResponse())
    recipe = Recipe(
        path=tmp_path / "recipe.yml",
        data={
            "name": "c3s-cica-atlas/era5-psl",
            "source": {
                "kind": "intake",
                "description": "Atlas source",
                "catalog": "c3s",
                "entry": "c3s-cica-atlas",
                "ds_id": "c3s-cica-atlas.psl.ERA5.mon.v25",
            },
            "reducer": {"name": "xarray_subset", "parameters": {"variable": "psl"}},
            "artifacts": [
                {
                    "path": "c3s-cica-atlas/ERA5/psl-small.nc",
                    "logical_name": "c3s-cica-atlas/ERA5/psl-small.nc",
                    "max_size": 1024,
                },
            ],
            "validation": {"openable": False},
        },
    )

    build_recipe(recipe, tmp_path / "artifacts")

    assert opened[0].parent == tmp_path / "artifacts/_sources"
    assert opened[0].name.endswith("-psl_ERA5_mon_194001-202512_v025.nc")
    assert opened[0].read_bytes() == b"netcdf"


def test_xarray_subset_requires_xarray(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "tas_input.nc"
    source.write_bytes(b"netcdf")
    monkeypatch.delitem(sys.modules, "xarray", raising=False)

    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "xarray":
            raise ImportError("No module named xarray")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    recipe = Recipe(
        path=tmp_path / "recipe.yml",
        data={
            "name": "example/no-xarray",
            "source": {"kind": "direct_url", "description": "local", "url": str(source)},
            "reducer": {"name": "xarray_subset"},
            "artifacts": [
                {"path": "example/tas.nc", "logical_name": "example/tas.nc", "max_size": 1024},
            ],
            "validation": {"openable": False},
        },
    )

    with pytest.raises(RuntimeError, match=r"mini-climate-data\[netcdf\]"):
        build_recipe(recipe, tmp_path / "artifacts")
