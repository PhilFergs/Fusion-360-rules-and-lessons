from dataclasses import dataclass

import pytest

from philsfusion.catalog import SHELL_GROUPS, build_foundation_registry
from philsfusion.lifecycle import Lifecycle


@dataclass
class FakeRegistration:
    ui: "FakeUi"
    group_id: str
    handler_refs: tuple[object, ...]
    disposed: bool = False

    def dispose(self):
        if self.disposed:
            return
        self.disposed = True
        self.ui.visible_control_ids.remove(self.group_id)
        for handler in self.handler_refs:
            self.ui.retained_handlers.remove(handler)
        self.ui.deleted_group_ids.append(self.group_id)


class FakeUi:
    def __init__(self):
        self.visible_control_ids = set()
        self.retained_handlers = []
        self.deleted_group_ids = []
        self.fail_on_group_id = None

    def register_group(self, group, command_bindings):
        if group.control_id == self.fail_on_group_id:
            raise RuntimeError(f"failed to create {group.control_id}")
        if group.control_id in self.visible_control_ids:
            raise AssertionError(f"duplicate control: {group.control_id}")

        handlers = tuple(object() for _spec, _callback in command_bindings)
        self.visible_control_ids.add(group.control_id)
        self.retained_handlers.extend(handlers)
        return FakeRegistration(self, group.control_id, handlers)

    @property
    def retained_handler_count(self):
        return len(self.retained_handlers)


def make_lifecycle(fake_ui):
    return Lifecycle(
        adapter=fake_ui,
        registry=build_foundation_registry(),
        groups=SHELL_GROUPS,
        handler_factory=lambda spec: lambda: spec.command_id,
    )


def test_start_stop_start_does_not_duplicate_controls():
    fake_ui = FakeUi()
    lifecycle = make_lifecycle(fake_ui)

    lifecycle.start()
    lifecycle.start()
    lifecycle.stop()
    lifecycle.stop()
    lifecycle.start()

    assert fake_ui.visible_control_ids == {
        "PhilsFusionTools_BOM",
        "PhilsFusionTools_Create",
        "PhilsFusionTools_Modify",
        "PhilsFusionTools_Fabricate",
        "PhilsFusionTools_Export",
        "PhilsFusionTools_Cleanup",
        "PhilsFusionTools_Help",
    }
    assert fake_ui.retained_handler_count == 1
    assert lifecycle.is_active is True


def test_stop_releases_groups_in_reverse_order():
    fake_ui = FakeUi()
    lifecycle = make_lifecycle(fake_ui)
    lifecycle.start()

    lifecycle.stop()

    assert fake_ui.deleted_group_ids == [
        "PhilsFusionTools_Help",
        "PhilsFusionTools_Cleanup",
        "PhilsFusionTools_Export",
        "PhilsFusionTools_Fabricate",
        "PhilsFusionTools_Modify",
        "PhilsFusionTools_Create",
        "PhilsFusionTools_BOM",
    ]
    assert fake_ui.retained_handler_count == 0
    assert lifecycle.is_active is False


def test_failed_start_rolls_back_every_created_group():
    fake_ui = FakeUi()
    fake_ui.fail_on_group_id = "PhilsFusionTools_Fabricate"
    lifecycle = make_lifecycle(fake_ui)

    with pytest.raises(RuntimeError, match="Fabricate"):
        lifecycle.start()

    assert fake_ui.visible_control_ids == set()
    assert fake_ui.retained_handler_count == 0
    assert lifecycle.is_active is False

