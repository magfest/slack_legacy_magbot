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
    'CommandNotFoundFilter',
    'Health',
    'Help',
    'Plugins',
    'TextCmds',
    'Utils',
    'VersionChecker',
)
