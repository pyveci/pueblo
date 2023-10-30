import importlib
import logging
import sys


def setup_logging(level=logging.INFO, verbose: bool = False):
    try:
        importlib.import_module("colorlog")
        setup_logging_colorlog(level=level, verbose=verbose)
    except ImportError:
        setup_logging_standard(level=level, verbose=verbose)


def setup_logging_standard(level=logging.INFO, verbose: bool = False):
    log_format = "%(asctime)-15s [%(name)-26s] %(levelname)-8s: %(message)s"
    logging.basicConfig(format=log_format, stream=sys.stderr, level=level)


def setup_logging_colorlog(level=logging.INFO, verbose: bool = False):
    import colorlog
    from colorlog.escape_codes import escape_codes

    reset = escape_codes["reset"]
    log_format = f"%(asctime)-15s [%(name)-26s] %(log_color)s%(levelname)-8s:{reset} %(message)s"

    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(log_format))

    logging.basicConfig(format=log_format, level=level, handlers=[handler])


def tweak_log_levels():
    logging.getLogger("urllib3.connectionpool").setLevel(level=logging.INFO)
