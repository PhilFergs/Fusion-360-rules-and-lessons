from collections.abc import Callable
from functools import wraps
from pathlib import Path

from philsfusion.commands.specs import build_command_registry
from philsfusion.registry import RiskLevel
from philsfusion.services.safety import (
    ExecutionResult,
    PlannedChange,
    PreflightPlan,
    format_preflight,
    format_result,
)


def _fusion_dialog_values():
    import adsk.core

    return (
        adsk.core.MessageBoxButtonTypes.YesNoButtonType,
        adsk.core.MessageBoxIconTypes.WarningIconType,
        adsk.core.DialogResults.DialogYes,
    )


def confirm_plan(ui, plan: PreflightPlan, *, yes_result=None) -> bool:
    if plan.blocking_errors:
        ui.messageBox(
            format_preflight(plan),
            "Phils Fusion Tools Preflight Blocked",
        )
        return False
    if not plan.is_executable:
        return False
    if not plan.requires_confirmation:
        return True

    if yes_result is None:
        buttons, icon, yes_result = _fusion_dialog_values()
        result = ui.messageBox(
            format_preflight(plan),
            "Confirm Phils Fusion Tools Changes",
            buttons,
            icon,
        )
    else:
        result = ui.messageBox(
            format_preflight(plan),
            "Confirm Phils Fusion Tools Changes",
        )
    return result == yes_result


def confirm_command(
    ui,
    command_id: str,
    command_name: str,
    *,
    change_count: int = 1,
    summary: str = "Apply the current command settings.",
    yes_result=None,
) -> bool:
    spec = build_command_registry().by_id(command_id)
    subject = (
        f"{change_count} selected items"
        if change_count != 1
        else "Current command selection"
    )
    plan = PreflightPlan(
        command_id=spec.command_id,
        risk=spec.risk,
        changes=(PlannedChange(spec.risk.value, subject, summary),),
    )
    return confirm_plan(ui, plan, yes_result=yes_result)


def confirm_overwrite(
    ui,
    path: Path,
    summary: str,
    *,
    command_id: str,
    yes_result=None,
) -> bool:
    target = Path(path)
    if not target.exists():
        return True

    spec = build_command_registry().by_id(command_id)
    blocking_errors = ()
    if target.is_dir():
        blocking_errors = ("The selected output path is a directory.",)

    plan = PreflightPlan(
        command_id=spec.command_id,
        risk=RiskLevel.FILE_OVERWRITE,
        changes=(
            PlannedChange(
                "overwrite",
                str(target),
                f"Overwrite the existing file. {summary}",
            ),
        ),
        warnings=("The existing file will be replaced only after validation.",),
        blocking_errors=blocking_errors,
    )
    return confirm_plan(ui, plan, yes_result=yes_result)


def show_result(ui, result: ExecutionResult, title: str) -> None:
    ui.messageBox(format_result(result), title)


def confirmed(command_id: str):
    def decorate(notify: Callable):
        @wraps(notify)
        def wrapped(self, args):
            from . import context as ctx

            spec = build_command_registry().by_id(command_id)
            if spec.risk is RiskLevel.FILE_OVERWRITE:
                return notify(self, args)
            if not confirm_command(ctx.ui(), command_id, spec.name):
                return None
            return notify(self, args)

        return wrapped

    return decorate
