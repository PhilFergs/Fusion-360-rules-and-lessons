_app = None
_ui = None
_handlers = []


def init(app, ui):
    global _app, _ui
    _app = app
    _ui = ui
    clear_handlers()


def app():
    return _app


def ui():
    return _ui


def handlers():
    return _handlers


def add_handler(h):
    if h is not None:
        _handlers.append(h)


def clear_handlers():
    _handlers.clear()


def handler_count():
    return len(_handlers)

