# Save this file as config.py to customize your settings

import logging
import os


BACKEND = 'Slack'
BOT_DATA_DIR = '/srv/data'
BOT_EXTRA_PLUGIN_DIR = '/srv/plugins'
PLUGINS_CALLBACK_ORDER = (None, )
BOT_LOG_FILE = None
BOT_LOG_LEVEL = logging.DEBUG
BOT_LOG_SENTRY = False
SENTRY_DSN = ''
SENTRY_LOGLEVEL = BOT_LOG_LEVEL
BOT_ADMINS = ('*',)
BOT_ADMINS_NOTIFICATIONS = ()
BOT_PREFIX_OPTIONAL_ON_CHAT = True
BOT_ALT_PREFIXES = ('magbot',)
BOT_ALT_PREFIX_SEPARATORS = (':', ',', ';')
HIDE_RESTRICTED_COMMANDS = True
DIVERT_TO_PRIVATE = ()
DIVERT_TO_THREAD = ()
CHATROOM_PRESENCE = ()
CHATROOM_RELAY = {}
REVERSE_CHATROOM_RELAY = {}

BOT_IDENTITY = {
    'username': os.environ.get('BOT_USERNAME'),
    'token': os.environ.get('BOT_TOKEN'),
}

CORE_PLUGINS = (
    'ACLs',
    'Backup',
    'Health',
    'Help',
    'Plugins',
    'TextCmds',
    'Utils',
    'VersionChecker',
)


# ===========================================================================
# MAGFest specific configuration
# ===========================================================================

SSH_HOST = os.environ.get('SSH_HOST', 'salt-master.example.com')
SSH_USERNAME = os.environ.get('SSH_USERNAME', 'root')
SSH_PASSWORD = os.environ.get('SSH_PASSWORD', '')
SSH_KEY = os.environ.get('SSH_KEY', '/srv/ssh/magbot_id_rsa')

SALT_HOST = os.environ.get('SALT_HOST', 'salt-master.example.com')
SALT_AUTH = os.environ.get('SALT_AUTH', 'ldap')
SALT_USERNAME = os.environ.get('SALT_USERNAME', 'username')
SALT_PASSWORD = os.environ.get('SALT_PASSWORD', 'password')
SALT_API_URL = os.environ.get('SALT_API_URL', 'https://salt-master.example.com:8000')


# ===========================================================================
# Uncomment to use Redis for storage backend
#
# Requires:
#     mkdir -p srv/storage_plugins
#     cd srv/storage_plugins
#     git clone https://github.com/sijis/err-storage-redis.git
# ===========================================================================
#
# BOT_EXTRA_STORAGE_PLUGINS_DIR = '/srv/storage_plugins'
# STORAGE = 'Redis'
# STORAGE_CONFIG = {
#     'host': '192.168.0.17',
#     'port': 6379,
#     'db': 0,
# }
