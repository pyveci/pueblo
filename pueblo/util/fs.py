import typing as t
from pathlib import Path


def relative_to(items: t.List[Path], path: Path) -> t.List[Path]:
    """
    Compute relative path to given directory.
    """
    return [item.relative_to(path) for item in items]


def list_files(path: Path, pattern: str) -> t.List[Path]:
    """
    Enumerate all files in given directory.
    """
    return list(path.glob(pattern))


def list_directories(path: Path, pattern: str) -> t.List[Path]:
    """
    Enumerate all directories in given directory.
    """
    items = list_files(path, pattern)
    return [item for item in items if item.is_dir()]
