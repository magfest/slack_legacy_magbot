from datetime import datetime, timedelta
from errbot import BotPlugin, botcmd


def get_timestamp_from_api(call):
    # api_json = json.loads(call)
    messages = call.get('messages')
    if messages:
        for message in messages:
            return float(message.get('ts'))


class Archives(BotPlugin):

    @botcmd
    def archive_sweep(self, mess, args):
        """Perform an archive sweep of all channels on slack. Default is 90 days."""
        pass
        channels = self._bot.channels()
        message = []
        try:
            days = int(args) if len(args) > 0 else 90
        except TypeError:
            days = 90
        archive_past_this_date = datetime.now() - timedelta(days=days)
        for channel in channels:
            channel_id = channel['id']
            channel_name = channel['name']
            timestamp = get_timestamp_from_api(self._bot.sc.api_call('channels.history', channel=channel_id, count=1))
            self[channel_id] = {
                'ts': datetime.utcfromtimestamp(timestamp),
                'name': channel_name
            }
        for key in self.keys():
            if self[key]['ts'] < archive_past_this_date:
                message.append('<#{key}|{name}> has not had activity in {days} days and should be archived.'.format(
                    name=self[key]['name'], key=key, days=days))
        if len(message) == 0:
            message.append('No channels need to be archived.')

        return "\n".join(message)
