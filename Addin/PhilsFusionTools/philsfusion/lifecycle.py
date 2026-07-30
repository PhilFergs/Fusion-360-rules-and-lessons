from collections.abc import Callable, Iterable
from typing import Any, Protocol

from philsfusion.catalog import GroupSpec
from philsfusion.registry import CommandRegistry, CommandSpec

CommandCallback = Callable[[], None]
CommandBinding = tuple[CommandSpec, CommandCallback]


class UiRegistration(Protocol):
    handler_refs: tuple[object, ...]

    def dispose(self) -> None: ...


class UiAdapter(Protocol):
    def register_group(
        self,
        group: GroupSpec,
        command_bindings: tuple[CommandBinding, ...],
    ) -> UiRegistration: ...


class Lifecycle:
    def __init__(
        self,
        *,
        adapter: UiAdapter,
        registry: CommandRegistry,
        groups: Iterable[GroupSpec],
        handler_factory: Callable[[CommandSpec], CommandCallback],
    ) -> None:
        self._adapter = adapter
        self._registry = registry
        self._groups = tuple(groups)
        self._handler_factory = handler_factory
        self._registrations: list[UiRegistration] = []
        self._handler_refs: list[Any] = []
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def retained_handler_count(self) -> int:
        return len(self._handler_refs)

    def start(self) -> None:
        if self._active:
            return

        try:
            for group in self._groups:
                bindings = tuple(
                    (spec, self._handler_factory(spec))
                    for spec in self._registry.ordered(group.name)
                )
                registration = self._adapter.register_group(group, bindings)
                self._registrations.append(registration)
                self._handler_refs.extend(registration.handler_refs)
        except Exception:
            self._dispose_all()
            raise

        self._active = True

    def stop(self) -> None:
        if not self._registrations:
            self._active = False
            return

        errors = self._dispose_all()
        self._active = False
        if errors:
            details = "; ".join(str(error) for error in errors)
            raise RuntimeError(f"toolbar cleanup failed: {details}")

    def _dispose_all(self) -> tuple[Exception, ...]:
        errors = []
        while self._registrations:
            registration = self._registrations.pop()
            try:
                registration.dispose()
            except Exception as error:
                errors.append(error)
        self._handler_refs.clear()
        self._active = False
        return tuple(errors)
