import sys
from os.path import dirname, join, realpath


sys.path.append(join(dirname(dirname(realpath(__file__))), 'plugins'))  # noqa: E402
pytest_plugins = ['errbot.backends.test']
