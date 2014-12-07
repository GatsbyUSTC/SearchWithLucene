from message import MessageSend, MessageRecv

MAGIC = 'SOCIAL-TV-BACKEND'

class HandShakeSend(MessageSend):
    def __init__(self, name, *args, **kwargs):
        super(HandShakeSend, self).__init__(
            type_str = 'handshake',
            *args,
            **kwargs)
        self.body['name']  = name
        self.body['magic'] = MAGIC

class HandShakeRecv(MessageRecv):
    def __init__(self, *args, **kwargs):
        super(HandShakeRecv, self).__init__(*args, **kwargs)
        self.name = None

    def parse(self, data):
        self.require_fields(data, 'magic', 'name')
        if MAGIC != data['magic']:
            return False
        self.name = data['name']
        return True

    def get_name(self):
        return self.name

    @classmethod
    def get_message_type(cls):
        return 'handshake'

