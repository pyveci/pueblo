from pathlib import Path

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
