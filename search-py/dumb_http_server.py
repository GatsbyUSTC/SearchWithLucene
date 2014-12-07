from functools import partial
import json
import logging
import string
import tornado.web
from tornado.ioloop import IOLoop
from common.task import ProcessMsgTask
from connection import BaseServer
from message import BaseMessage, MessageRecv, MessageSend

class _DummySession(object):
    ioloop = IOLoop.instance()
    def __init__(self, session_mgr, response):
        self.session_mgr = session_mgr
        self.response    = response
        self.closed      = False

    def get_session_mgr(self):
        return self.session_mgr

    def close(self):
        self.closed = True

    def write_message(self, msg, callback, targeted):
        if self.closed:
            return
        self.closed = True
        body = msg.build_msg_body()
        body = json.loads(body)
        del body['__id']
        del body['__flags']
        if '__timeout' in body:
            del body['__timeout']
        body = json.dumps(body)
        def write_result():
            self.response.write(body)
            self.response.finish()
        self.ioloop.add_callback(callback = write_result)

class _PseudoSend(MessageSend):
    def __init__(self, content):
        body     = json.loads(content)
        msg_id   = body.get('__id') or BaseMessage.gen_msg_id()
        type_str = body['type']
        super(_PseudoSend, self).__init__(
            type_str = type_str,
            msg_id   = msg_id)
        self.body = body

class ArbitraryRecv(MessageRecv):
    def parse(self, data):
        from message import config
        return self.get_flag(config.FLAG_RESPONSE)

    @classmethod
    def get_message_type(cls):
        return '*'

    def handle_impl(self):
        self.error(
            error_id  = 'message-type',
            error_msg = 'unknown message type (%s)' % self.get_type())
        self.mark_replied()

class PseudoRecv(MessageRecv):
    def __init__(self, body, session, remote):
        super(PseudoRecv, self).__init__(
            msg_id   = BaseMessage.gen_msg_id(),
            type_str = body['type'],
            flags    = 0,
            body     = json.dumps(body),
            session  = session,
            timeout  = 60)

        self.remote = remote

    def handle_impl(self):
        msg = _PseudoSend(content = self.body_str)
        logging.debug('built packet: %s', msg.build_msg_body())
        self.send_internal(
            session = self.remote,
            message = msg,
            recv_callback = self.__handle_recv)

    def __handle_recv(self, msg):
        self.reply(_PseudoSend(content = msg.body_str))

class _MainHandler(tornado.web.RequestHandler):
    ioloop  = IOLoop.instance()
    AUTH_ON = False
    def initialize(self, server):
        self.server  = server
        self.message = None
        self.session_mgr = self.server.session_mgr

    def prepare(self):
        if not self.AUTH_ON:
            return
        from django.conf import settings
        cookie_name = settings.SESSION_COOKIE_NAME
        key = self.get_cookie(name = cookie_name)
        if not key:
            from tornado.web import HTTPError
            raise HTTPError(400)
        from django.contrib.sessions.backends.db import SessionStore
        s = SessionStore(session_key=key)
        from django.contrib.auth import SESSION_KEY
        user_id = s.get(SESSION_KEY)
        if not user_id:
            from tornado.web import HTTPError
            raise HTTPError(400)
        self.user_id = user_id

    def on_connection_close(self):
        message      = self.message
        self.message = None
        message.session.close()
        message.on_timeout()

    def __build_message(self, user_id, body, remote):
        logging.debug("request: %s", body)
        body = json.loads(body)
        body['user_id']  = user_id
        body['__header'] = self.request.headers

        session = _DummySession(
            session_mgr = self.server.session_mgr,
            response    = self)

        self.message = PseudoRecv(
            body    = body,
            session = session,
            remote  = remote)

        ProcessMsgTask(self.message).queue()

    def write_error_msg(self, error_id, error_msg):
        body = {
            "type":         "error",
            "error_id":     error_id,
            "error_msg":    error_msg
        }
        def write_result():
            self.write(json.dumps(body))
            self.finish()
        self.ioloop.add_callback(callback = write_result)

    def parse_service_name(self, name):
        VALID_RANGE = string.ascii_lowercase + string.digits + '-' + '_'
        if not name or len(name) < 2 or string.lower(name[0])!= 's':
            return None
        name = string.lower(name)
        while len(name) and (name[-1] not in VALID_RANGE):
            name = name[:-1]
        return name

    @tornado.web.asynchronous
    def post(self, service_name):
        if self.AUTH_ON:
            user_id = self.user_id
        else:
            user_id = int(self.get_query_argument('user_id', '17'))
        service_name = self.parse_service_name(service_name)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        if not service_name:
            self.write_error_msg(
                error_id  = 'service_name',
                error_msg = 'unspecified service name.')
        remote = self.session_mgr.session_by_name(service_name)
        if not remote:
            self.write_error_msg(
                error_id  = 'service_name',
                error_msg = 'service %s does not exist.' % service_name)
        else:
            self.__build_message(user_id, self.request.body, remote)

class DumbHttpServer(BaseServer):
    def __init__(self, listen_port, *args, **kwargs):
        super(DumbHttpServer, self).__init__(*args, **kwargs)
        application = tornado.web.Application([
            (r"/(.*)", _MainHandler, dict(server = self)),
        ])
        self.application   = application
        self.listen_port   = listen_port

    def start(self):
        self.application.listen(self.listen_port)
        ArbitraryRecv.register()

    def shutdown(self):
        ArbitraryRecv.cancel_register()

