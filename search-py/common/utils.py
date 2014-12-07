from calendar import timegm
from datetime import datetime, timedelta
import logging
import os
import sys
import common

def get_base_dir():
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def add_lib_path(path = None):
    libpath = os.path.join(common.get_base_dir(), 'libs')
    if not path is None:
        libpath = os.path.join(libpath, path)
    if not libpath in sys.path:
        sys.path.append(libpath)

def timestamp(now = datetime.utcnow()):
    return int(timegm(now.utctimetuple()) * 1000 + now.microsecond / 1000)

def from_timestamp(timestamp):
    return datetime.utcfromtimestamp(timestamp / 1000) +    \
            timedelta(microsecond = timestamp % 1000)

def now_time():
    return datetime.utcnow()

def invoke(callback, args = (), kwargs = {}):
    from unittest import case
    try:
        if callback:
            callback(*args, **kwargs)
    except (AssertionError, case._ExpectedFailure, case._UnexpectedSuccess):
        raise
    except Exception:
        logging.exception("failed to invoke %s", callback)

def invoke_later(callback, priority = -20, *args, **kwargs):
    from common.task import CallbackTask
    try:
        if callback is not None:
            task = CallbackTask(callback = callback,    \
                    args = args,                        \
                    kwargs = kwargs)
            task.queue()
    except Exception:
        logging.exception('failed create invoke task for %s', callback)
