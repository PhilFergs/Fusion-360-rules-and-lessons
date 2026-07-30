import re
import string
from collections.abc import Iterator, Mapping

FUSION_INSTANCE_SUFFIX_RE = re.compile(r"(?:\s*\(\d+\)|:\d+)+\s*$")
PROFILE_FROM_NAME_RE = re.compile(
    r"^(?P<base>.+?)-(?P<profile>\d+(?:\.\d+)?(?:x\d+(?:\.\d+)?){1,3})$",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(r"/([@#])(\d+)/")


def clean_component_name(name: object) -> str:
    """Remove only Fusion's trailing occurrence-instance suffixes."""
    text = "" if name is None else str(name).strip()
    previous = None
    while text != previous:
        previous = text
        text = FUSION_INSTANCE_SUFFIX_RE.sub("", text).strip()
    return text


def split_name_and_profile(name: object) -> tuple[str, str]:
    clean_name = clean_component_name(name)
    if not clean_name:
        return "", ""
    match = PROFILE_FROM_NAME_RE.match(clean_name)
    if not match:
        return clean_name, ""
    base = match.group("base").strip()
    if not base:
        return clean_name, ""
    return base, match.group("profile").strip()


def csv_cell(value: object, delimiter: str, *, numeric: bool = False) -> str:
    text = "" if value is None else str(value).strip()
    if numeric and not any(char in text for char in (delimiter, '"', "\n", "\r")):
        return text

    needs_quote = any(char in text for char in (delimiter, '"', "\n", "\r"))
    escaped = text.replace('"', '""')
    return f'"{escaped}"' if needs_quote else escaped


def _natural_sort_key(value: object) -> tuple[tuple[int, object], ...]:
    clean = clean_component_name(value).casefold()
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part)
        for part in re.split(r"(\d+)", clean)
    )


def bom_row_sort_key(item: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _natural_sort_key(item.get("name", "")),
        _natural_sort_key(item.get("partnumber", "")),
        str(item.get("material", "")).casefold(),
        str(item.get("path", "")).casefold(),
    )


def item_number_sequence(template: str) -> Iterator[str]:
    elements: list[str | tuple[str, int]] = []
    counters: list[dict[str, object]] = []
    position = 0

    for match in PLACEHOLDER_RE.finditer(str(template)):
        if match.start() > position:
            elements.append(str(template)[position : match.start()])
        kind, length_text = match.groups()
        length = int(length_text)
        elements.append((kind, length))
        if kind == "@":
            counters.append({"kind": kind, "positions": [0] * length})
        else:
            counters.append({"kind": kind, "length": length, "position": 1})
        position = match.end()
    if position < len(str(template)):
        elements.append(str(template)[position:])

    def value(counter: Mapping[str, object]) -> str:
        if counter["kind"] == "@":
            return "".join(
                string.ascii_uppercase[index] for index in counter["positions"]
            )
        return str(counter["position"]).zfill(counter["length"])

    def increment() -> None:
        for counter in reversed(counters):
            if counter["kind"] == "@":
                positions = counter["positions"]
                for index in reversed(range(len(positions))):
                    positions[index] += 1
                    if positions[index] < len(string.ascii_uppercase):
                        return
                    positions[index] = 0
            else:
                counter["position"] += 1
                if counter["position"] <= 10 ** counter["length"] - 1:
                    return
                counter["position"] = 1

    first = True
    while True:
        if not first:
            increment()
        first = False
        counter_index = 0
        output = ""
        for element in elements:
            if isinstance(element, tuple):
                output += value(counters[counter_index])
                counter_index += 1
            else:
                output += element
        yield output
