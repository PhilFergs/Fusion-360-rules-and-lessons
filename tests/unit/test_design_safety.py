import ast
from pathlib import Path

from philsfusion.commands.design.safety_bridge import (
    confirm_command,
    confirm_overwrite,
    confirm_plan,
)
from philsfusion.registry import RiskLevel
from philsfusion.services.safety import PlannedChange, PreflightPlan

ROOT = Path(__file__).resolve().parents[2]
DESIGN_ROOT = (
    ROOT
    / "Addin"
    / "PhilsFusionTools"
    / "philsfusion"
    / "commands"
    / "design"
)


class FakeUi:
    def __init__(self, next_result="yes"):
        self.next_result = next_result
        self.messages = []

    def messageBox(self, text, title, *args):
        self.messages.append((text, title, args))
        return self.next_result


def test_routine_plan_runs_without_extra_dialog():
    ui = FakeUi()
    plan = PreflightPlan(
        command_id="Inspect",
        risk=RiskLevel.ROUTINE,
        changes=(PlannedChange("inspect", "Current selection", "Read data"),),
    )

    assert confirm_plan(ui, plan, yes_result="yes") is True
    assert ui.messages == []


def test_destructive_plan_requires_explicit_yes():
    ui = FakeUi(next_result="no")
    plan = PreflightPlan(
        command_id="Delete",
        risk=RiskLevel.DESTRUCTIVE,
        changes=(PlannedChange("delete", "2 bodies", "Delete split bodies"),),
    )

    assert confirm_plan(ui, plan, yes_result="yes") is False
    assert "Risk: destructive" in ui.messages[0][0]


def test_blocked_plan_never_executes():
    ui = FakeUi(next_result="yes")
    plan = PreflightPlan(
        command_id="Move",
        risk=RiskLevel.BULK,
        changes=(PlannedChange("move", "Part", "Move component"),),
        blocking_errors=("No writable design is active.",),
    )

    assert confirm_plan(ui, plan, yes_result="yes") is False
    assert "Blocking errors" in ui.messages[0][0]


def test_existing_output_requires_overwrite_confirmation(tmp_path):
    path = tmp_path / "parts.xlsx"
    path.write_bytes(b"old")
    ui = FakeUi(next_result="no")

    assert (
        confirm_overwrite(
            ui,
            path,
            "Export 12 parts",
            command_id="PhilsFusionTools_MultiPartExport",
            yes_result="yes",
        )
        is False
    )
    assert "overwrite" in ui.messages[0][0].casefold()


def test_new_output_does_not_add_a_redundant_confirmation(tmp_path):
    ui = FakeUi(next_result="no")

    assert (
        confirm_overwrite(
            ui,
            tmp_path / "new.csv",
            "Export rows",
            command_id="PhilsFusionTools_EAHoleExport",
            yes_result="yes",
        )
        is True
    )
    assert ui.messages == []


def test_alias_command_uses_canonical_risk_policy():
    ui = FakeUi(next_result="no")

    assert (
        confirm_command(
            ui,
            "PhilsDesignTools_Rotate",
            "Rotate Steel Member",
            change_count=3,
            yes_result="yes",
        )
        is False
    )
    assert "Risk: bulk" in ui.messages[0][0]
    assert "3 selected items" in ui.messages[0][0]


def test_every_non_routine_design_handler_has_a_safety_boundary():
    safe_markers = {"confirmed", "confirm_command", "confirm_overwrite"}
    exempt = {"bindings.py", "context.py", "core.py", "logger.py", "profile_schema.py"}

    for path in DESIGN_ROOT.glob("*.py"):
        if path.name in exempt:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if path.name in {"__init__.py", "safety_bridge.py", "steel_member.py"}:
            continue
        names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        decorator_names = {
            decorator.func.id
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            for decorator in node.decorator_list
            if isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
        }

        assert safe_markers & (names | decorator_names), path.name
