from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Protocol

from philsfusion.registry import CommandSpec


def _delete_owned(item: Any) -> None:
    if item is None:
        return
    if hasattr(item, "isValid") and not item.isValid:
        return
    item.deleteMe()


@dataclass(frozen=True, slots=True)
class InstalledCommand:
    owned_objects: tuple[Any, ...]
    handler_refs: tuple[object, ...]


class CommandAction(Protocol):
    def install(self, ui, controls, spec: CommandSpec) -> InstalledCommand: ...


class SimpleCommandAction:
    visible_control_count = 1
    legacy_ids: tuple[str, ...] = ()

    def __init__(
        self,
        callback: Callable[[], None],
        *,
        handler_factory: Callable[[Callable[[], None]], object],
        resource_folder: str = "",
    ) -> None:
        self._callback = callback
        self._handler_factory = handler_factory
        self._resource_folder = resource_folder

    def install(self, ui, controls, spec: CommandSpec) -> InstalledCommand:
        owned = []
        handlers = []
        try:
            stale = ui.commandDefinitions.itemById(spec.command_id)
            _delete_owned(stale)

            definition = ui.commandDefinitions.addButtonDefinition(
                spec.command_id,
                spec.name,
                spec.tooltip,
                self._resource_folder,
            )
            owned.append(definition)

            handler = self._handler_factory(self._callback)
            definition.commandCreated.add(handler)
            handlers.append(handler)

            control = controls.addCommand(definition)
            owned.append(control)
            return InstalledCommand(tuple(owned), tuple(handlers))
        except Exception:
            for item in reversed(owned):
                try:
                    _delete_owned(item)
                except Exception:
                    pass
            raise


class ModuleCommandAction:
    visible_control_count = 1

    def __init__(
        self,
        module_name: str,
        created_handler_name: str,
        *,
        legacy_bindings: tuple[str, ...] = (),
        legacy_handler_factory_name: str = "",
    ) -> None:
        self.module_name = module_name
        self.created_handler_name = created_handler_name
        self.legacy_ids = tuple(legacy_bindings)
        self.legacy_handler_factory_name = legacy_handler_factory_name

    def install(self, ui, controls, spec: CommandSpec) -> InstalledCommand:
        module = import_module(self.module_name)
        handler_type = getattr(module, self.created_handler_name)
        resource_folder = getattr(module, "RESOURCE_FOLDER", "")
        legacy_factories = {}
        if self.legacy_handler_factory_name:
            factory_builder = getattr(module, self.legacy_handler_factory_name)
            legacy_factories = factory_builder()
            missing = set(self.legacy_ids) - set(legacy_factories)
            if missing:
                missing_text = ", ".join(sorted(missing))
                raise ValueError(f"missing legacy handler factories: {missing_text}")
        owned = []
        handlers = []

        try:
            canonical, handler = self._create_definition(
                ui,
                spec.command_id,
                spec.name,
                spec.tooltip,
                resource_folder,
                handler_type,
            )
            owned.append(canonical)
            handlers.append(handler)

            control = controls.addCommand(canonical)
            owned.append(control)

            for legacy_id in self.legacy_ids:
                legacy, legacy_handler = self._create_definition(
                    ui,
                    legacy_id,
                    spec.name,
                    spec.tooltip,
                    resource_folder,
                    legacy_factories.get(legacy_id, handler_type),
                )
                owned.append(legacy)
                handlers.append(legacy_handler)

            return InstalledCommand(tuple(owned), tuple(handlers))
        except Exception:
            for item in reversed(owned):
                try:
                    _delete_owned(item)
                except Exception:
                    pass
            raise

    @staticmethod
    def _create_definition(
        ui,
        command_id: str,
        name: str,
        tooltip: str,
        resource_folder: str,
        handler_factory,
    ):
        stale = ui.commandDefinitions.itemById(command_id)
        _delete_owned(stale)

        definition = ui.commandDefinitions.addButtonDefinition(
            command_id,
            name,
            tooltip,
            resource_folder,
        )
        try:
            handler = handler_factory()
            definition.commandCreated.add(handler)
            return definition, handler
        except Exception:
            _delete_owned(definition)
            raise
