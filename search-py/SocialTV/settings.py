import os
# Django settings for SocialTV project.

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'socialtv',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'socialtv',
        'PASSWORD': 'SocialTV',
        'HOST': '155.69.146.82',        # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
        'OPTIONS': {
            "init_command": "SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED", # for lower version of MySQL: storage_engine=INNODB
            #"autocommit":  True,
        },
        'CONN_MAX_AGE': 2 * 60 * 60, # 2 hours. The lifetime of a database connection, in seconds.
    }
}

# issue: (2006, 'MySQL server has gone away')
#[mysqld]
#interactive_timeout=180
#wait_timeout=180

SESSION_EXPIRE_AT_BROWSER_CLOSE=True
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
#TIME_ZONE = None
TIME_ZONE = 'Asia/Singapore'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    #'/host/Dropbox/socialtv/temp/portal/static',
    #'/var/www/SocialTV/static/',
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'rdla2uc=hqxn%%^8fczsoj4e&20y###h)x1c4f1s%td9(9q$@r'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'SocialTV.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'SocialTV.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'database',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

LOGIN_URL = '/'
SERVER_EMAIL = 'cloud.centric.media.platform@gmail.com'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'cloud.centric.media.platform@gmail.com'
EMAIL_HOST_PASSWORD = 'ccmp111111'

PORTAL_SERVER = '155.69.146.82'
PORTAL_PORT = 9999

PORTAL_URL = 'http://%s:%d/' % (PORTAL_SERVER, PORTAL_PORT)
VIDEO_TEMP_URL = 'http://127.0.0.1:9797/'
TORNADO_ADDR = 'http://localhost:7080/%s/'

XMPP_SERVER  = '155.69.146.82'
XMPP_PORT    = 5222
XMPP_DOMAIN  = 'socialtv'
XMPP_URL     = PORTAL_URL + 'http-bind/'
XMPP_MGR_URL = 'http://155.69.146.82:9090/plugins/userService/userservice?'
XMPP_MGR_KEY = 'Y73n8erj'
XMPP_MGR_ADD_USER   = XMPP_MGR_URL + 'type=add&secret=' + XMPP_MGR_KEY + '&username={account}&password={pwd}&name={name}&email={email}'
XMPP_MGR_ADD_ROSTER = XMPP_MGR_URL + 'type=add_roster&secret=' + XMPP_MGR_KEY + '&username={account}&item_jid={other_jid}&name={other_name}&subscription=3'

HDFS_VIDEO_PATH = 'http://155.69.146.82:9999/raw_video/'
HDFS_IMG_PATH   = 'http://155.69.146.82:9999/content/files/'
SHARED_CONTENT_URL = 'http://155.69.146.82:9999/migration/contents/'

BASE_DIR = '/var/www/SocialTV'
TEMP_DIR = os.path.join(BASE_DIR, 'temp/')
UPLOAD_PREFIX = 'upload/'
UPLOAD_DIR = os.path.join(TEMP_DIR, UPLOAD_PREFIX)
UPLOAD_VIDEO_URL = VIDEO_TEMP_URL + UPLOAD_PREFIX
YOUTUBE_PREFIX = 'youtube/'
YOUTUBE_DIR = os.path.join(TEMP_DIR, YOUTUBE_PREFIX)
YOUTUBE_VIDEO_URL = VIDEO_TEMP_URL + YOUTUBE_PREFIX
SESSION_KEY_FOREGROUND_IMAGE = os.path.join(BASE_DIR, 'foreground.png')
SESSION_KEY_BASE_URL = PORTAL_URL + 'f/'
SESSION_KEY_PRIVATE_OLD_STYLE = True

UPLOAD_DIR_READABLE = os.path.join(UPLOAD_DIR, 'readable/')
UPLOAD_DIR_READABLE_URL = '/static/upload/'
HDFS_COMMAND = ['./hdfs', 'dfs', '-put', '{input}',     \
    'hdfs://169.254.1.36:54310/social-tv/contents/']

SEARCH_URL = 'http://127.0.0.1:8080'