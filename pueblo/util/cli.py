import logging
import textwrap
import typing as t

from pueblo.util.logging import setup_logging

logger = logging.getLogger(__name__)


def boot_click(
    ctx: "click.Context", verbose: bool = False, debug: bool = False  # type: ignore[name-defined]  # noqa: F821
):
    """
    Bootstrap the CLI application.
    """

    # Adjust log level according to `verbose` / `debug` flags.
    log_level = logging.INFO
    if debug:
        log_level = logging.DEBUG

    # Setup logging, according to `verbose` / `debug` flags.
    setup_logging(level=log_level, verbose=verbose)


def docstring_format_verbatim(text: t.Optional[str]) -> str:
    """
    Format docstring to be displayed verbatim as a help text by Click.

    - https://click.palletsprojects.com/en/8.1.x/documentation/#preventing-rewrapping
    - https://github.com/pallets/click/issues/56
    """
    text = text or ""
    text = textwrap.dedent(text)
    lines = [line if line.strip() else "\b" for line in text.splitlines()]
    return "\n".join(lines)


def make_command(cli, name, helpfun, aliases=None):
    """
    Convenience shortcut for creating a subcommand.
    """
    return cli.command(
        name,
        help=docstring_format_verbatim(helpfun.__doc__),
        context_settings={"max_content_width": 100},
        aliases=aliases,
    )
