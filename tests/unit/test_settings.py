import json

from philsfusion.services.settings import SettingsStore, migrate_bom_settings


def test_settings_save_is_atomic_and_versioned(tmp_path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path)

    store.save({"ui": {"last_group": "Export"}})

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 2
    assert data["ui"]["last_group"] == "Export"
    assert not list(tmp_path.glob("*.tmp-*"))


def test_corrupt_settings_are_quarantined(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")

    settings = SettingsStore(path).load()

    assert settings["schema_version"] == 2
    quarantined = list(tmp_path.glob("settings.corrupt-*.json"))
    assert len(quarantined) == 1
    assert quarantined[0].read_text(encoding="utf-8") == "{broken"


def test_save_preserves_previous_settings_when_validation_fails(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"schema_version": 2, "ui": {"theme": "old"}}', encoding="utf-8")
    store = SettingsStore(path)

    try:
        store.save({"schema_version": 99})
    except ValueError as error:
        assert "schema_version" in str(error)
    else:
        raise AssertionError("invalid settings were accepted")

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["ui"]["theme"] == "old"


def test_bom_migration_preserves_known_preferences_without_executable_values():
    migrated = migrate_bom_settings(
        {
            "_BOMCreationMethod": "Grouped By Part Name",
            "_BOMExportFileType": "XLSX (.xlsx)",
            "_includeHiddenItems": True,
            "_appSettingsFilename": "C:/old/settings.plist",
        }
    )

    assert migrated["bom"]["creation_method"] == "Grouped By Part Name"
    assert migrated["bom"]["export_type"] == "XLSX (.xlsx)"
    assert migrated["bom"]["include_hidden_items"] is True
    assert "_appSettingsFilename" not in json.dumps(migrated)
    assert migrated["migration"]["source"] == "PhilsBom"
