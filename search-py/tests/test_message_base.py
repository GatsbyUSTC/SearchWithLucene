import logging
from message import MessageRecv

class MessageTest(object):
    def __init__(self, test_case, send_ctor, recv_ctor = None):
        self.test_case = test_case
        self.send_ctor = send_ctor
        self.recv_ctor = recv_ctor
        self.params    = []
        if recv_ctor:
            recv_ctor.register()

    def add_param(self, name, value, get_method = None):
        param_tuple = (name, value, get_method)
        self.params.append(param_tuple)

    def __build_ctor_parmas(self):
        kwargs = {}
        for param in self.params:
            (name, value, _) = param
            kwargs[name] = value
        return kwargs

    def __check_values(self, msg):
        for param in self.params:
            (name, value, get_method) = param
            if get_method:
                self.test_case.assertEqual(
                    value, get_method(msg),
                    'mismatched value for %s' % name)

    def commit(self):
        test_case = self.test_case
        kwargs    = self.__build_ctor_parmas()
        msg       = self.send_ctor(**kwargs)
        msg_str   = msg.build_msg_body()
        logging.debug('serialized message: %s', msg_str)

        if self.recv_ctor:
            msg_recv = MessageRecv.parse_message(msg_str, session = None)
            test_case.assertIsNotNone(msg_recv, 'failed to parse message')
            self.__check_values(msg_recv)

