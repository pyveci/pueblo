from pathlib import Path

import pandas as pd
from dask.utils import is_dataframe_like
from pandas._testing import raise_assert_detail

from pueblo.testing.notebook import monkeypatch_pytest_notebook_treat_cell_exit_as_notebook_skip
from pueblo.testing.snippet import pytest_module_function, pytest_notebook

HERE = Path(__file__).parent


def test_monkeypatch_pytest_notebook_treat_cell_exit_as_notebook_skip():
    monkeypatch_pytest_notebook_treat_cell_exit_as_notebook_skip()


def test_pytest_module_function(request, capsys):
    outcome = pytest_module_function(request=request, filepath=HERE / "testing" / "dummy.py")
    assert isinstance(outcome[0], Path)
    assert outcome[0].name == "dummy.py"
    assert outcome[1] == 0
    assert outcome[2] == "test_pytest_module_function.main"

    out, err = capsys.readouterr()
    assert out == "Hallo, Räuber Hotzenplotz.\n"


def test_pytest_notebook(request):
    from _pytest._py.path import LocalPath

    outcomes = pytest_notebook(request=request, filepath=HERE / "testing" / "dummy.ipynb")
    assert isinstance(outcomes[0][0], LocalPath)
    assert outcomes[0][0].basename == "dummy.ipynb"
    assert outcomes[0][1] == 0
    assert outcomes[0][2] == "notebook: nbregression(dummy)"


def test_list_python_files():
    from pueblo.testing.folder import list_python_files, str_list

    outcome = str_list(list_python_files(HERE / "testing"))
    assert outcome == ["dummy.py"]


def test_list_notebooks():
    from pueblo.testing.folder import list_notebooks, str_list

    outcome = str_list(list_notebooks(HERE / "testing"))
    assert outcome == ["dummy.ipynb"]


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
