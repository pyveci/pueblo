import logging
import sys
import warnings

from pueblo.ngr.core import run
from pueblo.util.program import MiniRunner

logger = logging.getLogger()


class NGRRunner(MiniRunner):

    def configure(self):
        subparsers = self.parser.add_subparsers(dest="command")

        test = subparsers.add_parser("test", help="Invoke test suite")
        test.add_argument("target")
        test.add_argument("--accept-no-venv", action="store_true", help="Whether to accept not running in venv")
        test.add_argument(
            "--dotnet-version", type=str, help=".NET version, like `net6.0`, `net7.0`, or `5.0.x`, `6.0.x`"
        )
        test.add_argument("--gradle-wrapper", action="store_true", help="Regenerate Gradle wrapper")
        test.add_argument("--npgsql-version", type=str, help="Version of Npgsql")

    def run(self):
        if not self.args.target:
            logger.error("Unable to invoke target: Not given or empty")
            self.parser.print_help()
            sys.exit(1)

        if self.args.accept_no_venv:
            warnings.warn("The `--accept-no-venv` option is deprecated and will be ignored.", stacklevel=2)

        try:
            run(self.args.target, self.args.__dict__)
        except NotImplementedError as ex:
            logger.critical(ex)
            sys.exit(1)


def main(args=None, prog_name=None):
    """
    Main program.

    - Setup logging.
    - Read command-line parameters.
    - Run sanity checks.
    - Invoke runner.
    """
    runner = NGRRunner(name=prog_name, args_input=args)
    return runner.run()
