from unittest import TestCase, skip
from Queue import Queue, Empty
import random
from threading import Lock, Thread, Event
from tornado.iostream import StreamClosedError
from common import invoke, invoke_later
from connection import BaseSessionNew, StreamMessageMixin, BaseSessionInit, \
        BaseConnection, BaseClient, SessionManager
from message import MessageSend, MessageRecv
from tests import timeout, TimeoutError, catch_exceptions

class LoopBackConnection(BaseConnection, BaseClient):
    def __init__(self):
        super(LoopBackConnection, self).__init__()
        self.data_queue  = Queue()
        self.lock        = Lock()
        self.recv_thread = None
        self.event       = None
        self.writing     = False
        self.read_task   = None

    def ready(self):
        return self.recv_thread

    def connect(self):
        with self.lock:
            if self.recv_thread:
                raise Exception('already connected')
            self.event = Event()
            self.recv_thread = Thread(target = self.recv_loop, name = 'recv_thread')
            self.recv_thread.daemon = True
            self.recv_thread.start()

    def close(self):
        with self.lock:
            thread = self.recv_thread
            if thread is None:
                return
            self.recv_thread = None
            not_empty = self.data_queue.qsize() > 0
        self.event.set()
        thread.join(2)
        self.invoke_handler('disconnect')
        if not_empty:
            raise Exception('data queue not empty after closed')

    def __check_close(self):
        if not self.ready():
            raise StreamClosedError()

    def write(self, data, callback = None):
        try:
            succeed = True
            self.__check_close()
            assert isinstance(data, str)
            with self.lock:
                if self.writing:
                    raise Exception("already writing")
                self.writing = True
            for b in data:
                self.data_queue.put(b)
        except Exception:
            succeed = False
            raise
        finally:
            self.writing = False
            kwargs = {'succeed': succeed}
            invoke(callback, kwargs = kwargs)

    def read(self, expect_len, callback = None):
        with self.lock:
            self.__check_close()
            if self.read_task:
                raise Exception("already reading")
            self.event.set()
            self.read_task = (expect_len, callback)
    
    def recv_loop(self):
        self.invoke_handler('connect')
        while self.recv_thread:
            self.event.wait()
            task = self.read_task
            if not task:
                if not self.ready():
                    break
                else:
                    continue
            (size, handler) = task
            result = ''
            try:
                while len(result) < size:
                    self.__check_close()
                    result += self.data_queue.get()
            except Exception:
                result = None
                raise
            finally:
                self.read_task = None
                kwargs = {}
                kwargs['data'] = result
                invoke(callback = handler, kwargs = kwargs)
        task = self.read_task
        if task:
            (size, handler, args, kwargs) = task
            kwargs = kwargs or {}
            kwargs['succeed'] = False
            kwargs['data']    = None
            invoke(callback = handler, args = args, kwargs = kwargs)

    def get_remote_addr(self):
        return ("remote", 1234)

    def get_local_addr(self):
        return ("localhost", 5678)

def gen_text():
    import string
    DATA_CHARS = string.ascii_letters + string.digits

    data = ''
    length = random.randint(100, 1000 + 1)
    while length > 0:
        data += random.choice(DATA_CHARS)
        length -= 1
    return data

class LoopBackSession(BaseSessionNew):
    @classmethod
    def get_identifier_by_addr(cls, address):
        return "dummy![%s]:%d" % address

    def get_identifier_impl(self):
        return self.get_identifier_by_addr(self.connection.get_remote_addr())

