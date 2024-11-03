from pathlib import Path

HERE = Path(__file__).parent
TESTDATA_FOLDER = HERE / "testdata" / "folder"
TESTDATA_SNIPPET = HERE / "testdata" / "snippet"


def test_monkeypatch_pytest_notebook_treat_cell_exit_as_notebook_skip():
    """
    Verify loading a monkeypatch supporting Jupyter Notebook testing.
    """
    from pueblo.testing.notebook import monkeypatch_pytest_notebook_treat_cell_exit_as_notebook_skip

    monkeypatch_pytest_notebook_treat_cell_exit_as_notebook_skip()


def test_pytest_module_function(request, capsys):
    """
    Verify running an arbitrary Python function from an arbitrary Python file.
    """
    from pueblo.testing.snippet import pytest_module_function

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

    from pueblo.testing.snippet import pytest_notebook

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


def test_folder_list_notebooks():
    """
    Verify utility function for enumerating all Jupyter Notebook files in given directory.
    """
    from pueblo.testing.folder import list_notebooks, str_list

    outcome = str_list(list_notebooks(TESTDATA_FOLDER))
    assert outcome == ["dummy.ipynb"]


def test_notebook_list_notebooks():
    """
    Verify recursive Jupyter Notebook enumerator utility.
    """
    from pueblo.testing.notebook import list_notebooks

    outcome = list_notebooks(TESTDATA_FOLDER)
    assert outcome[0].name == "dummy.ipynb"


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


def pytest_generate_tests(metafunc):
    """
    Generate test cases for Jupyter Notebooks, one test case per .ipynb file.
    """
    from pueblo.testing.notebook import generate_notebook_tests, generate_tests, list_notebooks

    # That's for testing. "foobar" and "bazqux" features are never used.
    generate_tests(metafunc, path=TESTDATA_FOLDER, fixture_name="foobar")
    generate_notebook_tests(metafunc, notebook_paths=list_notebooks(TESTDATA_FOLDER), fixture_name="bazqux")

    # That's for real.
    generate_notebook_tests(metafunc, notebook_paths=list_notebooks(TESTDATA_FOLDER))


def test_notebook_run_direct(notebook):
    """
    Execute Jupyter Notebook, one test case per .ipynb file.
    """
    from testbook import testbook

    with testbook(notebook) as tb:
        tb.execute()


def test_notebook_run_api(notebook):
    """
    Execute Jupyter Notebook using API.
    """
    from pueblo.testing.notebook import run_notebook

    run_notebook(notebook)
