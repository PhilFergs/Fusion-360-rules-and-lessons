import json
import os
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

SCHEMA_VERSION = 2
DEFAULT_SETTINGS = {
    "schema_version": SCHEMA_VERSION,
    "ui": {},
    "bom": {},
    "migration": {},
}

BOM_KEY_MAP = {
    "_BOMCreationMethod": "creation_method",
    "_BOMExportFileType": "export_type",
    "_BOMDelimiterType": "delimiter_type",
    "_BOMExportFilenameOption": "filename_option",
    "_includeHiddenItems": "include_hidden_items",
    "_includeParentComponents": "include_parent_components",
    "_includeLinkedComponents": "include_linked_components",
    "_linkedRootParentOnly": "linked_root_parent_only",
    "_splitProfileToMaterial": "split_profile_to_material",
    "_lengthUnit": "length_unit",
    "_areaUnit": "area_unit",
    "_volumeUnit": "volume_unit",
    "_massUnit": "mass_unit",
    "_comUnit": "centre_of_mass_unit",
    "_settingsDictionaryText": "columns",
}


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _normalized_settings(settings: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(settings, Mapping):
        raise TypeError("settings must be a mapping")

    supplied_version = settings.get("schema_version", SCHEMA_VERSION)
    if supplied_version != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")

    normalized = deepcopy(DEFAULT_SETTINGS)
    for key, value in settings.items():
        if key == "schema_version":
            continue
        normalized[key] = deepcopy(value)

    for section in ("ui", "bom", "migration"):
        if not isinstance(normalized.get(section), Mapping):
            raise ValueError(f"{section} settings must be a mapping")
        normalized[section] = dict(normalized[section])
    return normalized


class SettingsStore:
    def __init__(self, path: Path, schema_version: int = SCHEMA_VERSION) -> None:
        if schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        self.path = Path(path)
        self.schema_version = schema_version

    def load(self) -> dict[str, object]:
        if not self.path.exists():
            return deepcopy(DEFAULT_SETTINGS)
        if not self.path.is_file():
            raise IsADirectoryError(self.path)

        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            return _normalized_settings(loaded)
        except (json.JSONDecodeError, TypeError, ValueError):
            quarantine = self.path.with_name(
                f"{self.path.stem}.corrupt-{_utc_stamp()}{self.path.suffix}"
            )
            os.replace(self.path, quarantine)
            return deepcopy(DEFAULT_SETTINGS)

    def save(self, settings: Mapping[str, object]) -> None:
        normalized = _normalized_settings(settings)
        payload = (
            json.dumps(normalized, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        ).encode("utf-8")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f"{self.path.name}.tmp-{uuid4().hex}")
        try:
            with temporary.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            _normalized_settings(
                json.loads(temporary.read_text(encoding="utf-8"))
            )
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)


def migrate_bom_settings(raw: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(raw, Mapping):
        raise TypeError("BOM settings must be a mapping")

    bom: dict[str, object] = {}
    for old_key, new_key in BOM_KEY_MAP.items():
        value = raw.get(old_key)
        if isinstance(value, (str, int, float, bool, list, tuple, dict)):
            bom[new_key] = deepcopy(value)

    return {
        "schema_version": SCHEMA_VERSION,
        "ui": {},
        "bom": bom,
        "migration": {
            "source": "PhilsBom",
            "source_schema": 1,
        },
    }
