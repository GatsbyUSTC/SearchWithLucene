import json
import logging
from message import MessageRecv, MessageSend
class XmppMessageRecv(MessageRecv):
    __xmpp_mapping = {}

    def __init__(self, xmpp_type, *args, **kwargs):
        MessageRecv.__init__(self, *args, **kwargs)
        self.xmpp_type = xmpp_type

    @classmethod
    def register_message(cls, ctor, xmpp_type = '*', type_str = '*'):
        mapping_xmpp = __xmpp_mapping.get(xmpp_type) or {}
        mapping_xmpp[type_str]   = ctor
        __xmpp_mapping[xmpp_type] = mapping_xmpp

    @classmethod
    def __find_ctor_type(cls, mapping, type_str):
        if mapping is None:
            return None
        return mapping.get(type_str) or mapping.get('*')

    @classmethod
    def __find_ctor(cls, type_str, xmpp_type):
        return cls.__find_ctor_type(cls.__xmpp_mapping.get(xmpp_type), type_str) or \
            cls.__find_ctor_type(cls.__xmpp_mapping.get('*'), type_str)

    @staticmethod
    def __parse_raw_msg(msg):
        xmpp_type  = msg['type']
        properties = msg['properties'].get_properties()
        msg_type   = properties['type']
        body       = msg['body']
        return (body, xmpp_type, msg_type, properties)

    @classmethod
    def parse_message(cls, msg):
        """Parse a XMPP message, and return the parsed message
        Keyword arguments:
        body      -- the message body
        xmpp_type -- type of the XMPP message (chat, headline, ...)
        type_str  -- type string stated in the properties section of the message
        """
        try:
            (body, xmpp_type, msg_type, properties) = cls.__parse_raw_msg(msg)
            ctor = cls.__find_ctor(
                 type_str = type_str,
                 xmpp_type = xmpp_type)
            if constructor is None:
                logging.warning('invalid xmpp message type (xmpp_type = %s, type_str = %s): %s',
                        xmpp_type, type_str, body)
                return None
            message = constructor(
                type_str   = type_str,
                body       = body,
                xmpp_type  = xmpp_type,
                properties = properties)
            if message and message.parse(body):
                return message
            else:
                logging.warning('failed to parse message (xmpp_type = %s, type_str = %s): %s',
                        xmpp_type, type_str, body)
        except Exception:
            logging.exception('exception in parsing message: %s', msg)
        return None

class XmppMessageSend(MessageSend):
    def __init__(self, xmpp_type = 'chat', msg_id = None, *args, **kwargs):
        MessageSend.__init__(self, msg_id = msg_id, *args, **kwargs)
        self.properties = {'type': self.type_str}
        self.xmpp_type = xmpp_type

    def build_msg_body(self):
        raise NotImplementedError()

    def build_msg(self):
        client = self.session.get_client()
        msg = client.makeMessage(
            mto   = client.get_domain(),
            mbody = self.build_msg_body(),
            mtype = self.xmpp_type)
        msg['id'] = self.msg_id
        msg['properties'] = self.properties
        return msg

    def serialize(self):
        return self.build_msg()

class GenericXmppMsgSend(XmppMessageSend):
    def __init__(self, body, *args, **kwargs):
        super(XmppMessageSend, self).__init__(
            type_str = 'generic',
            xmpp_type = 'headline',
            *args, **kwargs)
        self.body = body

    def build_msg_body(self):
        return self.body

def _generic_xmpp_msg(type_str, body, xmpp_type, properties):
    return MessageRecv.parse_message(body)

def register_messages():
    XmppMessageRecv.register_message(
        ctor      = _generic_xmpp_msg,
        xmpp_type = 'generic',
        type_str  = '*')

