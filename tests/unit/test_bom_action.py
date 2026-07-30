from pathlib import Path
from types import ModuleType

from philsfusion.commands.bom.action import build_bom_actions
from philsfusion.commands.specs import build_command_registry


class FakeEvent:
    def __init__(self):
        self.handlers = []

    def add(self, handler):
        self.handlers.append(handler)


class FakeDefinition:
    def __init__(self, command_id):
        self.id = command_id
        self.commandCreated = FakeEvent()
        self.isValid = True

    def deleteMe(self):
        self.isValid = False


class FakeDefinitions:
    def __init__(self):
        self.items = {}

    def itemById(self, command_id):
        item = self.items.get(command_id)
        return item if item is not None and item.isValid else None

    def addButtonDefinition(self, command_id, _name, _tooltip, _resource_folder):
        definition = FakeDefinition(command_id)
        self.items[command_id] = definition
        return definition


class FakeControls:
    def __init__(self):
        self.items = {}

    def addCommand(self, definition):
        self.items[definition.id] = definition
        return definition


class FakeUi:
    def __init__(self):
        self.commandDefinitions = FakeDefinitions()


class FakeCreatedHandler:
    pass


class FakeRuntimeCleanup:
    isValid = True

    def deleteMe(self):
        self.isValid = False


def test_bom_actions_bind_canonical_and_hidden_legacy_definitions(monkeypatch):
    module = ModuleType("philsfusion.commands.bom.legacy")
    module.ContextMenuCommandCreatedEventHandler = FakeCreatedHandler
    module.CommandCreatedEventHandler = FakeCreatedHandler
    module.BomRuntimeCleanup = FakeRuntimeCleanup
    module.COMMAND_ICON = "create-icon"
    module.COMMAND_ICON_SETTINGS = "settings-icon"
    monkeypatch.setattr(
        "philsfusion.fusion.actions.import_module",
        lambda _name: module,
    )
    actions = build_bom_actions()
    registry = build_command_registry()
    ui = FakeUi()
    controls = FakeControls()

    create = actions["bom.create"].install(
        ui,
        controls,
        registry.by_id("PhilsFusionTools_CreateBOM"),
    )
    settings = actions["bom.settings"].install(
        ui,
        controls,
        registry.by_id("PhilsFusionTools_BOMSettings"),
    )

    assert set(controls.items) == {
        "PhilsFusionTools_CreateBOM",
        "PhilsFusionTools_BOMSettings",
    }
    assert set(ui.commandDefinitions.items) == {
        "PhilsFusionTools_CreateBOM",
        "PhilsFusionTools_BOMSettings",
        "PhilsBom_contextMenuButton1",
        "PhilsBom_contextMenuButton2",
    }
    assert len(create.handler_refs) == 2
    assert len(settings.handler_refs) == 2
    assert any(isinstance(item, FakeRuntimeCleanup) for item in create.owned_objects)


def test_bom_actions_use_distinct_legacy_icon_folders():
    actions = build_bom_actions()

    assert actions["bom.create"].resource_attribute == "COMMAND_ICON"
    assert actions["bom.settings"].resource_attribute == "COMMAND_ICON_SETTINGS"
    assert actions["bom.create"].cleanup_factory_name == "BomRuntimeCleanup"


def test_legacy_create_bom_uses_atomic_payload_promotion():
    source = (
        Path(__file__).resolve().parents[2]
        / "Addin"
        / "PhilsFusionTools"
        / "philsfusion"
        / "commands"
        / "bom"
        / "legacy.py"
    ).read_text(encoding="utf-8")

    assert "atomic_write_bytes(" in source
    assert 'with open(filePath, "w"' not in source
    assert "ExportXLSX(filePath)" not in source
    assert "ExportXML(filePath)" not in source
    assert "ExportJSON(filePath)" not in source
    assert "def ExportXLSX" not in source
    assert "def ExportXML" not in source
    assert "def ExportJSON" not in source


def test_settings_execute_handler_recognizes_canonical_and_legacy_ids():
    source = (
        Path(__file__).resolve().parents[2]
        / "Addin"
        / "PhilsFusionTools"
        / "philsfusion"
        / "commands"
        / "bom"
        / "legacy.py"
    ).read_text(encoding="utf-8")

    assert '"PhilsFusionTools_BOMSettings"' in source
    assert 'COMMAND_ID + "_contextMenuButton2"' in source
