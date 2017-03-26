from typing import AnyStr, Union
import logging
import sys


class Logger(logging.Logger):
    def __init__(self, name: AnyStr = None, verbose: bool = None,
                 *args, **kwargs):
        if verbose is None:
            verbose = False
        super().__init__(name, *args, **kwargs)
        self.verbose = verbose

    def log(self, level: Union[AnyStr, int], msg: AnyStr = None,
            verbose_msg: AnyStr = None,
            *args, **kwargs):
        if msg is not None:
            super().log(level, msg, *args, **kwargs)
        if self.verbose and verbose_msg is not None:
            super().log(level, verbose_msg, *args, **kwargs)

    def info(self, msg: AnyStr = None, verbose_msg: AnyStr = None,
             *args, **kwargs):
        if msg is not None:
            super().info(msg, *args, **kwargs)
        if self.verbose and verbose_msg is not None:
            super().info(verbose_msg, *args, **kwargs)

    def debug(self, msg: AnyStr = None, verbose_msg: AnyStr = None,
              *args, **kwargs):
        if msg is not None:
            super().debug(msg, *args, **kwargs)
        if self.verbose and verbose_msg is not None:
            super().debug(verbose_msg, *args, **kwargs)

    def warning(self, msg: AnyStr = None, verbose_msg: AnyStr = None,
                *args, **kwargs):
        if msg is not None:
            super().warning(msg, *args, **kwargs)
        if self.verbose and verbose_msg is not None:
            super().warning(verbose_msg, *args, **kwargs)

    def error(self, msg: AnyStr = None, verbose_msg: AnyStr = None,
              *args, **kwargs):
        if msg is not None:
            super().error(msg, *args, **kwargs)
        if self.verbose and verbose_msg is not None:
            super().error(verbose_msg, *args, **kwargs)

    def critical(self, msg: AnyStr = None, verbose_msg: AnyStr = None,
                 *args, **kwargs):
        if msg is not None:
            super().critical(msg, *args, **kwargs)
        if self.verbose and verbose_msg is not None:
            super().critical(verbose_msg, *args, **kwargs)


class LessThanFilter(logging.Filter):
    def __init__(self, exclusive_maximum, name=""):
        super(LessThanFilter, self).__init__(name)
        self.max_level = exclusive_maximum

    def filter(self, record):
        return True if record.levelno < self.max_level else False

logging.setLoggerClass(Logger)

MAINLOGGER = logging.getLogger("main")

MAINLOGGER.setLevel(logging.DEBUG)

logging_handler_out = logging.StreamHandler(sys.stdout)
logging_handler_out.setLevel(logging.INFO)
logging_handler_out.addFilter(LessThanFilter(logging.WARNING))
MAINLOGGER.addHandler(logging_handler_out)
logging_handler_err = logging.StreamHandler(sys.stderr)
logging_handler_err.setLevel(logging.WARNING)
MAINLOGGER.addHandler(logging_handler_err)
