from __future__ import annotations

import sys
from types import SimpleNamespace

from mini_climate_data import fetching
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
    assert (
        registry_url(version="data-test")
        == "https://raw.githubusercontent.com/macpingu/mini-climate-data/data-test/registry.json"
    )


def test_fetch_loads_remote_registry_by_default(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "pooch", FakePoochModule)

    def fake_load_remote_registry(base_url: str, version: str) -> dict[str, str]:
        assert base_url == "https://raw.githubusercontent.com/macpingu/mini-climate-data/"
        assert version == "data"
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
