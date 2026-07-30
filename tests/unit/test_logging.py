import json

import pytest

from philsfusion.services.logging import OperationalLogger


def test_operational_log_is_structured_and_excludes_design_data(tmp_path):
    logger = OperationalLogger(tmp_path / "PhilsFusionTools.log")

    logger.write(
        "startup",
        status="healthy",
        version="2.0.0",
        command_id="PhilsFusionTools_CreateBOM",
    )

    record = json.loads(logger.path.read_text(encoding="utf-8"))
    assert record["event"] == "startup"
    assert record["status"] == "healthy"
    assert "written_at_utc" in record
    assert not {"document", "selection", "geometry", "rows"} & set(record)

    with pytest.raises(ValueError, match="not permitted"):
        logger.write("command", document="secret design")


def test_operational_log_rotates_and_keeps_bounded_backups(tmp_path):
    logger = OperationalLogger(
        tmp_path / "PhilsFusionTools.log",
        max_bytes=160,
        backup_count=2,
    )

    for index in range(20):
        logger.write("test", status="ok", detail=f"entry-{index:02d}")

    assert logger.path.is_file()
    assert (tmp_path / "PhilsFusionTools.log.1").is_file()
    assert (tmp_path / "PhilsFusionTools.log.2").is_file()
    assert not (tmp_path / "PhilsFusionTools.log.3").exists()
