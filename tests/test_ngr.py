import sys
from functools import lru_cache
from pathlib import Path

import pytest
from click.testing import CliRunner

import pueblo.ngr.cli
from pueblo.util.fs import list_directories, relative_to

PROGRAM_NAME = "ngr"

HERE = Path(__file__).parent


@pytest.mark.ngr
def test_ngr_version():
    """
    Invoke `ngr --version`.
    """
    runner = CliRunner()

    result = runner.invoke(
        pueblo.ngr.cli,
        args="--version",
        catch_exceptions=False,
        prog_name=PROGRAM_NAME,
    )
    assert result.exit_code == 0


@lru_cache
def list_target_samples(path: Path):
    """
    Enumerate all example test directories, each is a minimal `ngr test` target.
    """
    samples = relative_to(list_directories(path, "ngr/*"), path)
    return [sample for sample in samples if ".pytest_cache" not in str(sample)]


@pytest.mark.ngr
@pytest.mark.parametrize("sample", list_target_samples(HERE), ids=map(str, list_target_samples(HERE)))
@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires Python 3.9 or higher")
def test_ngr_sample(sample: Path):
    """
    Invoke minimal `ngr test` target.
    """
    if str(sample) == "ngr/meltano" and sys.version_info >= (3, 13):
        raise pytest.skip("Meltano not available for Python 3.13 yet")

    runner = CliRunner()

    result = runner.invoke(
        pueblo.ngr.cli,
        args=f"test --accept-no-venv tests/{sample}",
        catch_exceptions=False,
        prog_name=PROGRAM_NAME,
    )
    assert result.exit_code == 0


def test_ngr_make():
    """
    Invoke minimal `ngr test` target.
    """
    runner = CliRunner()

    result = runner.invoke(
        pueblo.ngr.cli,
        args="test --accept-no-venv tests/ngr/make",
        catch_exceptions=False,
        prog_name=PROGRAM_NAME,
    )
    assert result.exit_code == 0
