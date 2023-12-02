from pathlib import Path

import pytest


@pytest.fixture
def readme_file() -> Path:
    return Path(__file__).parent.parent / "README.md"


def get_readme_url(infix: str = "", scheme: str = "https:") -> str:
    return f"{scheme}//github.com/pyveci/pueblo/{infix}README.md"


@pytest.fixture
def readme_url_https_raw() -> str:
    return get_readme_url(infix="raw/main/")


@pytest.fixture
def readme_url_github_https_bare() -> str:
    return get_readme_url(scheme="github+https:")


@pytest.fixture
def readme_url_github_https_raw() -> str:
    return get_readme_url(infix="raw/main/", scheme="github+https:")


@pytest.fixture
def readme_url_github_https_blob() -> str:
    return get_readme_url(infix="blob/main/", scheme="github+https:")
