from collections import deque
from functools import partial
import logging
import struct
from threading import RLock, Lock
from Queue import Queue, Empty
from common import invoke, invoke_later
from common.task import ProcessMsgTask
from message import MessageRecv
from message.common import HandShakeSend
from exception import InvalidSessionSendError

class BaseConnection(object):
    def __init__(self):
        self.callbacks  = {}
        self.lock       = RLock()

    def ready(self):
        raise NotImplementedError()

    def read(self, expect_len, callback = None):
        raise NotImplementedError()

    def write(self, data, callback = None):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def get_remote_addr(self):
        raise NotImplementedError()

    def get_local_addr(self):
        raise NotImplementedError()

    def set_handler(self, event, callback = None, args = (), kwargs = {}):
        self.callbacks[event] = (callback, args, kwargs)

    def invoke_handler(self, event, kwargs = {}):
        with self.lock:
            cb_tuple = self.callbacks.get(event)
            if cb_tuple is None:
                return
            (callback, args, _kwargs) = cb_tuple
        _kwargs = _kwargs or {}
        _kwargs.update(kwargs or {})
        kwargs = _kwargs
        invoke(callback = callback, args = args, kwargs = kwargs)

class BaseClient(object):
    def connect(self):
        raise NotImplementedError()

class SessionManager(object):
    def __init__(self):
        self.lock        = RLock()
        self.sessions    = []
        self.by_name     = {}
        self.by_key      = {}

    def session_by_name(self, name):
        result = None
        with self.lock:
            se_list = self.by_name.get(name)
            if se_list and len(se_list):
                result = se_list.popleft()
                se_list.append(result)
        return result

    def session_by_identifier(self, identifier):
        with self.lock:
            return self.by_key.get(identifier)

    def ensure_session_exists(self, key, connection, ctor, kwargs = {}):
        with self.lock:
            if self.by_key.get(key):
                return
            self.__create_session_nolock(connection, ctor, kwargs)

    def create_session(self, key, connection, ctor, kwargs = {}):
        with self.lock:
            session = self.by_key.get(key)
            if session:
                logging.warn("session already exists (%s)", key)
                session.drop_connection()
                self.remove_session(session)
            self.ensure_session_exists(key, connection, ctor, kwargs)

    def remove_session_by_key(self, key):
        session = self.session_by_identifier(key)
        if session:
            self.remove_session(session)

    def remove_session(self, session):
        with self.lock:
            if not session in self.sessions:
                return
            key = session.get_identifier()
            name = session.get_name()
            if key in self.by_key:
                del self.by_key[key]
            se_list = self.by_name.get(name)
            if se_list and session in se_list:
                se_list.remove(session)
            self.sessions.remove(session)

    def __create_session_nolock(self, connection, ctor, kwargs, manage = True):
        kwargs = kwargs or {}
        kwargs['connection'] = connection
        kwargs['mgr'] = self
        session = ctor(**kwargs)
        session.init_session(
            handler = partial(
                self.__after_session_init,
                session = session,
                manage = manage))

    def __handle_read(self, session, msg):
        if msg:
            ProcessMsgTask(msg).queue()
        try:
            self.__set_read_handler(session)
        except IOError:
            session.drop_connection()
            self.remove_session(session)

    def __handle_close(self, session):
        with self.lock:
            need2remove = session in self.sessions
        if need2remove:
            self.remove_session(session)

    def __set_read_handler(self, session):
        session.read_message(
            callback = self.__handle_read,
            kwargs = {
                'session' : session
            })

    def __after_session_init(self, session, manage, succeed):
        try:
            if not succeed:
                logging.error('failed to init session %s', session)
                return
            if manage:
                self.__set_read_handler(session)
                session.on_close(
                    handler = partial(self.__handle_close, session = session))
            self.__add_session(session)
        except Exception:
            logging.exception('after_session_init')
            session.drop_connection()

    def add_managed_session(self, session):
        try:
            self.__set_read_handler(session)
            session.on_close(
                handler = partial(self.__handle_close, session = session))
            self.__add_session(session)
        except Exception:
            logging.exception('add_managed_session')
            session.drop_connection()

    def __add_session(self, session):
        try:
            with self.lock:
                key = session.get_identifier()
                name = session.get_name()
                self.by_key[key] = session
                se_list = self.by_name.get(name)
                if not se_list:
                    se_list = deque()
                    self.by_name[name] = se_list
                se_list.append(session)
                self.sessions.append(session)
        except Exception:
            logging.exception('add_session')
            session.drop_connection()

