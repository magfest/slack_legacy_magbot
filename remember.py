import re

from errbot import BotPlugin, botcmd, re_botcmd


class Remember(BotPlugin):
    @re_botcmd(name='remember', pattern=r'^\s*(?:what is|rem(?:ember)?)\s+(.*)$', flags=re.IGNORECASE)
    def remember(self, mess, match):
        """Remember something"""
        memories = self.get('memories', {})
        args = match.group(1).strip()
        key, _, value = args.partition(' is ')
        key = key.strip()
        value = value.strip()

        if not key:
            return "What do you want me to remember?\n " \
                "You can see what I remember by typing: `{0}what do you remember`\n " \
                "You can add a new memory by typing: `{0}remember <name> is <something>`".format(self._bot.prefix)
        elif value:
            try:
                current_value = memories[key.lower()]
                return "`{0}` is already {1}.\nYou must `forget {0}` first.".format(key, current_value)
            except KeyError:
                memories[key.lower()] = value
                self['memories'] = memories
                return "OK, I'll remember {}.".format(key)
        try:
            return memories[key.lower()]
        except KeyError:
            return "I don't remember anything matching `{0}`.\n " \
                "You can see what I remember by typing: `{1}what do you remember`\n " \
                "You can add a new memory by typing: `{1}remember {0} is <something>`".format(key, self._bot.prefix)

    @botcmd
    def forget(self, mess, key):
        """Forget something"""
        memories = self.get('memories', {})
        key = key.strip()
        try:
            value = memories[key.lower()]
            del memories[key.lower()]
            self['memories'] = memories
            return "I've forgotten {} is {}.".format(key, value)
        except KeyError:
            return "I don't remember anything matching `{0}`.\n " \
                "You can see what I remember by typing: `{1}what do you remember`".format(key, self._bot.prefix)

    @re_botcmd(
        name='memories',
        pattern=r'^\s*(what(\s|_)+do(\s|_)+you(\s|_)+remember|memories)\s*$',
        flags=re.IGNORECASE)
    def what_do_you_remember(self, mess, args):
        """Display a list of all memories"""
        memories = self.get('memories', {})
        if not memories:
            return "I don't remember anything.\n " \
                "You can add a new memory by typing: `{0}remember <name> is <something>`".format(self._bot.prefix)
        return '\n'.join(['I remember:'] + [s for s in sorted(memories.keys())])
