import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import adsk.core

from philsfusion import __version__
from philsfusion.catalog import SHELL_GROUPS, GroupSpec, build_foundation_registry
from philsfusion.commands.design import context as design_context
from philsfusion.commands.design.bindings import build_design_actions
from philsfusion.fusion.actions import SimpleCommandAction
from philsfusion.lifecycle import CommandBinding, Lifecycle
from philsfusion.registry import CommandSpec
from philsfusion.services.diagnostics import build_diagnostics, format_diagnostics
from philsfusion.services.settings import SETTINGS_SCHEMA_VERSION

PANEL_ID = "PhilsFusionToolsPanel"
PANEL_NAME = "Phils Fusion Tools"
WORKSPACE_ID = "FusionSolidEnvironment"
TAB_ID = "SolidTab"
PANEL_AFTER_ID = "SolidModifyPanel"


def _delete_fusion_object(item: Any) -> None:
    if item is None:
        return
    if hasattr(item, "isValid") and not item.isValid:
        return
    item.deleteMe()


class _CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, callback):
        super().__init__()
        self._callback = callback

    def notify(self, _args):
        self._callback()


@dataclass
class _FusionRegistration:
    owned_objects: tuple[Any, ...]
    handler_refs: tuple[object, ...]
    disposed: bool = False

    def dispose(self) -> None:
        if self.disposed:
            return
        self.disposed = True

        errors = []
        for item in reversed(self.owned_objects):
            try:
                _delete_fusion_object(item)
            except Exception as error:
                errors.append(error)
        if errors:
            details = "; ".join(str(error) for error in errors)
            raise RuntimeError(details)


class FusionUiAdapter:
    def __init__(self, ui):
        self._ui = ui
        self._panel = None

    def register_group(
        self,
        group: GroupSpec,
        command_bindings: tuple[CommandBinding, ...],
    ) -> _FusionRegistration:
        owned = []
        handlers = []
        try:
            panel, panel_created = self._get_panel()
            if panel_created:
                owned.append(panel)

            stale_control = panel.controls.itemById(group.control_id)
            _delete_fusion_object(stale_control)

            resource_folder = self._resource_folder(group.name.casefold())
            group_control = panel.controls.addDropDown(
                group.name,
                resource_folder,
                group.control_id,
            )
            group_control.isEnabled = group.available
            owned.append(group_control)

            for spec, callback in command_bindings:
                installed = callback.install(self._ui, group_control.controls, spec)
                owned.extend(installed.owned_objects)
                handlers.extend(installed.handler_refs)

            return _FusionRegistration(tuple(owned), tuple(handlers))
        except Exception:
            for item in reversed(owned):
                try:
                    _delete_fusion_object(item)
                except Exception:
                    pass
            raise

    def _get_panel(self):
        if self._panel is not None and self._panel.isValid:
            return self._panel, False

        workspace = self._ui.workspaces.itemById(WORKSPACE_ID)
        if workspace is None:
            raise RuntimeError(f"Fusion workspace not found: {WORKSPACE_ID}")

        solid_tab = workspace.toolbarTabs.itemById(TAB_ID)
        panels = solid_tab.toolbarPanels if solid_tab else workspace.toolbarPanels
        panel = panels.itemById(PANEL_ID)
        if panel is not None:
            _delete_fusion_object(panel)

        self._panel = panels.add(PANEL_ID, PANEL_NAME, PANEL_AFTER_ID, False)
        if self._panel is None:
            raise RuntimeError("Fusion did not create the Phils Fusion Tools panel")
        return self._panel, True

    @staticmethod
    def _resource_folder(resource_key):
        resource_path = Path(__file__).resolve().parents[1] / "resources" / resource_key
        return str(resource_path) if resource_path.is_dir() else ""


class PhilsFusionApplication:
    def __init__(self, app, ui, install_root: Path):
        self._app = app
        self._ui = ui
        self._install_root = install_root
        self._build_info = self._load_build_info()
        self._design_actions = build_design_actions()
        self._lifecycle = Lifecycle(
            adapter=FusionUiAdapter(ui),
            registry=build_foundation_registry(),
            groups=SHELL_GROUPS,
            handler_factory=self._make_action,
        )

    def start(self):
        design_context.init(self._app, self._ui)
        try:
            self._lifecycle.start()
        except Exception:
            design_context.clear_handlers()
            raise

    def stop(self):
        try:
            self._lifecycle.stop()
        finally:
            design_context.clear_handlers()

    def _make_action(self, spec: CommandSpec):
        design_action = self._design_actions.get(spec.handler_key)
        if design_action is not None:
            return design_action

        callbacks = {
            "help.diagnostics": self._show_diagnostics,
            "help.about_migration": self._show_about_migration,
        }
        action_callback = callbacks.get(spec.handler_key)
        if action_callback is None:
            def migration_callback():
                self._show_migration_pending(spec)

            action_callback = migration_callback
        return SimpleCommandAction(
            action_callback,
            handler_factory=_CommandCreatedHandler,
            resource_folder=FusionUiAdapter._resource_folder(spec.resource_key),
        )

    def _show_migration_pending(self, spec: CommandSpec):
        self._ui.messageBox(
            f"{spec.name} is being migrated into Phils Fusion Tools 2.0.",
            "Phils Fusion Tools",
        )

    def _show_about_migration(self):
        self._ui.messageBox(
            "Phils Fusion Tools 2.0\n\n"
            "Unified BOM, design, fabrication, export, and cleanup tools.\n"
            "Command migration is in progress in this development build.",
            "About Phils Fusion Tools",
        )

    def _show_diagnostics(self):
        info = self._build_info
        documents = Path(os.path.expanduser("~/Documents"))
        diagnostics = build_diagnostics(
            version=__version__,
            source_commit=info.get("commit", "development"),
            package_fingerprint=info.get("package_tree_hash", "development"),
            install_path=str(self._install_root),
            settings_schema=SETTINGS_SCHEMA_VERSION,
            startup_health="healthy" if self._lifecycle.is_active else "stopped",
            migration_status=info.get("artifact", "foundation"),
            log_path=str(documents / "PhilsFusionTools" / "logs" / "PhilsFusionTools.log"),
        )
        self._ui.messageBox(format_diagnostics(diagnostics), "Phils Fusion Tools Diagnostics")

    def _load_build_info(self):
        path = self._install_root / "build-info.json"
        if not path.is_file():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}


def create_application():
    app = adsk.core.Application.get()
    if app is None or app.userInterface is None:
        raise RuntimeError("Fusion user interface is unavailable")
    install_root = Path(__file__).resolve().parents[1]
    return PhilsFusionApplication(app, app.userInterface, install_root)
