import contextlib
import importlib.util
import logging
import sys
import typing as t
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import ModuleType
from urllib.parse import urlparse

from attrs import define

from pueblo.sfa.pep723 import collect_requirements

logger = logging.getLogger(__name__)


class InvalidTarget(Exception):
    """
    Raised when the target specification format is invalid.

    This exception is raised when the target string does not conform to the expected
    format of either a module path (e.g., 'acme.app:foo') or a file path
    (e.g., '/path/to/acme/app.py').
    """

    pass


@define
class ApplicationAddress:
    target: str
    property: str
    is_url: bool = False

    @classmethod
    def from_spec(cls, spec: str, default_property=None):
        """
        Parse entrypoint specification to application address instance.

        https://packaging.python.org/en/latest/specifications/entry-points/

        :param spec: Entrypoint address (e.g. module 'acme.app:main', file path '/path/to/acme/app.py:main')
        :param default_property: Name of the property to load if not specified in target (default: "api")
        :return:
        """
        is_url = False
        prop = None
        if cls.is_valid_url(spec):
            # Decode launch target location address from URL.
            # URL: https://example.org/acme/app.py#foo
            url = urlparse(spec)
            frag = url.fragment
            target = url.geturl().replace(f"#{frag}", "")
            prop = frag
            is_url = True

        else:
            # Decode launch target location address from Python module or path.
            # Module: acme.app:foo
            # Path:   /path/to/acme/app.py:foo
            target_fragments = spec.split(":")
            if len(target_fragments) > 1:
                target = target_fragments[0]
                prop = target_fragments[1]
            else:
                target = target_fragments[0]

        prop = prop or default_property
        if not prop:
            raise ValueError("Property can not be discovered, and no default property was supplied")

        return cls(target=target, property=prop, is_url=is_url)

    @staticmethod
    def is_valid_url(url) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False


@define
class SingleFileApplication:
    """
    Load Python code from any source, addressed by file path or module name.

    https://packaging.python.org/en/latest/specifications/entry-points/

    Warning:
        This component executes arbitrary Python code. Ensure the target is from a trusted
        source to prevent security vulnerabilities.

    Args:
        address: Application entrypoint address

    Example:
        >>> app = SingleFileApplication.from_spec("myapp.api:server")
        >>> app.load()
        >>> app.run()
    """  # noqa: E501

    address: ApplicationAddress
    _path: t.Optional[Path] = None
    _module: t.Optional[ModuleType] = None
    _entrypoint: t.Optional[t.Callable] = None

    @classmethod
    def from_spec(cls, spec: str, default_property=None):
        address = ApplicationAddress.from_spec(spec=spec, default_property=default_property)
        return cls(address=address)

    @property
    def path(self) -> Path:
        if self._path is None:
            raise ValueError("Path not defined")
        return self._path

    @property
    def entrypoint(self) -> t.Union[t.Callable[..., t.Any], None]:
        return self._entrypoint

    def run(self, *args, **kwargs):
        return t.cast(t.Callable, self._entrypoint)(*args, **kwargs)

    def load(self):
        target = self.address.target
        prop = self.address.property
        is_url = self.address.is_url

        # Sanity checks, as suggested by @coderabbitai. Thanks.
        if not is_url and (not target or (":" in target and len(target.split(":")) != 2)):
            raise InvalidTarget(
                f"Invalid target format: {target}. "
                "Use either a Python module entrypoint specification, "
                "a filesystem path, or a remote URL."
            )

        # Validate property name follows Python identifier rules.
        if not prop.isidentifier():
            raise ValueError(f"Invalid property name: {prop}")

        # Import launch target. Treat input location either as a filesystem path
        # (/path/to/acme/app.py), or as a module address specification (acme.app).
        # Optionally, install inline dependencies per PEP 723.
        self.load_any()
        with self.install():
            self.import_module()

        # Invoke launch target.
        msg_prefix = f"Failed to import: {target}"
        try:
            entrypoint = getattr(self._module, prop, None)
            if entrypoint is None:
                raise AttributeError(f"Module has no instance attribute '{prop}'")
            if not callable(entrypoint):
                raise TypeError(f"Entrypoint is not callable: {entrypoint}")
            self._entrypoint = entrypoint
        except AttributeError as ex:
            raise AttributeError(f"{msg_prefix}: {ex}") from ex
        except ImportError as ex:
            raise ImportError(f"{msg_prefix}: {ex}") from ex
        except TypeError as ex:
            raise TypeError(f"{msg_prefix}: {ex}") from ex
        except Exception as ex:
            raise RuntimeError(f"{msg_prefix}: Unexpected error: {ex}") from ex

    def install(self):

        if self._path is None:
            return contextlib.nullcontext()

        requirements = collect_requirements(self._path)
        if not requirements:
            return contextlib.nullcontext()

        import instld

        return instld(*requirements)

    def import_module(self):
        if self.path.is_file():
            mod = self.load_file(self.path)
        else:
            mod = importlib.import_module(self.address.target)

        self._module = mod

    def load_any(self):
        if self.address.is_url:
            import fsspec

            url = urlparse(self.address.target)
            url_path = Path(url.path)
            name = "_".join([url_path.parent.stem, url_path.stem])
            suffix = url_path.suffix
            app_file = NamedTemporaryFile(prefix=f"{name}_", suffix=suffix, delete=False)
            target = app_file.name
            logger.info(f"Loading remote single-file application, source: {url}")
            logger.info(f"Writing remote single-file application, target: {target}")
            fs = fsspec.open(f"simplecache::{self.address.target}")
            with fs as f:
                app_file.write(f.read())
            app_file.flush()
            self._path = Path(app_file.name)
        else:
            self._path = Path(self.address.target)
            if not self._path.is_file():
                sys.path += [str(Path.cwd())]
                module = importlib.util.find_spec(self.address.target)
                if module is not None and module.origin is not None:
                    self._path = Path(module.origin)

    @staticmethod
    def load_file(path: Path) -> ModuleType:
        """
        Load a Python file as a module using importlib.

        Args:
            path: Path to the Python file to load

        Returns:
            The loaded module object

        Raises:
            ImportError: If the module cannot be loaded
        """

        # Validate file extension
        if path.suffix != ".py":
            raise ValueError(f"File must have .py extension: {path}")

        # Use absolute path hash for uniqueness of name.
        unique_id = hash(str(path.absolute()))
        name = f"__{path.stem}_{unique_id}__"

        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed loading module from file: {path}")
        app = importlib.util.module_from_spec(spec)
        sys.modules[name] = app
        try:
            spec.loader.exec_module(app)
            return app
        except Exception as ex:
            sys.modules.pop(name, None)
            raise ImportError(f"Failed to execute module '{app}': {ex}") from ex


def run(spec: str, options: t.Dict[str, str]):
    app = SingleFileApplication.from_spec(spec=spec)
    app.load()
    return app.run()
