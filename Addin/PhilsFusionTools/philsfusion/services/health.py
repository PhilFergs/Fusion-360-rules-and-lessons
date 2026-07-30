import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class HealthSnapshot:
    status: str
    version: str
    source_commit: str
    package_fingerprint: str
    groups: int
    public_commands: int
    compatibility_aliases: int
    settings_migration: str
    startup_errors: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.status != "healthy":
            raise ValueError("health status must be healthy")
        if not HEX_40.fullmatch(self.source_commit):
            raise ValueError("source commit must be a 40-character lowercase hash")
        if not HEX_64.fullmatch(self.package_fingerprint):
            raise ValueError("package fingerprint must be a 64-character lowercase hash")
        if self.groups <= 0 or self.public_commands <= 0:
            raise ValueError("health command and group counts must be positive")
        if self.startup_errors:
            raise ValueError("a healthy snapshot cannot contain startup errors")


def write_health(path: Path, snapshot: HealthSnapshot) -> Path:
    if not isinstance(snapshot, HealthSnapshot):
        raise TypeError("snapshot must be a HealthSnapshot")
    snapshot.validate()

    target = Path(path)
    data = asdict(snapshot)
    data["startup_errors"] = list(snapshot.startup_errors)
    data["written_at_utc"] = _utc_now()
    payload = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f"{target.name}.tmp-{uuid4().hex}")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        checked = json.loads(temporary.read_text(encoding="utf-8"))
        if checked["status"] != "healthy":
            raise ValueError("health validation failed")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target
