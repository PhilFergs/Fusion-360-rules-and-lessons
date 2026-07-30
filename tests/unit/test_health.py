import json

import pytest

from philsfusion.services.health import HealthSnapshot, write_health


def _snapshot(**overrides):
    values = {
        "status": "healthy",
        "version": "2.0.0",
        "source_commit": "a" * 40,
        "package_fingerprint": "b" * 64,
        "groups": 7,
        "public_commands": 25,
        "compatibility_aliases": 28,
        "settings_migration": "completed",
        "startup_errors": (),
    }
    values.update(overrides)
    return HealthSnapshot(**values)


def test_health_snapshot_proves_exact_runtime_identity(tmp_path):
    path = tmp_path / "health.json"

    write_health(path, _snapshot())

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"
    assert data["groups"] == 7
    assert data["public_commands"] == 25
    assert data["startup_errors"] == []
    assert len(data["package_fingerprint"]) == 64
    assert data["written_at_utc"].endswith("Z")


def test_invalid_health_does_not_replace_previous_snapshot(tmp_path):
    path = tmp_path / "health.json"
    path.write_text('{"status":"previous"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="fingerprint"):
        write_health(path, _snapshot(package_fingerprint="bad"))

    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "previous"

