from functools import partial
import logging
from Queue import Queue, Empty
from sleekxmpp import ClientXMPP
from sleekxmpp.jid import JID
from sleekxmpp.exceptions import IqError, IqTimeout
from threading import Thread, Semaphore, Lock, Event
from tornado.iostream import StreamClosedError
from common import invoke
from connection import BaseConnection, BaseServer, BaseSessionNew,  \
    BaseMessageMixin, BaseSessionInit
from message import XmppMessageRecv, XmppMessageSend
from message.stanza import register_stanza_plugins

class XmppConnection(ClientXMPP, BaseConnection, BaseServer):
    def start(self):
        self.connect(address = self.server_addr)
        self.process(block = False)

    def shutdown(self):
        self.close()

    def __init__(self, jid, password, server_addr, local_name,  \
            session_mgr, server_port = 5222):
        ClientXMPP.__init__(self, jid, password)
        BaseConnection.__init__(self)
        BaseServer.__init__(
            self,
            local_name  = local_name,
            session_mgr = session_mgr)

        self.add_event_handler('session_start', self.__session_start)
        self.add_event_handler('session_end', self.__session_end)
        self.add_event_handler('message', self.__on_message)
        self.add_event_handler('got_online', self.__roster_online)
        self.add_event_handler('got_offline', self.__roster_offline)
        self.register_plugin('xep_0199') # XMPP Ping
        self.register_plugin('xep_0033') # Extended Stanza Addressing
        register_stanza_plugins()

        import ssl
        self.ssl_version    = ssl.PROTOCOL_SSLv3
        self.server_addr    = server_addr
        self.write_pending  = Queue()
        self.write_thread   = None
        self.write_sema4    = None
        self.sessions       = {}
        self.server_addr    = (server_addr, server_port)
        self.local_name     = JID(jid).bare
        self.session_lock   = Lock()

    def ready(self):
        return self.write_thread is not None

    def read(self, expect_len = None, callback = None):
        raise NotImplementedError()

    def build_identifier_by_jid(self, jid):
        return 'xmpp![%s]:%s' % (self.local_name, jid)

    def ensure_session_exists(self, jid):
        if JID(jid).bare == self.local_name:
            return None
        identifier = self.build_identifier_by_jid(jid)
        self.session_mgr.ensure_session_exists(
            key = identifier, connection = self,
            ctor = XmppSession,
            kwargs = {
                'local_name': self.local_name,
                'target_jid': jid,
                'identifier': identifier})
        session = self.session_mgr.session_by_identifier(identifier)
        if session:
            with self.session_lock:
                self.sessions[str(jid)] = session
        return session

    def remove_session(self, jid):
        jid = str(jid)
        with self.session_lock:
            if self.sessions.get(jid):
                del self.sessions[jid]

    def __on_message(self, msg):
        session = self.ensure_session_exists(msg['from'])
        if session:
            session.queue_message(msg)

    def __check_closed(self):
        if not self.ready():
            raise StreamClosedError("Stream is closed")

    def write(self, data, callback = None):
        self.__check_closed()
        if not isinstance(data, XmppMessageSend):
            msg = self.build_msg(data)
        else:
            msg = data
        self.write_pending.put((msg, callback))

    @staticmethod
    def build_msg(msg):
        from message.xmpp import GenericXmppMsgSend
        session = msg.session
        return GenericXmppMsgSend(
            session = session,
            body    = msg.build_msg_body())

    def close(self):
        self.disconnect()

    def __get_socket_obj(self):
        return self.socket

    def get_local_addr(self):
        if self.ready():
            sock = self.__get_socket_obj()
            return sock.getsockname()
        return None

    def get_remote_addr(self):
        if self.ready():
            sock = self.__get_socket_obj()
            return sock.getsockname()
        return None

    def get_roster_name(self, jid):
        if not isinstance(jid, JID):
            if jid.find('@') > -1:
                jid = JID(jid)
            else:
                jid = JID(local=jid, domain=self.boundjid.domain)
        rosters = self.client_roster
        jid = jid.bare
        if rosters.has_jid(jid):
            return rosters[jid]['name']
        logging.error('failed to parse jid ' + jid)
        return jid

    def __roster_online(self, presence):
        jid = presence['from']
        self.ensure_session_exists(jid)
        self.invoke_handler(
            'roster_online', kwargs = {
                'jid':  jid,
                'name': self.get_roster_name(jid)
            })

    def __roster_offline(self, presence):
        jid = presence['from']
        self.session_mgr.remove_session_by_key(jid)
        self.remove_session(jid)
        self.invoke_handler(
            'roster_offline', kwargs = {
                'jid':  jid,
                'name': self.get_roster_name(jid)
            })

    def __session_start(self, _):
        self.send_presence()
        try:
            self.get_roster()
            self.__start_threads()
        except IqError as err:
            logging.error('There was an error getting the roster')
            logging.error(err.iq['error']['condition'])
            self.disconnect()
        except IqTimeout:
            logging.error('Server is taking too long to respond')
            self.disconnect()

    def __start_threads(self):
        self.write_sema4 = Semaphore(0)
        started_event    = Event()
        thread = Thread(
            target = self.__write_loop,
            name = 'xmpp_send',
            kwargs = { 'started_event': started_event })
        thread.daemon = True
        self.write_thread = thread
        thread.start()
        started_event.wait()

    def __stop_threads(self):
        self.write_sema4.release()
        thread = self.write_thread
        self.write_thread = None
        self.write_sema4  = None
        thread.join(1)

    def __session_end(self, _):
        self.__stop_threads()
        sessions = None
        with self.session_lock:
            sessions = self.sessions
            self.sessions = {}
        for session in sessions.values():
            session.drop_connection()

    def __write_loop(self, started_event):
        started_event.set()
        while self.write_thread:
            self.write_sema4.acquire(True)
            try:
                (msg, callback) = self.write_pending.get_nowait()
            except Empty:
                continue
            succeed = True
            try:
                self.send(msg, now = True)
            except Exception:
                succeed = False
                logging.exception('failed to write %s', msg)
            finally:
                invoke(callback = callback, kwargs = {'succeed': succeed})

