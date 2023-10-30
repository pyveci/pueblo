import os
from unittest import mock

import pytest

from pueblo.util.environ import getenvpass


@pytest.fixture(scope="function", autouse=True)
def init_testcase():
    """
    Make sure each test case uses a blank canvas.
    """
    if "ACME_API_KEY" in os.environ:
        del os.environ["ACME_API_KEY"]


def test_getenvpass_prompt(mocker):
    mocker.patch("getpass.getpass", return_value="foobar")
    getenvpass("ACME_API_KEY", "really?", skip_pytest_notebook=False)
    assert os.environ.get("ACME_API_KEY") == "foobar"


def test_getenvpass_environ():
    with mock.patch("getpass.getpass"), mock.patch("pytest.exit") as exit_mock:
        getenvpass("ACME_API_KEY", "really?")
        assert os.environ.get("ACME_API_KEY") is None
        exit_mock.assert_called_once_with(
            "ACME_API_KEY not given [skip-notebook]",
        )
