import logging
import shlex
import subprocess
import sys
import typing as t
from pathlib import Path

logger = logging.getLogger()


def mp(path: Path, pattern: str) -> bool:
    """
    mp -- match path.

    Evaluate if path matches pattern, i.e. if the `glob` operation on a
    path yields any results.
    """
    return len(list(path.glob(pattern))) > 0


def run_command(command: str, errors="raise") -> t.Union[bool, Exception]:
    """
    A basic convenience wrapper around `subprocess.check_call`.
    """
    logger.info(f"Running command: {command}")
    try:
        subprocess.check_call(shlex.split(command))  # noqa: S603
    except subprocess.CalledProcessError as ex:
        if errors == "return":
            return ex
        elif errors == "bool":  # noqa: RET505
            return False
        else:
            raise
    return True


def setup_logging_old(level=logging.INFO, verbose: bool = False) -> None:
    """
    Set up logging subsystem.
    """
    log_format = "%(asctime)-15s [%(name)-10s] %(levelname)-8s: %(message)s"

    if verbose:
        level = logging.DEBUG
    logging.basicConfig(format=log_format, stream=sys.stderr, level=level)


def is_venv():
    """
    Identify whether the runner was invoked within a Python virtual environment.

    https://stackoverflow.com/a/42580137
    """
    return hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
