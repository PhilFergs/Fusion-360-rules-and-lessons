import pytest

from philsfusion.registry import CommandRegistry, CommandSpec, RiskLevel


def make_spec(
    command_id: str,
    order: int,
    *,
    group: str = "Create",
    aliases: tuple[str, ...] = (),
    risk: RiskLevel = RiskLevel.ROUTINE,
) -> CommandSpec:
    return CommandSpec(
        command_id=command_id,
        name=command_id,
        tooltip="Test command",
        group=group,
        order=order,
        resource_key=command_id,
        handler_key=command_id,
        risk=risk,
        aliases=aliases,
    )


def test_registry_rejects_duplicate_command_ids():
    registry = CommandRegistry()
    registry.register(make_spec("PhilsFusionTools_Test", 1))

    with pytest.raises(ValueError, match="duplicate command id"):
        registry.register(make_spec("PhilsFusionTools_Test", 2))


def test_registry_orders_commands_by_order_then_name():
    registry = CommandRegistry()
    registry.register(make_spec("PhilsFusionTools_B", 20))
    registry.register(make_spec("PhilsFusionTools_A", 10))
    registry.register(make_spec("PhilsFusionTools_C", 20))

    assert [item.command_id for item in registry.ordered("Create")] == [
        "PhilsFusionTools_A",
        "PhilsFusionTools_B",
        "PhilsFusionTools_C",
    ]


def test_registry_rejects_alias_owned_by_another_command():
    registry = CommandRegistry()
    registry.register(
        make_spec("PhilsFusionTools_A", 10, aliases=("PhilsDesignTools_Legacy",))
    )

    with pytest.raises(ValueError, match="duplicate command alias"):
        registry.register(
            make_spec("PhilsFusionTools_B", 20, aliases=("PhilsDesignTools_Legacy",))
        )


def test_registry_resolves_canonical_ids_and_aliases():
    registry = CommandRegistry()
    spec = make_spec(
        "PhilsFusionTools_A",
        10,
        aliases=("PhilsDesignTools_Legacy",),
    )
    registry.register(spec)

    assert registry.by_id("PhilsFusionTools_A") is spec
    assert registry.by_id("PhilsDesignTools_Legacy") is spec


@pytest.mark.parametrize(
    ("risk", "requires_confirmation"),
    [
        (RiskLevel.ROUTINE, False),
        (RiskLevel.BULK, True),
        (RiskLevel.DESTRUCTIVE, True),
        (RiskLevel.FILE_OVERWRITE, True),
    ],
)
def test_risk_policy_matches_balanced_prompt_design(risk, requires_confirmation):
    assert risk.requires_confirmation is requires_confirmation
