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
    message = ['|Event|Price|Sold|Remaining|', '|:---|---:|---:|---:|']
    for name in sorted(responses.keys(), key=lambda s: s.lower()):
        response = responses[name]
        message.append('|{name}|${price}|{sold}|{remaining}|'.format(
            name=name,
            price=response['badges_price'],
            sold=response['badges_sold'],
            remaining=response['remaining_badges']))
    return '\n'.join(message)


class Badges(BotPlugin):
    @botcmd
    def badges(self, mess, args):
        """Display badge counts for current MAGFest events."""
        if len(self) > 0:
            return _format_events({s: requests.get(self[s]).json() for s in self})
        return 'No events currently in list. You can add an event with the following command:\n' \
            '`{}badges event add [<name>] <url>`'.format(self._bot.prefix)

    @botcmd(split_args_with=None)
    def badges_event_add(self, mess, args):
        """Add an event to the list of events checked for badge counts."""
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
        return 'Event "{}" added to list:\n\n{}'.format(name, _format_events({name: response}))

    @botcmd(split_args_with=None)
    def badges_event_remove(self, mess, args):
        """Remove an event from the list of events checked for badge counts."""
        if len(args) < 1:
            return 'Usage: `{}badges event remove <name>`'.format(self._bot.prefix)
        name = args[0]
        try:
            del self[name]
            return 'Event "{}" removed from list.'.format(name)
        except KeyError:
            return 'The event "{}" is not in the list. ' \
                'You can view the event list with the following command:\n' \
                '`{}badges event list`'.format(name, self._bot.prefix)

    @botcmd
    def badges_event_list(self, mess, args):
        """List all events to check badges along with the URL for each."""
        if len(self) > 0:
            return '|Name|URL|\n|:---|:---|\n' + '\n'.join(
                ['|{name}|{url}|'.format(
                    name=name,
                    url=self[name]
                ) for name in self])

        return 'No events currently in list. You can add an event with the following command:\n' \
            '`{}badges event add [<name>] <url>`'.format(self._bot.prefix)
