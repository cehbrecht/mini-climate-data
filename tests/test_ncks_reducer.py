from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mini_climate_data.recipes import Recipe
from mini_climate_data.reducers import build_recipe


def test_ncks_subset_builds_command_from_recipe(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "tas_input.nc"
    source.write_bytes(b"netcdf")
    recipe_path = tmp_path / "recipe.yml"
    recipe_path.write_text(
        f"""
name: example/tas-subset
source:
  kind: direct_url
  description: Local source file for reducer command construction.
  url: file://{source}
reducer:
  name: ncks_subset
  parameters:
    variable: tas
    dimensions:
      time: 0
      lat:
        stride: 10
      lon:
        stride: 10
    backend_options:
      compression_level: 1
      netcdf4_classic: true
artifacts:
  - path: example/tas-small.nc
    logical_name: example/tas-small.nc
    max_size: 1024
validation:
  openable: false
""",
        encoding="utf-8",
    )
    commands: list[list[str]] = []

    def fake_run(command: list[str], check: bool) -> None:
        commands.append(command)
        Path(command[-1]).write_bytes(b"reduced")

    monkeypatch.setattr("mini_climate_data.reducers.nco.subprocess.run", fake_run)

    written = build_recipe(recipe_path, tmp_path / "artifacts")

    assert written == [tmp_path / "artifacts/example/tas-small.nc"]
    assert commands == [
        [
            "ncks",
            "-h",
            "-7",
            "-L",
            "1",
            "-d",
            "time,0",
            "-d",
            "lat,,,10",
            "-d",
            "lon,,,10",
            "--variable",
            "tas",
            str(source),
            str(tmp_path / "artifacts/example/tas-small.nc"),
        ]
    ]


def test_ncks_subset_matches_input_glob_to_declared_artifacts(tmp_path: Path, monkeypatch) -> None:
    first = tmp_path / "a.nc"
    second = tmp_path / "b.nc"
    first.write_bytes(b"a")
    second.write_bytes(b"b")
    recipe = Recipe(
        path=tmp_path / "recipe.yml",
        data={
            "name": "example/glob",
            "source": {"kind": "direct_url", "description": "unused", "url": str(first)},
            "reducer": {
                "name": "ncks_subset",
                "parameters": {"input_glob": str(tmp_path / "*.nc"), "variables": ["tas", "pr"]},
            },
            "artifacts": [
                {"path": "example/a.nc", "logical_name": "example/a.nc", "max_size": 1024},
                {"path": "example/b.nc", "logical_name": "example/b.nc", "max_size": 1024},
            ],
            "validation": {"openable": False},
        },
    )
    commands: list[list[str]] = []

    def fake_run(command: list[str], check: bool) -> None:
        commands.append(command)
        Path(command[-1]).write_bytes(b"reduced")

    monkeypatch.setattr("mini_climate_data.reducers.nco.subprocess.run", fake_run)

    written = build_recipe(recipe, tmp_path / "artifacts")

    assert written == [tmp_path / "artifacts/example/a.nc", tmp_path / "artifacts/example/b.nc"]
    assert [command[-2] for command in commands] == [str(first), str(second)]
    assert all(command[-4:-2] == ["--variable", "tas,pr"] for command in commands)


def test_ncks_subset_requires_artifacts_to_match_inputs(tmp_path: Path) -> None:
    first = tmp_path / "a.nc"
    second = tmp_path / "b.nc"
    first.write_bytes(b"a")
    second.write_bytes(b"b")
    recipe = Recipe(
        path=tmp_path / "recipe.yml",
        data={
            "name": "example/mismatch",
            "source": {"kind": "direct_url", "description": "unused", "url": str(first)},
            "reducer": {
                "name": "ncks_subset",
                "parameters": {"input_glob": str(tmp_path / "*.nc")},
            },
            "artifacts": [
                {"path": "example/a.nc", "logical_name": "example/a.nc", "max_size": 1024},
            ],
            "validation": {"openable": False},
        },
    )

    with pytest.raises(ValueError, match="one declared artifact per input file"):
        build_recipe(recipe, tmp_path / "artifacts")


def test_ncks_subset_rejects_bad_compression_level(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "tas_input.nc"
    source.write_bytes(b"netcdf")
    recipe = Recipe(
        path=tmp_path / "recipe.yml",
        data={
            "name": "example/bad-compression",
            "source": {"kind": "direct_url", "description": "local", "url": str(source)},
            "reducer": {
                "name": "ncks_subset",
                "parameters": {"backend_options": {"compression_level": 99}},
            },
            "artifacts": [
                {"path": "example/tas.nc", "logical_name": "example/tas.nc", "max_size": 1024},
            ],
            "validation": {"openable": False},
        },
    )

    def fake_run(command: list[str], check: bool) -> Any:
        raise AssertionError("ncks should not run with invalid parameters")

    monkeypatch.setattr("mini_climate_data.reducers.nco.subprocess.run", fake_run)

    with pytest.raises(ValueError, match="compression_level"):
        build_recipe(recipe, tmp_path / "artifacts")
