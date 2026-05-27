from __future__ import annotations

import sys
from types import SimpleNamespace

from mini_climate_data.fetching import fetch


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
