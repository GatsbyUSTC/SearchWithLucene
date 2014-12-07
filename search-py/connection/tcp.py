from functools import partial
import logging
import socket
from threading import Lock
from tornado.iostream import IOStream as TCPStream
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer as TornadoTcpServer
from connection.base import BaseConnection, BaseClient,     \
        BaseServer, StreamMessageMixin, BaseSessionNew, BaseSessionInit

class _TCPBase(BaseConnection):
    def __init__(self, connection = None):
        super(_TCPBase, self).__init__()
        self.connection       = None
        self.is_connected     = False
        if connection:
            self.set_connection(connection)

    def set_connection(self, conn):
        with self.lock:
            self.is_connected = True
            self.connection   = conn
            conn.set_close_callback(self.handle_closed)

    def ready(self):
        return self.is_connected

    def after_handle_closed(self):
        pass

    def handle_closed(self):
        with self.lock:
            self.is_connected  = False
            self.connection    = None
            self.after_handle_closed()
        self.invoke_handler('disconnect')

    def before_close(self):
        pass

    def close(self):
        with self.lock:
            conn = self.connection
            if not conn or conn.closed():
                return
            self.connection  = None
            self.is_connected = False
            conn.set_close_callback(None)
            self.before_close()
        conn.close()

    def write(self, data, callback = None):
        with self.lock:
            self.__check_closed()
            self.connection.write(
                data = data,
                callback = partial(callback, succeed = True))

    def read(self, expect_len, callback = None):
        with self.lock:
            self.__check_closed()
            self.connection.read_bytes(num_bytes = expect_len,  \
                    callback = callback)

    def __check_closed(self):
        if not self.ready():
            raise StreamClosedError("Stream is closed")

    def __get_socket_obj(self):
        with self.lock:
            self.__check_closed()
            return self.connection.socket

    def get_remote_addr(self):
        sock = self.__get_socket_obj()
        return sock.getpeername()

    def get_local_addr(self):
        sock = self.__get_socket_obj()
        return sock.getsockname()

class TCPClient(_TCPBase, BaseClient):
    def __init__(self, address, port):
        super(TCPClient, self).__init__()
        self.remote_addr       = address
        self.remote_port       = port
        self.is_connecting     = False

    def connecting(self):
        return self.is_connecting

    def connect(self):
        with self.lock:
            if self.connecting() or self.ready():
                return
            self.is_connecting = True
            socket_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            connection = TCPStream(socket_fd)
            self.set_connection(connection)
        connection.connect(address = (self.remote_addr, self.remote_port),  \
                callback = self.handle_connect)

    def handle_connect(self):
        with self.lock:
            self.is_connecting = False
            self.is_connected  = True
        self.invoke_handler('connect')

    def after_handle_closed(self):
        self.is_connecting = False

class TCPServer(BaseServer):
    def __init__(self, local_port, local_addr = '', *args, **kwargs):
        super(TCPServer, self).__init__(*args, **kwargs)
        self.local_addr = local_addr
        self.local_port = local_port
        self.server = TornadoTcpServer()
        self.server.handle_stream = self.handle_stream

    def start(self):
        self.server.listen(port = self.local_port, address = self.local_addr)
        self.server.start()

    def shutdown(self):
        self.server.stop()

    def handle_stream(self, stream, address):
        tcp_conn = _TCPBase(stream)
        key = _TCPSession.get_identifier_by_addr(address)
        self.create_session(
            key = key,
            connection = tcp_conn,
            ctor = TCPMsgSession)

class _TCPSession(BaseSessionNew):
    def __init__(self, *args, **kwargs):
        super(_TCPSession, self).__init__(*args, **kwargs)

    def init_session(self, handler = None):
        initializer = BaseSessionInit(self, handler)
        initializer.start()

    @classmethod
    def get_identifier_by_addr(cls, addr):
        return 'tcp![%s]:%d' % addr

class _TCPClientSession(_TCPSession):
    def __init__(self, address, port, *args, **kwargs):
        connection = TCPClient(address = address, port = port)
        connection.set_handler(
            event = 'connect',
            callback = self.__after_connected,
            kwargs = {'connection': connection})
        self.__init_lock    = Lock()
        self.__init_handler = None
        self.__connected    = False
        connection.connect()
        super(_TCPClientSession, self).__init__(
            connection = connection,
            identifier = "pending",
            *args, **kwargs)

    def __after_connected(self, connection):
        connection.set_handler(event = 'connect')
        identifier = self.get_identifier_by_addr(
            self.connection.get_local_addr())
        self.set_identifier(identifier)
        handler = None
        with self.__init_lock:
            handler = self.__init_handler
            self.__init_handler = None
            self.__connected = True
        if handler:
            self.__invoke_general_init(handler)

    def __invoke_general_init(self, handler):
        super(_TCPClientSession, self).init_session(handler)

    def init_session(self, handler = None):
        invoke_init = False
        with self.__init_lock:
            invoke_init = self.__connected
            if not invoke_init:
                self.__init_handler = handler
        if invoke_init:
            self.__invoke_general_init(handler)

class TCPMsgSession(_TCPSession, StreamMessageMixin):
    pass

class TCPClientMsgSession(_TCPClientSession, StreamMessageMixin):
    pass

