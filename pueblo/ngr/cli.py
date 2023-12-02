import argparse
import logging
import sys
from argparse import ArgumentDefaultsHelpFormatter

from pueblo import __version__, setup_logging
from pueblo.ngr.core import run

logger = logging.getLogger()


def read_command_line_arguments(args=None, prog_name=None):
    """
    Parse and return command line arguments.
    """
    parser = argparse.ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, prog=prog_name)
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        help="print package version of pueblo/ngr",
        version=f"%(prog)s ({__version__})",
    )

    subparsers = parser.add_subparsers(dest="command")

    test = subparsers.add_parser("test", help="Invoke test suites")
    test.add_argument("target")
    test.add_argument("--accept-no-venv", action="store_true", help="Whether to accept not running in venv")
    test.add_argument("--dotnet-version", type=str, help=".NET version, like `net6.0`, `net7.0`, or `5.0.x`, `6.0.x`")
    test.add_argument("--npgsql-version", type=str, help="Version of Npgsql")

    return parser, parser.parse_args(args=args)


def main(args=None, prog_name=None):
    """
    Main program.

    - Setup logging.
    - Read command-line parameters.
    - Run sanity checks.
    - Invoke runner.
    """
    setup_logging()
    parser, args = read_command_line_arguments(args=args, prog_name=prog_name)
    if not args.command:
        logger.error("Unable to invoke subcommand: Not given or empty")
        parser.print_help()
        sys.exit(1)
    if not args.target:
        logger.error("Unable to invoke target: Not given or empty")
        parser.print_help()
        sys.exit(1)

    try:
        run(args.target, args.__dict__)
    except NotImplementedError as ex:
        logger.critical(ex)
        sys.exit(1)
