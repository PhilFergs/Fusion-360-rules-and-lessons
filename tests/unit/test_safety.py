from philsfusion.registry import RiskLevel
from philsfusion.services.safety import (
    ExecutionResult,
    PlannedChange,
    PreflightPlan,
    format_preflight,
    format_result,
)


def test_result_with_failures_is_not_success():
    result = ExecutionResult(
        succeeded=("A",),
        failed=("B: transform restore failed",),
    )

    assert result.is_success is False


def test_result_requires_at_least_one_success():
    assert ExecutionResult(skipped=("A",)).is_success is False


def test_destructive_empty_plan_is_invalid_and_requires_confirmation():
    plan = PreflightPlan(command_id="Delete", risk=RiskLevel.DESTRUCTIVE)

    assert plan.is_executable is False
    assert plan.requires_confirmation is True


def test_routine_plan_does_not_require_confirmation():
    plan = PreflightPlan(
        command_id="Inspect",
        risk=RiskLevel.ROUTINE,
        changes=(PlannedChange("inspect", "Bracket", "Read dimensions"),),
    )

    assert plan.is_executable is True
    assert plan.requires_confirmation is False


def test_blocking_error_prevents_execution():
    plan = PreflightPlan(
        command_id="Export",
        risk=RiskLevel.FILE_OVERWRITE,
        changes=(PlannedChange("write", "parts.csv", "Export 12 rows"),),
        blocking_errors=("Output folder is not writable.",),
    )

    assert plan.is_executable is False


def test_format_preflight_is_complete_and_deterministic():
    plan = PreflightPlan(
        command_id="BulkRename",
        risk=RiskLevel.BULK,
        changes=(
            PlannedChange("rename", "Part A", "A -> PL-001"),
            PlannedChange("rename", "Part B", "B -> PL-002"),
        ),
        warnings=("Two referenced components will be updated.",),
    )

    assert format_preflight(plan) == (
        "Command: BulkRename\n"
        "Risk: bulk\n"
        "Changes: 2\n"
        "Confirmation required: yes\n"
        "Planned changes:\n"
        "  1. [rename] Part A: A -> PL-001\n"
        "  2. [rename] Part B: B -> PL-002\n"
        "Warnings:\n"
        "  1. Two referenced components will be updated."
    )


def test_format_result_reports_every_outcome_category():
    result = ExecutionResult(
        succeeded=("Part A renamed",),
        skipped=("Part B already matched",),
        failed=("Part C: write failed",),
        recovery=("Part C name restored",),
    )

    assert format_result(result) == (
        "Status: failed\n"
        "Succeeded: 1\n"
        "Skipped: 1\n"
        "Failed: 1\n"
        "Recovery actions: 1\n"
        "Succeeded items:\n"
        "  1. Part A renamed\n"
        "Skipped items:\n"
        "  1. Part B already matched\n"
        "Failed items:\n"
        "  1. Part C: write failed\n"
        "Recovery:\n"
        "  1. Part C name restored"
    )
