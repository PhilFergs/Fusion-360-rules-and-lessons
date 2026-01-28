#Author-Kevin Ramsay
#Description-PhilsBom

import datetime
import os
import traceback

BC = None

_LOG_DIR = os.path.join(os.path.expanduser("~"), "Documents", "PhilsBom")
_LOG_PATH = os.path.join(_LOG_DIR, "PhilsBom_boot.log")


def _boot_log(message):
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(f"[{ts}] {message}\n")
    except Exception:
        # Never let logging break the add-in boot path.
        pass


_boot_log("BOOT: import start")

try:
    import adsk.core
    import adsk.fusion

    from . import _PhilsBom as BC
    _boot_log("BOOT: import success")
except Exception:
    _boot_log("BOOT: import failed\n" + traceback.format_exc())
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox("Failed to load imports:\n{}".format(traceback.format_exc()))
    except Exception:
        _boot_log("BOOT: import failure messagebox failed\n" + traceback.format_exc())

def run(context):
    ui = None

    try:
        _boot_log("BOOT: run called")
        app = adsk.core.Application.get()
        ui = app.userInterface

        if BC is None:
            _boot_log("BOOT: run aborted (BC is None)")
            ui.messageBox("PhilsBom failed to load. Check PhilsBom_boot.log.")
            return

        BC.run(context)
        _boot_log("BOOT: run completed")
    except Exception:
        _boot_log("BOOT: run failed\n" + traceback.format_exc())
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


def stop(context):
    ui = None

    try:
        _boot_log("BOOT: stop called")
        app = adsk.core.Application.get()
        ui = app.userInterface

        if BC is None:
            _boot_log("BOOT: stop aborted (BC is None)")
            return

        BC.stop(context)
        _boot_log("BOOT: stop completed")
    except Exception:
        _boot_log("BOOT: stop failed\n" + traceback.format_exc())
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
