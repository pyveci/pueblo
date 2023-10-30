from pueblo.util.environ import getenvpass
from pueblo.util.logging import setup_logging

try:
    from importlib.metadata import PackageNotFoundError, version
except (ImportError, ModuleNotFoundError):  # pragma:nocover
    from importlib_metadata import PackageNotFoundError, version  # type: ignore[no-redef]

__appname__ = "pueblo"

try:
    __version__ = version(__appname__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"