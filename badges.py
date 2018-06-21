import json
import urllib

import requests
from errbot import BotPlugin, botcmd


def _normalize_url(url):
    url = (url or '').strip()
    if not url:
        return ''

    scheme, _, location = url.rpartition('://')
    domain, _, path = location.partition('/')
    subdomain, _, basedomain = domain.partition('.')

    scheme = scheme or 'https'

    path = path.strip('/')
    if not path:
        path = 'uber/registration/stats'
    elif not path.endswith('registration/stats'):
        path += '/registration/stats'

    if not basedomain:
        domain = subdomain + '.uber.magfest.org'

    return (subdomain, '{}://{}/{}'.format(scheme, domain, path))


def _format_events(responses):
    message = []
    for name, response in sorted(responses.items(), key=lambda x: x[0].lower()):
        message.append('{} badges sold/remaining: {} / {}'.format(
            name,
            response['badges_sold'],
            response['remaining_badges']))
    return '\n'.join(message)


class Badges(BotPlugin):

    def _sync(self):
        if getattr(getattr(self, '_store'), 'shelf'):
            self._store.shelf.sync()

    @botcmd
    def badges(self, mess, args):
        """Display badge counts for current MAGFest events."""
        if len(self) > 0:
            return _format_events({s: requests.get(self[s]).json() for s in self})
        return 'No events currently in list.\n ' \
            'You can add an event by typing: `{}badges event add [<name>] <url>`'.format(self._bot.prefix)

    @botcmd
    def badges_event_add(self, mess, args):
        """Add an event to the list of events checked for badge counts."""
        args = args.rsplit(maxsplit=1)
        if len(args) < 1:
            return 'Usage: `{}badges event add [<name>] <url>`'.format(self._bot.prefix)
        elif len(args) == 1:
            raw_url = args[0]
            name, url = _normalize_url(raw_url)
        else:
            name = args[0]
            raw_url = args[1]
            _, url = _normalize_url(raw_url)

        try:
            response = requests.get(url).json()
        except Exception as ex:
            message = ['Error contacting given url: {}'.format(raw_url)]
            if raw_url != url:
                message.append('Tried to contact: {}'.format(url))
            message.append('\`\`\`')
            message.append(str(ex))
            message.append('\`\`\`')
            return '\n'.join(message)

        self[name] = url
        self._sync()
        return 'Event "{}" added to list:\n\n{}'.format(name, _format_events({name: response}))

    @botcmd
    def badges_event_remove(self, mess, name=''):
        """Remove an event from the list of events checked for badge counts."""
        name = name.strip()
        if not name:
            return 'Usage: `{}badges event remove <name>`'.format(self._bot.prefix)
        try:
            del self[name]
            self._sync()
            return 'Event "{}" removed from list.'.format(name)
        except KeyError:
            return 'The event "{}" is not in the list.\n ' \
                'You can view the event list by typing: `{}badges event list`'.format(name, self._bot.prefix)

    @botcmd
    def badges_event_list(self, mess, args):
        """List all events to check badges along with the URL for each."""
        if len(self) > 0:
            return '\n'.join(['{}: {}'.format(name, self[name]) for name in self])

        return 'No events currently in list.\n ' \
            'You can add an event by typing: `{}badges event add [<name>] <url>`'.format(self._bot.prefix)
