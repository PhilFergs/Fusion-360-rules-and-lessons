import json
import zipfile
from io import BytesIO
from xml.etree import ElementTree

import pytest

from philsfusion.commands.bom.exporters import (
    build_payload,
    extension_for_export_type,
    validate_payload,
)
from philsfusion.services.files import atomic_write_bytes, plan_output_path

CSV_TEXT = 'Part,Qty,Note\nBracket,2,"Cut, drill"\n'


@pytest.mark.parametrize(
    "export_type",
    ["CSV (.csv)", "XML (.xml)", "JSON (.json)", "XLSX (.xlsx)"],
)
def test_every_bom_payload_validates(export_type):
    payload = build_payload(CSV_TEXT, export_type)

    validate_payload(payload, export_type)


def test_json_and_xml_preserve_csv_values():
    json_rows = json.loads(build_payload(CSV_TEXT, "JSON (.json)"))
    xml_root = ElementTree.fromstring(build_payload(CSV_TEXT, "XML (.xml)"))

    assert json_rows == [{"Part": "Bracket", "Qty": "2", "Note": "Cut, drill"}]
    assert xml_root.findtext("./row/note") == "Cut, drill"


def test_xlsx_contains_required_workbook_parts():
    payload = build_payload(CSV_TEXT, "XLSX (.xlsx)")

    with zipfile.ZipFile(BytesIO(payload)) as archive:
        assert {
            "[Content_Types].xml",
            "_rels/.rels",
            "xl/workbook.xml",
            "xl/_rels/workbook.xml.rels",
            "xl/worksheets/sheet1.xml",
        } <= set(archive.namelist())
        ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))


def test_failed_validation_preserves_existing_file(tmp_path):
    target = tmp_path / "bom.xlsx"
    target.write_bytes(b"old")
    plan = plan_output_path(target, overwrite=True)

    with pytest.raises(ValueError, match="workbook"):
        atomic_write_bytes(
            plan,
            b"bad",
            lambda path: validate_payload(path.read_bytes(), "XLSX (.xlsx)"),
        )

    assert target.read_bytes() == b"old"


def test_export_extensions_are_explicit():
    assert extension_for_export_type("CSV (.csv)") == ".csv"
    assert extension_for_export_type("XLSX (.xlsx)") == ".xlsx"
    with pytest.raises(ValueError, match="Unsupported BOM export type"):
        extension_for_export_type("PDF")