class TestLookBackSession(TestCase):
    def setUp(self):
        connection = LoopBackConnection()
        connection.connect()
        self.connection = connection
        self.session = LoopBackSession(connection, local_name = 'dummy', mgr = None)

    def tearDown(self):
        self.session.drop_connection()
        self.assertFalse(self.connection.ready())

    @catch_exceptions(sleep_before_exit = 0)
    def __send_data(self, data):
        finish = Event()
        data = data.encode('utf-8', errors = 'replace')
        self.session.write(
            data = data,
            callback = self.__handle_send,
            kwargs = {'event' : finish})
        result = finish.wait(10)
        self.assertTrue(result)
        return data

    @catch_exceptions(sleep_before_exit = 0)
    def __send_data_now(self, data):
        finish = Event()
        data = data.encode('utf-8', errors = 'replace')
        self.session.write_invoke_now(
            data = data,
            callback = self.__handle_send,
            kwargs = {'event' : finish})
        result = finish.wait(10)
        self.assertTrue(result)
        return data

    def __handle_send(self, succeed, event):
        try:
            self.assertTrue(succeed, msg = "failed to send data")
        finally:
            event.set()

    def __handle_recv(self, event, data, original):
        try:
            self.assertIsNotNone(data, msg = "failed to recv data")
            self.assertEqual(data, original)
        finally:
            event.set()

    @catch_exceptions(sleep_before_exit = 0)
    def __start_recv_data(self, data):
        finish = Event()
        self.session.read(expect_len = len(data), \
                callback = self.__handle_recv,
                kwargs = {
                    'event'     : finish,
                    'original'  : data
                })
        return finish

    @catch_exceptions(sleep_before_exit = 0)
    def __start_recv_data_now(self, data):
        finish = Event()
        self.session.read_invoke_now(expect_len = len(data), \
                callback = self.__handle_recv,
                kwargs = {
                    'event'     : finish,
                    'original'  : data
                })
        return finish

    @catch_exceptions(sleep_before_exit = 0)
    def __end_recv_data(self, finish):
        result = finish.wait(10)
        self.assertTrue(result)

    def __recv_data_now(self, data):
        finish = self.__start_recv_data_now(data)
        self.__end_recv_data(finish)

    def __recv_data(self, data):
        finish = self.__start_recv_data(data)
        self.__end_recv_data(finish)

    def test_send_recv_now(self):
        data = gen_text()
        self.__send_data(data)
        self.__recv_data_now(data)
        self.session.drop_connection()

    def test_send_now_recv(self):
        data = gen_text()
        self.__send_data_now(data)
        self.__recv_data(data)
        self.session.drop_connection()

    def test_recv_now_send(self):
        data = gen_text()
        arg  = self.__start_recv_data_now(data)
        self.__send_data(data)
        self.__end_recv_data(arg)
        self.session.drop_connection()

    def test_recv_send_now(self):
        data = gen_text()
        arg  = self.__start_recv_data(data)
        self.__send_data_now(data)
        self.__end_recv_data(arg)
        self.session.drop_connection()

    def test_sendrecv(self):
        data = gen_text()
        self.__send_data(data)
        self.__recv_data(data)
        self.session.drop_connection()

    def test_recvsend(self):
        data = gen_text()
        arg  = self.__start_recv_data(data)
        self.__send_data(data)
        self.__end_recv_data(arg)
        self.session.drop_connection()

    def test_recv_now_multi_send(self):
        data = []
        for i in range(0,100):
            data.append(gen_text())
        for _data in data:
            self.__send_data(_data)
        _data = data[0]
        data = data[1:]
        arg = self.__start_recv_data_now(_data)
        for _data in data:
            self.__end_recv_data(arg)
            arg = self.__start_recv_data_now(_data)
        self.__end_recv_data(arg)
        self.session.drop_connection()

    def test_recv_multi_send(self):
        data = []
        for i in range(0,100):
            data.append(gen_text())
        for _data in data:
            self.__send_data(_data)
        _data = data[0]
        data = data[1:]
        arg = self.__start_recv_data(_data)
        for _data in data:
            self.__end_recv_data(arg)
            arg = self.__start_recv_data(_data)
        self.__end_recv_data(arg)
        self.session.drop_connection()

    def test_recv_multi_send_now(self):
        data = []
        for i in range(0,100):
            data.append(gen_text())
        for _data in data:
            self.__send_data_now(_data)
        _data = data[0]
        data = data[1:]
        arg = self.__start_recv_data_now(_data)
        for _data in data:
            self.__end_recv_data(arg)
            arg = self.__start_recv_data_now(_data)
        self.__end_recv_data(arg)
        self.session.drop_connection()

    def test_sendrecv_now(self):
        data = gen_text()
        self.__send_data_now(data)
        self.__recv_data_now(data)
        self.session.drop_connection()

    def test_recvsend_now(self):
        data = gen_text()
        arg  = self.__start_recv_data_now(data)
        self.__send_data_now(data)
        self.__end_recv_data(arg)
        self.session.drop_connection()

