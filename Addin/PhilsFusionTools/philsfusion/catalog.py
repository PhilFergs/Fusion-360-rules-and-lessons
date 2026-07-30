from dataclasses import dataclass

from philsfusion.commands.specs import build_command_registry


@dataclass(frozen=True, slots=True)
class GroupSpec:
    name: str
    control_id: str
    tooltip: str
    available: bool


SHELL_GROUPS = (
    GroupSpec("BOM", "PhilsFusionTools_BOM", "Bill of materials tools", True),
    GroupSpec("Create", "PhilsFusionTools_Create", "Create structural components", True),
    GroupSpec("Modify", "PhilsFusionTools_Modify", "Modify and organize components", True),
    GroupSpec(
        "Fabricate",
        "PhilsFusionTools_Fabricate",
        "Prepare fabrication information",
        True,
    ),
    GroupSpec("Export", "PhilsFusionTools_Export", "Export fabrication files", True),
    GroupSpec("Cleanup", "PhilsFusionTools_Cleanup", "Clean and normalize designs", True),
    GroupSpec("Help", "PhilsFusionTools_Help", "Diagnostics and support", True),
)


def build_foundation_registry():
    return build_command_registry()
