# ruff: noqa: E402
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
from dask.utils import is_dataframe_like
from pandas._testing import raise_assert_detail

HERE = Path(__file__).parent


def assert_shape_equal(left: pd.DataFrame, right: pd.DataFrame, obj: str = "DataFrame"):
    if left.shape != right.shape:
        raise_assert_detail(obj, f"{obj} shape mismatch", f"{repr(left.shape)}", f"{repr(right.shape)}")


def test_dataframe_factory_dummy():
    from pueblo.testing.dataframe import DataFrameFactory

    dff = DataFrameFactory(rows=42, columns=4)
    frame_reference = pd.DataFrame.from_records([{"abc": "def", "ghi": "jkl"}])
    frame_generated = dff.make("dummy")
    assert is_dataframe_like(frame_generated)
    assert_shape_equal(frame_reference, frame_generated)


def test_dataframe_factory_mixed():
    from pueblo.testing.dataframe import DataFrameFactory

    dff = DataFrameFactory(rows=42, columns=4)
    frame_reference = pd.DataFrame.from_dict(
        {
            "A": range(5),
            "B": range(5),
            "C": range(5),
            "D": range(5),
        }
    )
    frame_generated = dff.make("mixed")
    assert is_dataframe_like(frame_generated)
    assert_shape_equal(frame_reference, frame_generated)


def test_dataframe_factory_dateindex():
    from pueblo.testing.dataframe import DataFrameFactory

    dff = DataFrameFactory(rows=42, columns=4)
    frame_reference = pd.DataFrame.from_dict(
        {
            "A": range(42),
            "B": range(42),
            "C": range(42),
            "D": range(42),
        }
    )
    frame_generated = dff.make("dateindex")
    assert is_dataframe_like(frame_generated)
    assert_shape_equal(frame_reference, frame_generated)


def test_dataframe_factory_wide():
    from pueblo.testing.dataframe import DataFrameFactory

    dff = DataFrameFactory(rows=42, columns=4)
    frame_reference = pd.DataFrame.from_dict(
        {
            "A": range(42),
            "B": range(42),
            "C": range(42),
            "D": range(42),
        }
    )
    frame_generated = dff.make("wide")
    assert is_dataframe_like(frame_generated)
    assert_shape_equal(frame_reference, frame_generated)

    assert "time" in frame_generated.index.names
    assert "tag" in frame_generated.columns
