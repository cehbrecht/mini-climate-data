# Contributing

Thanks for helping make tiny climate fixtures easier to trust.

`mini-climate-data` is recipe-first: generated artifacts are disposable outputs,
while recipes, reducers, validation, tests, and docs are the durable source of truth.

## Setup

The base package install stays small:

```console
python -m pip install .
```

Install optional runtime groups only when needed:

```console
python -m pip install ".[fetch]"          # fetch published artifacts with pooch
python -m pip install ".[netcdf]"         # xarray/h5netcdf NetCDF reducers
python -m pip install ".[intake]"         # intake catalog sources
python -m pip install ".[all]"            # all optional runtime integrations
```

For local development with the full optional stack:

```console
conda env create -f environment.yml
conda activate mini-climate-data
make dev
```

For a lighter pip-only setup:

```console
python -m pip install -e ".[dev,all]"
```

## Checks

Run the same checks used by CI before opening a pull request:

```console
make lint
make test
```

Use `make format` to apply Ruff fixes and formatting.

## Recipes

- Add recipe YAML under `recipes/`.
- Keep source metadata explicit: include source kind, description, license, and citation where applicable.
- Use packaged reducers from `mini_climate_data.reducers`; do not add project-local reducer scripts in recipes.
- Declare every generated artifact with a stable `logical_name` and strict `max_size`.
- Add checksums only after artifacts are built and ready to publish.

## Reducers

- Reducers live in `src/mini_climate_data/reducers/`.
- Prefer reducer-neutral recipe parameters for common operations such as variable, dimension, and coordinate selection.
- Keep heavy or provider-specific Python dependencies behind optional extras in `pyproject.toml`.
- If a reducer requires external command-line tools, fail with a clear error and document the requirement.

## Generated Data

Do not commit generated NetCDF or Zarr artifacts to the source tree. Generated data
belongs on the disposable `data` branch or in local `artifacts/` output directories.

The Python package should contain code, recipes, schemas, and lightweight metadata
only.

## Documentation

Update `README.md`, `docs/design.md`, and `CHANGES.md` when a change affects user
workflow, recipe format, reducer behavior, dependency groups, or publishing rules.
