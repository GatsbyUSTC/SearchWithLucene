from message import MessageSend, MessageRecv

class ErrorSend(MessageSend):
    def __init__(self, error_id, error_msg, *args, **kwargs):
        kwargs = kwargs or {}
        if 'type_str' not in kwargs:
            kwargs['type_str'] = 'error'
        super(ErrorSend, self).__init__(*args, **kwargs)
        self.body['error_id']  = error_id
        self.body['error_msg'] = error_msg 

class ErrorRecv(MessageRecv):
    @classmethod
    def get_message_type(cls):
        return 'error'

    def parse(self, data):
        self.require_fields(data, 'error_id', 'error_msg')
        self.error_id  = data['error_id']
        self.error_msg = data['error_msg']
        return True

    def get_error_id(self):
        return self.error_id

    def get_error_msg(self):
        return self.error_msg

class TimeoutSend(ErrorSend):
    def __init__(self, *args, **kwargs):
        super(TimeoutSend, self).__init__(
            error_id  = 'timeout',
            error_msg = 'It takes too long to process the message.',
            type_str  = 'error-timeout',
            *args, **kwargs)

class TimeoutRecv(ErrorRecv):
    @classmethod
    def get_message_type(cls):
        return 'error-timeout'

    def handle_impl(self):
        self.mark_replied()

class IgnoredSend(ErrorSend):
    def __init__(self, type_str, *args, **kwargs):
        super(IgnoredSend, self).__init__(
            type_str  = 'error-ignore',
            error_id  = 'ignore',
            error_msg = 'The message of type \'%s\' was ignored.' % type_str,
            *args, **kwargs)

class IgnoredRecv(ErrorRecv):
    @classmethod
    def get_message_type(cls):
        return 'error-ignore'

    def handle_impl(self):
        self.mark_replied()

