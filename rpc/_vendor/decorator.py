import datetime
import time
import traceback
import uuid

from .config import TerminalColor
from .log import logging


def selfPrint(*args, debug=0, **kargs):
    kargs["stacklevel"] = kargs.get("stacklevel", 0) + 4
    if debug:
        logging.debug(*args, **kargs)
    else:
        logging.info(*args, **kargs)


TimeFormater = "%Y-%m-%d %H:%M:%S.%f"


def formatTimerString(uid, funcname, mark, cost=None, start=None, end=None):
    justSize = 0
    return f"{TerminalColor.GREEN}    Function: {str(funcname).ljust(justSize)}     Mark: {mark.ljust(justSize)} {(':%s' % cost) if cost else ''}    {('Start:%s' % start) if start else ''}  {('End:%s' % end) if end else ''}"


def secs2date(seconds):
    return datetime.datetime.fromtimestamp(seconds)


def timeFunc(func):
    def timeit_wrapper(*args, **kwargs):
        uid = ""
        infoFunc = selfPrint
        funcname = str(func.__qualname__ if callable(func) and hasattr(func, "__qualname__") else type(func))
        infoFunc(formatTimerString(uid, funcname, "start"))
        startTime = time.time()
        startNs = time.perf_counter_ns()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise e
        finally:
            infoFunc(formatTimerString(uid, funcname, "END", cost=f"{'{:,.1f}'.format((time.perf_counter_ns() - startNs)/10**6)}ms", start=secs2date(startTime)))

    timeit_wrapper.__doc__ = func.__doc__
    return timeit_wrapper


class Timer:
    def __init__(self, string="", func=None, debug=0):
        self.mark = string
        self.func = func or selfPrint
        self.isDebug = debug
        self.funcname = traceback.extract_stack()[-2][2]
        self.uuid = str(uuid.uuid4()) + " Timer".ljust(6)

    def __call__(self):
        return (time.perf_counter_ns() - self._start_time) / 10**6

    def __enter__(self):
        self._start_t = time.time()
        self._start_time = time.perf_counter_ns()
        self.func(
            formatTimerString(self.uuid, self.funcname, self.mark + " Timer start", "", "", ""),
            **(dict(debug=self.isDebug) if self.func is selfPrint else {}),
        )
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.func(
            formatTimerString(
                self.uuid,
                self.funcname,
                self.mark + " Timer END",
                format(float(self()), ",") + "ms",
                secs2date(self._start_t).strftime(TimeFormater),
                "",
            ),
            **(dict(debug=self.isDebug) if self.func is selfPrint else {}),
        )
