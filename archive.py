from datetime import datetime, timedelta
from errbot import BotPlugin, botcmd
from errcron import CrontabMixin


def _get_timestamp_for_message(message):
    try:
        return float(message['ts'])
    except ValueError:
        raise ValueError("A message timestamp was malformed.")
    except AttributeError:
        raise AttributeError("A timestamp was not found for some message.")


def _parse_args_for_days(args, default_number_of_days=90):
    return int(args) if args else default_number_of_days


def _get_timestamp_from_api_post_message_response(res):
    try:
        return res['ts']
    except AttributeError as e:
        raise AttributeError("An error occurred while getting the timestamp from a posted message response.\n"
                             .format(e))


class Archive(CrontabMixin, BotPlugin):
    CRONTAB = [
        '@midnight .archive_channels'
    ]

    def activate(self):
        super().activate()
        self['archive'] = self['archive'] if self.get('archive') else {}

    def _get_message_for_channel(self, channel_id, timestamp=False):
        try:
            if timestamp:
                return self._bot.api_call('channels.history', channel=channel_id, count=1, latest=timestamp,
                                          inclusive=True)['messages'][0]
            else:
                return self._bot.api_call('channels.history', channel=channel_id, count=1)['messages'][0]
        except Exception as e:
            raise Exception("An error occurred while fetching a message for channel: {}\n{}".format(channel_id, e))

    def _get_channels(self):
        channels = self._bot.channels()
        return channels, '' if len(channels) == 1 or -1 else 's'

    def _post_message_to_channel(self, channel, text, as_user=False, attachments=None, icon_emoji=None, icon_url=None,
                                 link_names=False, markdown=True, parse=None, reply_broadcast=False,
                                 thread_timestamp=None, unfurl_links=True, unfurl_media=False, username=None):
        """
        The details of each parameter can be found here: https://api.slack.com/methods/chat.postMessage
        :param channel:	Channel, private group, or IM channel to send message to. Can be an encoded ID, or a name.
        :param text: Text of the message to send. Provide no more than 40,000 characters or risk truncation.
        :param as_user: Pass true to post the message as the authed user, instead of as a bot. Defaults to false.
        :param attachments: A JSON-based array of structured attachments, presented as a URL-encoded string.
        :param icon_emoji: 	Emoji to use as the icon for this message. Overrides icon_url.
         Must be used in conjunction with as_user set to false, otherwise ignored.
        :param icon_url: URL to an image to use as the icon for this message.
         Must be used in conjunction with as_user set to false, otherwise ignored.
        :param link_names: Find and link channel names and usernames.
        :param markdown: Disable Slack markup parsing by setting to false. Enabled by default.
        :param parse: Change how messages are treated. Defaults to none.
        :param reply_broadcast: Used in conjunction with thread_timestamp and
         indicates whether reply should be made visible to everyone in the channel or conversation.
        :param thread_timestamp: Provide another message's timestamp value to make this message a reply.
         Avoid using a reply's timestamp value; use its parent instead.
        :param unfurl_links: Pass true to enable unfurling of primarily text-based content.
        :param unfurl_media: Pass false to disable unfurling of media content.
        :param username: Set your bot's user name. Must be used in conjunction with as_user set to false,
         otherwise ignored.
        :return: {
                    "ok": true,
                    "channel": "C1H9RESGL",
                    "ts": "1503435956.000247",
                    "message": {
                        "text": "Here's a message for you",
                        "username": "ecto1",
                        "bot_id": "B19LU7CSY",
                        "attachments": [
                            {
                                "text": "This is an attachment",
                                "id": 1,
                                "fallback": "This is an attachment's fallback"
                            }
                        ],
                        "type": "message",
                        "subtype": "bot_message",
                        "ts": "1503435956.000247"
                    }
                }
                OR
                {
                    "ok": false,
                    "error": "too_many_attachments"
                }

        """
        api_arguments= {
            'channel': channel,
            'text': text,
            'as_user': as_user,
            'mrkdwn': markdown if markdown else False,  # This prevents markdown from being anything but True or False
            'parse': parse,
            'reply_broadcast': reply_broadcast if not reply_broadcast else True,  # Forces True or False
            'unfurl_links': unfurl_links if unfurl_links else False,
            'unfurl_media': unfurl_media if not unfurl_media else True,
            'link_names': link_names if not link_names else True
        }
        if attachments:
            api_arguments['attachments'] = attachments
        if icon_emoji:
            api_arguments['icon_emoji'] = icon_emoji
        if icon_url:
            api_arguments['icon_url'] = icon_url
        if thread_timestamp:
            api_arguments['thread_ts'] = thread_timestamp
        if username:
            api_arguments['username'] = username

        try:
            return self._bot.api_call('channels.postMessage', **api_arguments)
        except Exception as e:
            raise Exception("A message occurred while posting in channel: {}\n{}".format(channel, e))

    @botcmd
    def archive_list(self, mess, args):
        """
            List all channels whose most recent message is at least the given number of days old.
            Defaults to 90 days.
        """
        channels, is_one_channel = self._get_channels()
        final_reply = []
        try:
            days = _parse_args_for_days(args)
        except ValueError:
            return 'Usage: `!archive list [DAYS]` where DAYS is a number like 30 or 365. Defaults to 90'
        archive_past_this_date = datetime.now() - timedelta(days=days)
        yield "Querying {} channel{} for {} latest message.".format(len(channels), is_one_channel,
                                                                    'its' if is_one_channel else 'their')
        for channel in channels:
            timestamp = _get_timestamp_for_message(self._get_message_for_channel(channel['id']))
            if timestamp:
                channel_date = datetime.utcfromtimestamp(timestamp)
                if channel_date < archive_past_this_date:
                    age = (datetime.now() - channel_date).days
                    final_reply.append('<#{}|{}> has not had activity in {} days'.format(channel['id'], channel['name'],
                                                                                     age))
        if len(final_reply) == 0:
            final_reply.append('No channel{} exist'
                               ' that {} been used in the last {} days.'.format(is_one_channel,
                                                                                'haven\'t' if is_one_channel else
                                                                                'hasn\'t', days))

        return '\n'.join(final_reply)

    @botcmd
    def archive_alert(self, mess, args):
        """
            Post a message capable of archiving a channel in channels without traffic in a given number of days.
            Defaults to 90 days.
        """
        channels, is_one_channel = self._get_channels()
        final_reply = []
        try:
            days = _parse_args_for_days(args)
        except ValueError:
            return 'Usage: `!archive list [DAYS]` where DAYS is a number like 30 or 365. Defaults to 90'
        archive_past_this_date = datetime.now() - timedelta(days=days)
        yield "Querying {} channel{} for {} latest message.".format(len(channels), is_one_channel,
                                                                    'its' if is_one_channel else 'their')

        channels_to_maybe_archive = []
        for channel in channels:
            timestamp = _get_timestamp_for_message(self._get_message_for_channel(channel['id']))
            if timestamp:
                channel_date = datetime.utcfromtimestamp(timestamp)
                if channel_date < archive_past_this_date:
                    age = (datetime.now() - channel_date).days
                    final_reply.append('<#{}|{}> has not had activity in {} days.'
                                       ' Open the channel to veto archiving.'.format(channel['id'], channel['name'], age))
                    channels_to_maybe_archive.append((channel['id'], channel['name'], age))

        for channel_id, channel_name, age in channels_to_maybe_archive:
            res = self._post_message_to_channel(channel_id, 'This channel has not had activity in {} days.'
                                                            ' Please react :no: 5 times within 24 hours'
                                                            ' to prevent this channel'
                                                            ' from being archived.'.format(age))
            timestamp = _get_timestamp_from_api_post_message_response(res)
            self['archive'][timestamp] = {
                                          'id': channel_id,
                                          'expires_at': datetime.now() + timedelta(hours=24),
                                          'name': channel_name
                                         }

        if len(channels_to_maybe_archive) == 0:
            final_reply.append('No channel{} exist'
                               ' that {} been used in the last {} days.'.format(is_one_channel,
                                                                                'haven\'t' if is_one_channel else
                                                                                'hasn\'t', days))

        return '\n'.join(final_reply)

    @botcmd
    def archive_now(self, mess, args):
        return self.archive_channels()

    def archive_channels(self):
        final_reply = []
        for timestamp in self['archive'].keys():
            item = self['archive'][timestamp]
            if item['expires_at'] < datetime.now():
                res = self._get_message_for_channel(item['id'], timestamp=timestamp)
                archive = False
                if res.get('reactions'):
                    for reaction in res.get('reactions'):
                        if reaction.get('name') == 'no':
                            if reaction.get('count') > 5:
                                archive = True
                if archive:
                    self._post_message_to_channel(item['id'], 'This channel is being automatically archived.')
                    self._bot.api_call('channels.archive', channel=item['id'])
                    final_reply.append("<#{}|{}> has been archived.".format(item['id'], item['name']))
        return "\n".join(final_reply)