class LoopBackMessageQueue(LoopBackSession, StreamMessageMixin):
    pass

class RawMessageSend(MessageSend):
    def __init__(self, text, *args, **kwargs):
        super(RawMessageSend, self).__init__(
            type_str = 'raw-msg-test',
            *args, **kwargs)
        self.body['content'] = text

class RawMessageRecv(MessageRecv):
    def __init__(self, *args, **kwargs):
        super(RawMessageRecv, self).__init__(*args, **kwargs)
        self.content = None

    def parse(self, data):
        self.require_fields(data, 'content')
        self.content = data['content']
        return True

    def get_content(self):
        return self.content

    @classmethod
    def get_message_type(cls):
        return 'raw-msg-test'

class TestLoopBackMessageQueue(TestCase):
    def setUp(self):
        connection = LoopBackConnection()
        connection.connect()
        self.connection = connection
        self.msg_queue = LoopBackMessageQueue(connection, local_name = 'dummy', mgr = None)
        RawMessageRecv.register()

    def tearDown(self):
        self.msg_queue.drop_connection()
        self.assertFalse(self.connection.ready())
        RawMessageRecv.cancel_register()

    @catch_exceptions(sleep_before_exit = 0)
    def __send_data(self, data):
        finish = Event()
        msg = RawMessageSend(text = data, session = self.msg_queue)
        self.msg_queue.write_message(
            msg = msg,
            callback = self.__handle_send,
            kwargs = {
                'event'     : finish
            })
        result = finish.wait(10)
        self.assertTrue(result)
        return data

    def __handle_send(self, succeed, event):
        try:
            self.assertTrue(succeed, msg = "failed to send data")
        finally:
            event.set()

    def __handle_recv(self, event, msg, original):
        try:
            self.assertIsNotNone(msg, msg = "failed to recv data")
            self.assertEqual(msg.get_content(), original)
        finally:
            event.set()

    @catch_exceptions(sleep_before_exit = 0)
    def __start_recv_data(self, data):
        finish = Event()
        self.msg_queue.read_message(
            callback = self.__handle_recv,
            kwargs = {
                'event'     : finish,
                'original'  : data
                })
        return finish

    @catch_exceptions(sleep_before_exit = 0)
    def __end_recv_data(self, finish):
        result = finish.wait(1000)
        self.assertTrue(result)

    def __recv_data(self, data):
        remaining = None
        if isinstance(data, list):
            if len(data) > 1:
                remaining = data[1:]
            data = data[0]
        finish = self.__start_recv_data(data)
        self.__end_recv_data(finish)
        if remaining:
            self.__recv_data(remaining)

    def test_sendrecv(self):
        data = gen_text()
        self.__send_data(data)
        self.__recv_data(data)
        self.msg_queue.drop_connection()

    def test_recvsend(self):
        data = gen_text()
        arg  = self.__start_recv_data(data)
        self.__send_data(data)
        self.__end_recv_data(arg)
        self.msg_queue.drop_connection()

    def test_multi_recvsend(self):
        text = []
        for i in range(0,100):
            text.append(gen_text())
        for _text in text:
            self.__send_data(_text)

        self.__recv_data(text)
        self.msg_queue.drop_connection()

class DummyConnection(BaseConnection, BaseClient):
    def __init__(self, *args, **kwargs):
        super(DummyConnection, self).__init__(*args, **kwargs)
        self.__ready = False

    def connect(self):
        self.__ready = True
        self.invoke_handler('connect')

    def close(self):
        self.__ready = False
        self.invoke_handler('disconnect')

    def __check_closed(self):
        if not self.ready():
            raise StreamClosedError()

    def read(self, expect_len, callback):
        self.__check_closed()

    def write(self, data, callback):
        self.__check_closed()

    def ready(self):
        return self.__ready

