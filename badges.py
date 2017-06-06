from errbot import BotPlugin, botcmd
import requests
import json

class Badges(BotPlugin): 
    @botcmd
    def badges(self, mess, args):
        """ Shows badge counts for all current Mag events """        
        if len(self) > 0:
            response = '|Event|Price|Sold|Remaining|\n|:---|---:|---:|---:|\n'
            for name in self:
                badgeResponse = requests.get(self[name]).json()
                #yield str (badgeResponse)
                row = '|{name}|{price}|{sold}|{remaining}|\n'.format(
                    name=name,
                    price='$' + str(badgeResponse['badges_price']),
                    sold=badgeResponse['badges_sold'],
                    remaining=badgeResponse['remaining_badges'])
                response += row
            return response
                
        else:
            return u'No events currently in list. ' \
                    'Use {prefix}badges event add to define one.'.format(
                        prefix=self._bot.prefix
                    )

    @botcmd(split_args_with=None)
    def badges_event_add(self, mess, args):
        """ Add a new event to the events checked when asking for badge counts """
        if len(args) < 2:
            return u'usage: {prefix}badges event add <name> <url>'.format(
                prefix=self._bot.prefix
            )
        name = args[0]
        url = args[1] 
        self[name] = url
        return u'Event added to list.'
    
    @botcmd(split_args_with=None)
    def badges_event_remove(self, mess, args):
        """ Remove an event from the events checked when asking for badge counts """
        if len(args) < 1:
            return u'usage: {prefix}badges event remove <name>'.format(
                prefix=self._bot.prefix
            )
        name = args[0]
        try:
            del self[name]
            return u'Event removed from list.'
        except KeyError:
            return u'That event is not in the list. ' \
                   'Use {prefix}badges events list to see all events.'.format(
                       prefix=self._bot.prefix
                   )
    @botcmd
    def badges_event_list(self, mess, args):
        """List all events to check badges along with the URL for each."""
        if len(self) > 0:
            return u'|Name|URL|\n|:---|:---|\n' + u'\n'.join(
                ['|{name}|{url}|'.format(
                    name=name,
                    url=self[name]
                ) for name in self])
        else:
            return u'No events currently in list. ' \
                   'Use {prefix}badges event add to define one.'.format(
                       prefix=self._bot.prefix
                   )