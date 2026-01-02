import os
import datetime


def _log_dir():
    # Put logs directly beside the add-in scripts
    try:
        return os.path.dirname(os.path.realpath(__file__))
    except Exception:
        return os.getcwd()


def _log_path():
    return os.path.join(_log_dir(), "PhilsDesignTools.log")


def log(message: str):
    """Append a timestamped line to PhilsDesignTools.log."""
    try:
        path = _log_path()
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {message}\n")
    except Exception:
        # Never let logging crash the add-in
        pass

