import contextlib
import logging
import shlex
import shutil
import subprocess
import sys
import typing as t
from abc import abstractmethod
from pathlib import Path

from pueblo.ngr.model import ItemType
from pueblo.ngr.util import is_venv, mp, run_command

logger = logging.getLogger()


class RunnerBase:
    def __init__(self, path: Path, options: t.Dict) -> None:
        self.path = path
        self.options = options
        self.type: t.Optional[ItemType] = None
        if hasattr(self, "__post_init__"):
            self.__post_init__()
        self.has_makefile = mp(self.path, "Makefile")
        self.peek()

    def run(self) -> None:
        # Change working directory to designated path.
        # From there, address paths relatively.

        with contextlib.chdir(self.path):
            self.path = Path(".")

            logger.info("Environment Information")
            self.info()
            logger.info("Installing")
            self.install()
            logger.info("Testing")
            self.test()

    @abstractmethod
    def peek(self) -> None:
        raise NotImplementedError("Method must be implemented")

    @abstractmethod
    def info(self) -> None:
        pass

    @abstractmethod
    def install(self) -> None:
        raise NotImplementedError("Method must be implemented")

    @abstractmethod
    def test(self) -> None:
        raise NotImplementedError("Method must be implemented")


class DotNetRunner(RunnerBase):
    """
    .NET test suite runner.

    - Knows how to invoke `dotnet {restore,list,test}` appropriately.
    - Optionally accepts the `--npgsql-version=` command-line option, to specify the Npgsql version.
    """

    def __post_init__(self) -> None:
        self.has_csproj: t.Optional[bool] = None
        self.framework: t.Optional[str] = None

    def peek(self) -> None:
        self.has_csproj = mp(self.path, "*.csproj")

        dotnet_version_full = subprocess.check_output(shlex.split("dotnet --version")).decode().strip()  # noqa: S603
        dotnet_version_major = dotnet_version_full[0]
        self.framework = f"net{dotnet_version_major}.0"

        if self.has_csproj:
            self.type = ItemType.DOTNET

    def info(self) -> None:
        """
        Display environment information.
        """
        run_command("dotnet --version")
        run_command("dotnet --info")

    def install(self) -> None:
        """
        Install dependencies from `.csproj` file.
        """
        self.adjust_npgql_version()
        run_command("dotnet restore")
        run_command("dotnet list . package")

    def adjust_npgql_version(self):
        if "npgsql_version" not in self.options:
            logger.info("[MATRIX] Not modifying Npgsql version")
            return
        npgsql_version = self.options.get("npgsql_version")
        logger.info(f"[MATRIX] Modifying Npgsql version: {npgsql_version}")
        cmd = f"""
            sed -E 's!<PackageReference Include="Npgsql" Version=".+?" />!<PackageReference Include="Npgsql" Version="{npgsql_version}" />!' \
            -i demo.csproj
        """  # noqa: E501
        run_command(cmd)

    def test(self) -> None:
        """
        Invoke `dotnet test`, with code coverage tracking.
        """
        run_command(f'dotnet test --framework={self.framework} --collect:"XPlat Code Coverage"')


class ElixirRunner(RunnerBase):
    """
    Basic Elixir runner.

    Currently, just knows to invoke `hex` and `mix` within a directory.
    """

    def __post_init__(self) -> None:
        self.mix_project: t.Optional[bool] = None

    def peek(self) -> None:
        self.mix_project = mp(self.path, "mix.exs")

        if self.mix_project:
            self.type = ItemType.ELIXIR

    def install(self) -> None:
        """
        Install package manager, and project dependencies.
        """
        run_command("mix local.hex --force --if-missing")
        run_command("mix deps.get")

    def test(self) -> None:
        """
        Run test suite.
        """
        run_command("mix test")


class GolangRunner(RunnerBase):
    """
    Basic Golang runner.

    Currently, just knows to invoke `go {build,test}` within a directory.
    """

    def __post_init__(self) -> None:
        self.has_go_mod: t.Optional[bool] = None

    def peek(self) -> None:
        self.has_go_mod = mp(self.path, "go.mod")

        if self.has_go_mod:
            self.type = ItemType.GOLANG

    def install(self) -> None:
        """
        Invoke `go build`.
        """
        run_command("go build")

    def test(self) -> None:
        """
        Invoke `go test -v`.
        """
        run_command("go test -v")


class HaskellRunner(RunnerBase):
    """
    Basic Haskell runner.

    Currently, just knows to invoke `stack {build,test}` within a directory.
    """

    def __post_init__(self) -> None:
        self.has_cabal_file: t.Optional[bool] = None

    def peek(self) -> None:
        self.has_cabal_file = mp(self.path, "*.cabal")

        if self.has_cabal_file:
            self.type = ItemType.HASKELL

    def install(self) -> None:
        """
        Install project dependencies.
        """
        run_command("stack build")

    def test(self) -> None:
        """
        Run test suite.
        """
        run_command("stack test")


