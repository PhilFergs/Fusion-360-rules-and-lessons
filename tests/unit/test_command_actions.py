from types import ModuleType

import pytest

from philsfusion.fusion.actions import ModuleCommandAction, SimpleCommandAction
from philsfusion.registry import CommandSpec, RiskLevel

ROTATE_SPEC = CommandSpec(
    command_id="PhilsFusionTools_RotateSteelMember",
    name="Rotate Steel Member",
    tooltip="Rotate selected steel members",
    group="Modify",
    order=10,
    resource_key="rotate-steel-member",
    handler_key="design.rotate",
    risk=RiskLevel.BULK,
    aliases=("PhilsDesignTools_Rotate",),
)


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


class FakeControl:
    def __init__(self, command_id):
        self.id = command_id
        self.isValid = True

    def deleteMe(self):
        self.isValid = False


class FakeControls:
    def __init__(self):
        self.items = {}

    def addCommand(self, definition):
        control = FakeControl(definition.id)
        self.items[definition.id] = control
        return control


class FakeUi:
    def __init__(self):
        self.commandDefinitions = FakeDefinitions()


class FakeCreatedHandler:
    pass


def test_module_action_installs_one_visible_and_hidden_compatibility_definitions(
    monkeypatch,
):
    module = ModuleType("tests.fake_rotate")
    module.RotateCreatedHandler = FakeCreatedHandler
    module.RESOURCE_FOLDER = "legacy-resource"
    monkeypatch.setattr(
        "philsfusion.fusion.actions.import_module",
        lambda name: module if name == module.__name__ else None,
    )
    ui = FakeUi()
    controls = FakeControls()
    action = ModuleCommandAction(
        module.__name__,
        "RotateCreatedHandler",
        legacy_bindings=("PhilsDesignTools_Rotate",),
    )

    installed = action.install(ui, controls, ROTATE_SPEC)

    assert set(controls.items) == {"PhilsFusionTools_RotateSteelMember"}
    assert set(ui.commandDefinitions.items) == {
        "PhilsFusionTools_RotateSteelMember",
        "PhilsDesignTools_Rotate",
    }
    assert len(installed.handler_refs) == 2
    assert action.visible_control_count == 1
    assert action.legacy_ids == ("PhilsDesignTools_Rotate",)


def test_module_action_replaces_stale_owned_definitions(monkeypatch):
    module = ModuleType("tests.fake_rotate")
    module.RotateCreatedHandler = FakeCreatedHandler
    monkeypatch.setattr("philsfusion.fusion.actions.import_module", lambda _name: module)
    ui = FakeUi()
    stale = ui.commandDefinitions.addButtonDefinition(
        ROTATE_SPEC.command_id,
        "stale",
        "stale",
        "",
    )
    controls = FakeControls()
    action = ModuleCommandAction(module.__name__, "RotateCreatedHandler")

    action.install(ui, controls, ROTATE_SPEC)

    assert stale.isValid is False
    assert ui.commandDefinitions.itemById(ROTATE_SPEC.command_id) is not stale


def test_module_action_rolls_back_if_handler_class_is_missing(monkeypatch):
    module = ModuleType("tests.fake_broken")
    monkeypatch.setattr("philsfusion.fusion.actions.import_module", lambda _name: module)
    ui = FakeUi()
    controls = FakeControls()
    action = ModuleCommandAction(module.__name__, "MissingHandler")

    with pytest.raises(AttributeError, match="MissingHandler"):
        action.install(ui, controls, ROTATE_SPEC)

    assert ui.commandDefinitions.itemById(ROTATE_SPEC.command_id) is None
    assert controls.items == {}


def test_simple_action_uses_injected_handler_factory():
    ui = FakeUi()
    controls = FakeControls()

    def callback():
        return None

    handler = object()
    action = SimpleCommandAction(
        callback,
        handler_factory=lambda supplied: handler if supplied is callback else None,
        resource_folder="help-resource",
    )

    installed = action.install(ui, controls, ROTATE_SPEC)

    definition = ui.commandDefinitions.itemById(ROTATE_SPEC.command_id)
    assert definition.commandCreated.handlers == [handler]
    assert installed.handler_refs == (handler,)
