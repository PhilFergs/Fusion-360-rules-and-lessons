import json
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_FIELDS = {
    "command_id",
    "detail",
    "error_count",
    "groups",
    "migration",
    "package_fingerprint",
    "public_commands",
    "status",
    "version",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class OperationalLogger:
    def __init__(
        self,
        path: Path,
        *,
        max_bytes: int = 2 * 1024 * 1024,
        backup_count: int = 3,
    ) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        if backup_count < 0:
            raise ValueError("backup_count cannot be negative")
        self.path = Path(path)
        self.max_bytes = max_bytes
        self.backup_count = backup_count

    def write(self, event: str, **fields: object) -> None:
        if not isinstance(event, str) or not event.strip():
            raise ValueError("event must be a non-empty string")
        disallowed = set(fields) - ALLOWED_FIELDS
        if disallowed:
            raise ValueError(
                "Log fields are not permitted: " + ", ".join(sorted(disallowed))
            )

        record = {
            "written_at_utc": _utc_now(),
            "event": event,
            **fields,
        }
        payload = (json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n").encode(
            "utf-8"
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        current_size = self.path.stat().st_size if self.path.is_file() else 0
        if current_size and current_size + len(payload) > self.max_bytes:
            self._rotate()
        with self.path.open("ab") as stream:
            stream.write(payload)

    def _rotate(self) -> None:
        if self.backup_count == 0:
            self.path.unlink(missing_ok=True)
            return

        oldest = self.path.with_name(f"{self.path.name}.{self.backup_count}")
        oldest.unlink(missing_ok=True)
        for index in reversed(range(1, self.backup_count)):
            source = self.path.with_name(f"{self.path.name}.{index}")
            if source.exists():
                source.replace(self.path.with_name(f"{self.path.name}.{index + 1}"))
        if self.path.exists():
            self.path.replace(self.path.with_name(f"{self.path.name}.1"))