class BaseServer(object):
    def __init__(self, local_name, session_mgr):
        self.session_mgr = session_mgr
        self.local_name  = local_name

    def start(self):
        raise NotImplementedError()

    def shutdown(self):
        raise NotImplementedError()

    def create_session(self, key, connection, ctor, ctor_kwargs = {}):
        ctor_kwargs = ctor_kwargs or {}
        ctor_kwargs['local_name'] = self.local_name
        self.session_mgr.create_session(key, connection, ctor, ctor_kwargs)

class BaseMessageMixin(object):
    def write_message(self, msg, callback = None, args = (), kwargs = {},   \
            targeted = False, error_on_close = False):
        body = self.build_body(msg)
        self.write_invoke_now(
            data     = body,
            callback = callback,
            args     = args,
            kwargs   = kwargs,
            targeted = targeted,
            error_on_close = error_on_close)

    def read_message(self, callback = None, args = (), kwargs = {}):
        raise NotImplementedError()

    def build_body(self, msg):
        return msg.serialize()

    def build_msg(self, data):
        data = data.decode('utf-8', errors = 'replace')
        return MessageRecv.parse_message(data, session = self)

    def handle_msg(self, callback, data, args = (), kwargs = {}):
        msg = None
        if data:
            msg = self.build_msg(data)
        kwargs = kwargs or {}
        kwargs['msg'] = msg
        invoke(callback, args = args, kwargs = kwargs)

class StreamMessageMixin(BaseMessageMixin):
    def read_message(self, callback = None, args = (), kwargs = {}):
        try:
            self.read_invoke_now(
                 expect_len = struct.calcsize('!I'),
                 callback = partial(self.__read_body, callback = callback),
                 args = args, kwargs = kwargs)
        except IOError:
            self.handle_msg(
                callback = callback,
                data     = None,
                args     = args,
                kwargs   = kwargs)

    def __read_body(self, callback, data, *args, **kwargs):
        if not data:
            self.handle_msg(
                callback = callback, data = None,
                args = args, kwargs = kwargs)
            return
        length = struct.unpack('!I', data)[0]
        try:
            self.read_invoke_now(
                expect_len = length,
                callback = partial(
                    self.handle_msg,
                    callback = callback,
                    args     = args,
                    kwargs   = kwargs))
        except IOError:
            self.handle_msg(
                callback = callback,
                data     = None,
                args     = args,
                kwargs   = kwargs)

class BaseSessionInit(object):
    MAGIC_HEAD = 'SOCIAL-TV-BACK'
    def __init__(self, session, handler):
        self.session = session
        self.handler = handler
        self.__finish_write = False
        self.__finish_read  = False
        self.__succeed      = True
        self.__response_sent = False

    def start(self):
        self.session.read_message(callback = self.__handle_recv)
        local_name = self.session.get_local_name()
        msg = HandShakeSend(session = self.session, name = local_name)
        self.session.write_message(
            msg = msg,
            callback = self.__handle_send)

    def __handle_send(self, succeed):
        if not succeed:
            self.finish(False)
        else:
            self.__finish_write = True
            self.__check_finish()

    def __handle_recv(self, msg):
        if not msg:
            self.finish(False)
        else:
            msg.mark_replied()
            self.session.set_name(msg.get_name())
            self.__finish_read = True
            self.__check_finish()

    def __check_finish(self):
        if self.__finish_read and self.__finish_write:
            self.finish(self.__succeed)

    def finish(self, succeed):
        if not self.__response_sent:
            self.__response_sent = True
            invoke(callback = self.handler, kwargs = {'succeed': succeed})

