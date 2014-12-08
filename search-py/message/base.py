from __future__ import absolute_import
from datetime import timedelta
from tornado.ioloop import IOLoop
from functools import wraps
import json
import logging
import random
from threading import Lock
from common import now_time
from exception import MissingArgumentError, WrongPacketTypeError, InvalidSessionSendError
from message import config

class BaseMessage(object):
    MASK_ID    = (1 << config.LENGTH_ID) - 1
    MASK_FLAGS = (1 << (32 - config.LENGTH_ID)) - 1

    @classmethod
    def gen_msg_id(cls):
        return random.getrandbits(config.LENGTH_ID) & cls.MASK_ID

    def __init__(self, msg_id, type_str, flags):
        self.__msgid = msg_id & self.MASK_ID
        self.__type  = type_str
        self.__flags = flags
        self.__time  = now_time()

    def get_creation_time(self):
        return self.__time

    def get_type(self):
        return self.__type

    def get_msgid(self):
        return self.__msgid

    def set_msgid(self, msg_id):
        self.__msgid = msg_id

    def get_flags(self):
        return self.__flags

    def get_flag(self, flag):
        return bool(self.__flags & flag)

    def set_flags(self, flags):
        self.__flags = flags & self.MASK_FLAGS

    def set_flag(self, flag, is_on = True):
        new_flags = self.__flags & ~flag
        if is_on:
            new_flags = new_flags | flag
        self.__flags = new_flags

class MessageSend(BaseMessage):
    def __init__(self, type_str, msg_id = None, flags = 0, session = None):
        BaseMessage.__init__(
            self,
            msg_id = msg_id or self.gen_msg_id(),
            type_str = type_str,
            flags = flags)
        self.body = {}
        self.session = session

    def build_msg_body(self):
        body = self.body
        body['__id']    = self.get_msgid()
        body['__flags'] = self.get_flags()
        body['type']    = self.get_type()
        return json.dumps(body)

    def build_msg(self):
        from connection import DataSend
        body = self.build_msg_body()
        return DataSend(body)

    def serialize(self):
        return self.build_msg().serialize()