class DummySessionInit(BaseSessionInit):
    def start(self):
        connection = self.session.connection
        connection.set_handler('connect', self.__after_connect)
        connection.connect()

    def __after_connect(self):
        self.finish(True)

class DummySession(BaseSessionNew, StreamMessageMixin):
    def __init__(self, remote_name, *args, **kwargs):
        super(DummySession, self).__init__(*args, **kwargs)
        self.set_name(remote_name)

    def init_session(self, handler):
        initializer = DummySessionInit(self, handler)
        initializer.start()

class TestSessionManager(TestCase):
    def setUp(self):
        self.mgr = SessionManager()
        self.__create_session(key = '1abcd', name = 'session1')
        self.__create_session(key = '1bcde', name = 'session1')
        self.__create_session(key = '1cdef', name = 'session1')
        self.__create_session(key = '1defg', name = 'session1')
        self.__create_session(key = '2abcd', name = 'session2')
        self.__create_session(key = '2bcde', name = 'session2')
        self.__create_session(key = '2cdef', name = 'session2')

    def __check_no_session(self):
        mgr = self.mgr
        with mgr.lock:
            self.assertEqual(len(mgr.sessions), 0, 'remaining sessions: %s' % str(mgr.sessions))
            self.assertDictEqual(mgr.by_key, {})
            remaining = []
            for name in mgr.by_name:
                remaining.extend(mgr.by_name[name])
            self.assertEqual(len(remaining), 0, 'remaining sessions: %s' % str(remaining))

    def __create_session(self, key, name):
        self.mgr.create_session(
            key = key, connection = DummyConnection(),
            ctor = DummySession,
            kwargs = {
                'local_name':  'local',
                'remote_name': name,
                'identifier':  key
            }
        )

    def __ensure_session_exists(self, key, name):
        self.mgr.ensure_session_exists(
            key = key, connection = DummyConnection(),
            ctor = DummySession,
            kwargs = {
                'local_name':  'local',
                'remote_name': name,
                'identifier':  key
            }
        )

    def tearDown(self):
        self.__check_no_session()

    def __close_all(self):
        sessions = self.mgr.sessions[:]
        while len(sessions):
            session = sessions.pop()
            session.drop_connection()

    def test_session_by_name(self):
        mgr = self.mgr
        sessions = []
        expected = [
            '1abcd', '1bcde', '1cdef', '1defg','1abcd',
            '2abcd', '2bcde', '2cdef', '2abcd']
        for i in range(1,6):
            session = mgr.session_by_name('session1')
            self.assertIsNotNone(session, 'failed to retrieve session by name')
            sessions.append(session.get_identifier())
        for i in range(1,5):
            session = mgr.session_by_name('session2')
            self.assertIsNotNone(session, 'failed to retrieve session by name')
            sessions.append(session.get_identifier())
        self.assertListEqual(sessions, expected)
        self.__close_all()

    def __get_session_identifiers(self):
        with self.mgr.lock:
            return [session.get_identifier() for session in self.mgr.sessions]

    def test_enusre_session_exists(self):
        original = self.__get_session_identifiers()
        self.__ensure_session_exists(key = '1abcd', name = 'session1')
        self.__ensure_session_exists(key = '1abcdn', name = 'session1')
        sessions = self.__get_session_identifiers()
        sessions.remove('1abcdn')
        self.assertListEqual(original, sessions)
        self.__close_all()

    def test_remove_session(self):
        mgr = self.mgr
        original = self.__get_session_identifiers()
        self.__ensure_session_exists(key = '1abcdn', name = 'session1')
        original.append('1abcdn')
        sessions = self.__get_session_identifiers()
        self.assertListEqual(original, sessions)
        original.remove('1abcdn')
        session = self.mgr.session_by_identifier('1abcdn')
        self.mgr.remove_session(session)
        sessions = self.__get_session_identifiers()
        session.drop_connection()
        self.assertListEqual(original, sessions)
        self.__close_all()

