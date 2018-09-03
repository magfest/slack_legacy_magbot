import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from collections import OrderedDict
from functools import wraps

from errbot import BotPlugin, botcmd
from magbot import gen, FabricMixin, MagbotMixin, SaltMixin


ENVS = ['prod', 'staging', 'load', 'dev']
EVENT_NAMES = ['super', 'labs', 'stock', 'west']


def parse_reggie_args(func):

    @wraps(func)
    def with_parse_reggie_args(self, msg, args):
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

            yield from gen(func)(self, msg, args, grains=grains, regex_grains=regex_grains, targets=targets)

    return with_parse_reggie_args


class Infrastructure(MagbotMixin, FabricMixin, SaltMixin, BotPlugin):
    """
    Infrastructure automation utilities.
    """

    def _update_infrastructure_repo(self):
        with self.FabricConnection() as c:
            c.sudo('git -C /srv/infrastructure pull')
            c.sudo('salt-run fileserver.update')

    @botcmd(split_args_with=None)
    @parse_reggie_args
    @SaltMixin.salt_async_cmd('Deploying latest reggie to {}... (takes a few minutes)')
    def deploy(self, msg, args, grains, regex_grains, targets):
        """Deploy reggie to target servers"""
        self._update_infrastructure_repo()
        yield self.salt_api.local_async(targets, 'state.apply', expr_form='compound')

    @botcmd(split_args_with=None)
    @parse_reggie_args
    @SaltMixin.salt_cmd
    def ip_addrs(self, msg, args, grains, regex_grains, targets):
        """List ip addresses of target reggie servers"""
        results = self.salt_api.local(targets, 'network.ip_addrs', expr_form='compound')
        for servers in results.get('return', []):
            for server, ip_addrs in servers.items():
                ip_addrs[:] = [s for s in ip_addrs if not s.startswith('10.10.')]
        yield results

    @botcmd(split_args_with=None)
    @parse_reggie_args
    @SaltMixin.salt_cmd
    def ping(self, msg, args, grains, regex_grains, targets):
        """Ping target reggie servers"""
        yield self.salt_api.local(targets, 'test.ping', expr_form='compound')

    @botcmd
    @SaltMixin.salt_async_cmd('Updating magbot... (takes a few minutes)')
    def update_magbot(self, msg, args):
        """Update magbot"""
        self._update_infrastructure_repo()
        yield self.salt_api.local_async('mcp', 'state.sls', 'docker_magbot')

    @botcmd
    @SaltMixin.salt_async_cmd('Updating mcp... (takes a few minutes)')
    def update_mcp(self, msg, args):
        """Update mcp"""
        self._update_infrastructure_repo()
        yield self.salt_api.local_async('mcp', 'state.apply')
