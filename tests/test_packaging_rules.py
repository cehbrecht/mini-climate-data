from __future__ import annotations

from pathlib import Path

GENERATED_SUFFIXES = {".nc", ".zarr"}


def test_generated_artifacts_are_not_committed_to_source_tree() -> None:
    ignored_roots = {".git", ".pytest_cache", "artifacts", "build-artifacts", "data", "dist"}
    offenders: list[Path] = []

    for path in Path(".").rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored_roots for part in path.parts):
            continue
        if path.suffix in GENERATED_SUFFIXES:
            offenders.append(path)

    assert offenders == []


def test_build_config_excludes_generated_artifacts() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert '"/data"' in pyproject
    assert '"*.nc"' in pyproject
    assert '"*.zarr"' in pyproject


def test_cli_alias_is_configured() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'mini-climate-data = "mini_climate_data.cli:main"' in pyproject
    assert 'mcd = "mini_climate_data.cli:main"' in pyproject
