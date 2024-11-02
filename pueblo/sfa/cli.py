import logging
import sys

from pueblo import setup_logging
from pueblo.sfa.core import run
from pueblo.util.program import MiniRunner

logger = logging.getLogger()


class SFARunner(MiniRunner):

    def configure(self):
        subparsers = self.parser.add_subparsers(dest="command")

        subcommand_run = subparsers.add_parser("run", help="Invoke application")
        subcommand_run.add_argument("target")

    def run(self):
        if not self.args.target:
            logger.error("Unable to invoke target: Not given or empty")
            self.parser.print_help()
            sys.exit(1)

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
    setup_logging()
    runner = SFARunner(name=prog_name, args_input=args)
    return runner.run()
