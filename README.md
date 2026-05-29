# mini-climate-data

[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![CI](https://github.com/macpingu/mini-climate-data/actions/workflows/ci.yml/badge.svg)](https://github.com/macpingu/mini-climate-data/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange)](docs/design.md)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-46a7f5)](https://docs.astral.sh/ruff/)
[![Dependencies](https://img.shields.io/badge/dependencies-optional-lightgrey)](pyproject.toml)

Reproducible recipes and tiny generated climate datasets for tests, examples, and CI.

`mini-climate-data` helps replace ad hoc climate test files with small,
traceable artifacts. Recipes describe where source data came from, which packaged
reducer builds the tiny artifact, and how the result should be validated.

The package is intentionally lightweight by default. Heavier reducer and catalog
dependencies are optional.

## Status

Early scaffold. The API, recipe format, and data publishing workflow may still change.

## Get Started

```console
python -m pip install .
mcd list
mcd build recipes/example/hello-climate.yml
mcd validate recipes/example/hello-climate.yml
```

Generated artifacts are fetched by stable logical name:

```python
import mini_climate_data as mcd

path = mcd.fetch("cmip6/tas-small.nc")
```

Generated data is kept on a git branch named `data` by default. Maintainers can build
and publish it locally from a separate worktree:

```console
mcd data init
mcd data build-all --recipes recipes/example
mcd data validate --recipes recipes/example
mcd data registry --recipes recipes/example
mcd data publish
```

Use `--branch` and `--worktree` to target a test or snapshot data branch. For a clean
local rebuild, run `mcd data clean --yes` before rebuilding. Remote original source
files are cached with `pooch`; data-store builds keep that cache outside the data
worktree by default at `.cache/mini-climate-data/sources`.

Defaults are stored in the packaged `mini_climate_data/config/defaults.toml`. To
override them locally, create `mini-climate-data.toml` in the repository root or point
`MINI_CLIMATE_DATA_CONFIG` at a TOML file:

```toml
[data_store]
branch = "data-test"
worktree = ".worktrees/data-test"
source_cache = "/big/local/cache/mini-climate-data/sources"

[fetch]
version = "data-test"
```

## Development

```console
conda env create -f environment.yml
conda activate mini-climate-data
make dev
make test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development details and
[docs/design.md](docs/design.md) for the current prototype notes.
