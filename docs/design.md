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

## Initial Workflow

```console
mini-climate-data list
mini-climate-data build recipes/example/hello-climate.yml
mini-climate-data validate recipes/example/hello-climate.yml
mini-climate-data build-registry
```

Publishing to the `data` branch should be owned by CI once repository permissions and release policy are settled.
