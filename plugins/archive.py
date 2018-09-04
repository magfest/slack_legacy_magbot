from datetime import datetime, timedelta
from errbot import BotPlugin, botcmd


class Archive(BotPlugin):

    def _get_timestamp_for_channel(self, channel_id):
        try:
            message = self._bot.sc.api_call('channels.history', channel=channel_id, count=1)['messages'][0]
            return float(message['ts'])
        except Exception:
            return None

    @botcmd
    def archive_list(self, mess, args):
        """List all channels whose most recent message is at least the given number of days old. Defaults to 90 days."""
        channels = self._bot.channels()
        message = []
        args = args
        try:
            days = int(args) if args else 90
        except ValueError:
            return 'Usage: `!archive list [DAYS]` where DAYS is a number like 30 or 365. Defaults to 90'
        archive_past_this_date = datetime.now() - timedelta(days=days)
        for channel in channels:
            timestamp = self._get_timestamp_for_channel(channel['id'])
            if timestamp:
                channel_date = datetime.utcfromtimestamp(timestamp)
                if channel_date < archive_past_this_date:
                    age = (datetime.now() - channel_date).days
                    message.append('<#{}|{}> has not had activity in {} days'.format(channel['id'], channel['name'],
                                                                                     age))
        if len(message) == 0:
            message.append('No channels that haven\'t been used in the last {} days.'.format(days))

        return '\n'.join(message)
