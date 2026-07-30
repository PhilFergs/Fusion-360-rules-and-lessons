import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class OutputPlan:
    target: Path
    temporary: Path
    overwrite: bool
    target_existed: bool


def plan_output_path(target: Path, overwrite: bool) -> OutputPlan:
    target = Path(target)
    if target.is_dir():
        raise IsADirectoryError(target)

    target_existed = target.exists()
    if target_existed and not overwrite:
        raise FileExistsError(target)

    temporary = target.with_name(f"{target.name}.tmp-{uuid4().hex}")
    return OutputPlan(
        target=target,
        temporary=temporary,
        overwrite=overwrite,
        target_existed=target_existed,
    )


def atomic_write_bytes(
    plan: OutputPlan,
    payload: bytes,
    validator: Callable[[Path], object],
) -> Path:
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    if plan.target.exists() and not plan.overwrite:
        raise FileExistsError(plan.target)

    plan.target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with plan.temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        validator(plan.temporary)
        os.replace(plan.temporary, plan.target)
    finally:
        plan.temporary.unlink(missing_ok=True)

    return plan.target
