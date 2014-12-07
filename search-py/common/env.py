import common

def register_messages():
    from message.common import register_message as register_common
    register_common()

def init_base():
    common.add_lib_path()
    register_messages()

def init_django():
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SocialTV.settings")
    from django.conf import settings
    import django
    if hasattr(django, 'setup'):
        django.setup()
    from database import models

