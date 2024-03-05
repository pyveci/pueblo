import typing as t
from pathlib import Path

import pytest


def monkeypatch_pytest_notebook_treat_cell_exit_as_notebook_skip():
    """
    Patch `pytest-notebook`, in fact `nbclient.client.NotebookClient`,
    to propagate cell-level `pytest.exit()` invocations as signals
    to mark the whole notebook as skipped.

    In order not to be too intrusive, the feature only skips notebooks
    when being explicitly instructed, by adding `[skip-notebook]` at the
    end of the `reason` string. Example:

        import pytest
        if "ACME_API_KEY" not in os.environ:
            pytest.exit("ACME_API_KEY not given [skip-notebook]")

    https://github.com/chrisjsewell/pytest-notebook/issues/43
    """
    from nbclient.client import NotebookClient
    from nbclient.exceptions import CellExecutionError
    from nbformat import NotebookNode

    async_execute_cell_dist = NotebookClient.async_execute_cell

    async def async_execute_cell(
        self,
        cell: NotebookNode,
        cell_index: int,
        execution_count: t.Optional[int] = None,
        store_history: bool = True,
    ) -> NotebookNode:
        try:
            return await async_execute_cell_dist(
                self,
                cell,
                cell_index,
                execution_count=execution_count,
                store_history=store_history,
            )
        except CellExecutionError as ex:
            if ex.ename == "Exit" and ex.evalue.endswith("[skip-notebook]"):
                raise pytest.skip(ex.evalue) from ex
            else:  # noqa: RET506
                raise

    NotebookClient.async_execute_cell = async_execute_cell  # type: ignore[method-assign,unused-ignore]


def list_path(path: Path, suffix: str = ".ipynb"):
    """
    Enumerate all Jupyter Notebook files found in given directory.
    """
    for item in path.iterdir():
        if item.suffix == suffix:
            yield item


def generate_tests(metafunc, paths: t.Union[t.List[Path], None] = None, path: t.Union[Path, None] = None):
    """
    Generate test cases for Jupyter Notebooks.
    To be used from `pytest_generate_tests`.
    """
    if path:
        paths = list(list_path(path))
    elif paths:
        paths = list(paths)
    else:
        raise ValueError("Path is missing")
    if "notebook" in metafunc.fixturenames:
        names = [nb_path.name for nb_path in paths]
        metafunc.parametrize("notebook", paths, ids=names)
