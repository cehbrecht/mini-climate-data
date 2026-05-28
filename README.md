# mini-climate-data

Reproducible recipes and tiny generated climate datasets for tests, examples, and CI.

`mini-climate-data` is designed to replace ad hoc reduced climate files with a traceable workflow:

- `main` contains package code, recipes, reducers, validation, tests, and docs.
- `data` is a disposable generated branch for reduced artifacts and a `pooch` registry.
- Python packages never include generated data artifacts.
- Every artifact is traceable to a recipe and reducer.
- Users add recipes; supported reduction code lives in the `mini_climate_data` package.

## Status

This repository is in early scaffold form. The first implementation provides a package layout, recipe schema, CLI, validation helpers, registry generation, and tests that enforce the package/data split.

## Usage

```console
mcd list
mcd build recipes/example/hello-climate.yml
mcd validate recipes/example/hello-climate.yml
mcd build-registry
```

Downstream packages will fetch generated artifacts by stable logical name:

```python
from mini_climate_data import fetch

path = fetch("cmip6/tas-small.nc")
```

See [docs/design.md](docs/design.md) for the branch and recipe model.

## Installation

The base install keeps heavy climate and catalog libraries optional:

```console
python -m pip install .
```

Install extras only for the features you need:

```console
python -m pip install ".[fetch]"          # fetch published artifacts with pooch
python -m pip install ".[netcdf]"         # xarray/h5netcdf NetCDF reducers
python -m pip install ".[intake]"         # intake catalog sources
python -m pip install ".[all]"            # all optional runtime integrations
```

## Development

The conda environment installs the heavier local-development stack from conda-forge.
`make dev` then installs this package in editable mode.

```console
conda env create -f environment.yml
conda activate mini-climate-data
make dev
make test
make lint
make format
```
