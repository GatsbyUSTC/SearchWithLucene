from search import SearchRecv, LoadExternalRecv

def register_message():
    for msg_type in (SearchRecv,LoadExternalRecv,):
        msg_type.register()
