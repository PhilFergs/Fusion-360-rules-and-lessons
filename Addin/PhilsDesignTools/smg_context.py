import adsk.core

_app = None
_ui = None
_handlers = []  # keep references alive


def init(app, ui):
    global _app, _ui, _handlers
    _app = app
    _ui = ui
    if _handlers is None:
        _handlers = []


def app():
    return _app


def ui():
    return _ui


def handlers():
    return _handlers


def add_handler(h):
    if h is not None:
        _handlers.append(h)

