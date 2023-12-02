import pytest
from pathlibfs import Path as PathPlus

from pueblo.io import to_io
from pueblo.io.universal import path_without_scheme

README_NEEDLE = "A Python toolbox library"


def test_to_io_failure():
    with pytest.raises(TypeError) as ex:
        with to_io(None):
            pass
    assert ex.match("Unable to converge to IO handle. type=<class 'NoneType'>, value=None")


def test_to_io_file(readme_file):
    with to_io(readme_file) as fp:
        content = fp.read()
        assert README_NEEDLE in content


def test_to_io_memory(readme_file):
    infile = open(readme_file, "r")
    with to_io(infile) as fp:
        content = fp.read()
        assert README_NEEDLE in content


def test_to_io_url(readme_url_https_raw):
    with to_io(readme_url_https_raw) as fp:
        content = fp.read()
        assert README_NEEDLE in content


def test_to_io_github_url_bare(readme_url_github_https_bare):
    with to_io(readme_url_github_https_bare) as fp:
        content = fp.read()
        assert README_NEEDLE in content


def test_to_io_github_url_raw(readme_url_github_https_raw):
    with to_io(readme_url_github_https_raw) as fp:
        content = fp.read()
        assert README_NEEDLE in content


def test_to_io_github_url_blob(readme_url_github_https_blob):
    with to_io(readme_url_github_https_blob) as fp:
        content = fp.read()
        assert README_NEEDLE in content


def test_path_without_scheme_absolute():
    assert path_without_scheme("foo://localhost/bar/baz") == PathPlus("file:////localhost/bar/baz")


def test_path_without_scheme_relative():
    assert path_without_scheme("/bar/baz") == PathPlus("file:///bar/baz")
