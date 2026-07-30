import importlib
import sys
from pathlib import Path
from types import ModuleType

from philsfusion.commands.specs import PROFILE_LEGACY_IDS

ROOT = Path(__file__).resolve().parents[2]
STEEL_MEMBER_PATH = (
    ROOT
    / "Addin"
    / "PhilsFusionTools"
    / "philsfusion"
    / "commands"
    / "design"
    / "steel_member.py"
)


def _import_with_fake_adsk(monkeypatch):
    class EventHandler:
        def __init__(self):
            pass

    core = ModuleType("adsk.core")
    core.CommandCreatedEventHandler = EventHandler
    core.InputChangedEventHandler = EventHandler
    core.CommandEventHandler = EventHandler
    fusion = ModuleType("adsk.fusion")
    adsk = ModuleType("adsk")
    adsk.core = core
    adsk.fusion = fusion
    monkeypatch.setitem(sys.modules, "adsk", adsk)
    monkeypatch.setitem(sys.modules, "adsk.core", core)
    monkeypatch.setitem(sys.modules, "adsk.fusion", fusion)
    sys.modules.pop("philsfusion.commands.design.steel_member", None)
    return importlib.import_module("philsfusion.commands.design.steel_member")


def test_legacy_profile_handlers_use_one_shared_implementation(monkeypatch):
    module = _import_with_fake_adsk(monkeypatch)

    factories = module.legacy_profile_handler_factories()

    assert set(factories) == set(PROFILE_LEGACY_IDS)
    handlers = [factory() for factory in factories.values()]
    assert {handler.__class__.__name__ for handler in handlers} == {
        "SteelMemberCommandCreatedHandler"
    }
    assert {handler.default_family for handler in handlers} == {
        "EA",
        "SHS",
        "RHS",
        "I_BEAM",
        "PFC",
        "C_CHANNEL",
    }


def test_steel_member_never_executes_another_command_definition():
    source = STEEL_MEMBER_PATH.read_text(encoding="utf-8")

    assert ".execute()" not in source
    assert "generate_ea_from_lines" in source
    assert "generate_shs_from_lines" in source
    assert "generate_rhs_from_lines" in source
    assert "generate_ub_from_lines" in source
    assert "generate_pfc_from_lines" in source
    assert "generate_c_channel_from_lines" in source
