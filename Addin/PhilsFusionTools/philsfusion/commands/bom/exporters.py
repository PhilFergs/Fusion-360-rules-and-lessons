import csv
import json
import re
import zipfile
from io import BytesIO, StringIO
from xml.etree import ElementTree

EXPORT_EXTENSIONS = {
    "CSV (.csv)": ".csv",
    "XML (.xml)": ".xml",
    "JSON (.json)": ".json",
    "XLSX (.xlsx)": ".xlsx",
}
REQUIRED_XLSX_PARTS = {
    "[Content_Types].xml",
    "_rels/.rels",
    "xl/workbook.xml",
    "xl/_rels/workbook.xml.rels",
    "xl/worksheets/sheet1.xml",
}
XML_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def extension_for_export_type(export_type: str) -> str:
    try:
        return EXPORT_EXTENSIONS[export_type]
    except KeyError as error:
        raise ValueError(f"Unsupported BOM export type: {export_type}") from error


def _csv_rows(csv_text: str) -> list[list[str]]:
    if not isinstance(csv_text, str):
        raise TypeError("csv_text must be a string")
    rows = list(csv.reader(StringIO(csv_text)))
    if not rows or not rows[0]:
        raise ValueError("BOM data has no header row")
    return rows


def _xml_name(header: str, index: int) -> str:
    name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(header).strip()).strip("_")
    if not name:
        name = f"column_{index}"
    if not (name[0].isalpha() or name[0] == "_"):
        name = f"column_{name}"
    return name.casefold()


def _build_xml(rows: list[list[str]]) -> bytes:
    root = ElementTree.Element("data")
    names = [_xml_name(header, index) for index, header in enumerate(rows[0], 1)]
    for values in rows[1:]:
        row = ElementTree.SubElement(root, "row")
        for name, value in zip(names, values, strict=False):
            ElementTree.SubElement(row, name).text = value
    return ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _worksheet_xml(rows: list[list[str]]) -> bytes:
    worksheet = ElementTree.Element("worksheet", xmlns=XML_NAMESPACE)
    sheet_data = ElementTree.SubElement(worksheet, "sheetData")
    for row_index, values in enumerate(rows, 1):
        row = ElementTree.SubElement(sheet_data, "row", r=str(row_index))
        for column_index, value in enumerate(values, 1):
            reference = f"{_column_name(column_index)}{row_index}"
            cell = ElementTree.SubElement(row, "c", r=reference, t="inlineStr")
            inline = ElementTree.SubElement(cell, "is")
            ElementTree.SubElement(inline, "t").text = value
    return ElementTree.tostring(
        worksheet,
        encoding="utf-8",
        xml_declaration=True,
    )


def _write_zip_entry(archive: zipfile.ZipFile, name: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o600 << 16
    archive.writestr(info, payload)


def _build_xlsx(rows: list[list[str]]) -> bytes:
    content_types = b"""<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""
    package_rels = b"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
    workbook = b"""<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="BOM" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    workbook_rels = b"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""

    output = BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, payload in (
            ("[Content_Types].xml", content_types),
            ("_rels/.rels", package_rels),
            ("xl/workbook.xml", workbook),
            ("xl/_rels/workbook.xml.rels", workbook_rels),
            ("xl/worksheets/sheet1.xml", _worksheet_xml(rows)),
        ):
            _write_zip_entry(archive, name, payload)
    return output.getvalue()


def build_payload(csv_text: str, export_type: str) -> bytes:
    extension_for_export_type(export_type)
    rows = _csv_rows(csv_text)
    if export_type == "CSV (.csv)":
        return csv_text.encode("utf-8")
    if export_type == "JSON (.json)":
        records = [
            dict(zip(rows[0], values, strict=False))
            for values in rows[1:]
        ]
        return (json.dumps(records, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if export_type == "XML (.xml)":
        return _build_xml(rows)
    return _build_xlsx(rows)


def validate_payload(payload: bytes, export_type: str) -> None:
    extension_for_export_type(export_type)
    if not isinstance(payload, bytes) or not payload:
        raise ValueError("BOM payload is empty")

    try:
        if export_type == "CSV (.csv)":
            _csv_rows(payload.decode("utf-8"))
        elif export_type == "JSON (.json)":
            data = json.loads(payload.decode("utf-8"))
            if not isinstance(data, list):
                raise ValueError("JSON BOM root must be a list")
        elif export_type == "XML (.xml)":
            root = ElementTree.fromstring(payload)
            if root.tag != "data":
                raise ValueError("XML BOM root must be data")
        else:
            with zipfile.ZipFile(BytesIO(payload)) as archive:
                missing = REQUIRED_XLSX_PARTS - set(archive.namelist())
                if missing:
                    raise ValueError(
                        "XLSX workbook is missing: " + ", ".join(sorted(missing))
                    )
                for name in REQUIRED_XLSX_PARTS:
                    if name.endswith(".xml"):
                        ElementTree.fromstring(archive.read(name))
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        ElementTree.ParseError,
        zipfile.BadZipFile,
    ) as error:
        noun = "workbook" if export_type == "XLSX (.xlsx)" else "payload"
        raise ValueError(f"Invalid {export_type} BOM {noun}: {error}") from error
