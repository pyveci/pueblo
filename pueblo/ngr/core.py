"""
-----
About
-----

Next Generation Runner (ngr): Effortless invoke programs and test harnesses.

-------
Backlog
-------
- After a few iterations, refactor to separate package.
- Look at https://pypi.org/project/ur/
"""
import logging
import os
import typing as t
from pathlib import Path

from pueblo.ngr.model import ItemType
from pueblo.ngr.runner import (
    DotNetRunner,
    ElixirRunner,
    GolangRunner,
    HaskellRunner,
    JavaRunner,
    JavaScriptRunner,
    JuliaRunner,
    MakeRunner,
    MeltanoRunner,
    PhpRunner,
    PythonRunner,
    RubyRunner,
    RunnerBase,
    RustRunner,
)

logger = logging.getLogger()


class NextGenerationRunner:
    """
    Run a <thing> based on its shape.
    """

    def __init__(self, thing: t.Any, options: t.Dict) -> None:
        self.thing = thing
        self.options = options
        self.path = Path(self.thing)
        self.runner: t.Optional[RunnerBase] = None
        self.type: t.Optional[ItemType] = None
        self.runners = {
            # Language runners, listed alphabetically.
            ItemType.DOTNET: DotNetRunner,
            ItemType.ELIXIR: ElixirRunner,
            ItemType.GOLANG: GolangRunner,
            ItemType.HASKELL: HaskellRunner,
            ItemType.JAVA: JavaRunner,
            ItemType.JAVASCRIPT: JavaScriptRunner,
            ItemType.JULIA: JuliaRunner,
            ItemType.MELTANO: MeltanoRunner,
            ItemType.PHP: PhpRunner,
            ItemType.PYTHON: PythonRunner,
            ItemType.RUBY: RubyRunner,
            ItemType.RUST: RustRunner,
            # Makefile runner, as fallback.
            ItemType.MAKE: MakeRunner,
        }
        self.identify()

    @property
    def runner_names(self):
        names = []
        for runner in self.runners.keys():
            names.append(runner.name)
        return names

    def identify(self) -> None:
        """
        Identify type of <thing>.
        """
        for type_, class_ in self.runners.items():
            logger.info(f"Probing: type={type_}, class={class_}")
            try:
                self.runner = class_(path=self.path, options=self.options)  # type: ignore[abstract]
                self.type = self.runner.type
            except Exception:
                logger.exception("Unknown error")
            if self.type is not None:
                break

        if self.type is None:
            raise NotImplementedError(
                f"Unable to identify invocation target. "
                f"Supported types: {self.runner_names}. "
                f"Target path: {self.path} "
                f"Current path: {os.getcwd()}"
            )

    def run(self) -> None:
        """
        Invoke / run <thing>.
        """
        if self.path.exists():
            if self.path.is_file():
                raise NotImplementedError(f"Invoking a file is not implemented yet ;]: {self.path}")
            elif self.path.is_dir():  # noqa: RET506
                type_name = self.type and self.type.name or None
                logger.info(f"Invoking {type_name} in directory: {self.path}")
                if self.runner is not None:
                    self.runner.run()
                else:
                    raise RuntimeError("No runner found")
            else:
                raise ValueError(f"Path is neither file nor directory: {self.path}")


def run(thing: t.Any, options: t.Dict) -> None:
    """
    Invoke the runner with a single argument, the <thing>.
    """
    ngr = NextGenerationRunner(thing=thing, options=options)
    return ngr.run()
