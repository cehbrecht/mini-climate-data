from __future__ import annotations

import pytest

from mini_climate_data.reducers import REDUCERS
from mini_climate_data.reducers.base import Reducer


def test_registered_reducers_implement_base_api() -> None:
    assert REDUCERS
    assert all(isinstance(reducer, Reducer) for reducer in REDUCERS.values())


def test_reducer_base_class_requires_build() -> None:
    with pytest.raises(TypeError):
        Reducer()
