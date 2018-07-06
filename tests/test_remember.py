import magbot.remember  # noqa: F401


extra_plugin_dir = '../magbot'


def test_remember(testbot):
    testbot.assertCommand('!what do you remember', "I don't remember anything")
    testbot.assertCommand('!remember Test Key', "I don't remember anything matching Test Key")
    testbot.assertCommand('!remember Test Key is Test Value', "OK, I'll remember Test Key")
    testbot.assertCommand('!remember Test Key', 'Test Value')
    testbot.assertCommand('!remember TEST KEY', 'Test Value')
    testbot.assertCommand('!remember test key', 'Test Value')
    testbot.assertCommand('!what do you remember', 'I remember:\ntest key')
    testbot.assertCommand('!forget Test Key', "I've forgotten Test Key is Test Value")
    testbot.assertCommand('!what do you remember', "I don't remember anything")
