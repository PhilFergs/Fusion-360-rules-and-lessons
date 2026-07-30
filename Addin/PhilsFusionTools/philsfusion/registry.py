from dataclasses import dataclass
from enum import Enum

GROUP_ORDER = (
    "BOM",
    "Create",
    "Modify",
    "Fabricate",
    "Export",
    "Cleanup",
    "Help",
)


class RiskLevel(Enum):
    ROUTINE = "routine"
    BULK = "bulk"
    DESTRUCTIVE = "destructive"
    FILE_OVERWRITE = "file_overwrite"

    @property
    def requires_confirmation(self) -> bool:
        return self is not RiskLevel.ROUTINE


@dataclass(frozen=True, slots=True)
class CommandSpec:
    command_id: str
    name: str
    tooltip: str
    group: str
    order: int
    resource_key: str
    handler_key: str
    risk: RiskLevel
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        text_fields = {
            "command_id": self.command_id,
            "name": self.name,
            "tooltip": self.tooltip,
            "resource_key": self.resource_key,
            "handler_key": self.handler_key,
        }
        for field_name, value in text_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.group not in GROUP_ORDER:
            raise ValueError(f"unsupported command group: {self.group}")
        if not isinstance(self.order, int) or self.order < 0:
            raise ValueError("order must be a non-negative integer")
        if len(set(self.aliases)) != len(self.aliases):
            raise ValueError("aliases must be unique within a command")
        if self.command_id in self.aliases:
            raise ValueError("command id cannot also be an alias")
        if any(not isinstance(alias, str) or not alias.strip() for alias in self.aliases):
            raise ValueError("aliases must be non-empty strings")


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, CommandSpec] = {}
        self._aliases: dict[str, CommandSpec] = {}

    def register(self, spec: CommandSpec) -> None:
        if spec.command_id in self._commands or spec.command_id in self._aliases:
            raise ValueError(f"duplicate command id: {spec.command_id}")

        for alias in spec.aliases:
            if alias in self._aliases or alias in self._commands:
                raise ValueError(f"duplicate command alias: {alias}")

        self._commands[spec.command_id] = spec
        for alias in spec.aliases:
            self._aliases[alias] = spec

    def ordered(self, group: str | None = None) -> tuple[CommandSpec, ...]:
        if group is not None and group not in GROUP_ORDER:
            raise ValueError(f"unsupported command group: {group}")

        specs = self._commands.values()
        if group is not None:
            specs = (spec for spec in specs if spec.group == group)

        group_positions = {name: index for index, name in enumerate(GROUP_ORDER)}
        return tuple(
            sorted(
                specs,
                key=lambda spec: (
                    group_positions[spec.group],
                    spec.order,
                    spec.name.casefold(),
                    spec.command_id,
                ),
            )
        )

    def by_id(self, command_id: str) -> CommandSpec:
        try:
            return self._commands[command_id]
        except KeyError:
            return self._aliases[command_id]
