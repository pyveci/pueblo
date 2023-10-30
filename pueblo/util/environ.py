import getpass
import os

from dotenv import find_dotenv, load_dotenv


def getenvpass(env_var: str, prompt: str, skip_pytest_notebook: bool = True) -> None:
    """
    Read variable from environment or `.env` file.
    If it is not defined, prompt interactively.

    FIXME: Needs a patch to make it work with `pytest-notebook`,
           see https://github.com/chrisjsewell/pytest-notebook/issues/43.
    """
    load_dotenv(find_dotenv())
    if env_var not in os.environ:
        if "PYTEST_CURRENT_TEST" in os.environ and skip_pytest_notebook:
            import pytest

            pytest.exit(f"{env_var} not given [skip-notebook]")
        else:
            os.environ[env_var] = getpass.getpass(prompt)
