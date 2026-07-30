import ast
from pathlib import Path

from philsfusion.commands.design.bindings import (
    BINDING_DEFINITIONS,
    build_design_actions,
)
from philsfusion.commands.specs import LEGACY_ALIAS_IDS, build_command_registry

ROOT = Path(__file__).resolve().parents[2]
DESIGN_ROOT = (
    ROOT
    / "Addin"
    / "PhilsFusionTools"
    / "philsfusion"
    / "commands"
    / "design"
)


def test_every_design_handler_key_has_one_action_and_all_aliases_are_hidden():
    actions = build_design_actions()
    design_specs = [
        spec
        for spec in build_command_registry().ordered()
        if spec.group not in {"BOM", "Help"}
    ]
    design_aliases = {alias for spec in design_specs for alias in spec.aliases}

    assert set(actions) == {spec.handler_key for spec in design_specs}
    assert all(action.visible_control_count == 1 for action in actions.values())
    assert set().union(*(set(action.legacy_ids) for action in actions.values())) == (
        design_aliases
    )
    assert design_aliases < set(LEGACY_ALIAS_IDS)


def test_binding_handler_classes_exist_in_their_modules():
    for binding in BINDING_DEFINITIONS.values():
        module_name = binding.module_name.rsplit(".", 1)[-1]
        source_path = DESIGN_ROOT / f"{module_name}.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        class_names = {
            node.name for node in tree.body if isinstance(node, ast.ClassDef)
        }

        assert binding.created_handler_name in class_names


def test_split_commands_use_distinct_handlers_from_one_module():
    split = BINDING_DEFINITIONS["design.split"]
    delete = BINDING_DEFINITIONS["design.split_delete"]

    assert split.module_name == delete.module_name
    assert split.created_handler_name == "SplitCreatedHandler"
    assert delete.created_handler_name == "SplitDeleteCreatedHandler"


def test_profile_binding_uses_family_specific_legacy_factories():
    binding = BINDING_DEFINITIONS["design.steel_member"]

    assert binding.legacy_handler_factory_name == (
        "legacy_profile_handler_factories"
    )