class JavaRunner(RunnerBase):
    """
    Java test suite runner.

    - Knows how to invoke either Gradle or Maven.
    """

    def __post_init__(self) -> None:
        self.has_pom_xml: t.Optional[bool] = None
        self.has_gradle_files: t.Optional[bool] = None

    def peek(self) -> None:
        self.has_pom_xml = mp(self.path, "pom.xml")
        self.has_gradle_files = mp(self.path, "*.gradle")

        if self.has_pom_xml or self.has_gradle_files:
            self.type = ItemType.JAVA

    def info(self) -> None:
        """
        Display environment information.
        """
        run_command("java -version")

    def install(self) -> None:
        """
        Install dependencies.
        """
        if self.has_pom_xml:
            run_command("mvn install")
        elif self.has_gradle_files:
            if shutil.which("gradle"):
                run_command("gradle wrapper")
            run_command("./gradlew install")
        else:
            raise NotImplementedError("Unable to invoke target: install")

    def test(self) -> None:
        """
        Invoke software tests.
        """
        if self.has_makefile:
            run_command("make test")
        elif self.has_pom_xml:
            run_command("mvn test")
        elif self.has_gradle_files:
            run_command("./gradlew check")
        else:
            raise NotImplementedError("Unable to invoke target: test")


class JavaScriptRunner(RunnerBase):
    """
    Basic runner for JavaScript projects.

    Currently, just knows to invoke `npm {install,test}` within a directory.
    """

    def __post_init__(self) -> None:
        self.has_package_json: t.Optional[bool] = None

    def peek(self) -> None:
        self.has_package_json = mp(self.path, "package.json")

        if self.has_package_json:
            self.type = ItemType.JAVASCRIPT

    def install(self) -> None:
        """
        Invoke `npm install`.
        """
        run_command("npm install")

    def test(self) -> None:
        """
        Invoke `npm test`.
        """
        run_command("npm test")


class JuliaRunner(RunnerBase):
    """
    Basic runner for Julia projects.

    Currently, just knows to invoke `Pkg.{build,test}` within a directory.
    """

    def __post_init__(self) -> None:
        self.has_project_toml: t.Optional[bool] = None

    def peek(self) -> None:
        self.has_project_toml = mp(self.path, "Project.toml")

        if self.has_project_toml:
            self.type = ItemType.JULIA

    def install(self) -> None:
        """
        Invoke `Pkg.build()`.
        """
        run_command("julia --project=. --depwarn=error --eval='using Pkg; Pkg.build()'")

    def test(self) -> None:
        """
        Invoke `Pkg.test()`.
        """
        run_command("julia --project=. --depwarn=error --eval='using Pkg; Pkg.test()'")


class MakeRunner(RunnerBase):
    """
    Basic Make runner.

    Currently, just knows to invoke `make test` within a directory.
    """

    def peek(self) -> None:
        if self.has_makefile:
            self.type = ItemType.MAKE

    def install(self) -> None:
        """
        Effectively an optional noop, but let's try.
        """
        try:
            run_command("make install")
        except Exception:
            logger.exception("Command failed: make install")

    def test(self) -> None:
        """
        Invoke `make test`.
        """
        run_command("make test")


class PhpRunner(RunnerBase):
    """
    Basic PHP runner.

    Currently, just knows to invoke `composer` within a directory.
    """

    def __post_init__(self) -> None:
        self.has_composer_json: t.Optional[bool] = None

    def peek(self) -> None:
        self.has_composer_json = mp(self.path, "composer.json")

        if self.has_composer_json:
            self.type = ItemType.PHP

    def install(self) -> None:
        """
        Install dependencies of PHP Composer package.
        """
        run_command("composer install")

    def test(self) -> None:
        """
        Invoke a script called `test`, defined in `composer.json`.
        """
        run_command("composer run test")


