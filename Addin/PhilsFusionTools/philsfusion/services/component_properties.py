import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable


@dataclass(frozen=True, slots=True)
class PropertyWriteResult:
    persisted: bool
    observed: str
    error: str


def _strip_version_suffix(text: str) -> str:
    return re.sub(r"\s+v\d+$", "", (text or "").strip(), flags=re.IGNORECASE).strip()


def _looks_like_profile_suffix(text: str) -> bool:
    normalized = _strip_version_suffix(text).upper().strip()
    if not normalized:
        return False

    known_tokens = (
        "SHS",
        "RHS",
        "CHS",
        "EA",
        "UA",
        "UB",
        "UC",
        "PFC",
        "C PURLIN",
        "C-PURLIN",
        "FLAT BAR",
        "PLATE",
        "PL",
    )
    if any(normalized.startswith(token) for token in known_tokens):
        return True

    # Stock profile suffixes commonly begin with dimensions such as 100x50x3.
    return bool(re.match(r"^\d+(?:\.\d+)?\s*[xX]\s*\d+", normalized))


def simplified_part_number(name: str) -> str:
    """Return the stable component-name prefix used as the part number."""
    text = _strip_version_suffix(name)
    if not text or text.startswith("<"):
        return ""

    split_match = re.match(r"^(.+?)\s*-\s*(.+)$", text)
    if split_match and _looks_like_profile_suffix(split_match.group(2)):
        return split_match.group(1).strip()

    space_match = re.match(r"^([A-Za-z]+\d+[A-Za-z0-9]*)\s+(.+)$", text)
    if space_match and _looks_like_profile_suffix(space_match.group(2)):
        return space_match.group(1).strip()

    return text


def component_metadata_id(component: Any) -> str:
    """Return a cloud model ID only when Fusion has registered the component."""
    try:
        model_id = component.mfgdmModelId
        if model_id:
            return str(model_id)
    except Exception:
        pass

    try:
        data_component = component.dataComponent
        if not data_component:
            return ""
        model_id = getattr(data_component, "mfgdmModelId", "")
        return str(model_id or "")
    except Exception:
        return ""


def wait_for_component_metadata(
    components: Iterable[Any],
    timeout_seconds: float = 45.0,
    poll_seconds: float = 0.5,
    *,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    event_pump: Callable[[], None] | None = None,
    on_poll: Callable[[tuple[Any, ...], float], None] | None = None,
) -> tuple[Any, ...]:
    """Wait until every target has cloud metadata, returning any still pending."""
    targets = tuple(components)
    timeout = max(0.0, float(timeout_seconds))
    interval = max(0.01, float(poll_seconds))
    started = monotonic()
    deadline = started + timeout

    while True:
        pending = tuple(target for target in targets if not component_metadata_id(target))
        if not pending:
            return ()

        now = monotonic()
        if now >= deadline:
            return pending

        if on_poll:
            on_poll(pending, now - started)
        if event_pump:
            event_pump()

        sleep(min(interval, max(0.0, deadline - monotonic())))


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
    *,
    attempts: int = 1,
    retry_seconds: float = 0.0,
    sleep: Callable[[float], None] = time.sleep,
    event_pump: Callable[[], None] | None = None,
) -> PropertyWriteResult:
    expected = str(value)
    max_attempts = max(1, int(attempts))
    retry_delay = max(0.0, float(retry_seconds))
    result = PropertyWriteResult(False, "", "write was not attempted")

    for attempt in range(max_attempts):
        try:
            setattr(target, attribute, expected)
        except Exception as error:
            result = PropertyWriteResult(False, "", str(error))
        else:
            try:
                observed = str(getattr(target, attribute) or "")
            except Exception as error:
                result = PropertyWriteResult(
                    False,
                    "",
                    f"write completed but read-back failed: {error}",
                )
            else:
                if observed == expected:
                    return PropertyWriteResult(True, observed, "")
                result = PropertyWriteResult(
                    False,
                    observed,
                    f"value did not persist (read back {observed!r})",
                )

        if attempt + 1 < max_attempts:
            if event_pump:
                event_pump()
            if retry_delay:
                sleep(retry_delay)

    return result
