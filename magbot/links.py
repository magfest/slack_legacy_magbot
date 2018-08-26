import random
import re
from functools import reduce

from pockets import listify

from errbot import BotPlugin, botcmd


_RE_FLAGS = {
    'a': re.ASCII,
    'i': re.IGNORECASE,
    'm': re.MULTILINE,
    's': re.DOTALL,
    'x': re.VERBOSE,
}
_RE_TRIGGER_REGEX = re.compile(r'^\/(.*?)\/([{}]*)$'.format(''.join(_RE_FLAGS.keys())), flags=re.IGNORECASE)
_RE_LINK_SPLIT = re.compile(r'(.*)(https?:\/\/.*$)', flags=re.IGNORECASE)


class LinkTrigger(object):

    @staticmethod
    def _normalize_phrase(phrase):
        return ' '.join(s.lower() for s in phrase.split() if s)

    def __init__(self, trigger_pattern, links=None):
        self.raw_trigger_pattern = trigger_pattern.strip()
        self.links = [link.strip() for link in listify(links) if link.strip()]

        match = _RE_TRIGGER_REGEX.match(self.raw_trigger_pattern)
        if match:
            flag_chars = sorted(set(match.group(2).strip().lower()))
            flags = reduce(lambda x, y: x | y, map(_RE_FLAGS.get, flag_chars)) if flag_chars else None
            pattern = match.group(1).strip()
            self.trigger_regex = re.compile(pattern.replace('\ ', '\s+').replace(' ', '\s+'), flags=flags)
            self.trigger_pattern = '/{}/{}'.format(pattern, ''.join(flag_chars))
            self.is_regex = True
        else:
            self.trigger_pattern = self._normalize_phrase(trigger_pattern)
            self.trigger_regex = re.compile(re.escape(self.trigger_pattern).replace('\ ', '\s+'), flags=re.IGNORECASE)
            self.is_regex = False

    def __repr__(self):
        return '{}({!r}, {!r})'.format(self.__class__.__name__, self.trigger_pattern, self.links)

    def is_match(self, phrase, fullmatch=False):
        if fullmatch:
            return bool(self.trigger_regex.fullmatch(phrase))
        return bool(self.trigger_regex.search(phrase))

    def add_links(self, links):
        self.links.extend([link.strip() for link in listify(links) if link.strip()])

    def remove_link(self, link):
        removed = None
        try:
            while self.links:
                self.links.remove(link)
                removed = link
        except ValueError:
            pass
        return removed

    def random_link(self):
        return random.choice(self.links) if self.links else None


