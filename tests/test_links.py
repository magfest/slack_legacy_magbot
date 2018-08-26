import magbot.links  # noqa: F401


extra_plugin_dir = '../magbot'


def test_remember(testbot):
    testbot.assertCommand('!links', "I don't know any trigger phrases")
    testbot.assertCommand('!links add', "I don't recognize that format")
    testbot.assertCommand('!links add phrase', "I don't recognize that format")
    testbot.assertCommand('!links add simple phrase', "I don't recognize that format")

    testbot.assertCommand('!links add simple phrase http://example.com', "Okay, I'll reply with that link")
    testbot.assertCommand('simple phrase', "http://example.com")
    testbot.assertCommand('  simple   phrase  ', "http://example.com")
    testbot.assertCommand('  SOME   SIMPLE   PHRASE!!!  ', "http://example.com")

    testbot.assertCommand('!links add simple phrase http://asdf.com', "Okay, I'll reply with that link")
    testbot.assertCommand('!links', 'http://example.com')
    testbot.assertCommand('!links', 'http://asdf.com')

    testbot.assertCommand('!links remove asdf', "I can't find any trigger phrases or links matching")
    testbot.assertCommand('!links remove http://asdf.com', "Okay, I've removed")
    testbot.assertCommand('!links', 'http://example.com')
    testbot.assertCommand('!links remove http://example.com', "Okay, I've removed")
    testbot.assertCommand('!links', "I don't know any trigger phrases")

    testbot.assertCommand('!links add simple phrase http://example.com', "Okay, I'll reply with that link")
    testbot.assertCommand('!links add simple phrase http://asdf.com', "Okay, I'll reply with that link")
    testbot.assertCommand('!links remove SIMPLE   PHRASE', "Okay, I've removed")
    testbot.assertCommand('!links', "I don't know any trigger phrases")
