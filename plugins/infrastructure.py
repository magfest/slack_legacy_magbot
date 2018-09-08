from errbot import BotPlugin
from magbot import FabricMixin, MagbotMixin, SaltMixin


ENVS = ['prod', 'staging', 'load', 'dev']
EVENT_NAMES = ['super', 'labs', 'stock', 'west']


reggie_target_args = {
    'default_targets': 'G@roles:reggie',
    'grain_args': [
        {'name': 'env', 'required': True, 'choices': ENVS, 'ignore': ['to', 'help', 'list']},
        {'name': 'event_name', 'choices': EVENT_NAMES},
        {'name': 'event_year', 'type': int},
    ],
}


class Infrastructure(MagbotMixin, FabricMixin, SaltMixin, BotPlugin):
    """
    Infrastructure automation utilities.
    """

    def _update_infrastructure_repo(self):
        with self.FabricConnection() as c:
            c.sudo('git -C /srv/infrastructure pull')
            c.sudo('salt-run fileserver.update')

    @SaltMixin.async_cmd('Deploying latest reggie to {args}... (takes a few minutes)', **reggie_target_args)
    def deploy(self, msg, args, targets):
        """Deploy reggie to target servers"""
        self._update_infrastructure_repo()
        yield self.salt_api.local_async(targets, 'state.apply', expr_form='compound')

    @SaltMixin.cmd(**reggie_target_args)
    def ip_addrs(self, msg, args, targets):
        """List ip addresses of target reggie servers"""
        results = self.salt_api.local(targets, 'network.ip_addrs', expr_form='compound')
        for servers in results.get('return', []):
            for server, ip_addrs in servers.items():
                ip_addrs[:] = [s for s in ip_addrs if not s.startswith('10.10.')]
        yield results

    @SaltMixin.cmd(**reggie_target_args)
    def ping(self, msg, args, targets):
        """Ping target reggie servers"""
        yield self.salt_api.local(targets, 'test.ping', expr_form='compound')

    @SaltMixin.async_cmd('Updating magbot... (takes a few minutes)')
    def update_magbot(self, msg, args, targets):
        """Update magbot"""
        self._update_infrastructure_repo()
        yield self.salt_api.local_async('mcp.magfest.net', 'state.sls', 'docker_magbot')

    @SaltMixin.async_cmd('Updating mcp... (takes a few minutes)')
    def update_mcp(self, msg, args, targets):
        """Update mcp"""
        self._update_infrastructure_repo()
        yield self.salt_api.local_async('mcp.magfest.net', 'state.apply')
