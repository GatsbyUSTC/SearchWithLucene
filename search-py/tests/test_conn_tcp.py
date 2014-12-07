from functools import partial
import logging
from Queue import Queue, Empty
import random
from threading import Event, Semaphore
from tornado.ioloop import IOLoop
from unittest import TestCase, skip
from common.task import TaskQueue, CallbackTask
from connection import TCPClientMsgSession, TCPServer, SessionManager, TCPClient
from tests import timeout, TimeoutError, catch_exceptions
from tests.test_conn_base import RawMessageRecv, RawMessageSend

def gen_text():
    import string
    DATA_CHARS = string.ascii_letters + string.digits

    data = ''
    length = random.randint(100, 1000 + 1)
    while length > 0:
        data += random.choice(DATA_CHARS)
        length -= 1
    return data

class _DataVeryfier(object):
    def __init__(self, test_case, key):
        self.test_case = test_case
        self.key       = key
        self.sent_data = []
        self.recv_ptr  = 0

    def send(self, data):
        data = list(data)
        self.sent_data.extend(data)

    def recv(self, data):
        case = self.test_case
        data = list(data)
        case.assertLess(
            self.recv_ptr + len(data),
            self.sent_data,
            msg = 'unexpected data: %s, ptr = %d' % (data, self.recv_ptr))
        case.assertListEqual(
            self.sent_data[self.recv_ptr:self.recv_ptr + len(data)],
            data,
            msg = 'unmached data: %s, ptr = %d' % (data, self.recv_ptr))
        self.recv_ptr += len(data)

    def close(self):
        case = self.test_case
        case.assertEqual(
            self.recv_ptr,
            len(self.sent_data),
            msg = 'unreceived data: %s' % self.sent_data[self.recv_ptr:])

class _DummyClient(object):
    def __init__(self, test_case, remote_port, result_set):
        self.client        = TCPClient(address = '127.0.0.1', port = remote_port)
        self.test_case     = test_case
        self.data_verifier = None
        self.result_set    = result_set
        self.finish_event  = Event()
        self.remain_sent   = random.randint(5, 10)

    def start(self):
        self.client.set_handler(
            event    = 'connect',
            callback = self.__handle_connect)
        self.client.connect()

    def __mark_finished(self):
        self.finish_event.set()

    def wait_finish(self):
        self.finish_event.wait()

    def __send_data(self, succeed):
        self.test_case.assertTrue(succeed, msg = 'failed to send data')
        if self.remain_sent < 1:
            self.client.connection.set_close_callback(
                self.__mark_finished())
            self.client.close()
        else:
            self.remain_sent -= 1
            data = gen_text().encode('utf-8', errors = 'replace')
            self.data_verifier.send(data)
            self.client.write(
                data     = data,
                callback = self.__send_data)

    def __handle_connect(self):
        addr = self.client.get_local_addr()
        key = TCPClientMsgSession.get_identifier_by_addr(addr)
        self.data_verifier = _DataVeryfier(
            test_case = self.test_case, key = key)
        self.result_set[key] = self.data_verifier
        self.__send_data(True)

class _DummySessionMgr(object):
    def __init__(self, result_data):
        self.result_data = result_data
        self.clients     = 0
        self.finish_event = Event()

    def create_session(self, key, connection, ctor, ctor_kwargs):
        self.clients += 1
        self.set_read_handler(connection, key)

    def set_read_handler(self, connection, key):
        try:
            connection.read(
                expect_len = 1,
                callback   = partial(
                    self.handle_read, connection = connection, key = key))
        except IOError:
            connection.close()
            self.clients -= 1
            self.result_data[key].close()
            self.finish_event.set()

    def wait_finish(self):
        while self.clients > 0:
            self.finish_event.wait()
            self.finish_event.clear()

    def extract_data(self, data):
        return data

    def handle_read(self, data, connection, key):
        if not data:
            self.clients -= 1
            connection.close()
            self.result_data[key].close()
            self.finish_event.set()
        else:
            if connection.ready():
                data = self.extract_data(data)
                self.result_data[key].recv(data)
                self.set_read_handler(connection, key)
            else:
                self.handle_read(None, connection, key)

