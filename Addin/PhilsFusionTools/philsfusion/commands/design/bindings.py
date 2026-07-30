from dataclasses import dataclass

from philsfusion.commands.specs import build_command_registry
from philsfusion.fusion.actions import ModuleCommandAction

_MODULE_ROOT = "philsfusion.commands.design"


@dataclass(frozen=True, slots=True)
class ModuleBindingDefinition:
    module_name: str
    created_handler_name: str
    legacy_handler_factory_name: str = ""


def _binding(
    module_name: str,
    created_handler_name: str,
    legacy_handler_factory_name: str = "",
) -> ModuleBindingDefinition:
    return ModuleBindingDefinition(
        f"{_MODULE_ROOT}.{module_name}",
        created_handler_name,
        legacy_handler_factory_name,
    )


BINDING_DEFINITIONS = {
    "design.steel_member": _binding(
        "steel_member",
        "SteelMemberCommandCreatedHandler",
        "legacy_profile_handler_factories",
    ),
    "design.component_set": _binding(
        "component_set",
        "ComponentSetCreatedHandler",
    ),
    "design.wireframe": _binding("wireframe", "WireframeCreatedHandler"),
    "design.rotate": _binding("rotate", "RotateCreatedHandler"),
    "design.rename": _binding("rename", "RenameCreatedHandler"),
    "design.split": _binding("split", "SplitCreatedHandler"),
    "design.split_delete": _binding("split", "SplitDeleteCreatedHandler"),
    "design.move_preserve_position": _binding(
        "move_preserve_position",
        "MovePreserveCreatedHandler",
    ),
    "design.bulk_replace_components": _binding(
        "bulk_replace_components",
        "BulkReplaceCreatedHandler",
    ),
    "design.holecut": _binding("holecut", "HoleCutCommandCreatedHandler"),
    "design.stub_arms": _binding("stub_arms", "StubArmsCreatedHandler"),
    "design.stub_arm_pair": _binding(
        "stub_arm_pair",
        "StubArmPairCreatedHandler",
    ),
    "design.stub_arms_bracket": _binding(
        "stub_arms_bracket",
        "StubArmsBracketCreatedHandler",
    ),
    "design.multi_part_export": _binding(
        "iges_export",
        "IGESExportCreatedHandler",
    ),
    "design.ea_hole_export": _binding(
        "ea_hole_export",
        "HoleExportCreatedHandler",
    ),
    "design.stub_arms_export": _binding(
        "stub_arms_export",
        "StubArmsExportCreatedHandler",
    ),
    "design.stub_arms_export_dxf": _binding(
        "stub_arms_export_dxf",
        "StubArmsExportDxfCreatedHandler",
    ),
    "design.sort_components": _binding(
        "sort_components",
        "SortComponentsCreatedHandler",
    ),
    "design.remove_length_names": _binding(
        "remove_length_names",
        "RemoveLengthNamesCreatedHandler",
    ),
    "design.normalize_component_structure": _binding(
        "normalize_component_structure",
        "NormalizeStructureCreatedHandler",
    ),
    "design.set_component_descriptions": _binding(
        "set_component_descriptions",
        "SetComponentDescriptionsCreatedHandler",
    ),
}


def build_design_actions():
    specs_by_handler = {
        spec.handler_key: spec
        for spec in build_command_registry().ordered()
        if spec.handler_key.startswith("design.")
    }
    if set(specs_by_handler) != set(BINDING_DEFINITIONS):
        missing = set(specs_by_handler) - set(BINDING_DEFINITIONS)
        unexpected = set(BINDING_DEFINITIONS) - set(specs_by_handler)
        raise ValueError(
            f"design action mismatch; missing={sorted(missing)} "
            f"unexpected={sorted(unexpected)}"
        )

    return {
        handler_key: ModuleCommandAction(
            binding.module_name,
            binding.created_handler_name,
            legacy_bindings=specs_by_handler[handler_key].aliases,
            legacy_handler_factory_name=binding.legacy_handler_factory_name,
        )
        for handler_key, binding in BINDING_DEFINITIONS.items()
    }
