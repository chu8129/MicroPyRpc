import logging as _logging
import sys

from .config import TerminalColor


class CustomFormatter(_logging.Formatter):
    format = f"  %(asctime)s %(name)s %(levelname)s (file:%(filename)s:%(lineno)d|func:%(funcName)s):    {TerminalColor.RESET}    %(message)s "

    FORMATS = {
        _logging.DEBUG: TerminalColor.WHITE + format + TerminalColor.RESET,
        _logging.INFO: TerminalColor.YELLOW + format + TerminalColor.RESET,
        _logging.WARNING: TerminalColor.RED + format + TerminalColor.RESET,
        _logging.ERROR: TerminalColor.BOLDRED + format + TerminalColor.RESET,
        _logging.CRITICAL: TerminalColor.HEADER + format + TerminalColor.RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = _logging.Formatter(log_fmt)
        return formatter.format(record)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def singleton(class_):
    class classSingleton(class_, metaclass=Singleton):
        pass

    classSingleton.__name__ = class_.__name__
    classSingleton.__doc__ = class_.__doc__
    return classSingleton


@singleton
class Logger:
    preSetParam = dict(stacklevel=3)

    def __init__(self):
        self.uuid = ""
        self.rootlogger = _logging.getLogger("rpc")
        self.rootlogger.propagate = False
        self.rootlogger.setLevel(self.get_level())

        if not self.rootlogger.handlers:
            streamHandler = _logging.StreamHandler(sys.stdout)
            streamHandler.setFormatter(self.get_formatter())
            streamHandler.setLevel(self.get_level())
            self.rootlogger.addHandler(streamHandler)

    def get_formatter(self):
        return CustomFormatter()

    def get_level(self):
        return _logging.INFO

    def debug(self, info, *args, **kwargs):
        kargs = self.preSetParam.copy()
        kargs.update(kwargs)
        self.rootlogger.debug(f":{self.uuid} > {info}", *args, **kargs)

    def info(self, info, *args, **kwargs):
        kargs = self.preSetParam.copy()
        kargs.update(kwargs)
        self.rootlogger.info(f":{self.uuid} > {info}", *args, **kargs)

    def warning(self, info, *args, **kwargs):
        kargs = self.preSetParam.copy()
        kargs.update(kwargs)
        self.rootlogger.warning(f":{self.uuid} > {info}", *args, **kargs)

    def error(self, info, *args, **kwargs):
        kargs = self.preSetParam.copy()
        kargs.update(kwargs)
        self.rootlogger.error(f":{self.uuid} > {info}", *args, **kargs)

    def critical(self, info, *args, **kwargs):
        kargs = self.preSetParam.copy()
        kargs.update(kwargs)
        self.rootlogger.critical(f":{self.uuid} > {info}", *args, **kargs)

    def logging(self, *args, **kargs):
        return self.info(*args, **kargs)


logging = log = Logger()
