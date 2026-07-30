from philsfusion.commands.specs import (
    LEGACY_ALIAS_IDS,
    PROFILE_LEGACY_IDS,
    PUBLIC_COMMAND_IDS,
    build_command_registry,
)
from philsfusion.registry import GROUP_ORDER, RiskLevel


def test_production_catalog_has_all_groups_and_no_visible_legacy_ids():
    registry = build_command_registry()
    specs = registry.ordered()

    assert len(specs) == 25
    assert {spec.group for spec in specs} == set(GROUP_ORDER)
    assert all(spec.command_id.startswith("PhilsFusionTools_") for spec in specs)
    assert set(PUBLIC_COMMAND_IDS) == {spec.command_id for spec in specs}
    assert not set(PUBLIC_COMMAND_IDS) & set(LEGACY_ALIAS_IDS)
    assert set(PROFILE_LEGACY_IDS) == {
        "PhilsDesignTools_EA",
        "PhilsDesignTools_SHS",
        "PhilsDesignTools_RHS",
        "PhilsDesignTools_IBeam",
        "PhilsDesignTools_PFC",
        "PhilsDesignTools_CChannel",
    }


def test_every_alias_resolves_to_its_canonical_command():
    registry = build_command_registry()

    for spec in registry.ordered():
        assert registry.by_id(spec.command_id) is spec
        for alias in spec.aliases:
            assert registry.by_id(alias) is spec


def test_risk_policy_matches_the_approved_command_matrix():
    registry = build_command_registry()

    expected_routine = {
        "PhilsFusionTools_BOMSettings",
        "PhilsFusionTools_CreateSteelMember",
        "PhilsFusionTools_Diagnostics",
        "PhilsFusionTools_AboutMigration",
    }
    expected_overwrite = {
        "PhilsFusionTools_CreateBOM",
        "PhilsFusionTools_MultiPartExport",
        "PhilsFusionTools_EAHoleExport",
        "PhilsFusionTools_StubArmsExport",
        "PhilsFusionTools_StubArmsDXF",
    }
    expected_destructive = {
        "PhilsFusionTools_SplitBody",
        "PhilsFusionTools_DeleteSplitBodies",
        "PhilsFusionTools_BulkReplaceComponents",
        "PhilsFusionTools_HoleCutFromFace",
        "PhilsFusionTools_NormalizeComponentStructure",
    }

    actual_by_risk = {
        risk: {spec.command_id for spec in registry.ordered() if spec.risk is risk}
        for risk in RiskLevel
    }
    assert actual_by_risk[RiskLevel.ROUTINE] == expected_routine
    assert actual_by_risk[RiskLevel.FILE_OVERWRITE] == expected_overwrite
    assert actual_by_risk[RiskLevel.DESTRUCTIVE] == expected_destructive
    assert actual_by_risk[RiskLevel.BULK] == (
        set(PUBLIC_COMMAND_IDS)
        - expected_routine
        - expected_overwrite
        - expected_destructive
    )


def test_every_group_has_stable_unique_order_values():
    registry = build_command_registry()

    for group in GROUP_ORDER:
        orders = [spec.order for spec in registry.ordered(group)]
        assert orders == sorted(orders)
        assert len(orders) == len(set(orders))
