# Design

`mini-climate-data` separates authoritative source from generated data.

The `main` branch contains package code, recipes, reducers, validation, tests, and documentation. It is the source of truth for how each tiny dataset is produced.

The `data` branch is a disposable generated cache. It contains reduced artifacts and a registry for downstream consumers. It should not be manually edited, merged back into `main`, or treated as authoritative.

Generated climate artifacts are deliberately excluded from the Python package. The package should contain code, recipe definitions, schemas, and lightweight metadata only. Consumers fetch data by logical name through `pooch`.

## Purpose

This project is intended to replace ad hoc climate test-data copies with a small,
reviewable build system. It borrows the useful idea from `mini-esgf-data`: start from
larger authoritative NetCDF files and reduce them into tiny fixtures for tests,
examples, and CI. It should not copy the old repository's generated data or recreate
one-off generation scripts.

The durable object in `mini-climate-data` is the recipe. A recipe explains where the
source data came from, which packaged reducer is used, what small artifact should be
written, and how the result is validated. Generated artifacts are disposable outputs
of those recipes.

Reducers should provide a small, friendly vocabulary for common reductions. For NetCDF
subsets that means selecting variables, dimensions, and coordinates without exposing
the user to backend-specific APIs first. Backend details such as `xarray.to_netcdf`
options, `h5netcdf`, or NCO compression flags can still be passed through
`backend_options` when a recipe needs them.

The preferred path is Python-native reduction with `xarray_subset`. The NCO-backed
`ncks_subset` reducer exists for cases where command-line subsetting of large local
ESGF files is faster, more memory-efficient, or closer to an existing operational
workflow. Both reducers should consume the same high-level recipe parameters where
possible.

## Recipe Contract

Each recipe records:

- source description, license, and citation where applicable
- packaged reducer name and parameters
- expected artifacts and logical names
- strict maximum artifact sizes
- validation checks
- checksums after artifacts are built

## Source Types

Recipes should make the original source explicit, but the source block should not force all providers into one access pattern.

Supported source kinds:

- `synthetic`: generated entirely by the reducer
- `direct_url`: a stable URL points directly to an original file
- `intake`: an intake catalog alias or URL and entry identify the original dataset
- `stac`: a STAC catalog alias or URL identifies the search/catalog source, intended for ESGF2-style catalogs

Catalogs can be referenced by short alias. Built-in aliases live in `src/mini_climate_data/catalogs.yml`; the first alias is `c3s`, pointing to the current cp4cds C3S manifest catalog.

A Copernicus Climate Data Store recipe using the current CDS intake catalog should look like this:

```yaml
source:
  kind: intake
  description: Copernicus Climate Data Store via the cp4cds C3S intake manifest.
  license: Copernicus C3S data license
  catalog: c3s
  entry: c3s-cica-atlas
  ds_id: cica-atlas-v025
  url_param: url
  parameters:
    # Provider-specific intake parameters go here.
```

For CDS manifest tables, `entry` is the intake subcatalog/table name, `ds_id` selects one
row, and `url_param` names the column containing the original file URL. `url_param`
defaults to `url`, so most CDS recipes can omit it. Reducers can resolve this with
`mini_climate_data.sources.resolve_intake_url`, then apply their own small, explicit
reduction.

## Reducers

Recipes select a reducer implemented in the `mini_climate_data` package. Users add recipe
YAML, not project-local Python scripts. This keeps reduction logic reviewed, tested, reusable,
and versioned with the package.

```yaml
reducer:
  name: xarray_subset
  parameters:
    variables: [tas]
    dimensions:
      time: 0
      lat:
        stride: 100
      lon:
        stride: 100
```

The scaffold includes `write_text` for smoke tests. The preferred NetCDF reducer is
`xarray_subset`, which keeps the workflow Python-native and easy to test. Recipes
name the local source file or glob, variables, dimensions, coordinate selections,
and output artifacts using reducer-neutral names. Backend-specific settings live under
`backend_options`.

```yaml
source:
  kind: direct_url
  description: Local original CMIP6 file mirrored from an authoritative archive.
  url: file:///badc/cmip6/data/CMIP6/.../tas_Amon_..._201501-210012.nc
reducer:
  name: xarray_subset
  parameters:
    variables: [tas]
    dimensions:
      time:
        index: 0
      lat:
        stride: 100
      lon:
        stride: 100
    backend_options:
      to_netcdf_kwargs:
        engine: h5netcdf
        encoding:
          tas:
            zlib: true
            complevel: 9
artifacts:
  - path: cmip6/tas-small.nc
    logical_name: cmip6/tas-small.nc
    max_size: 1048576
```

`h5py` should stay an implementation detail. The `netcdf` extra installs `h5netcdf`,
which uses `h5py` underneath and gives xarray a good HDF5/NetCDF4 writer without
recipes depending directly on h5py APIs.

`ncks_subset` is also available as an optional NCO-backed reducer for very large
local files where command-line subsetting is materially faster or lower-memory.

```yaml
source:
  kind: direct_url
  description: Local original CMIP6 file mirrored from an authoritative archive.
  url: file:///badc/cmip6/data/CMIP6/.../tas_Amon_..._201501-210012.nc
reducer:
  name: ncks_subset
  parameters:
    variables: [tas]
    dimensions:
      time:
        index: 0
      lat:
        stride: 100
      lon:
        stride: 100
    backend_options:
      compression_level: 9
      netcdf4_classic: true
artifacts:
  - path: cmip6/tas-small.nc
    logical_name: cmip6/tas-small.nc
    max_size: 1048576
```

For multiple source files, use `input_glob` and declare one artifact for each matched
file. This keeps output naming explicit and reviewable.

## Initial Workflow

```console
mcd list
mcd build recipes/example/hello-climate.yml
mcd validate recipes/example/hello-climate.yml
mcd build-registry
```

Publishing to the `data` branch should be owned by CI once repository permissions and release policy are settled.
