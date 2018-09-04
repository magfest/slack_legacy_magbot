import inspect
from datetime import datetime
from functools import wraps

import pepper
import yaml
from fabric.connection import Connection
from fabric.config import Config
from pepper.libpepper import PepperException


def gen(func):
    """
    Decorator to wrap a function in a generator.
    """
    is_generator = inspect.isgeneratorfunction(func)

    @wraps(func)
    def with_gen(*args, **kwargs):
        if is_generator:
            yield from func(*args, **kwargs)
        else:
            yield func(*args, **kwargs)
    return with_gen


def monkeypatch(Class, method_name):
    """
    Decorator to monkeypatch the given method on the given Class.
    """
    original_method = getattr(Class, method_name)

    def decorator(func):
        if not hasattr(original_method, '_monkeypatch_'):
            @wraps(original_method)
            def with_monkeypatch(self, *args, **kwargs):
                return func(self, original_method, *args, **kwargs)
            with_monkeypatch._monkeypatch_ = True
            setattr(Class, method_name, with_monkeypatch)
            return with_monkeypatch
    return decorator


@monkeypatch(Connection, 'run')
def _Connection_run(self, original_method, *args, **kwargs):
    kwargs['in_stream'] = False
    return original_method(self, *args, **kwargs)


@monkeypatch(Connection, 'sudo')
def _Connection_sudo(self, original_method, *args, **kwargs):
    kwargs['in_stream'] = False
    return original_method(self, *args, **kwargs)


class MagbotMixin(object):
    """
    Common magbot utilities.
    """

    DIVERT_TO_THREAD = ()

    def activate(self):
        self.bot_config.DIVERT_TO_THREAD = self.bot_config.DIVERT_TO_THREAD + self.DIVERT_TO_THREAD
        super().activate()

    def message_identifier(self, msg):
        return getattr(msg.frm, 'room', msg.frm)


class FabricMixin(object):
    """
    Fabric automation utilities.
    """

    def activate(self):
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
        super().activate()

    def FabricConnection(self):
        return Connection(**self.fabric_connection_kwargs)


class PollerMixin(object):
    """
    Polling utilities.
    """

    def program_next_poll(self, interval, method, times, args, kwargs):
        """
        If the poll function is called "times" times, a timeout method will
        be called with the same arguments. The timeout method should be
        declared on the class, and have the same name as the poll function
        with "_timeout" appended.
        """
        if times is not None and times <= 0:
            timeout_method = getattr(self, '{}_timeout'.format(method.__name__), None)
            if timeout_method:
                timeout_method(*args, **kwargs)
        super().program_next_poll(interval, method, times, args, kwargs)


