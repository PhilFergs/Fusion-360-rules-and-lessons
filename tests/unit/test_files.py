import xml.etree.ElementTree as ET

import pytest

from philsfusion.services.files import atomic_write_bytes, plan_output_path


def test_existing_target_requires_explicit_overwrite(tmp_path):
    target = tmp_path / "parts.csv"
    target.write_text("old", encoding="utf-8")

    with pytest.raises(FileExistsError):
        plan_output_path(target, overwrite=False)


def test_validator_failure_preserves_existing_target(tmp_path):
    target = tmp_path / "parts.xml"
    target.write_text("old", encoding="utf-8")
    plan = plan_output_path(target, overwrite=True)

    def reject(_path):
        raise ValueError("invalid")

    with pytest.raises(ValueError, match="invalid"):
        atomic_write_bytes(plan, b"<broken", reject)

    assert target.read_text(encoding="utf-8") == "old"
    assert not list(tmp_path.glob("*.tmp-*"))


def test_atomic_write_promotes_only_valid_payload(tmp_path):
    target = tmp_path / "parts.xml"
    plan = plan_output_path(target, overwrite=False)

    result = atomic_write_bytes(
        plan,
        b"<rows><row /></rows>",
        lambda path: ET.parse(path),
    )

    assert result == target
    assert ET.parse(target).getroot().tag == "rows"
    assert not list(tmp_path.glob("*.tmp-*"))


def test_output_plan_rejects_directory_target(tmp_path):
    with pytest.raises(IsADirectoryError):
        plan_output_path(tmp_path, overwrite=True)
