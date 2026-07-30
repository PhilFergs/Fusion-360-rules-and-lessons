import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGN_ROOT = (
    ROOT
    / "Addin"
    / "PhilsFusionTools"
    / "philsfusion"
    / "commands"
    / "design"
)

EXPECTED_MODULES = {
    "__init__.py",
    "bulk_replace_components.py",
    "component_set.py",
    "context.py",
    "core.py",
    "ea_hole_export.py",
    "holecut.py",
    "iges_export.py",
    "logger.py",
    "move_preserve_position.py",
    "normalize_component_structure.py",
    "profile_schema.py",
    "remove_length_names.py",
    "rename.py",
    "rotate.py",
    "set_component_descriptions.py",
    "sort_components.py",
    "split.py",
    "stub_arm_pair.py",
    "stub_arms.py",
    "stub_arms_bracket.py",
    "stub_arms_export.py",
    "stub_arms_export_dxf.py",
    "steel_member.py",
    "wireframe.py",
}


def test_every_preserved_non_profile_module_is_namespaced():
    actual = {path.name for path in DESIGN_ROOT.glob("*.py")}

    assert actual == EXPECTED_MODULES


def test_design_modules_never_import_global_smg_names():
    for path in DESIGN_ROOT.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imported_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_names.append(node.module)

        assert not [
            name for name in imported_names if name == "smg" or name.startswith("smg_")
        ], path.name


def test_design_modules_have_no_bare_except_statements():
    bare_except = re.compile(r"^\s*except\s*:\s*$", re.MULTILINE)

    for path in DESIGN_ROOT.glob("*.py"):
        assert bare_except.search(path.read_text(encoding="utf-8")) is None, path.name


def test_design_resources_do_not_contain_runtime_artifacts():
    forbidden_suffixes = {".pyc", ".log", ".bak"}
    resources = DESIGN_ROOT / "resources"

    for path in resources.rglob("*"):
        assert path.suffix.casefold() not in forbidden_suffixes
