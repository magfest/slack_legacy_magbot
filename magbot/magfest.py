import inspect
import yaml
from datetime import datetime
from functools import wraps

import pepper
from errbot import BotPlugin, botcmd
from pepper.libpepper import PepperException


ENVS = ['prod', 'staging', 'load', 'dev']
EVENT_NAMES = ['super', 'labs', 'stock', 'west']


def _pre_salt_auth(self):
    old_token = self.auth.get('token')
    self._salt_auth()
    new_token = self.auth.get('token')
    return old_token == new_token


def _failed_salt_auth(self, is_cached_auth, error):
    if is_cached_auth and 'authentication denied' in str(error).lower():
        self.log.debug('Cached Salt API token failed, attempting to update')
        self.auth = {}
        self._salt_auth()
    else:
        raise error


def salt_auth(func):
    if inspect.isgeneratorfunction(func):
        @wraps(func)
        def with_salt_auth(self, *args, **kwargs):
            try:
                is_cached_auth = _pre_salt_auth(self)
                yield from func(self, *args, **kwargs)
            except PepperException as error:
                _failed_salt_auth(self, is_cached_auth, error)
                yield from func(self, *args, **kwargs)
    else:
        @wraps(func)
        def with_salt_auth(self, *args, **kwargs):
            try:
                is_cached_auth = _pre_salt_auth(self)
                return func(self, *args, **kwargs)
            except PepperException as error:
                _failed_salt_auth(self, is_cached_auth, error)
                return func(self, *args, **kwargs)
    return with_salt_auth


def _validate_targets_from_args(args):
    if len(args) == 0:
        raise Exception('env is required')
    if args[0] in ['to', 'help', 'list']:
        return False
    if args[0] not in ENVS:
        raise Exception('unknown env: {}, valid values: {}'.format(args[0], ', '.join(ENVS)))
    if len(args) > 1 and ':' not in args[1] and args[1] not in EVENT_NAMES:
        raise Exception('unknown event_name: {}, valid values: {}'.format(args[1], ', '.join(EVENT_NAMES)))
    if len(args) > 2 and ':' not in args[2]:
        try:
            int(args[2])
        except Exception:
            raise Exception('unknown event_year: {}, must be a valid year'.format(args[2]))
    return True


def validate_targets(func):
    if inspect.isgeneratorfunction(func):
        @wraps(func)
        def with_validate_targets(self, msg, args):
            try:
                is_command = _validate_targets_from_args(args)
            except Exception as e:
                yield 'Parse error: {} \n {}{} env [event_name] [event_year] [roles:web]'.format(
                    e, self._bot.prefix, func.__name__)
            else:
                if is_command:
                    yield from func(self, msg, args)
    else:
        @wraps(func)
        def with_validate_targets(self, msg, args):
            try:
                is_command = _validate_targets_from_args(args)
            except Exception as e:
                return 'Parse error: {} \n {}{} env [event_name] [event_year] [roles:web]'.format(
                    e, self._bot.prefix, func.__name__)
            else:
                if is_command:
                    return func(self, msg, args)
    return with_validate_targets


class MAGFest(BotPlugin):

    def __init__(self, *args, **kwargs):
        self.api = None
        self.auth = {}
        super().__init__(*args, **kwargs)

    def _salt_auth(self):
        """
        The Salt API returns an auth dictionary that looks like this::

            self.auth = {
                'user': 'username',
                'perms': [{'*': ['.*']}],
                'eauth': 'ldap',
                'start': 1535780898.745305,
                'expire': 1535824098.745305,
                'token': 'XXXXXXXXXXXXX',
            }
        """
        if self.auth.get('expire'):
            seconds_to_expiration = (datetime.fromtimestamp(self.auth['expire']) - datetime.utcnow()).total_seconds()
            if seconds_to_expiration > 1800:
                # The auth token won't expire for at least 30 minutes
                self.log.debug('Using cached Salt API auth token')

        try:
            self.auth = self.api.login(
                self.bot_config.SALT_USERNAME, self.bot_config.SALT_PASSWORD, self.bot_config.SALT_AUTH)
            self.log.debug('Updated cached Salt API auth token')
        except Exception:
            self.log.error('Failed to authenticate against Salt API: user="{}", auth="{}"'.format(
                self.bot_config.SALT_USERNAME, self.bot_config.SALT_AUTH), exc_info=True)
            raise

    def _extract_jid_and_minions(self, results):
        if results.get('return'):
            result = results['return'][0]
            return (result.get('jid', None), result.get('minions', []))
        return (None, [])

    def _format_results(self, results):
        result = results.get('return', [])
        if len(result) == 1:
            result = result[0]
        return yaml.dump(result, default_flow_style=False)

    def _format_targets(self, args):
        targets = ['G@roles:reggie']
        for grain, value in zip(['env', 'event_name', 'event_year'], args):
            if value:
                if ':' in value:
                    grain, _, value = value.partition(':')
                targets.append('G@{}:{}'.format(grain, value))
        return ' and '.join(targets)

    def activate(self):
        try:
            self.api = pepper.Pepper(self.bot_config.SALT_API_URL)
            self.log.debug('Salt API: {}'.format(self.bot_config.SALT_API_URL))
        except Exception:
            self.log.error('Failed to initialize Salt API: {}'.format(self.bot_config.SALT_API_URL), exc_info=True)
            raise
        super().activate()

    @botcmd
    @salt_auth
    def job(self, msg, jid):
        """Lookup results of a job"""
        self.send(msg.frm, 'Looking up job {}... (takes a few minutes)'.format(jid), in_reply_to=msg)
        results = self.api.runner('jobs.lookup_jid', jid=jid)
        self.send(msg.frm, self._format_results(results), in_reply_to=msg)

    @botcmd(split_args_with=None)
    @validate_targets
    @salt_auth
    def ping(self, msg, args):
        """Pings target servers"""
        targets = self._format_targets(args)
        results = self.api.local(targets, 'test.ping', expr_form='compound')
        return self._format_results(results)

    @botcmd(split_args_with=None)
    @validate_targets
    @salt_auth
    def deploy(self, msg, args):
        """Deploy reggie to target servers"""
        yield 'Deploying latest to {}... (takes a few minutes)'.format(' '.join(args))
        targets = self._format_targets(args)
        results = self.api.local_async(targets, 'state.apply', expr_form='compound')
        jid, minions = self._extract_jid_and_minions(results)
        if minions:
            yield '**Started job id**: {} \n ' \
                '**Target servers**: \n {} \n ' \
                '**For results**: \`{}job {}\`'.format(jid, '\n'.join(sorted(minions)), self._bot.prefix, jid)
        else:
            yield 'No job started, no servers found for {}'.format(' '.join(args))
