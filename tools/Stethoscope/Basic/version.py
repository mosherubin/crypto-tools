import os

_VERSION_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'VERSION')


def get() -> str:
    try:
        with open(_VERSION_FILE, encoding='utf-8') as f:
            return f.read().strip()
    except OSError:
        return '?'