class Links(BotPlugin):

    def _find_link_trigger(self, phrase, fullmatch=False):
        try:
            key = phrase.strip()
            link_trigger = self[key]
            return (key, link_trigger)
        except KeyError:
            pass

        for key, link_trigger in self.items():
            if link_trigger.is_match(phrase, fullmatch=fullmatch):
                return (key, link_trigger)
        return (None, None)

    def _add_link_trigger(self, trigger_pattern, links):
        key, link_trigger = self._find_link_trigger(trigger_pattern, fullmatch=True)
        if not link_trigger:
            link_trigger = LinkTrigger(trigger_pattern)

        if not key:
            key = link_trigger.trigger_pattern

        link_trigger.add_links(links)
        self[key] = link_trigger

        return link_trigger

    def _remove_trigger_pattern_or_link(self, query):
        key, link_trigger = self._find_link_trigger(query, fullmatch=True)
        if link_trigger:
            del self[key]
            return self._format(link_trigger.trigger_pattern, link_trigger.links)

        removed = []
        link = query.strip()
        for key, link_trigger in list(self.items()):
            removed_link = link_trigger.remove_link(link)
            if removed_link:
                if link_trigger.links:
                    self[key] = link_trigger
                else:
                    del self[key]
                removed.append(self._format(link_trigger.trigger_pattern, [removed_link]))
        return '\n\n'.join(removed)

    def _format(self, trigger_pattern, links):
        parts = []
        if trigger_pattern:
            parts.append(trigger_pattern)
        if links:
            parts.extend(['• {}'.format(link) for link in sorted(links)])
        return '\n'.join(parts)

    def callback_message(self, msg):
        text = msg.body.strip()
        if text.startswith(self.bot_config.BOT_PREFIX):
            # This is a command, ignore it
            return

        text = text.lower() if self.bot_config.BOT_ALT_PREFIX_CASEINSENSITIVE else text
        if len(self.bot_config.BOT_ALT_PREFIXES) > 0 and text.startswith(self._bot.bot_alt_prefixes):
            # This is a command with an alternate prefix, ignore it
            return

        if msg.is_direct and self.bot_config.BOT_PREFIX_OPTIONAL_ON_CHAT:
            text = text if self.bot_config.BOT_ALT_PREFIX_CASEINSENSITIVE else text.lower()
            if text.startswith('links '):
                # This is a links command in a direct message, ignore it
                return

        key, link_trigger = self._find_link_trigger(msg.body)
        if link_trigger:
            link = link_trigger.random_link()
            if link:
                self.send(msg.frm, link)

    @botcmd
    def links(self, msg, args):
        """List all trigger phrases and URLs"""
        link_triggers = self.items()
        if not link_triggers:
            return "I don't know any trigger phrases\n " \
                "You can add a new link by typing: `{0}links add <phrase or /regex/i> <URL>`".format(self._bot.prefix)

        for key, link_trigger in link_triggers:
            self.send_card(title=key, body=self._format('', link_trigger.links), in_reply_to=msg, color='#e8e8e8')

    @botcmd
    def links_add(self, msg, args):
        """Add a trigger phrase and URL"""
        match = _RE_LINK_SPLIT.match(args)
        if not match:
            return "I don't recognize that format: `{0}`\n" \
                "You can add a new link by typing: `{1}links add <phrase or /regex/i> <URL>`" \
                .format(args, self._bot.prefix)
        else:
            links = []
            while match:
                trigger_pattern = match.group(1).strip()
                links.append(match.group(2).strip())
                match = _RE_LINK_SPLIT.match(trigger_pattern)
            link_trigger = self._add_link_trigger(trigger_pattern, links)
            return "Okay, I'll reply with that link whenever someone types `{}`".format(link_trigger.trigger_pattern)

    @botcmd
    def links_remove(self, msg, args):
        """Remove a trigger phrase or URL"""
        removed = self._remove_trigger_pattern_or_link(args)
        if removed:
            return "Okay, I've removed:\n{}".format(removed)
        else:
            return "I can't find any trigger phrases or links matching `{0}`\n " \
                "You can see what links I know about by typing: `{1}links`".format(args, self._bot.prefix)

    @botcmd
    def links_help(self, msg, args):
        """Display help on the *links* command"""
        return '''\
The links command tells me to listen for a trigger phrase and \
reply with a URL when I see a matching phrase.

Trigger phrases can be formatted simply:
\`\`\`
links add simple phrase http://m.memegen.com/2fpz9j.jpg
\`\`\`

Or trigger phrases can be a regular expression:
\`\`\`
links add /(complex|inscrutable) phrase/i https://i.imgflip.com/wgt6r.jpg
\`\`\`

Regular expressions start and end with a backslash, like this `/expression/`. \
Various flags are supported by appending the relevant flag characters \
to the expression, like this `/expression/i`. Multiple flags may be used for \
a single expression, `/expression/ims`:

• `a` ascii
• `i` ignore case
• `m` multiline
• `s` dot all
• `x` verbose

See the Python docs for more details: https://docs.python.org/3/library/re.html

Under the hood, simple trigger phrases are converted into case-insensitive \
regular expressions, where spaces match any contiguous whitespace. So:
\`\`\`
links add ship it https://madewith.mu/assets/shipit.jpg
\`\`\`

is equivalent to:
\`\`\`
links add /ship\s+it/i https://madewith.mu/assets/shipit.jpg
\`\`\`

and will match any of the following:
• "ship it"
• "Please... Ship it..."
• "   SHIP   IT   NOW!!!   "

Multiple links may be added for the same trigger phrase. In that case, one \
of the links will be randomly chosen for the reply.
'''
