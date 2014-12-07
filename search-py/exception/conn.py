class SendFailedError(Exception):
    pass

class InvalidSessionSendError(SendFailedError):
    pass