class TestTCPConnection(TestCase):
    def setUp(self):
        self.io_loop     = IOLoop.instance()
        self.result_set  = {}
        self.session_mgr = _DummySessionMgr(self.result_set)
        self.server      = TCPServer(
            local_port  = 8888,
            local_name  = 'server',
            session_mgr = self.session_mgr)
        self.stop_event  = Event()
        self.task_queue  = TaskQueue()
        self.task_queue.make_default()
        self.task_queue.start()
        self.server.start()
        CallbackTask(callback = self.__start_io_loop).queue()

    def __start_io_loop(self):
        self.io_loop.start()
        # self.io_loop.close(all_fds = True)
        self.stop_event.set()

    @catch_exceptions()
    def test(self):
        clients = []
        for i in range(1, random.randint(5, 10)):
            client = _DummyClient(self, 8888, self.result_set)
            client.start()
            clients.append(client)
        for client in clients:
            client.wait_finish()

    def tearDown(self):
        self.session_mgr.wait_finish()
        self.server.shutdown()
        self.io_loop.stop()
        self.stop_event.wait()
        self.task_queue.stop(wait = True)

class _DummySessionMgrForQueue(_DummySessionMgr):
    def __init__(self, result_data):
        self.result_data = result_data
        self.clients     = 0
        self.finish_sema = Semaphore(0)

    def create_session(self, key, connection, ctor, ctor_kwargs):
        self.clients += 1
        kwargs = ctor_kwargs or {}
        kwargs['connection'] = connection
        kwargs['mgr'] = self
        session = ctor(**kwargs)
        session.init_session(
            handler = partial(
                self.__after_session_init,
                session = session,
                key = key))
        session.on_close(handler = partial(
            self.__on_session_close,
            session = session,
            key = key))

    def __after_session_init(self, session, succeed, key):
        self.set_read_handler(session, key)

    def set_read_handler(self, session, key):
        try:
            session.read_message(
                callback   = partial(
                    self.handle_read, session = session, key = key))
        except IOError:
            connection.close()
            self.__on_session_close(session, key)

    def wait_finish(self):
        for i in range(0, self.clients):
            self.finish_sema.acquire()

    def __on_session_close(self, session, key):
        if self.result_data.get(key):
            self.result_data[key].close()
            del self.result_data[key]
            self.finish_sema.release()

    def handle_read(self, msg, session, key):
        if not msg:
            session.drop_connection()
        else:
            if session.connection.ready():
                data = self.extract_data(msg)
                self.result_data[key].recv(data)
                self.set_read_handler(session, key)
            else:
                self.handle_read(None, session, key)

    def extract_data(self, data):
        return data.get_content()

class TestTCPSession(TestCase):
    def setUp(self):
        self.io_loop     = IOLoop.instance()
        self.result_set  = {}
        self.session_mgr = _DummySessionMgrForQueue(self.result_set)
        self.server      = TCPServer(
            local_port  = 8888,
            session_mgr = self.session_mgr,
            local_name  = 'server')
        self.stop_event  = Event()
        self.task_queue  = TaskQueue()
        self.task_queue.make_default()
        self.task_queue.start()
        RawMessageRecv.register()
        self.server.start()
        CallbackTask(callback = self.__start_io_loop).queue()

    def __start_io_loop(self):
        self.io_loop.start()
        # self.io_loop.close(all_fds = True)
        self.stop_event.set()

    def __generate_data_blocks(self):
        result = []
        for i in range(1, 100):
            result.append(gen_text())
        return result

    @staticmethod
    def __release_sema4(sema4, *args, **kwargs):
        sema4.release()

    @catch_exceptions()
    def test(self):
        clients = []
        data_blocks = self.__generate_data_blocks()
        sema4 = Semaphore(0)
        for i in range(10, 20):
            client = TCPClientMsgSession(
                address = '127.0.0.1', port = 8888,
                local_name = 'dummy',
                mgr = self.session_mgr)
            client.init_session(
                handler = partial(
                    self.__release_sema4,
                    sema4 = sema4))
            clients.append(client)
        for client in clients:
            sema4.acquire()
        for client in clients:
            key = client.get_identifier()
            self.result_set[key] = _DataVeryfier(self, key)
        for block in data_blocks:
            client = random.choice(clients)
            key = client.get_identifier()
            self.result_set[key].send(block)
            msg = RawMessageSend(
                text    = block,
                session = client)
            client.write_message(
                msg = msg,
                callback = partial(
                    self.__release_sema4, sema4 = sema4))
        for block in data_blocks:
            sema4.acquire()
        for client in clients:
            client.drop_connection()

    def tearDown(self):
        self.session_mgr.wait_finish()
        self.server.shutdown()
        self.io_loop.stop()
        self.stop_event.wait()
        self.task_queue.stop(wait = True)
        RawMessageRecv.cancel_register()

