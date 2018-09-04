import archive  # noqa: F401


extra_plugin_dir = 'plugins'


def test_archive_list_no_channels(testbot, monkeypatch):
    monkeypatch.setattr(testbot._bot, 'channels', lambda: [], raising=False)
    testbot.assertCommand('!archive list', "No channels that haven't been used in the last 90 days.")
    testbot.assertCommand('!archive list 20', "No channels that haven't been used in the last 20 days.")
