import hashlib
import plistlib
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from philsfusion.services.settings import (
    BOM_KEY_MAP,
    SettingsStore,
    migrate_bom_settings,
)

DEFAULT_LEGACY_SETTINGS = {
    "_BOMCreationMethod": "Grouped By Component",
    "_BOMExportFileType": "XLSX (.xlsx)",
    "_BOMDelimiterType": "Comma (,)",
    "_BOMExportFilenameOption": "Document Name and Suffix",
    "_includeHiddenItems": False,
    "_includeParentComponents": False,
    "_includeLinkedComponents": True,
    "_linkedRootParentOnly": False,
    "_splitProfileToMaterial": False,
    "_initialDirectory": "",
    "_useCustomItemNumber": False,
    "_textCustomItemNumber": "Part /@2/ - /#3/",
    "_columnGroup": True,
    "_exportGroup": True,
    "_filenameGroup": True,
    "_unitsGroup": True,
    "_lengthUnit": "cm",
    "_areaUnit": "m^2",
    "_volumeUnit": "m^3",
    "_massUnit": "kg",
    "_comUnit": "cm",
    "_settingsDictionaryText": {},
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class BomSettingsBridge:
    def __init__(self, store: SettingsStore, legacy_path: Path) -> None:
        self.store = store
        self.legacy_path = Path(legacy_path)

    def load_legacy(self) -> dict[str, object]:
        settings = self._ensure_migration(self.store.load())
        legacy = deepcopy(DEFAULT_LEGACY_SETTINGS)
        reverse_map = {new: old for old, new in BOM_KEY_MAP.items()}
        for key, value in settings["bom"].items():
            old_key = reverse_map.get(key)
            if old_key is not None:
                legacy[old_key] = deepcopy(value)
        return legacy

    def save_legacy(self, values: Mapping[str, object]) -> None:
        settings = self._ensure_migration(self.store.load())
        migrated = migrate_bom_settings(values)
        settings["bom"].update(migrated["bom"])
        self.store.save(settings)

    def _ensure_migration(self, settings: dict[str, object]) -> dict[str, object]:
        migration = settings["migration"]
        if isinstance(migration.get("bom"), Mapping):
            return settings

        record = {
            "source_path": str(self.legacy_path),
            "completed_utc": _utc_now(),
        }
        if not self.legacy_path.is_file():
            record.update(
                status="skipped",
                reason="Legacy settings file was not found.",
            )
            migration["bom"] = record
            self.store.save(settings)
            return settings

        try:
            payload = self.legacy_path.read_bytes()
            raw = plistlib.loads(payload)
            if not isinstance(raw, Mapping):
                raise ValueError("Legacy plist root is not a dictionary")
        except (OSError, TypeError, ValueError, plistlib.InvalidFileException) as error:
            record.update(
                status="skipped",
                reason=f"Invalid legacy settings: {error}",
            )
            migration["bom"] = record
            self.store.save(settings)
            return settings

        migrated = migrate_bom_settings(raw)
        settings["bom"].update(migrated["bom"])
        record.update(
            status="completed",
            source_sha256=hashlib.sha256(payload).hexdigest(),
        )
        migration["bom"] = record
        self.store.save(settings)
        return settings
