import badges  # noqa: F401


extra_plugin_dir = 'plugins'


def test_badges(testbot):
    testbot.assertCommand('!badges', 'No events currently in list.')
    testbot.assertCommand('!badges event add unknown', 'Error contacting given url: unknown')
    testbot.assertCommand('!badges event add staging1', 'Event "staging1" added to list.')
    testbot.assertCommand('!badges', ':zeldaheart')
    testbot.assertCommand('!badges event remove staging1', 'Event "staging1" removed from list.')
    testbot.assertCommand('!badges', 'No events currently in list.')
