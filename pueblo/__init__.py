from pueblo.util.logging import setup_logging

try:
    from importlib.metadata import PackageNotFoundError, version  # ty: ignore[unresolved-import]
except (ImportError, ModuleNotFoundError):  # pragma:nocover
    from importlib_metadata import PackageNotFoundError, version  # ty: ignore[unresolved-import]

__appname__ = "pueblo"

try:
    __version__ = version(__appname__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
