from handshake import HandShakeSend, HandShakeRecv
from error import ErrorSend, ErrorRecv, TimeoutSend, TimeoutRecv, IgnoredSend, IgnoredRecv
from util  import GeneralResultSend, GeneralResultRecv, GeneralRequestSend, EnterpriseRecvBase
def register_message():
    for msg_type in (HandShakeRecv, TimeoutRecv, ErrorRecv, IgnoredRecv, GeneralResultRecv, ):
        msg_type.register()
