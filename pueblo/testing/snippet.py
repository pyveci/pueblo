import importlib
import typing as t
from pathlib import Path

import pytest


def fourty_two() -> int:
    """
    A dummy function to be patched by testing machinery.
    """
    return 42


def pytest_module_function(request: pytest.FixtureRequest, filepath: t.Union[str, Path], entrypoint: str = "main"):
    """
    From individual Python file, collect and wrap the `main` function into a test case.
    """
    from _pytest.monkeypatch import MonkeyPatch
    from _pytest.python import Function

    path = Path(filepath)

    # Temporarily add parent directory to module search path.
    with MonkeyPatch.context() as m:
        m.syspath_prepend(path.parent)

        # Import file as Python module.
        mod = importlib.import_module(path.stem)
        fun = getattr(mod, entrypoint)

        # Wrap the entrypoint function into a pytest test case, and run it.
        test = Function.from_parent(request.node, name=entrypoint, callobj=fun)
        test.runtest()
        return test.reportinfo()


def pytest_notebook(request: pytest.FixtureRequest, filepath: t.Union[str, Path]):
    """
    From individual Jupyter Notebook file, collect cells as pytest
    test cases, and run them.

    Not using `NBRegressionFixture`, because it would manually need to be configured.
    """
    from _pytest._py.path import LocalPath
    from pytest_notebook.plugin import pytest_collect_file

    tests = pytest_collect_file(LocalPath(filepath), request.node)
    if not tests:
        raise ValueError(f"No tests collected from notebook: {filepath}")
    infos = []
    for test in tests.collect():
        test.runtest()
        infos.append(test.reportinfo())
    return infos
