from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import os
import signal
import sys
import threading 
from time import sleep
import traceback

############################################################
# Timeout
############################################################

#http://www.saltycrane.com/blog/2010/04/using-python-timeout-decorator-uploading-s3/

class TimeoutError(Exception):
    def __init__(self, value = "Timed Out"):
        self.value = value
    def __str__(self):
        return repr(self.value)

def timeout(seconds_before_timeout):
    def decorate(f):
        def handler(signum, frame):
            raise TimeoutError()
        def new_f(*args, **kwargs):
            old = signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds_before_timeout)
            try:
                result = f(*args, **kwargs)
            finally:
                signal.signal(signal.SIGALRM, old)
            signal.alarm(0)
            return result
        new_f.func_name = f.func_name
        return new_f
    return decorate

class GlobalExceptionWatcher(object):
    def __init__(self, sleep_before_exit = 0.1):
        self.sleep_before_exit = sleep_before_exit

    def _store_excepthook(self):
        '''
        Uses as an exception handlers which stores any uncaught exceptions.
        '''
        formated_exc = self.__org_hook()
        self.__org_hook()
        exec_info = sys.exc_info()
        self._exceptions.append(exec_info)
        return formated_exc

    def __enter__(self):
        '''
        Register us to the hook.
        '''
        self._exceptions = []
        self.__org_hook = threading._format_exc
        threading._format_exc = self._store_excepthook

    def __exit__(self, _type, _value, _traceback):
        '''
        Remove us from the hook, assure no exception were thrown.
        '''
        if self.sleep_before_exit > 1e-5:
            sleep(self.sleep_before_exit)
        threading._format_exc = self.__org_hook
        if len(self._exceptions) > 0:
            if len(self._exceptions) > 1:
                tracebacks = ["".join(traceback.format_exception(*info)) for info in self._exceptions]
                tracebacks = os.linesep.join(tracebacks)
                raise Exception('Exceptions in other threads: %s' % tracebacks)
            else:
                (ex_type, ex_value, ex_traceback)  = self._exceptions[0]
                raise ex_type, ex_value, ex_traceback

def catch_exceptions(sleep_before_exit = 0.1):
    def decorate(f):
        def new_f(*args, **kwargs):
            with GlobalExceptionWatcher(sleep_before_exit = sleep_before_exit):
                return f(*args, **kwargs)
        new_f.func_name = f.func_name
        return new_f
    return decorate
