import os
import sys
import traceback

_application = None


def _ensure_local_package_path():
    addin_root = os.path.dirname(os.path.realpath(__file__))
    if addin_root not in sys.path:
        sys.path.insert(0, addin_root)


def _show_error(message):
    try:
        import adsk.core

        app = adsk.core.Application.get()
        if app and app.userInterface:
            app.userInterface.messageBox(message)
    except Exception:
        pass


def run(context):
    global _application

    try:
        _ensure_local_package_path()
        from philsfusion.app import create_application

        if _application is None:
            _application = create_application()
        _application.start()
    except Exception:
        _show_error("Phils Fusion Tools could not start:\n\n" + traceback.format_exc())


def stop(context):
    global _application

    try:
        if _application is not None:
            _application.stop()
    except Exception:
        _show_error("Phils Fusion Tools could not stop cleanly:\n\n" + traceback.format_exc())
    finally:
        _application = None
