import ast
from pathlib import Path

import pytest

from philsfusion.commands.design.profile_schema import (
    PROFILE_FAMILIES,
    profile_family,
    validate_profile_values,
    visible_field_ids,
)


def test_profile_schema_covers_every_legacy_family_once():
    assert tuple(family.key for family in PROFILE_FAMILIES) == (
        "EA",
        "SHS",
        "RHS",
        "I_BEAM",
        "PFC",
        "C_CHANNEL",
    )
    assert len({family.legacy_id for family in PROFILE_FAMILIES}) == 6


def test_switching_family_exposes_only_relevant_fields():
    assert visible_field_ids("SHS") == (
        "lines",
        "size",
        "thickness",
        "extra",
        "profile_name",
        "angle",
    )
    assert "section" in visible_field_ids("PFC")
    assert "hole_diameter" in visible_field_ids("EA")


def test_section_defaults_match_preserved_commands():
    assert profile_family("I_BEAM").default_section == "150 UB 14"
    assert profile_family("PFC").default_section == "150 PFC"
    assert profile_family("C_CHANNEL").default_section == "C100.15"


def test_schema_section_names_match_the_geometry_engine():
    core_path = Path(__file__).resolve().parents[2] / (
        "Addin/PhilsFusionTools/philsfusion/commands/design/core.py"
    )
    tree = ast.parse(core_path.read_text(encoding="utf-8"))
    tables = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id in {
            "UB_SECTIONS",
            "PFC_SECTIONS",
            "C_CHANNEL_SECTIONS",
        }:
            tables[target.id] = ast.literal_eval(node.value)

    assert profile_family("I_BEAM").sections == tuple(
        item["name"] for item in tables["UB_SECTIONS"]
    )
    assert profile_family("PFC").sections == tuple(
        item["name"] for item in tables["PFC_SECTIONS"]
    )
    assert profile_family("C_CHANNEL").sections == tuple(
        item["name"] for item in tables["C_CHANNEL_SECTIONS"]
    )


def test_profile_validation_rejects_bad_dimensions_section_and_angle():
    errors = validate_profile_values(
        "PFC",
        {
            "lines": 1,
            "section": "not a section",
            "extra": -1,
            "profile_name": False,
            "angle": 45,
        },
    )

    assert errors == (
        "section is not valid for PFC",
        "extra must be zero or greater",
        "angle must be one of 0, 90, 180, 270",
    )


def test_unknown_profile_family_is_rejected():
    with pytest.raises(KeyError, match="UNKNOWN"):
        profile_family("UNKNOWN")
