import hashlib
import plistlib

from philsfusion.commands.bom.settings_bridge import BomSettingsBridge
from philsfusion.services.settings import SettingsStore


def _write_plist(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = plistlib.dumps(values)
    path.write_bytes(payload)
    return payload


def test_first_load_migrates_plist_without_modifying_it(tmp_path):
    legacy_path = tmp_path / "PhilsBom" / "PhilsBom-Settings.plist"
    original = _write_plist(
        legacy_path,
        {
            "_BOMCreationMethod": "Grouped By Part Name",
            "_BOMExportFileType": "XLSX (.xlsx)",
            "_BOMDelimiterType": "Semicolon (;)",
            "_includeHiddenItems": True,
            "_useCustomItemNumber": True,
            "_textCustomItemNumber": "P-/#3/",
        },
    )
    store = SettingsStore(tmp_path / "PhilsFusionTools" / "settings.json")

    legacy = BomSettingsBridge(store, legacy_path).load_legacy()

    assert legacy["_BOMCreationMethod"] == "Grouped By Part Name"
    assert legacy["_BOMExportFileType"] == "XLSX (.xlsx)"
    assert legacy["_useCustomItemNumber"] is True
    assert legacy_path.read_bytes() == original
    saved = store.load()
    migration = saved["migration"]["bom"]
    assert migration["status"] == "completed"
    assert migration["source_path"] == str(legacy_path)
    assert migration["source_sha256"] == hashlib.sha256(original).hexdigest()
    assert migration["completed_utc"].endswith("Z")


def test_completed_migration_is_idempotent(tmp_path):
    legacy_path = tmp_path / "legacy.plist"
    _write_plist(legacy_path, {"_BOMCreationMethod": "Grouped By Bodies"})
    store = SettingsStore(tmp_path / "settings.json")
    bridge = BomSettingsBridge(store, legacy_path)
    assert bridge.load_legacy()["_BOMCreationMethod"] == "Grouped By Bodies"

    _write_plist(legacy_path, {"_BOMCreationMethod": "Indented"})

    assert bridge.load_legacy()["_BOMCreationMethod"] == "Grouped By Bodies"


def test_corrupt_plist_is_reported_without_overwriting_valid_json(tmp_path):
    legacy_path = tmp_path / "legacy.plist"
    legacy_path.write_bytes(b"not a plist")
    store = SettingsStore(tmp_path / "settings.json")
    store.save({"bom": {"creation_method": "Indented"}})

    legacy = BomSettingsBridge(store, legacy_path).load_legacy()

    assert legacy["_BOMCreationMethod"] == "Indented"
    saved = store.load()
    assert saved["bom"]["creation_method"] == "Indented"
    assert saved["migration"]["bom"]["status"] == "skipped"
    assert "invalid" in saved["migration"]["bom"]["reason"].casefold()


def test_missing_plist_records_skipped_once_and_uses_defaults(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    bridge = BomSettingsBridge(store, tmp_path / "missing.plist")

    legacy = bridge.load_legacy()

    assert legacy["_BOMCreationMethod"] == "Grouped By Component"
    assert legacy["_BOMExportFileType"] == "XLSX (.xlsx)"
    assert store.load()["migration"]["bom"]["status"] == "skipped"


def test_save_legacy_round_trips_all_supported_preferences(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    bridge = BomSettingsBridge(store, tmp_path / "missing.plist")
    bridge.save_legacy(
        {
            "_BOMCreationMethod": "Indented",
            "_BOMExportFileType": "JSON (.json)",
            "_initialDirectory": "C:/Exports",
            "_useCustomItemNumber": True,
            "_textCustomItemNumber": "ITEM-/#2/",
            "_columnGroup": False,
            "_settingsDictionaryText": {"Indented": []},
            "_appSettingsFilename": "must-not-be-persisted",
        }
    )

    loaded = bridge.load_legacy()

    assert loaded["_BOMCreationMethod"] == "Indented"
    assert loaded["_BOMExportFileType"] == "JSON (.json)"
    assert loaded["_initialDirectory"] == "C:/Exports"
    assert loaded["_textCustomItemNumber"] == "ITEM-/#2/"
    assert loaded["_columnGroup"] is False
    assert "_appSettingsFilename" not in loaded
