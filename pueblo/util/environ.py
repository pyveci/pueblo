import getpass
import os
import typing as t

from dotenv import find_dotenv, load_dotenv


def init_dotenv():
    """
    Find `.env` file and load environment variables.
    """
    load_dotenv(find_dotenv())


def getenvpass(env_var: str, prompt: t.Union[str, None] = None, skip_pytest_notebook: bool = True) -> None:
    """
    Read variable from environment or `.env` file.
    If it is not defined, prompt interactively.

    FIXME: Needs a patch to make it work with `pytest-notebook`,
           see https://github.com/chrisjsewell/pytest-notebook/issues/43.
    """

    init_dotenv()
    if env_var not in os.environ:
        if "PYTEST_CURRENT_TEST" in os.environ and skip_pytest_notebook:
            import pytest

            pytest.exit(f"{env_var} not given [skip-notebook]")
        elif prompt:
            os.environ[env_var] = getpass.getpass(prompt)
