.PHONY: install dev test lint format build clean data-init data-build data-validate data-registry data-clean data-status data-publish

PYTHON ?= python
PIP ?= $(PYTHON) -m pip
DATA_BRANCH ?= data
DATA_WORKTREE ?= .worktrees/data
DATA_RECIPES ?= recipes

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
	mcd data build-all --branch $(DATA_BRANCH) --worktree $(DATA_WORKTREE) --recipes $(DATA_RECIPES)

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
