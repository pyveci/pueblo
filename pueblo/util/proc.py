import subprocess
import typing as t
from contextlib import contextmanager

import psutil


@contextmanager
def process(*args, **kwargs) -> t.Generator[subprocess.Popen, None, None]:
    """
    Wrapper around `subprocess.Popen` to also terminate child processes after exiting.

    Implementation by Pedro Cattori. Thanks!
    -- https://gist.github.com/jizhilong/6687481#gistcomment-3057122
    """
    proc = subprocess.Popen(*args, **kwargs)  # noqa: S603
    try:
        yield proc
    finally:
        try:
            children = psutil.Process(proc.pid).children(recursive=True)
        except psutil.NoSuchProcess:
            return
        for child in children:
            child.kill()
        proc.kill()
