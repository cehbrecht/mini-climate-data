from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

from mini_climate_data import fetching
from mini_climate_data.config import (
    DEFAULT_BASE_URL,
    DEFAULT_DATA_BRANCH,
    ENV_BASE_URL,
    ENV_CONFIG,
    ENV_DATA_VERSION,
    REGISTRY_NAME,
    Settings,
    config_value,
    configured_base_url,
    configured_data_version,
    load_config,
)
from mini_climate_data.fetching import fetch, load_remote_registry, registry_url


class FakePoochModule:
    @staticmethod
    def os_cache(name: str) -> str:
        return f"/tmp/{name}"

    @staticmethod
    def create(**kwargs):
        return SimpleNamespace(fetch=lambda name: (name, kwargs))


def test_fetch_defaults_to_data_branch(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "pooch", FakePoochModule)

    name, kwargs = fetch(
        "cmip6/tas-small.nc",
        registry={"cmip6/tas-small.nc": "sha256:" + "a" * 64},
    )

    assert name == "cmip6/tas-small.nc"
    assert (
        kwargs["base_url"] == "https://raw.githubusercontent.com/macpingu/mini-climate-data/data/"
    )


def test_registry_url_uses_configured_version() -> None:
    assert registry_url(version="data-test") == f"{DEFAULT_BASE_URL}data-test/{REGISTRY_NAME}"


def test_configured_fetch_settings_read_environment(monkeypatch) -> None:
    monkeypatch.setenv(ENV_BASE_URL, "https://example.test/base")
    monkeypatch.setenv(ENV_DATA_VERSION, "data-preview")

    assert configured_base_url() == "https://example.test/base/"
    assert configured_data_version() == "data-preview"


def test_config_value_returns_string_constant() -> None:
    assert config_value("DEFAULT_DATA_BRANCH") == DEFAULT_DATA_BRANCH


def test_user_config_overrides_packaged_defaults(tmp_path, monkeypatch) -> None:
    user_config = tmp_path / "mini-climate-data.toml"
    user_config.write_text(
        """
[data_store]
branch = "data-preview"

[fetch]
base_url = "https://example.test/data"

[registry]
name = "custom-registry.json"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG, str(user_config))

    config = load_config()

    assert config["stores"]["default"]["branch"] == "data-preview"
    assert config["stores"]["default"]["worktree"] == ".worktrees/data"
    assert config["stores"]["default"]["base_url"] == "https://example.test/data"
    assert config["stores"]["default"]["registry"] == "custom-registry.json"


def test_named_store_config_can_resolve_registry_url(tmp_path: Path) -> None:
    config_path = tmp_path / "stores.toml"
    config_path.write_text(
        """
[stores.atlas]
base_url = "https://example.test/atlas"
branch = "published"
worktree = ".worktrees/atlas"
recipe_root = "recipes/c3s-cica-atlas"
registry = "atlas-registry.json"
""",
        encoding="utf-8",
    )
    settings = Settings.load(config_path)

    assert settings.store("atlas").source_cache == ".cache/mini-climate-data/sources"
    assert (
        registry_url(store="atlas", settings=settings)
        == "https://example.test/atlas/published/atlas-registry.json"
    )


def test_fetch_loads_remote_registry_by_default(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "pooch", FakePoochModule)

    def fake_load_remote_registry(
        base_url: str,
        version: str,
        *,
        store: str | None = None,
        settings: Settings | None = None,
    ) -> dict[str, str]:
        assert base_url == DEFAULT_BASE_URL
        assert version == DEFAULT_DATA_BRANCH
        assert store is None
        assert settings is not None
        return {"example/hello-climate.txt": "sha256:" + "b" * 64}

    monkeypatch.setattr(fetching, "load_remote_registry", fake_load_remote_registry)

    name, kwargs = fetch("example/hello-climate.txt")

    assert name == "example/hello-climate.txt"
    assert kwargs["registry"] == {"example/hello-climate.txt": "sha256:" + "b" * 64}


def test_load_remote_registry(monkeypatch) -> None:
    class Response:
        def read(self) -> bytes:
            return b'{"example/hello-climate.txt": "sha256:abc"}'

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

    def fake_urlopen(url: str) -> Response:
        assert url == "https://example.test/data/registry.json"
        return Response()

    monkeypatch.setattr(fetching, "urlopen", fake_urlopen)

    assert load_remote_registry("https://example.test", "data") == {
        "example/hello-climate.txt": "sha256:abc"
    }
