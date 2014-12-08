from functools import partial
from datetime import timedelta
import logging
import threading
from tornado.ioloop import IOLoop
from common import invoke
from common.task import TaskQueue

class BaseTask(object):
    __lock    = threading.Lock()
    __last_id = 0
    def __init__(self, name, description = None, priority = 0):
        self.__name        = name
        self.__description = description
        self.__priority    = priority
        self.__taskid      = self.__gen_task_id()
        self.__timeout     = None
        self.__skip_run    = False

    @classmethod
    def __gen_task_id(cls):
        with cls.__lock:
            cls.__last_id += 1
            return cls.__last_id

    def get_task_id(self):
        return self.__taskid

    def get_priority(self):
        return self.__priority

    def run(self):
        try:
            if self.is_skipped():
                logging.info('skip running task %s', self)
                return
            self.skip()
            self.run_impl()
        except Exception:
            logging.exception("failed to run %s", self)

    def run_impl(self):
        raise NotImplementedError()

    def set_timeout(self, minutes = 0, seconds = 0, \
            milliseconds = 0, callback = None):
        ioloop = IOLoop.instance()
        handle = self.__timeout
        deadline = timedelta(
            minutes = minutes,
            seconds = seconds,
            milliseconds = milliseconds)
        assert deadline > timedelta.resolution
        if handle:
            self.__timeout = None
            ioloop.remove_timeout(handle)
        def add_timeout():
            handle = ioloop.add_timeout(deadline,
                partial(self.__on_timeout, callback = callback))
            self.__timeout = handle
        ioloop.add_callback(callback = add_timeout)

    def __on_timeout(self, callback):
        if not self.is_skipped():
            logging.info('skipping task %s', self)
            self.skip()
            invoke(callback = callback)

    def skip(self):
        self.__skip_run = True

    def is_skipped(self):
        return self.__skip_run

    def queue(self):
        TaskQueue.get_instance().add_task(self)

    def to_tuple(self):
        return (self.get_priority(), self.get_task_id(), self)

    @staticmethod
    def get_task_from_tuple(task_tuple):
        return task_tuple[2]

    def __lt__(self, other):
        return (self.get_priority() < other.get_priority()) or  \
            (self.get_task_id() < other.get_task_id())

    def __repr__(self):
        if self.__description is None:
            return "task %s" % self.__name
        else:
            return "task %s (%s)" % (self.__name, self.__description)

class CallbackTask(BaseTask):
    def __init__(self, callback, priority = -10, name = "callback",  \
            args = (), kwargs = {}):
        super(CallbackTask, self).__init__(name = name, priority = priority)
        self.callback = callback
        self.args     = args
        self.kwargs   = kwargs

    def run_impl(self):
        self.callback(*self.args, **self.kwargs)

    def __repr__(self):
        return "invoke callback task (method = %s, args = %s, kwargs = %s)" % \
                (self.callback, self.args, self.kwargs)

class ProcessMsgTask(BaseTask):
    def __init__(self, message, priority = -1):
        super(ProcessMsgTask, self).__init__(
            name = 'process message',
            description = message.body_str,
            priority = priority
        )
        self.message = message

    def run_impl(self):
        try:
            self.message.handle()
        except Exception:
            logging.exception("failed to process message (%s)",     \
                    self.message.body_str)