class MessageRecv(BaseMessage):
    __message_mapping   = {}
    __pending_callbacks = {}
    __global_lock       = Lock()

    def __init__(self, msg_id, flags, type_str, body, session, timeout = None):
        super(MessageRecv, self).__init__(
            msg_id   = msg_id,
            type_str = type_str,
            flags    = flags)
        self.body_str  = body
        self.__replied = False
        self.session   = session
        self.__timeout = timedelta(seconds = timeout or 30.0)
        self.__timeout_handle  = None
        self.__timeout_removed = False
        self.pending_callback  = None
        self.__set_timeout()

    @staticmethod
    def require_fields(data, *args):
        missed = []
        for arg in args:
            if not arg in data:
                missed.append(arg)
        if len(missed):
            raise MissingArgumentError(missed)

    def parse(self, data):
        return True

    @classmethod
    def get_message_type(cls):
        raise NotImplementedError()

    def __remove_timeout(self):
        ioloop = IOLoop.instance()
        handle = self.__timeout_handle
        if handle:
            self.__timeout_handle = None
            ioloop.remove_timeout(handle)
        self.__timeout_removed = True

    def __set_timeout(self):
        if self.is_timeouted():
            self.on_timeout()
            return
        ioloop = IOLoop.instance()
        deadline = self.__timeout
        def add_timeout():
            handle = ioloop.add_timeout(deadline, self.on_timeout)
            self.__timeout_handle = handle
        ioloop.add_callback(callback = add_timeout)

    def handle_impl(self):
        from message.common import IgnoredSend
        msg = IgnoredSend(
            msg_id   = self.get_msgid(),
            type_str = self.get_type())
        self.reply(msg)

    def is_timeouted(self):
        return now_time() >= (self.get_creation_time() + self.__timeout)

    def on_timeout(self):
        if self.__timeout_removed:
            return
        if not self.__replied:
            logging.info("timeout on message %s", self.body_str)
        from message.common import TimeoutSend
        msg = TimeoutSend()
        self.reply(msg)

    def __build_wrapper(self, func):
        if not func:
            return None
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as err:
                self.error_by_exception(err)
                logging.exception(str(func))
        wrapper.message = self
        return wrapper

    def handle(self):
        if self.__replied or self.is_timeouted():
            return
        impl = self.pending_callback
        try:
            from django.conf import settings
            if settings.configured:
                # has django
                from django.core.signals import request_started, request_finished
                request_finished.send(sender = type(self))
                request_started.send(sender = type(self))
        except Exception:
            pass
        if not impl or not self.get_flag(config.FLAG_RESPONSE):
            impl = self.__build_wrapper(self.handle_impl)
            impl()
        else:
            self.__remove_timeout()
            impl(msg = self)

    def mark_replied(self):
        self.__replied = True

    def reply(self, msg):
        if self.__replied:
            return
        self.__replied = True
        self.__remove_timeout()
        msg.set_flag(config.FLAG_RESPONSE)
        msg.set_msgid(self.get_msgid())
        self.send_internal(self.session, message = msg)

    def reply_result(self, **kwargs):
        from message.common import GeneralResultSend
        msg = GeneralResultSend(result = kwargs)
        self.reply(msg)

    def error_by_exception(self, err):
        error_id  = type(err).__name__
        error_msg = str(err)
        self.error(error_id = error_id, error_msg = error_msg)

    def error(self, error_id, error_msg):
        from message.common import ErrorSend
        msg = ErrorSend(error_id = error_id, error_msg = error_msg)
        self.reply(msg)

    def send_internal(self, session, message, \
            send_callback = None, recv_callback = None):
        send_callback = self.__build_wrapper(send_callback)
        recv_callback = self.__build_wrapper(recv_callback)
        is_request    = self.session != session
        self.register_pending(message.get_msgid(), recv_callback)
        try:
            session.write_message(
                msg      = message,
                callback = send_callback,
                targeted = not is_request)
        except Exception as err:
            if is_request:
                self.error_by_exception(err)
            logging.exception("send %s to %s", message, session)
            self.remove_pending(message.get_msgid())

    def send(self, target_name, message, \
            send_callback = None, recv_callback = None):
        timeout = self.__timeout + self.get_creation_time() - now_time()
        message.body['__timeout'] = timeout.total_seconds()
        def dummy():
            session_mgr = self.session.get_session_mgr()
            target = session_mgr.session_by_name(name = target_name)
            if not target:
                raise InvalidSessionSendError('service not found.')
            self.send_internal(
                session = target,
                message = message,
                send_callback = send_callback,
                recv_callback = recv_callback)
        impl = self.__build_wrapper(dummy)
        impl()

    def send_request(self, target_name, type_str, request,      \
            send_callback = None, recv_callback = None):
        from message.common import GeneralRequestSend
        msg = GeneralRequestSend(type_str = type_str, request = request)
        self.send(target_name = target_name, message = msg,     \
            send_callback = send_callback, recv_callback = recv_callback)

    @classmethod
    def register_pending(cls, msg_id, callback):
        if not callback:
            return
        logging.debug("register callback %s for message %d.", callback, msg_id)
        with cls.__global_lock:
            cls.__pending_callbacks[msg_id] = callback

    @classmethod
    def remove_pending(cls, msg_id):
        with cls.__global_lock:
            if cls.__pending_callbacks.get(msg_id):
                del cls.__pending_callbacks[msg_id]

    @classmethod
    def __check_pending(cls, msg):
        if not msg.get_flag(config.FLAG_RESPONSE):
            return msg
        from message.common import TimeoutRecv
        msg_id = msg.get_msgid()
        with cls.__global_lock:
            if msg_id in cls.__pending_callbacks:
                callback = cls.__pending_callbacks[msg_id]
                msg.pending_callback = callback
                del cls.__pending_callbacks[msg_id]
                if isinstance(msg, TimeoutRecv):
                    original = callback.message
                    if original:
                        original.on_timeout()
        return msg

    @classmethod
    def register(cls):
        cls.register_message(
            ctor     = cls,
            msg_type = cls.get_message_type())

    @classmethod
    def cancel_register(cls):
        cls.register_message(
            ctor     = None,
            msg_type = cls.get_message_type())

    @staticmethod
    def __send_failed(session, msg_id, error_id, error_msg):
        from message.common import ErrorSend
        try:
            failed_msg = ErrorSend(
                error_id  = error_id,
                error_msg = error_msg)
            failed_msg.set_flag(config.FLAG_RESPONSE)
            failed_msg.set_msgid(msg_id)
            session.write_message(
                msg      = failed_msg,
                targeted = True)
        except Exception:
            logging.exception("send error")

    @classmethod
    def parse_message(cls, body, session):
        msg_id = None
        logging.debug("%s recv %s", session, body)
        try:
            body_str    = body
            body        = json.loads(body)
            type_str    = body['type']
            msg_id      = body['__id']
            flags       = body['__flags']
            timeout     = body.get('__timeout')
            constructor = cls.__message_mapping.get(type_str)
            if constructor is None:
                constructor = cls.__message_mapping.get('*')
                if not constructor:
                    logging.warning(
                        'invalid message type (%s): %s',
                        type_str, json.dumps(body))
                    cls.__send_failed(
                        session, msg_id = msg_id, error_id = 'invalid-type',
                        error_msg = 'unknown message type.')
                    return None
            message = constructor(
                msg_id   = msg_id,
                type_str = type_str,
                flags    = flags,
                body     = body_str,
                timeout  = timeout,
                session  = session)
            del body['type']
            if message and message.parse(body):
                message = cls.__check_pending(message)
                return message
            else:
                logging.warning(
                    'failed to parse message (%s): %s',
                    type_str, json.dumps(body))
                cls.__send_failed(
                    session, msg_id = msg_id, error_id = 'parse',
                    error_msg = 'failed to parse message.')
                return None
        except Exception as err:
            logging.exception("exception in parsing message: %s", body)
            if msg_id:
                cls.__send_failed(
                    session, msg_id = msg_id, error_id = 'parse-general',
                    error_msg = 'failed to parse message (%s).' % str(err))
            return None

    @classmethod
    def register_message(cls, ctor, msg_type):
        if ctor:
            cls.__message_mapping[msg_type] = ctor
        else:
            if msg_type in cls.__message_mapping:
                del cls.__message_mapping[msg_type]

    @staticmethod
    def expect_packet(msg, packet_type, description = None):
        if not isinstance(msg, packet_type):
            description = description or        \
                'expected %s, got %s' % (packet_type, type(msg))
            logging.debug(description + '\n%s', msg.body_str)
            raise WrongPacketTypeError(description)

def expect_packet(func, packet_type, description = None):
    @wraps(func)
    def wrapper(*args, **kwargs):
        msg = kwargs['msg']
        MessageRecv.expect_packet(msg, packet_type, description)
        return func(*args, **kwargs)
    return wrapper
