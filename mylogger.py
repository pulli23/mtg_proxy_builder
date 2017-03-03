from typing import Optional, AnyStr, Union
import logging
import sys


class Logger(logging.Logger):
    VERBOSE_LOGGING = False

    def __init__(self, name: Optional[AnyStr] = None, verbose: Optional[bool] = None,
                 *args, **kwargs):
        if verbose is None:
            verbose = Logger.VERBOSE_LOGGING
        super().__init__(name, *args, **kwargs)
        self.verbose = verbose

    def log(self, level: Union[AnyStr, int], msg: str, verbose_msg: Optional[str] = None,
            *args, **kwargs):
        if self.verbose:
            super().log(level, verbose_msg, *args, **kwargs)
        super().log(level, msg, *args, **kwargs)

    def info(self, msg: str, verbose_msg: Optional[str] = None,
             *args, **kwargs):
        if self.verbose:
            super().info(verbose_msg, *args, **kwargs)
        super().info(msg, *args, **kwargs)

    def debug(self, msg: str, verbose_msg: Optional[str] = None,
              *args, **kwargs):
        if self.verbose:
            super().debug(verbose_msg, *args, **kwargs)
        super().debug(msg, *args, **kwargs)

    def warning(self, msg: str, verbose_msg: Optional[str] = None,
                *args, **kwargs):
        if self.verbose:
            super().warning(verbose_msg, *args, **kwargs)
        super().warning(msg, *args, **kwargs)

    def error(self, msg: str, verbose_msg: Optional[str] = None,
              *args, **kwargs):
        if self.verbose:
            super().error(verbose_msg, *args, **kwargs)
        super().error(msg, *args, **kwargs)

    def critical(self, msg: str, verbose_msg: Optional[str] = None,
                 *args, **kwargs):
        if self.verbose:
            super().critical(verbose_msg, *args, **kwargs)
        super().critical(msg, *args, **kwargs)


class LessThanFilter(logging.Filter):
    def __init__(self, exclusive_maximum, name=""):
        super(LessThanFilter, self).__init__(name)
        self.max_level = exclusive_maximum

    def filter(self, record):
        #non-zero return means we log this message
        return True if record.levelno < self.max_level else False

logging.setLoggerClass(Logger)

MAINLOGGER = logging.getLogger("main")

MAINLOGGER.setLevel(logging.DEBUG)

logging_handler_out = logging.StreamHandler(sys.stdout)
logging_handler_out.setLevel(logging.DEBUG)
logging_handler_out.addFilter(LessThanFilter(logging.WARNING))
MAINLOGGER.addHandler(logging_handler_out)

logging_handler_err = logging.StreamHandler(sys.stderr)
logging_handler_err.setLevel(logging.WARNING)
MAINLOGGER.addHandler(logging_handler_err)