class _XmppInit(BaseSessionInit):
    def start(self):
        session = self.session
        name = session.connection.get_name()
        session.set_name(name)
        self.finish(True)

class _XmppSessionConnection(BaseConnection):
    def __init__(self, client, target_jid):
        super(_XmppSessionConnection, self).__init__()
        self.client         = client
        self.target_jid     = target_jid
        self.read_callback  = None
        self.ready2read     = Queue()
        self.read_lock      = Lock()

    def get_target_jid(self):
        return self.target_jid

    def get_identifier(self):
        return self.client.build_identifier_by_jid(self.target_jid)

    def ready(self):
        return self.client.ready()

    def queue_message(self, msg):
        callback = None
        with self.read_lock:
            callback = self.read_callback
            self.read_callback = None
            if not callback:
                self.ready2read.put(msg)
                return
        self.__serve_read(callback = callback, msg = msg)

    @staticmethod
    def __serve_read(callback, msg):
        invoke(callback = callback, kwargs = { 'data': msg})

    def __check_closed(self):
        if not self.client.ready():
            raise StreamClosedError("Stream is closed")

    def read(self, expect_len = None, callback = None):
        packet = None
        with self.read_lock:
            assert not self.read_callback
            self.read_callback = callback
            if self.ready2read.qsize():
                try:
                    packet = self.ready2read.get_nowait()
                    self.read_callback = None
                except Empty:
                    pass
        if packet:
            self.__serve_read(callback, packet)
        else:
            try:
                self.__check_closed()
            except:
                self.read_callback = None
                raise

    def write(self, data, callback = None):
        self.client.write(data = data, callback = callback)

    def close(self):
        self.client.remove_session(self.get_target_jid())
        self.invoke_handler('disconnect')

    def get_name(self):
        return self.client.get_roster_name(self.target_jid)

    def get_remote_addr(self):
        return self.target_jid

    def get_local_addr(self):
        return self.client.get_local_addr()

class _XmppSessionBase(BaseSessionNew):
    def __init__(self, connection, target_jid, *args, **kwargs):
        client = connection
        connection = _XmppSessionConnection(client, target_jid)
        super(_XmppSessionBase, self).__init__(connection, *args, **kwargs)

    def init_session(self, handler):
        initializer = _XmppInit(self, handler = handler)
        initializer.start()

    def queue_message(self, msg):
        self.connection.queue_message(msg)

class _XmppMessageMixin(BaseMessageMixin):
    def build_body(self, msg):
        return msg

    def build_msg(self, data):
        return XmppMessageRecv.parse_message(data)

    def read_message(self, callback = None, args = (), kwargs = {}):
        self.read_invoke_now(
            expect_len = None,
            callback   = partial(
                self.handle_msg, callback = callback,
                args = args, kwargs = kwargs))

class XmppSession(_XmppSessionBase, _XmppMessageMixin):
    pass
