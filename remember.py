import re

from errbot import BotPlugin, botcmd, re_botcmd


_REMEMBER_SPLIT_RE = re.compile(r'\s+is[\s\n]+', flags=re.IGNORECASE)


class Remember(BotPlugin):

    def _get_memory(self, key, escape=True):
        value = self[key.lower()]
        if escape:
            value = value.replace('`', '\`')
        return value

    def _set_memory(self, key, value=None):
        if value is None:
            del self[key.lower()]
        else:
            self[key.lower()] = value

    @re_botcmd(
        re_cmd_name_help='remember',
        pattern=r'^\s*(?:what is|rem(?:ember)?)(\s+.*|\s*)$',
        flags=re.IGNORECASE|re.DOTALL)
    def remember(self, msg, match):
        """Remember something"""
        args = _REMEMBER_SPLIT_RE.split(match.group(1).strip())
        if len(args) > 1:
            key = args[0].strip()
            value = args[1].strip()
        else:
            key = args[0].strip()
            value = ''

        if not key:
            return "What do you want me to remember?\n " \
                "You can see what I remember by typing: `{0}what do you remember`\n " \
                "You can add a new memory by typing: `{0}remember <name> is <something>`".format(self._bot.prefix)
        elif value:
            try:
                current_value = self._get_memory(key)
                return "But `{0}` is already {1}\nYou must `{2}forget {0}` first.".format(
                    key, current_value, self._bot.prefix)
            except KeyError:
                self._set_memory(key, value)
                return "OK, I'll remember {}.".format(key)
        try:
            return self._get_memory(key)
        except KeyError:
            return "I don't remember anything matching `{0}`\n " \
                "You can see what I remember by typing: `{1}what do you remember`\n " \
                "You can add a new memory by typing: `{1}remember {0} is <something>`".format(key, self._bot.prefix)

    @botcmd
    def forget(self, msg, key):
        """Forget something"""
        key = key.strip()
        try:
            value = self._get_memory(key)
            self._set_memory(key)
            return "I've forgotten {} is {}".format(key, value)
        except KeyError:
            return "I don't remember anything matching `{0}`\n " \
                "You can see what I remember by typing: `{1}what do you remember`".format(key, self._bot.prefix)

    @re_botcmd(
        re_cmd_name_help='what do you remember',
        pattern=r'^\s*(what(\s|_)+do(\s|_)+you(\s|_)+remember|memories)\s*$',
        flags=re.IGNORECASE)
    def what_do_you_remember(self, msg, args):
        """Display a list of all memories"""
        memories = self.keys()
        if not memories:
            return "I don't remember anything\n " \
                "You can add a new memory by typing: `{0}remember <name> is <something>`".format(self._bot.prefix)
        return '\n'.join(['I remember:'] + [s for s in sorted(memories)])
