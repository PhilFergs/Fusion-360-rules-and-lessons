from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PropertyWriteResult:
    persisted: bool
    observed: str
    error: str


def document_metadata_state(document: Any) -> str:
    try:
        is_saved = bool(document.isSaved)
        is_modified = bool(document.isModified)
    except Exception:
        return "unknown"

    if not is_saved:
        return "never-saved"
    if is_modified:
        return "changes-not-saved"
    return "ready"


def set_string_property_verified(
    target: Any,
    attribute: str,
    value: str,
) -> PropertyWriteResult:
    expected = str(value)
    try:
        setattr(target, attribute, expected)
    except Exception as error:
        return PropertyWriteResult(False, "", str(error))

    try:
        observed = str(getattr(target, attribute) or "")
    except Exception as error:
        return PropertyWriteResult(
            False,
            "",
            f"write completed but read-back failed: {error}",
        )

    if observed != expected:
        return PropertyWriteResult(
            False,
            observed,
            f"value did not persist (read back {observed!r})",
        )
    return PropertyWriteResult(True, observed, "")
