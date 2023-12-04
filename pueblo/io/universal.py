import contextlib
import io
import typing as t
from pathlib import Path

from pathlibfs import Path as PathPlus
from yarl import URL


@contextlib.contextmanager
def to_io(source: t.Union[str, Path, t.IO], mode: t.Literal["r", "rb", "rt"] = "rt") -> t.Generator[t.IO, None, None]:
    """
    Converge filesystem path, remote URL, or file-like object into an IO handle.
    """
    fp: t.IO
    if isinstance(source, io.TextIOWrapper):
        fp = source
    elif isinstance(source, (str, Path, PathPlus)):
        source = str(source)
        path = open_url(source)
        fp = path.open(mode=mode)
    else:
        raise TypeError(f"Unable to converge to IO handle. type={type(source)}, value={source}")
    yield fp
    fp.close()


def open_url(url: str) -> PathPlus:
    """
    Access URL, with specific handling for GitHub URLs.

    When approached using a GitHub HTTP URL, converge it to a pathlibfs / fsspec URL,
    and open it.

    Input URLs
    ----------
    github+https://foobar:ghp_lalala@github.com/acme/sweet-camino/path/to/document.md
    github+https://foobar:ghp_lalala@github.com/acme/sweet-camino/blob/main/path/to/document.md

    Output Path
    -----------
    fs = Path("github://path/to/document.md", username="foobar", token="ghp_lalala", org="acme", repo="sweet-camino")
    """
    uri = None
    try:
        uri = URL(url)
    except ValueError as ex:
        if "host is required for absolute urls" in str(ex):
            pass
        else:
            raise

    if uri and uri.scheme.startswith("github+https"):
        path_fragments = uri.path.split("/")[1:]
        path_kwargs = {
            "username": uri.user,
            "token": uri.password,
            "org": path_fragments[0],
            "repo": path_fragments[1],
        }

        real_path_fragments = path_fragments[2:]
        if path_fragments[2] in ["blob", "raw"]:
            real_path_fragments = path_fragments[4:]

        downstream_url = "github://" + "/".join(real_path_fragments)
        path = PathPlus(downstream_url, **path_kwargs)

    else:
        kwargs = {}
        if url.startswith("s3://"):
            kwargs["anon"] = True
        path = PathPlus(url, **kwargs)
    return path


def path_without_scheme(url_like: str) -> PathPlus:
    """
    Return a pathlibfs Path, without the scheme.
    """
    url = URL(str(url_like))
    if url.is_absolute():
        url = url.with_scheme("")
    return PathPlus(str(url))
