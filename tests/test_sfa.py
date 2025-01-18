# ruff: noqa: S603, S607
import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.sfa


from pueblo.sfa.core import ApplicationAddress, SingleFileApplication  # noqa: E402


def test_address_module():
    address = ApplicationAddress.from_spec("acme.app:main")
    assert address.target == "acme.app"
    assert address.property == "main"
    assert address.is_url is False


def test_address_path():
    address = ApplicationAddress.from_spec("/path/to/acme/app.py:main")
    assert address.target == "/path/to/acme/app.py"
    assert address.property == "main"
    assert address.is_url is False


def test_address_url():
    address = ApplicationAddress.from_spec("https://example.org/acme/app.py#main")
    assert address.target == "https://example.org/acme/app.py"
    assert address.property == "main"
    assert address.is_url is True


@pytest.mark.parametrize(
    "spec",
    [
        "tests.sfa.basic:main",
        "tests/sfa/basic.py:main",
        "https://github.com/pyveci/pueblo/raw/refs/heads/sfa/tests/sfa/basic.py#main",
    ],
)
def test_application_api_success(capsys, spec):
    if spec.startswith("https:"):
        pytest.importorskip("fsspec")
    app = SingleFileApplication.from_spec(spec)
    app.load()
    outcome = app.run()

    assert outcome == 42
    assert "Räuber Hotzenplotz" in capsys.readouterr().out


@pytest.mark.parametrize(
    "spec",
    [
        "pueblo.context:pueblo_cache_path",
        "pueblo/context.py:pueblo_cache_path",
        "https://github.com/pyveci/pueblo/raw/refs/heads/main/pueblo/context.py#pueblo_cache_path",
    ],
)
def test_application_api_not_callable(capsys, spec):
    if spec.startswith("https:"):
        pytest.importorskip("fsspec")
    app = SingleFileApplication.from_spec(spec)
    with pytest.raises(TypeError) as ex:
        app.load()
    assert ex.match("Failed to import: .+: Entrypoint is not callable")


@pytest.mark.parametrize(
    "spec",
    [
        "tests.sfa.basic:main",
        "tests/sfa/basic.py:main",
        "https://github.com/pyveci/pueblo/raw/refs/heads/sfa/tests/sfa/basic.py#main",
    ],
)
def test_application_cli(mocker, capfd, spec):
    if spec.startswith("https:"):
        pytest.importorskip("fsspec")
    mocker.patch.dict(os.environ, {"PYTHONPATH": str(Path.cwd())})
    subprocess.check_call(["sfa", "run", spec])
    assert "Räuber Hotzenplotz" in capfd.readouterr().out


def test_application_cli_non_callable(capfd):
    subprocess.call(["sfa", "run", "pueblo.context:pueblo_cache_path"])
    assert "TypeError: Failed to import: pueblo.context: Entrypoint is not callable" in capfd.readouterr().err
