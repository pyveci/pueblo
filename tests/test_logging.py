import sys

from pueblo.util.logging import setup_logging, tweak_log_levels


def test_setup_logging_default():
    setup_logging()


def test_setup_logging_no_colorlog(mocker):
    mocker.patch.dict(sys.modules, {"colorlog": None})
    setup_logging()


def test_tweak_log_levels():
    tweak_log_levels()
