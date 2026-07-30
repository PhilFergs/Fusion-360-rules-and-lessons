from philsfusion.fusion.actions import ModuleCommandAction


class BomCommandAction(ModuleCommandAction):
    def __init__(
        self,
        created_handler_name: str,
        *,
        legacy_bindings: tuple[str, ...],
        resource_attribute: str,
    ) -> None:
        super().__init__(
            "philsfusion.commands.bom.legacy",
            created_handler_name,
            legacy_bindings=legacy_bindings,
            resource_attribute=resource_attribute,
            cleanup_factory_name="BomRuntimeCleanup",
        )


def build_bom_actions() -> dict[str, BomCommandAction]:
    return {
        "bom.create": BomCommandAction(
            "ContextMenuCommandCreatedEventHandler",
            legacy_bindings=("PhilsBom_contextMenuButton1",),
            resource_attribute="COMMAND_ICON",
        ),
        "bom.settings": BomCommandAction(
            "CommandCreatedEventHandler",
            legacy_bindings=("PhilsBom_contextMenuButton2",),
            resource_attribute="COMMAND_ICON_SETTINGS",
        ),
    }
