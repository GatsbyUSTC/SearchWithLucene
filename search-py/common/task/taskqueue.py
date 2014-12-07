from Queue import PriorityQueue, Empty
import threading

class TaskQueue(object):
    instance = None

    def __init__(self, num_thread = 2):
        self.num_thread  = num_thread
        self.__queue     = PriorityQueue()
        self.__threads   = []
        self.__available = threading.Semaphore(0)
        self.__lock      = threading.Lock()
        self.__started   = False
        self.__stopped   = False

    def add_task_tuple(self, task_tuple):
        self.__queue.put(task_tuple)
        self.__available.release()
        self.start()

    @classmethod
    def get_instance(cls):
        instance = cls.instance
        if not instance:
            instance = TaskQueue()
            cls.instance = instance
            instance.make_default()
            instance.start()
        return instance

    def make_default(self):
        type(self).instance = self

    def start(self):
        with self.__lock:
            if self.__started:
                return
            if self.__stopped:
                raise ValueError('stopped')
            self.__started = True
        for i in range(0, self.num_thread):
            thread = threading.Thread(
                target = self.main_loop,
                name   = "TaskExecutor %d" % i)
            thread.daemon = True
            self.__threads.append(thread)
        for thread in self.__threads:
            thread.start()

    @classmethod
    def add_task(cls, task):
        from common.task import BaseTask
        if isinstance(task, BaseTask):
            task_tuple = task.to_tuple()
            cls.get_instance().add_task_tuple(task_tuple)

    def stop(self, wait = False):
        with self.__lock:
            if not self.__started:
                return
            self.__stopped = True
            if id(type(self).instance) == id(self):
                type(self).instance = None
        self.__available.release()
        for thread in self.__threads:
            if not wait:
                thread.join(1)
            else:
                thread.join()
        self.__threads = []

    def main_loop(self):
        from common.task import BaseTask
        while True:
            if self.__stopped:
                break
            task_tuple = None
            self.__available.acquire()
            if self.__stopped:
                self.__available.release()
                break
            try:
                task_tuple = self.__queue.get_nowait()
            except Empty:
                continue
            task   = BaseTask.get_task_from_tuple(task_tuple)
            task.run()

