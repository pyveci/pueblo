import logging

import click
from click_aliases import ClickAliasedGroup

from pueblo.util.cli import boot_click

logger = logging.getLogger(__name__)


def help_pueblo():
    """
    Pueblo - a Python toolbox library.

    pueblo --version
    """  # noqa: E501


@click.group(cls=ClickAliasedGroup)
@click.version_option(package_name="pueblo")
@click.option("--verbose", is_flag=True, required=False, help="Turn on logging")
@click.option("--debug", is_flag=True, required=False, help="Turn on logging with debug level")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, debug: bool):
    return boot_click(ctx, verbose, debug)
