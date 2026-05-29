.PHONY: help install dev test lint format build clean data-init data-build data-validate data-registry data-clean data-status data-publish

PYTHON ?= python
PIP ?= $(PYTHON) -m pip
CONFIG_VALUE = $(PYTHON) src/mini_climate_data/config.py $(1)
DATA_BRANCH ?= $(shell $(call CONFIG_VALUE,DEFAULT_DATA_BRANCH))
DATA_WORKTREE ?= $(shell $(call CONFIG_VALUE,DEFAULT_DATA_WORKTREE))
DATA_RECIPES ?= $(shell $(call CONFIG_VALUE,DEFAULT_RECIPE_ROOT))
SOURCE_CACHE ?= $(shell $(call CONFIG_VALUE,DEFAULT_SOURCE_CACHE))

help:
	@printf "Available targets:\n"
	@printf "  install        Install the package\n"
	@printf "  dev            Install editable development dependencies\n"
	@printf "  test           Run the test suite\n"
	@printf "  lint           Run ruff checks\n"
	@printf "  format         Format and fix lint issues\n"
	@printf "  build          Build package artifacts\n"
	@printf "  clean          Remove local build/test caches\n"
	@printf "  data-init      Create or reuse the data worktree\n"
	@printf "  data-build     Build all recipes into the data worktree\n"
	@printf "  data-validate  Validate data worktree artifacts\n"
	@printf "  data-registry  Write registry.json in the data worktree\n"
	@printf "  data-clean     Remove declared generated data files\n"
	@printf "  data-status    Show data worktree git status\n"
	@printf "  data-publish   Commit and push generated data\n"
	@printf "\nData variables: DATA_BRANCH=%s DATA_WORKTREE=%s DATA_RECIPES=%s SOURCE_CACHE=%s\n" "$(DATA_BRANCH)" "$(DATA_WORKTREE)" "$(DATA_RECIPES)" "$(SOURCE_CACHE)"

install:
	$(PIP) install .

dev:
	$(PIP) install -e ".[dev,all]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

build:
	$(PYTHON) -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache

data-init:
	mcd data init --branch $(DATA_BRANCH) --worktree $(DATA_WORKTREE)

data-build:
	mcd data build-all --branch $(DATA_BRANCH) --worktree $(DATA_WORKTREE) --source-cache $(SOURCE_CACHE) --recipes $(DATA_RECIPES)

data-validate:
	mcd data validate --branch $(DATA_BRANCH) --worktree $(DATA_WORKTREE) --recipes $(DATA_RECIPES)

data-registry:
	mcd data registry --branch $(DATA_BRANCH) --worktree $(DATA_WORKTREE) --recipes $(DATA_RECIPES)

data-clean:
	mcd data clean --branch $(DATA_BRANCH) --worktree $(DATA_WORKTREE) --recipes $(DATA_RECIPES) --yes

data-status:
	mcd data status --branch $(DATA_BRANCH) --worktree $(DATA_WORKTREE)

data-publish:
	mcd data publish --branch $(DATA_BRANCH) --worktree $(DATA_WORKTREE)
