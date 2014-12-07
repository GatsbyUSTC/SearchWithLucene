from unittest import TestCase, skip
from message.common import HandShakeSend, HandShakeRecv
from test_message_base import MessageTest

class TestHandShake(TestCase):
    def test(self):
        tester = MessageTest(
                self, send_ctor = HandShakeSend, recv_ctor = HandShakeRecv)
        m = HandShakeRecv
        tester.add_param('name', 'dummy', m.get_name)
        tester.commit()