class BaseSessionNew(object):
    def __init__(self, connection, local_name, mgr, identifier = None):
        if not identifier:
            addr = connection.get_remote_addr()
            identifier = self.get_identifier_by_addr(addr)
        self.__name          = None
        self.__local_name    = local_name
        self.connection      = connection
        self.task_lock       = Lock()
        self.write_queue     = Queue()
        self.__close_handler = None
        self.__identifier    = identifier
        self.reading_task    = None
        self.writing_task    = None
        self.session_mgr     = mgr
        connection.set_handler(
            event = 'disconnect',
            callback = self.on_disconnect)

    def get_local_name(self):
        return self.__local_name

    def get_session_mgr(self):
        return self.session_mgr

    def batch_add_task(self, task_list):
        with self.task_lock:
            for task in tasl_list:
                self.write_queue.put(task)
        self.__check_write()

    def get_write_queue(self):
        with self.task_lock:
            write_queue = self.write_queue
            self.write_queue = Queue()
        targeted = []
        untargeted = []
        while not write_queue.empty():
            task = write_queue.get_nowait()
            if task['targeted']:
                targeted.append(task)
            else:
                untargeted.append(task)
        return (targeted, untargeted)

    def on_close(self, handler = None):
        self.__close_handler = handler

    def drop_connection_impl(self, connection):
        connection.close()

    def drop_connection(self):
        with self.task_lock:
            connection = self.connection
            task = self.writing_task
            if task:
                self.write_queue.put(task)
        if connection and connection.ready():
            self.drop_connection_impl(connection)
            self.on_disconnect()

    @classmethod
    def get_identifier_by_addr(cls, address):
        # tcp![1.2.3.4]:1234
        raise NotImplementedError()

    def get_identifier(self):
        return self.__identifier

    def set_identifier(self, identifier):
        self.__identifier = identifier

    def get_name(self):
        return self.__name

    def set_name(self, name):
        self.__name = name

    def __eq__(self, other):
        return self.get_identifier() == other.get_identifier()

    def init_session(self, handler):
        initializer = BaseSessionInit(self, handler = handler)
        initializer.start()

    def write_invoke_now(self, data, callback = None,       \
            args = (), kwargs = {}, targeted = False, error_on_close = False):
        if error_on_close and not self.connection.ready():
            raise IOError('connection not ready.')
        self.write_queue.put({
            'data':     data,
            'callback': callback,
            'args':     args,
            'kwargs':   kwargs,
            'targeted': targeted
        })
        self.__check_write()

    def read_invoke_now(self, expect_len, callback = None,  \
            args = (), kwargs = {}):
        task = {
            'expect_len':   expect_len,
            'callback':     callback,
            'args':         args,
            'kwargs':       kwargs
        }
        with self.task_lock:
            if self.reading_task:
                logging.error(
                    'already reading in session %s(%s)',
                    self.get_identifier(),
                    self.get_name())
                task = None
            else:
                self.reading_task = task
        if not task:
            kwargs = kwargs or {}
            kwargs['data']    = None
            invoke(callback = callback, args = args, kwargs = kwargs)
            self.drop_connection()
        else:
            self.read_impl(
                expect_len = expect_len,
                callback   = self.__after_read)

    def write(self, data, callback = None, args = (), kwargs = {},  \
            targeted = False, error_on_close = False):
        if not callback:
            self.write_invoke_now(data, error_on_close = error_on_close)
        else:
            self.write_invoke_now(
                data     = data,
                callback = partial(invoke_later, callback = callback),
                args     = args,
                kwargs   = kwargs,
                targeted = targeted,
                error_on_close = error_on_close)

    def read(self, expect_len, callback = None, args = (), kwargs = {}):
        if not callback:
            self.read_invoke_now(expect_len)
        else:
            self.read_invoke_now(
                expect_len = expect_len,
                callback = partial(invoke_later, callback = callback),
                args     = args,
                kwargs   = kwargs)

    def write_impl(self, data, callback = None):
        try:
            self.connection.write(data = data, callback = callback)
        except Exception:
            self.drop_connection()
            raise

    def read_impl(self, expect_len, callback = None):
        try:
            self.connection.read(expect_len = expect_len, callback = callback)
        except Exception:
            self.drop_connection()
            raise

    def on_disconnect(self):
        with self.task_lock:
            callback = self.__close_handler
            self.__close_handler = None
        if callback:
            invoke(callback = callback)

    def __check_write(self):
        task = None
        with self.task_lock:
            if self.writing_task or not self.connection.ready():
                return
            try:
                self.writing_task = self.write_queue.get_nowait()
            except Empty:
                return
            task = self.writing_task
        if task:
            try:
                self.write_impl(task['data'], callback = self.__after_write)
            except Exception:
                logging.exception('write')
                self.drop_connection()

    def __after_write(self, succeed):
        with self.task_lock:
            task = self.writing_task
            self.writing_task = None
        assert task is not None
        callback = task['callback']
        args     = task['args']
        kwargs   = task['kwargs']
        kwargs   = kwargs or {}
        kwargs['succeed'] = succeed
        invoke(callback = callback, args = args, kwargs = kwargs)
        self.__check_write()

    def __after_read(self, data):
        with self.task_lock:
            task = self.reading_task
            self.reading_task = None
        assert task is not None
        callback = task['callback']
        args     = task['args']
        kwargs   = task['kwargs'] or {}
        kwargs['data'] = data
        invoke(callback = callback, args = args, kwargs = kwargs)

    def __repr__(self):
        return "session %s (%s)" % (self.get_name(), self.get_identifier())
 
