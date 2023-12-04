from pathlib import Path

from pueblo.testing.notebook import monkeypatch_pytest_notebook_treat_cell_exit_as_notebook_skip
from pueblo.testing.snippet import pytest_module_function, pytest_notebook

HERE = Path(__file__).parent
TESTDATA_FOLDER = HERE / "testdata" / "folder"
TESTDATA_SNIPPET = HERE / "testdata" / "snippet"


def test_monkeypatch_pytest_notebook_treat_cell_exit_as_notebook_skip():
    """
    Verify loading a monkeypatch supporting Jupyter Notebook testing.
    """
    monkeypatch_pytest_notebook_treat_cell_exit_as_notebook_skip()


def test_pytest_module_function(request, capsys):
    """
    Verify running an arbitrary Python function from an arbitrary Python file.
    """
    outcome = pytest_module_function(request=request, filepath=TESTDATA_FOLDER / "dummy.py")
    assert isinstance(outcome[0], Path)
    assert outcome[0].name == "dummy.py"
    assert outcome[1] == 0
    assert outcome[2] == "test_pytest_module_function.main"

    out, err = capsys.readouterr()
    assert out == "Hallo, Räuber Hotzenplotz.\n"


def test_pytest_notebook(request):
    """
    Verify executing code cells in an arbitrary Jupyter Notebook.
    """
    from _pytest._py.path import LocalPath

    outcomes = pytest_notebook(request=request, filepath=TESTDATA_FOLDER / "dummy.ipynb")
    assert isinstance(outcomes[0][0], LocalPath)
    assert outcomes[0][0].basename == "dummy.ipynb"
    assert outcomes[0][1] == 0
    assert outcomes[0][2] == "notebook: nbregression(dummy)"


def test_list_python_files():
    """
    Verify utility function for enumerating all Python files in given directory.
    """
    from pueblo.testing.folder import list_python_files, str_list

    outcome = str_list(list_python_files(TESTDATA_FOLDER))
    assert outcome == ["dummy.py"]


def test_list_notebooks():
    """
    Verify utility function for enumerating all Jupyter Notebook files in given directory.
    """
    from pueblo.testing.folder import list_notebooks, str_list

    outcome = str_list(list_notebooks(TESTDATA_FOLDER))
    assert outcome == ["dummy.ipynb"]


def test_notebook_injection():
    """
    Execute a Jupyter Notebook with custom code injected into a cell.
    """
    from testbook import testbook

    notebook = TESTDATA_SNIPPET / "notebook.ipynb"
    with testbook(str(notebook)) as tb:
        tb.inject(
            """
            import pandas as pd
            df = pd.DataFrame.from_dict({"baz": "qux"}, orient="index")
            """,
            run=True,
            after=3,
        )
        tb.execute()
        output = tb.cell_output_text(5)
        assert output == "0\nbaz  qux"


def test_notebook_patching():
    """
    Execute a Jupyter Notebook calling code which has been patched.
    """
    from testbook import testbook

    notebook = TESTDATA_SNIPPET / "notebook.ipynb"
    with testbook(str(notebook)) as tb:
        with tb.patch("pueblo.testing.snippet.fourty_two", return_value=33.33):
            tb.execute()
        output = tb.cell_output_text(6)
        assert output == "33.33"
