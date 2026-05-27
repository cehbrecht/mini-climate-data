# Design

`mini-climate-data` separates authoritative source from generated data.

The `main` branch contains package code, recipes, reducers, validation, tests, and documentation. It is the source of truth for how each tiny dataset is produced.

The `data` branch is a disposable generated cache. It contains reduced artifacts and a registry for downstream consumers. It should not be manually edited, merged back into `main`, or treated as authoritative.

Generated climate artifacts are deliberately excluded from the Python package. The package should contain code, recipe definitions, schemas, and lightweight metadata only. Consumers fetch data by logical name through `pooch`.

## Recipe Contract

Each recipe records:

- source provenance, license, and citation where applicable
- reducer script and parameters
- expected artifacts and logical names
- strict maximum artifact sizes
- validation checks
- checksums after artifacts are built

## Source Types

Recipes should make the original source explicit, but the source block should not force all providers into one access pattern.

Supported source kinds:

- `synthetic`: generated entirely by the reducer
- `direct_url`: a stable URL points directly to an original file
- `intake`: an intake catalog URL and entry identify the original dataset
- `stac`: a STAC catalog URL identifies the search/catalog source, intended for ESGF2-style catalogs

A Copernicus Climate Data Store recipe using the current CDS intake catalog should look like this:

```yaml
source:
  kind: intake
  provenance: Copernicus Climate Data Store via the cp4cds C3S intake manifest.
  license: Copernicus C3S data license
  catalog_url: https://raw.githubusercontent.com/cp4cds/c3s_34g_manifests/master/intake/catalogs/c3s.yaml
  entry: some_catalog_entry
  parameters:
    # Provider-specific intake parameters go here.
```

Reducers can open the entry with `mini_climate_data.sources.open_intake_source`, then apply their own small, explicit reduction.

## Initial Workflow

```console
mini-climate-data list
mini-climate-data build recipes/example/hello-climate.yml
mini-climate-data validate recipes/example/hello-climate.yml
mini-climate-data build-registry
```

Publishing to the `data` branch should be owned by CI once repository permissions and release policy are settled.
