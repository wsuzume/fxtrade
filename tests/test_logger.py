import pytest

from logging import getLogger, Logger
from fxtrade.logger import is_logger

def test_is_logger():
    logger = getLogger('mylogger')

    assert is_logger(logger)

def test_Logger():
    logger = Logger('mylogger')

    assert is_logger(logger)