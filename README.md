# mini-climate-data

Reproducible recipes and tiny generated climate datasets for tests, examples, and CI.

`mini-climate-data` is designed to replace ad hoc reduced climate files with a traceable workflow:

- `main` contains package code, recipes, reducers, validation, tests, and docs.
- `data` is a disposable generated branch for reduced artifacts and a `pooch` registry.
- Python packages never include generated data artifacts.
- Every artifact is traceable to a recipe and reducer.

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

## Development

```console
make dev
make test
make lint
make format
```
