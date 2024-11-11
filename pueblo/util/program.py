import argparse
import logging
import sys
import typing as t
from argparse import ArgumentDefaultsHelpFormatter

from pueblo import __version__, setup_logging

logger = logging.getLogger()


class MiniRunner:

    def __init__(self, name: t.Any, args_input: t.Any):

        self.name = name
        self.args_input = args_input

        self._parser: t.Optional[argparse.ArgumentParser] = None
        self._parsed_args: t.Optional[argparse.Namespace] = None
        self._runner: t.Optional[t.Callable] = None

        self.setup()

    @property
    def parser(self) -> argparse.ArgumentParser:
        if self._parser is None:
            raise RuntimeError("Command line parser not initialized")
        return self._parser

    @property
    def args(self) -> argparse.Namespace:
        if self._parsed_args is None:
            raise RuntimeError("Command line arguments not parsed")
        return self._parsed_args

    def setup(self):
        self.setup_cli()
        self.configure()
        self.read_cli()

    def setup_cli(self):
        self._parser = argparse.ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, prog=self.name)
        self._parser.add_argument(
            "-V",
            "--version",
            action="version",
            help="print package version",
            version=f"%(prog)s ({__version__})",
        )

    def configure(self):
        pass

    def read_cli(self):
        """
        Parse and return command line arguments.
        """
        self._parsed_args = self.parser.parse_args(args=self.args_input)

    def start(self):
        self.boot()
        self.run()

    def boot(self):
        """
        Main program.

        - Setup logging.
        - Read command-line parameters.
        - Run sanity checks.
        - Invoke runner.
        """
        setup_logging()
        self.read_cli()
        if not self.args.command:
            logger.error("Unable to invoke subcommand: Not given or empty")
            self.parser.print_help()
            sys.exit(1)

    def run(self):
        pass
