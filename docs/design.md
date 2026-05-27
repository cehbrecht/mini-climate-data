# Design

`mini-climate-data` separates authoritative source from generated data.

The `main` branch contains package code, recipes, reducers, validation, tests, and documentation. It is the source of truth for how each tiny dataset is produced.

The `data` branch is a disposable generated cache. It contains reduced artifacts and a registry for downstream consumers. It should not be manually edited, merged back into `main`, or treated as authoritative.

Generated climate artifacts are deliberately excluded from the Python package. The package should contain code, recipe definitions, schemas, and lightweight metadata only. Consumers fetch data by logical name through `pooch`.

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
  name: subset_netcdf
  parameters:
    variables: [tas]
    time: 2000-01-01
```

The scaffold includes `write_text` for smoke tests. The first real reducer is
`ncks_subset`, a small wrapper around NCO's `ncks` command. It deliberately avoids
dataset-specific hard-coding: recipes name the local source file or glob, variables,
dimension selectors, compression, and output artifacts.

```yaml
source:
  kind: direct_url
  description: Local original CMIP6 file mirrored from an authoritative archive.
  url: file:///badc/cmip6/data/CMIP6/.../tas_Amon_..._201501-210012.nc
reducer:
  name: ncks_subset
  parameters:
    variable: tas
    selectors:
      - dimension: time
        start: 0
      - dimension: lat
        stride: 100
      - dimension: lon
        stride: 100
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