class PythonRunner(RunnerBase):
    """
    Basic Python runner.

    Currently, just knows to invoke `pytest` within a directory.

    # TODO: Need to run within a virtualenv to be isolated from the parent environment.
    """

    def __post_init__(self) -> None:
        self.has_python_files: t.Optional[bool] = None
        self.has_setup_py: t.Optional[bool] = None
        self.has_setup_cfg: t.Optional[bool] = None
        self.has_pyproject_toml: t.Optional[bool] = None
        # TODO: Rename to `is_poetry`, by introspecting `pyproject.toml` for `[tool.poetry]`.
        self.has_poetry_lock: t.Optional[bool] = None
        self.has_requirements_txt: t.Optional[bool] = None

    def peek(self) -> None:
        self.has_python_files = mp(self.path, "*.py")
        self.has_setup_py = mp(self.path, "setup.py")
        self.has_setup_cfg = mp(self.path, "setup.cfg")
        self.has_pyproject_toml = mp(self.path, "pyproject.toml")
        self.has_poetry_lock = mp(self.path, "poetry.lock")
        self.has_requirements_txt = mp(self.path, "requirements*.txt")
        self.is_pipx_installed = shutil.which("pipx")
        self.is_poetry_installed = shutil.which("poetry")

        if self.has_python_files or self.has_setup_py or self.has_pyproject_toml or self.has_requirements_txt:
            self.type = ItemType.PYTHON

    def run(self) -> None:
        # Sanity check. When invoking a Python thing within a sandbox,
        # don't install system-wide.
        if not is_venv():
            if not self.options.get("accept_no_venv", False):
                logger.error("Unable invoke target without virtualenv. Use `--accept-no-venv` to override.")
                sys.exit(1)

        return super().run()

    def install(self) -> None:
        """
        Install dependencies of Python thing, based on its shape.

        TODO: Heuristically figure out which "extra" packages to install from the outside.
              Example names for minimal test/development dependencies: dev,devel,tests,testing.
        """
        requirements_txt = list(self.path.glob("requirements*.txt"))
        if requirements_txt:
            pip_requirements_args = [f"-r {item}" for item in requirements_txt]
            pip_cmd = f"pip install {' '.join(pip_requirements_args)}"
            run_command(pip_cmd)

        if self.has_poetry_lock:
            # TODO: Add list of extras.
            # TODO: Poetry also knows dependency groups, e.g. `--with=test`.
            if not self.is_poetry_installed:
                if not self.is_pipx_installed:
                    run_command("pip install pipx")
                run_command("pipx install poetry")
            try:
                run_command("poetry install --with=test")
            except Exception:
                run_command("poetry install")

        elif self.has_pyproject_toml or self.has_setup_cfg or self.has_setup_py:
            # By default, assume to run `pip install`.
            pip_install = True

            # `pyproject.toml` files are sometimes only used for configuring tools,
            # but not for defining project metadata. When still trying to install,
            # they will error out like `error: Multiple top-level modules discovered
            # in a flat-layout`.
            if self.has_pyproject_toml:
                pyproject_toml_file = self.path / "pyproject.toml"
                pyproject_toml = pyproject_toml_file.read_text()
                if "[project]" not in pyproject_toml:
                    pip_install = False

            if pip_install:
                run_command("pip install --editable='.[develop,test]'")

    def test(self) -> None:
        """
        Test a Python thing, based on which test runner is installed.

        TODO: Figure out how to invoke target `poe check`, which is popular amongst
              users of `pueblo`. It bundles linter/checkstyle and software test targets
              into a single entrypoint, similar to what `gradle check` is doing.
        """

        if self.has_poetry_lock:
            # TODO: poetry run which pytest
            run_command("poetry run pytest --config-file=.")

        else:
            has_pytest = shutil.which("pytest") is not None
            if has_pytest:
                run_command("pytest")
            else:
                raise NotImplementedError("No handler to invoke Python item")


class RubyRunner(RunnerBase):
    """
    Basic Ruby runner.

    Currently, just knows to invoke Bundler and Rake within a directory.

    - https://bundler.io/
    - https://en.wikipedia.org/wiki/Rake_(software)
    """

    def __post_init__(self) -> None:
        self.has_gemfile: t.Optional[bool] = None
        self.has_rakefile: t.Optional[bool] = None

    def peek(self) -> None:
        self.has_gemfile = mp(self.path, "Gemfile")
        self.has_rakefile = mp(self.path, "Rakefile")

        if self.has_gemfile or self.has_rakefile:
            self.type = ItemType.RUBY

    def install(self) -> None:
        """
        Install dependencies using Ruby's Bundler, defined in `Gemfile`.
        """
        run_command("bundle install")

    def test(self) -> None:
        """
        Invoke a rake target called `test`, defined in `Rakefile`.
        """
        run_command("bundle exec rake test")


class RustRunner(RunnerBase):
    """
    Basic Rust runner.

    Currently, just knows to invoke `cargo {build,run}` within a directory.
    """

    def __post_init__(self) -> None:
        self.has_cargo_toml: t.Optional[bool] = None

    def peek(self) -> None:
        self.has_cargo_toml = mp(self.path, "Cargo.toml")

        if self.has_cargo_toml:
            self.type = ItemType.RUST

    def install(self) -> None:
        """
        Invoke `cargo build`.
        """
        run_command("cargo build")

    def test(self) -> None:
        """
        Invoke `cargo test`.
        """
        run_command("cargo test")
