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


def _format_details(details):
    if not details:
        return ""
    if isinstance(details, str):
        return details
    try:
        parts = []
        for k, v in details.items():
            parts.append(f"{k}={v}")
        return ", ".join(parts)
    except Exception:
        return str(details)


def log_command(cmd_name: str, details=None):
    msg = cmd_name
    detail_str = _format_details(details)
    if detail_str:
        msg += f": {detail_str}"
    log(msg)
