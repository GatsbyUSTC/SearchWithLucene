import struct

class DataSend(object):
    def __init__(self, data):
        self.data = data

    def serialize(self):
        raw_data = self.data.encode('utf-8', errors = 'replace')
        length   = len(raw_data)
        return struct.pack('!I', length) + raw_data

class XmppDataSend(DataSend):
    def serialize_impl(self):
        pass

    def serialize(self):
        return self.data
