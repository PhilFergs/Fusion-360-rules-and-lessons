from dataclasses import dataclass
from numbers import Real

ANGLES = (0, 90, 180, 270)

UB_SECTIONS = (
    "150 UB 14",
    "150 UB 18",
    "180 UB 16.1",
    "180 UB 18.1",
    "180 UB 22.2",
    "200 UB 18.2",
    "200 UB 22.2",
    "200 UB 25.4",
    "200 UB 29.8",
    "250 UB 25.7",
    "250 UB 31.4",
    "250 UB 37.3",
    "310 UB 32",
    "310 UB 40.4",
    "310 UB 46.2",
    "360 UB 44.7",
    "360 UB 50.7",
    "360 UB 56.7",
    "410 UB 53.7",
    "410 UB 59.7",
    "460 UB 67.1",
    "460 UB 74.6",
    "460 UB 82.1",
    "530 UB 82",
    "530 UB 92.4",
    "610 UB 101",
    "610 UB 113",
    "610 UB 125",
)

PFC_SECTIONS = (
    "75 PFC",
    "100 PFC",
    "125 PFC",
    "150 PFC",
    "180 PFC",
    "200 PFC",
    "230 PFC",
    "250 PFC",
    "300 PFC",
    "380 PFC",
)

C_CHANNEL_SECTIONS = (
    "C100.10",
    "C100.12",
    "C100.15",
    "C100.19",
    "C150.10",
    "C150.12",
    "C150.15",
    "C150.19",
    "C150.24",
    "C200.15",
    "C200.19",
    "C200.24",
    "C250.15",
    "C250.19",
    "C250.24",
)


@dataclass(frozen=True, slots=True)
class ProfileFamily:
    key: str
    label: str
    fields: tuple[str, ...]
    legacy_id: str
    default_section: str = ""
    sections: tuple[str, ...] = ()


PROFILE_FAMILIES = (
    ProfileFamily(
        "EA",
        "Equal Angle (EA)",
        (
            "lines",
            "flange",
            "thickness",
            "extra",
            "hole_diameter",
            "hole_gauge",
            "fillet",
            "holes_enabled",
            "profile_name",
            "angle",
        ),
        "PhilsDesignTools_EA",
    ),
    ProfileFamily(
        "SHS",
        "Square Hollow Section (SHS)",
        ("lines", "size", "thickness", "extra", "profile_name", "angle"),
        "PhilsDesignTools_SHS",
    ),
    ProfileFamily(
        "RHS",
        "Rectangular Hollow Section (RHS)",
        (
            "lines",
            "width",
            "depth",
            "thickness",
            "extra",
            "profile_name",
            "angle",
        ),
        "PhilsDesignTools_RHS",
    ),
    ProfileFamily(
        "I_BEAM",
        "Universal Beam (UB)",
        ("lines", "section", "extra", "profile_name", "angle"),
        "PhilsDesignTools_IBeam",
        UB_SECTIONS[0],
        UB_SECTIONS,
    ),
    ProfileFamily(
        "PFC",
        "Parallel Flange Channel (PFC)",
        ("lines", "section", "extra", "profile_name", "angle"),
        "PhilsDesignTools_PFC",
        PFC_SECTIONS[3],
        PFC_SECTIONS,
    ),
    ProfileFamily(
        "C_CHANNEL",
        "Lipped C Channel",
        ("lines", "section", "extra", "profile_name", "angle"),
        "PhilsDesignTools_CChannel",
        C_CHANNEL_SECTIONS[2],
        C_CHANNEL_SECTIONS,
    ),
)

_BY_KEY = {family.key: family for family in PROFILE_FAMILIES}


def profile_family(key: str) -> ProfileFamily:
    try:
        return _BY_KEY[key]
    except KeyError:
        raise KeyError(f"unknown profile family: {key}") from None


def visible_field_ids(family_key: str) -> tuple[str, ...]:
    return profile_family(family_key).fields


def validate_profile_values(
    family_key: str,
    values: dict[str, object],
) -> tuple[str, ...]:
    family = profile_family(family_key)
    errors = []

    line_count = values.get("lines")
    if not isinstance(line_count, int) or line_count < 1:
        errors.append("at least one line is required")

    if "section" in family.fields and values.get("section") not in family.sections:
        errors.append(f"section is not valid for {family.key}")

    for field in family.fields:
        if field in {"lines", "section", "profile_name", "holes_enabled", "angle"}:
            continue
        value = values.get(field)
        if not isinstance(value, Real):
            errors.append(f"{field} must be numeric")
        elif field == "extra" and value < 0:
            errors.append("extra must be zero or greater")
        elif field != "extra" and value <= 0:
            errors.append(f"{field} must be greater than zero")

    if values.get("angle") not in ANGLES:
        errors.append("angle must be one of 0, 90, 180, 270")

    return tuple(errors)
