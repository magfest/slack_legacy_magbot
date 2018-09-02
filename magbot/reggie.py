import yaml
from collections import OrderedDict
from datetime import datetime
from functools import wraps

import pepper
from errbot import BotPlugin, botcmd
from fabric.connection import Connection
from fabric.config import Config
from pepper.libpepper import PepperException


def monkeypatch(Class, method_name):
    original_method = getattr(Class, method_name)

    def monkeypatch_decorator(func):
        if not hasattr(original_method, '_monkeypatch_'):
            @wraps(original_method)
            def with_monkeypatch(self, *args, **kwargs):
                return func(self, original_method, *args, **kwargs)
            with_monkeypatch._monkeypatch_ = True
            setattr(Class, method_name, with_monkeypatch)
            return with_monkeypatch
    return monkeypatch_decorator


@monkeypatch(Connection, 'run')
def _Connection_run(self, original_method, *args, **kwargs):
    kwargs['in_stream'] = False
    return original_method(self, *args, **kwargs)


@monkeypatch(Connection, 'sudo')
def _Connection_sudo(self, original_method, *args, **kwargs):
    kwargs['in_stream'] = False
    return original_method(self, *args, **kwargs)


ENVS = ['prod', 'staging', 'load', 'dev']
EVENT_NAMES = ['super', 'labs', 'stock', 'west']


def salt_auth(func):
    @wraps(func)
    def with_salt_auth(self, *args, **kwargs):
        old_token = self.auth.get('token')
        self._salt_auth()
        new_token = self.auth.get('token')
        try:
            yield from func(self, *args, **kwargs)
        except PepperException as error:
            if old_token == new_token and 'authentication denied' in str(error).lower():
                self.log.debug('Cached Salt API token failed, attempting to update')
                self.auth = {}
                self._salt_auth()
                yield from func(self, *args, **kwargs)
            else:
                raise error
    return with_salt_auth


def parse_grain_args(func):
    @wraps(func)
    def with_parse_grain_args(self, msg, args):
        grain_args = ['event_year', 'event_name', 'env']
        grains = OrderedDict()
        regex_grains = OrderedDict()
        for arg in args:
            if ':' in arg:
                grain, _, value = arg.partition(':')
                if value:
                    regex_grains[grain] = value
            elif grain_args and arg:
                grains[grain_args.pop()] = arg

        error = None
        if 'env' not in grains or not grains['env']:
            error = 'env is required'
        elif grains['env'] in ['to', 'help', 'list']:  # Legacy deploy command, ignore
            yield None
        elif grains['env'] not in ENVS:
            error = 'unknown env: \`{}\`, valid values: {}'.format(grains['env'], ', '.join(ENVS))
        elif 'event_name' in grains and grains['event_name'] not in EVENT_NAMES:
            error = 'unknown event_name: \`{}\`, valid values: {}'.format(grains['event_name'], ', '.join(EVENT_NAMES))
        elif 'event_year' in grains:
            try:
                int(grains['event_year'])
            except Exception:
                error = 'unknown event_year: \`{}\`, must be a valid year'.format(grains['event_year'])

        if error:
            yield 'Parse error: {} \n ' \
                  'Usage: \`{}{} env [event_name] [event_year] [roles:(web|db)]\`'.format(
                      error, self._bot.prefix, func.__name__)

        else:
            targets = ['G@roles:reggie']
            for grain, value in grains.items():
                targets.append('G@{}:{}'.format(grain, value))
            for grain, value in regex_grains.items():
                targets.append('P@{}:{}'.format(grain, value))
            targets = ' and '.join(targets)

            yield from func(self, msg, args, grains, regex_grains, targets)
    return with_parse_grain_args


class Reggie(BotPlugin):

    DIVERT_TO_THREAD = ('ip_addrs', 'job', 'update_magbot', 'update_mcp')

    def __init__(self, *args, **kwargs):
        self.api = None
        self.auth = {}
        super().__init__(*args, **kwargs)

    def activate(self):
        self.bot_config.DIVERT_TO_THREAD = self.bot_config.DIVERT_TO_THREAD + self.DIVERT_TO_THREAD

        self.fabric_connection_kwargs = {
            'host': self.bot_config.SALT_HOST,
            'user': self.bot_config.SALT_USERNAME,
            'config': Config({
                'sudo': {
                    'username': self.bot_config.SALT_USERNAME,
                    'password': self.bot_config.SALT_PASSWORD,
                },
            }),
            'connect_kwargs': {
                'key_filename': '/srv/ssh/{}_id_rsa'.format(self.bot_config.SALT_USERNAME),
            },
        }

        try:
            self.api = pepper.Pepper(self.bot_config.SALT_API_URL)
            self.log.debug('Salt API: {}'.format(self.bot_config.SALT_API_URL))
        except Exception:
            self.log.error('Failed to initialize Salt API: {}'.format(self.bot_config.SALT_API_URL), exc_info=True)
            raise
        super().activate()

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

    def _format_results(self, results, compact=False):
        result = results.get('return', [])
        if len(result) == 1:
            result = result[0]
        return yaml.dump(result, default_flow_style=compact)

    def _update_infrastructure_repo(self):
        with Connection(**self.fabric_connection_kwargs) as c:
            self.log.debug(c.sudo('git -C /srv/infrastructure pull'))
            self.log.debug(c.sudo('salt-run fileserver.update'))

    @botcmd(split_args_with=None)
    @parse_grain_args
    @salt_auth
    def deploy(self, msg, args, grains, regex_grains, targets):
        """Deploy reggie to target servers"""
        yield 'Deploying latest to {}... (takes a few minutes)'.format(' '.join(args))
        self._update_infrastructure_repo()
        results = self.api.local_async(targets, 'state.apply', expr_form='compound')
        jid, minions = self._extract_jid_and_minions(results)
        if minions:
            minion_list = ('\n' + (' \n'.join(sorted(minions)))) if len(minions) > 1 else minions[0]
            yield '**Started job**: {}/molten/job/{} \n ' \
                  '**Target servers**: {}'.format(self.bot_config.SALT_API_URL, jid, minion_list)
        else:
            yield 'No job started, no servers found for {}'.format(' '.join(args))

    @botcmd(split_args_with=None)
    @parse_grain_args
    @salt_auth
    def ip_addrs(self, msg, args, grains, regex_grains, targets):
        """Lists ip addresses of target servers"""
        results = self.api.local(targets, 'network.ip_addrs', expr_form='compound')
        yield self._format_results(results)

    @botcmd
    @salt_auth
    def job(self, msg, jid):
        """Lookup results of a job"""
        yield 'Looking up job {}... (takes a few minutes)'.format(jid)
        results = self.api.runner('jobs.lookup_jid', jid=jid)
        yield self._format_results(results)

    @botcmd(split_args_with=None)
    @parse_grain_args
    @salt_auth
    def ping(self, msg, args, grains, regex_grains, targets):
        """Ping target servers"""
        results = self.api.local(targets, 'test.ping', expr_form='compound')
        yield self._format_results(results)

    @botcmd
    @salt_auth
    def update_magbot(self, msg, args):
        """Updates magbot"""
        yield 'Updating magbot... (takes a few minutes)'
        self._update_infrastructure_repo()
        results = self.api.local('mcp', 'state.sls', 'docker_magbot')
        yield self._format_results(results)

    @botcmd
    @salt_auth
    def update_mcp(self, msg, args):
        """Updates mcp"""
        yield 'Updating mcp... (takes a few minutes)'
        self._update_infrastructure_repo()
        results = self.api.local('mcp', 'state.apply')
        yield self._format_results(results)
