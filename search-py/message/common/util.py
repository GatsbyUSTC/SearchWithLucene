from __future__ import absolute_import
from functools import wraps
from message import MessageSend, MessageRecv, config

class GeneralResultSend(MessageSend):
    def __init__(self, result, *args, **kwargs):
        super(GeneralResultSend, self).__init__(
            type_str = 'result', *args, **kwargs)
        self.body.update(result)

class GeneralResultRecv(MessageRecv):
    def parse(self, data):
        self.result = data
        return self.get_flag(config.FLAG_RESPONSE)

    def get_result(self):
        return self.result

    @classmethod
    def get_message_type(cls):
        return 'result'

class GeneralRequestSend(MessageSend):
    def __init__(self, type_str, request, *args, **kwargs):
        super(GeneralRequestSend, self).__init__(
            type_str = type_str, *args, **kwargs)
        self.body.update(request)

class EnterpriseRecvBase(MessageRecv):
    def __require_enterprise(self, func):
        from database import models
        if not func:
            return None
        @wraps(func)
        def wrapper(*args, **kwargs):
            euser = models.EnterpriseUser.objects.select_related('enterprise') \
                .filter(user = self.user_id)[:1]
            if not len(euser):
                self.error(
                    error_id  = 'not-enterprise',
                    error_msg = 'You are not an Enterprise user.')
                return
            self.enterprise = euser[0].enterprise
            return func(*args, **kwargs)
        return wrapper

    def parse(self, data):
        self.require_fields(data, 'user_id')
        self.user_id = data['user_id']
        return self.parse_enterprise(data)

    def handle_impl(self):
        func = self.__require_enterprise(self.handle_enterprise)
        func()

    def parse_enterprise(self, data):
        return True

    def handle_enterprise(self):
        raise NotImplementedError()

