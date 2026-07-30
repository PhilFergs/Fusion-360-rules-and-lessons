import datetime
import os
from pathlib import Path

_log_path_override = None


def _default_log_path():
    documents = Path(os.path.expanduser("~/Documents"))
    return documents / "PhilsFusionTools" / "logs" / "design-tools.log"


def configure(path):
    global _log_path_override
    _log_path_override = Path(path)


def _log_path():
    return _log_path_override or _default_log_path()


def log(message: str):
    """Append one timestamped line without exposing model data by default."""
    try:
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with path.open("a", encoding="utf-8") as stream:
            stream.write(f"[{ts}] {message}\n")
    except Exception:
        # Logging must never prevent a Fusion command from completing.
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
