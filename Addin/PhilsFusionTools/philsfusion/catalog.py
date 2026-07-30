from dataclasses import dataclass

from philsfusion.registry import CommandRegistry, CommandSpec, RiskLevel


@dataclass(frozen=True, slots=True)
class GroupSpec:
    name: str
    control_id: str
    tooltip: str
    available: bool


SHELL_GROUPS = (
    GroupSpec("BOM", "PhilsFusionTools_BOM", "Bill of materials tools", False),
    GroupSpec("Create", "PhilsFusionTools_Create", "Create structural components", False),
    GroupSpec("Modify", "PhilsFusionTools_Modify", "Modify and organize components", False),
    GroupSpec(
        "Fabricate",
        "PhilsFusionTools_Fabricate",
        "Prepare fabrication information",
        False,
    ),
    GroupSpec("Export", "PhilsFusionTools_Export", "Export fabrication files", False),
    GroupSpec("Cleanup", "PhilsFusionTools_Cleanup", "Clean and normalize designs", False),
    GroupSpec("Help", "PhilsFusionTools_Help", "Diagnostics and support", True),
)


def build_foundation_registry() -> CommandRegistry:
    registry = CommandRegistry()
    registry.register(
        CommandSpec(
            command_id="PhilsFusionTools_Diagnostics",
            name="Diagnostics",
            tooltip="Show installation and startup diagnostics",
            group="Help",
            order=10,
            resource_key="diagnostics",
            handler_key="diagnostics",
            risk=RiskLevel.ROUTINE,
        )
    )
    return registry