class SaltMixin(PollerMixin):
    """
    Salt API utilities.
    """

    @staticmethod
    def salt_auth(func):
        """
        Decorator to authenticate against the Salt API before calling the function.
        """
        @wraps(func)
        def with_salt_auth(self, *args, **kwargs):
            old_token = self._cached_salt_auth.get('token')
            self._renew_salt_auth()
            new_token = self._cached_salt_auth.get('token')
            try:
                yield from gen(func)(self, *args, **kwargs)
            except PepperException as error:
                if old_token == new_token and 'authentication denied' in str(error).lower():
                    self.log.debug('Cached Salt API token failed, attempting to update')
                    self._cached_salt_auth = {}
                    self._renew_salt_auth()
                    yield from gen(func)(self, *args, **kwargs)
                else:
                    raise error

        return with_salt_auth

    @staticmethod
    def salt_cmd(salutation=None):
        """
        Decorator to format results from the Salt API.
        """
        def decorator(func):
            @wraps(func)
            def with_salt_cmd(self, msg, args, **kwargs):
                if salutation:
                    yield salutation.format(args=' '.join(args))

                for results in SaltMixin.salt_auth(func)(self, msg, args, **kwargs):
                    yield self._format_results(results)

            return with_salt_cmd
        return decorator(salutation) if callable(salutation) else decorator

    @staticmethod
    def salt_async_cmd(salutation=None, interval=20, times=12):
        """
        Decorator to poll for asynchronous results from the Salt API.
        """
        def decorator(func):
            @wraps(func)
            def with_salt_async_cmd(self, msg, args, **kwargs):
                if salutation:
                    yield salutation.format(args=' '.join(args))

                for async_results in SaltMixin.salt_auth(func)(self, msg, args, **kwargs):
                    results = async_results['return'][0]
                    jid = results.get('jid', None)
                    minions = results.get('minions', [])
                    yield self._format_async_results(args, jid, minions)

                    if jid:
                        self._current_jobs[jid] = {'minion_results': {}}
                        self.start_poller(
                            interval,
                            self.salt_async_poller,
                            times=times,
                            args=[jid, minions, msg, args],
                            kwargs=kwargs)

            return with_salt_async_cmd
        return decorator(salutation) if callable(salutation) else decorator

    def __init__(self, *args, **kwargs):
        self.salt_api = None
        self._cached_salt_auth = {}
        self._current_jobs = {}
        super().__init__(*args, **kwargs)

    def activate(self):
        try:
            self.salt_api = pepper.Pepper(self.bot_config.SALT_API_URL)
            self.log.debug('Salt API: {}'.format(self.bot_config.SALT_API_URL))
        except Exception:
            self.log.error('Failed to initialize Salt API: {}'.format(self.bot_config.SALT_API_URL), exc_info=True)
            raise
        super().activate()

    def _format_async_results(self, args, jid, minions):
        if jid:
            message = ['**Started job**: {}/molten/job/{}'.format(self.bot_config.SALT_API_URL, jid)]
            if len(minions) == 1:
                message.append('**Target server**: {}'.format(minions[0]))
            elif minions:
                message.append('**Target servers**: \n {}'.format(' \n '.join(sorted(minions))))
            return ' \n '.join(message)
        return 'No job started, no servers found for {}'.format(' '.join(args))

    def _format_results(self, results):
        result = results.get('return', [])
        if not result:
            result = results
        elif len(result) == 1:
            result = result[0]
        return yaml.dump(result, default_flow_style=False)

    def _renew_salt_auth(self):
        """
        The Salt API returns an auth dictionary that looks like this::

            self._cached_salt_auth = {
                'user': 'username',
                'perms': [{'*': ['.*']}],
                'eauth': 'ldap',
                'start': 1535780898.745305,
                'expire': 1535824098.745305,
                'token': 'XXXXXXXXXXXXX',
            }
        """
        if self._cached_salt_auth.get('expire'):
            expiration = datetime.fromtimestamp(self._cached_salt_auth['expire'])
            seconds_to_expiration = (expiration - datetime.utcnow()).total_seconds()
            if seconds_to_expiration > 900:
                # The auth token won't expire for at least 15 minutes
                self.log.debug('Using cached Salt API auth token')
                return

        try:
            self._cached_salt_auth = self.salt_api.login(
                self.bot_config.SALT_USERNAME, self.bot_config.SALT_PASSWORD, self.bot_config.SALT_AUTH)
            self.log.debug('Updated cached Salt API auth token')
        except Exception:
            self.log.error('Failed to authenticate against Salt API: user="{}", auth="{}"'.format(
                self.bot_config.SALT_USERNAME, self.bot_config.SALT_AUTH), exc_info=True)
            raise

    def salt_async_poller(self, jid, minions, msg, args, **kwargs):
        """
        Called on an interval to check for results of an async salt command.
        """
        job_info = self._current_jobs[jid]
        job_results = self.salt_api.runner('jobs.lookup_jid', jid=jid, returned=True)
        is_first_response = not bool(job_info['minion_results'])
        returned_minions = job_results['return'][0]
        missing_minions = set(minions).difference(returned_minions.keys())

        new_minion_results = {}
        for minion, states in returned_minions.items():
            if minion not in job_info['minion_results']:
                success = all(state['result'] for name, state in states.items())
                new_minion_results[minion] = 'succeeded' if success else 'failed'
                job_info['minion_results'][minion] = new_minion_results[minion]

        if missing_minions:
            self._current_jobs[jid] = job_info
        else:
            self.stop_poller(self.salt_async_poller, args=[jid, minions, msg, args], kwargs=kwargs)
            del self._current_jobs[jid]

        if new_minion_results:
            response = self._format_results(new_minion_results)
            if is_first_response:
                response = '**Results**:{} {}'.format('' if len(minions) == 1 else ' \n', response)
            self.send(self.message_identifier(msg), response)

    def salt_async_poller_timeout(self, jid, minions, msg, args, **kwargs):
        """
        Called if salt_async_poller() is repeatedly called and stop_poller() is never called.
        """
        job_info = self._current_jobs[jid]
        del self._current_jobs[jid]
        missing_minions = set(minions).difference(job_info['minion_results'].keys())
        if missing_minions:
            missing_minion_results = {minion: 'never responded' for minion in missing_minions}
            self.send(self.message_identifier(msg), self._format_results(missing_minion_results))
