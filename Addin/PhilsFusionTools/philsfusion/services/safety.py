from dataclasses import dataclass

from philsfusion.registry import RiskLevel


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _normalize_text_tuple(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    normalized = tuple(values)
    for value in normalized:
        _require_text(value, field_name)
    return normalized


@dataclass(frozen=True, slots=True)
class PlannedChange:
    kind: str
    subject: str
    summary: str

    def __post_init__(self) -> None:
        _require_text(self.kind, "kind")
        _require_text(self.subject, "subject")
        _require_text(self.summary, "summary")


@dataclass(frozen=True, slots=True)
class PreflightPlan:
    command_id: str
    risk: RiskLevel
    changes: tuple[PlannedChange, ...] = ()
    warnings: tuple[str, ...] = ()
    blocking_errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.command_id, "command_id")
        if not isinstance(self.risk, RiskLevel):
            raise TypeError("risk must be a RiskLevel")

        changes = tuple(self.changes)
        if any(not isinstance(change, PlannedChange) for change in changes):
            raise TypeError("changes must contain PlannedChange values")

        object.__setattr__(self, "changes", changes)
        object.__setattr__(
            self,
            "warnings",
            _normalize_text_tuple(self.warnings, "warning"),
        )
        object.__setattr__(
            self,
            "blocking_errors",
            _normalize_text_tuple(self.blocking_errors, "blocking error"),
        )

    @property
    def requires_confirmation(self) -> bool:
        return self.risk.requires_confirmation

    @property
    def is_executable(self) -> bool:
        return bool(self.changes) and not self.blocking_errors


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    succeeded: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()
    recovery: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("succeeded", "skipped", "failed", "recovery"):
            values = _normalize_text_tuple(getattr(self, field_name), field_name)
            object.__setattr__(self, field_name, values)

    @property
    def is_success(self) -> bool:
        return bool(self.succeeded) and not self.failed


def _append_items(lines: list[str], heading: str, items: tuple[str, ...]) -> None:
    if not items:
        return
    lines.append(f"{heading}:")
    lines.extend(f"  {index}. {item}" for index, item in enumerate(items, start=1))


def format_preflight(plan: PreflightPlan) -> str:
    lines = [
        f"Command: {plan.command_id}",
        f"Risk: {plan.risk.value}",
        f"Changes: {len(plan.changes)}",
        f"Confirmation required: {'yes' if plan.requires_confirmation else 'no'}",
    ]
    if plan.changes:
        lines.append("Planned changes:")
        lines.extend(
            f"  {index}. [{change.kind}] {change.subject}: {change.summary}"
            for index, change in enumerate(plan.changes, start=1)
        )
    _append_items(lines, "Warnings", plan.warnings)
    _append_items(lines, "Blocking errors", plan.blocking_errors)
    return "\n".join(lines)


def format_result(result: ExecutionResult) -> str:
    if result.is_success:
        status = "success"
    elif result.failed:
        status = "failed"
    else:
        status = "no changes"

    lines = [
        f"Status: {status}",
        f"Succeeded: {len(result.succeeded)}",
        f"Skipped: {len(result.skipped)}",
        f"Failed: {len(result.failed)}",
        f"Recovery actions: {len(result.recovery)}",
    ]
    _append_items(lines, "Succeeded items", result.succeeded)
    _append_items(lines, "Skipped items", result.skipped)
    _append_items(lines, "Failed items", result.failed)
    _append_items(lines, "Recovery", result.recovery)
    return "\n".join(lines)
