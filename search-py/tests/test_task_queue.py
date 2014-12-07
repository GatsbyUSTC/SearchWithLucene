import time
from tornado.ioloop import IOLoop
from threading import Event, current_thread
from unittest import TestCase, skip
from common.task import BaseTask, TaskQueue, CallbackTask
from tests import catch_exceptions

class TimeoutTask(BaseTask):
    def __init__(self, wait_time, timeout, expected_run, *args, **kwargs):
        self.wait_time = wait_time
        self.finish    = Event()
        self.executed  = False
        self.timeouted = False
        self.finished  = False
        description    = 'wait_time = %s, timeout = %s, expected_run = %s' % \
            (wait_time, timeout, expected_run)
        self.expected_run = expected_run
        super(TimeoutTask, self).__init__(
            name = 'TimeoutTest',
            description = description,
            *args, **kwargs)
        if timeout > 0:
            self.set_timeout(callback = self.on_timeout, milliseconds = timeout)

    def mark_finish(self):
        assert not self.finished
        self.finished = True
        self.finish.set()

    def wait_for_finish(self, testcase):
        self.finish.wait()
        testcase.assertEqual(self.expected_run, self.executed, msg = str(self))

    def on_timeout(self):
        self.timeouted = True
        self.mark_finish()

    def run_impl(self):
        self.executed = True
        time.sleep(self.wait_time / 1000.0)
        self.mark_finish()

class TestTimeoutTask(TestCase):
    def setUp(self):
        self.tasks      = []
        self.io_loop    = IOLoop.instance()
        self.stop_event = Event()
        self.task_queue = TaskQueue()
        self.task_queue.make_default()
        self.task_queue.start()
        CallbackTask(callback = self.__start_io_loop).queue()

    def __start_io_loop(self):
        self.io_loop.start()
        # self.io_loop.close(all_fds = True)
        self.stop_event.set()

    def __wait_all(self):
        for task in self.tasks:
            task.wait_for_finish(self)

    def __task(self, **kwargs):
        task = TimeoutTask(priority = len(self.tasks), **kwargs)
        self.tasks.append(task)
        task.queue()

    @catch_exceptions(sleep_before_exit = 0)
    def test_timeout(self):
        self.__task(wait_time = 100, timeout = 1000, expected_run = True)
        self.__task(wait_time = 100, timeout = 2000, expected_run = True)
        self.__task(wait_time = 100, timeout = 150, expected_run = False)
        self.__task(wait_time = 100, timeout = 230, expected_run = True)
        self.__task(wait_time = 100, timeout = 290, expected_run = False)
        self.__task(wait_time = 100, timeout = None, expected_run = True)
        self.__task(wait_time = 100, timeout = 350, expected_run = False)
        self.__task(wait_time = 100, timeout = 450, expected_run = True)
        self.__wait_all()

    def tearDown(self):
        self.io_loop.stop()
        self.stop_event.wait()
        self.task_queue.stop(wait = True)

