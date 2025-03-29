from logging import DEBUG, getLogger, Formatter, StreamHandler
from logging.handlers import TimedRotatingFileHandler

from pathlib import Path
from typing import Iterable, Optional, Union

from .core import type_checked

def default_formatter():
    return Formatter(
                '| %(name)s | %(asctime)s | %(levelname)s : %(message)s |',
                datefmt='%Y-%m-%d %H:%M:%S %z'
           )

def console_handler(level=DEBUG, formatter=None):
    if formatter is None:
        formatter = default_formatter()

    handler = StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)
    
    return handler
    
def file_handler(filename, level=DEBUG, formatter=None):
    if formatter is None:
        formatter = default_formatter()

    handler = TimedRotatingFileHandler(filename=filename, when='D', interval=1)
    handler.setLevel(level)
    handler.setFormatter(formatter)

    return handler

def get_default_logger(name, handler, level=DEBUG):
    logger = getLogger(name)

    # logger is already initialized
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(level)
    logger.propagate = False

    if not isinstance(handler, Iterable):
        logger.addHandler(handler)
    else:
        for h in handler:
            logger.addHandler(h)
    
    return logger

def is_logger(x):
    def check_attr(x, attr):
        if not hasattr(x, attr):
            raise AttributeError(f"Logger object must have attribute '{attr}'.")
    
    check_attr(x, 'debug')
    check_attr(x, 'info')
    check_attr(x, 'warning')
    check_attr(x, 'error')
    check_attr(x, 'critical')
    check_attr(x, 'log')

    return True

class Logger:
    def __init__(self,
                 name: str,
                 data_dir: Optional[Union[str, Path]]):
        self._name = type_checked(name, str)
        self._data_dir = Path(data_dir) if data_dir is not None else None
        #self._logfile_name = self._data_dir / 'log'

        if self._name == '':
            raise ValueError("root logger not allowed.")

        handler = [ console_handler() ]

        # if self._data_dir is not None:
        #     handler.append(file_handler(self.filename))

        self._logger = get_default_logger(self._name, handler)
    
    @property
    def name(self):
        return self._name

    @property
    def filename(self):
        return self._logfile_name

    @property
    def logger(self):
        return self._logger
    
    def isEnabledFor(self, level):
        return self._logger.isEnabledFor(level)

    def debug(self, msg, *args, **kwargs):
        return self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        return self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        return self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        return self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        return self._logger.critical(msg, *args, **kwargs)
    
    def log(self, level, msg, *args, **kwargs):
        return self._logger.log(level, msg, *args, **kwargs)