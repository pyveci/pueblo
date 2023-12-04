# ruff: noqa: E402
import dataclasses
import typing as t

import magic
import pytest

pytest.importorskip("pathlibfs")
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


@dataclasses.dataclass
class RemoteFile:
    url: str
    mimetypes: t.List[str]


def remote_files() -> t.List[RemoteFile]:
    return [
        RemoteFile(
            url="https://github.com/daq-tools/skeem/raw/main/tests/testdata/basic.ods",
            mimetypes=["application/vnd.oasis.opendocument.spreadsheet"],
        ),
        RemoteFile(
            url="github://daq-tools:skeem@/tests/testdata/basic.ods",
            mimetypes=["application/vnd.oasis.opendocument.spreadsheet"],
        ),
        RemoteFile(
            url="github+https://github.com/daq-tools/skeem/raw/main/tests/testdata/basic.ods",
            mimetypes=["application/vnd.oasis.opendocument.spreadsheet"],
        ),
        RemoteFile(
            url="gs://gcp-public-data-landsat/LC08/01/001/003/LC08_L1GT_001003_20140812_20170420_01_T2/LC08_L1GT_001003_20140812_20170420_01_T2_B3.TIF",
            mimetypes=["image/tiff"],
        ),
        RemoteFile(
            url="s3://fmi-gridded-obs-daily-1km/Netcdf/Tday/tday_2023.nc",
            mimetypes=["application/x-netcdf", "application/octet-stream"],
        ),
    ]


@pytest.mark.parametrize("remote_file", remote_files(), ids=[rf.url for rf in remote_files()])
def test_to_io_remote_files(remote_file):
    with to_io(remote_file.url, mode="rb") as fp:
        content = fp.read(100)
        mimetype = magic.from_buffer(content, mime=True)
        assert mimetype in remote_file.mimetypes
