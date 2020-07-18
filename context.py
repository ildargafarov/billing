"""
Application context
"""
from werkzeug.local import Local, release_local


class ApplicationContext(Local):
    """
    Thread-safe application context.
    Holds services as attributes
    """
    def __contains__(self, key):
        return hasattr(self, key)


def init_context():
    """
    Initialize context
    :return: None
    """
    _app_context_local.app_ctx = ApplicationContext()


def teardown_context():
    """
    Release context
    :return: None
    """
    release_local(app_ctx)
    release_local(_app_context_local)


_app_context_local = Local()
app_ctx = _app_context_local("app_ctx")
