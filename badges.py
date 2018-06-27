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

def _draw_bar(sold,left,bar_len):
    total = sold + left
    filled_len = int(round(bar_len * sold / float(total)))
    bar = ':zeldaheart:' * filled_len + ':zeldaheart-empty:' * (bar_len - filled_len)
    return bar

def _get_event_color(sold_pct):
    if sold_pct < 50:
        return 'green'
    elif sold_pct < 80:
        return 'yellow'
    else:
        return 'red'

class Badges(BotPlugin):

    @botcmd
    def badges(self, mess, args):
        """Display badge counts for current MAGFest events."""
        if len(self) > 0:
            responses = {s: requests.get(self[s]).json() for s in self}
            for name, response in sorted(responses.items(), key=lambda x: x[0].lower()):
                sold   = response['badges_sold']
                left = response['remaining_badges']
                total  = sold + left
                bar_len = 10
                per_bar = round(total/bar_len)
                sold_pct = int((sold / total)*100)
                left_pct = int((left / total)*100)
                #price = response['badges_price']
                bar = _draw_bar(sold,left,bar_len)
                self.send_card(title='{}'.format(name),
                    body='{}\n{} sold, {} remaining'.format(bar,sold,left),
                    in_reply_to=mess,
                    color=_get_event_color(sold_pct))
            return
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
        return 'Event "{}" added to list.'.format(name)

    @botcmd
    def badges_event_remove(self, mess, name=''):
        """Remove an event from the list of events checked for badge counts."""
        name = name.strip()
        if not name:
            return 'Usage: `{}badges event remove <name>`'.format(self._bot.prefix)
        try:
            del self[name]
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
