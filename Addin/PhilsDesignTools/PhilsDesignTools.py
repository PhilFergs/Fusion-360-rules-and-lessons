import adsk.core
import traceback
import os
import sys


def _ensure_local_on_syspath():
    """
    Make sure the add-in folder is on sys.path before importing any smg_* modules.
    This is REQUIRED for multi-file add-ins in Fusion.
    """
    this_dir = os.path.dirname(os.path.realpath(__file__))
    if this_dir not in sys.path:
        sys.path.append(this_dir)


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface

    try:
        _ensure_local_on_syspath()

        # Import internal modules only after sys.path is patched.
        import smg_context as ctx
        import smg_ea as ea_mod
        import smg_shs as shs_mod
        import smg_rhs as rhs_mod
        import smg_rotate as rot_mod
        import smg_rename as rename_mod
        import smg_split as split_mod
        import smg_ea_hole_export as hole_export_mod
        import smg_iges_export as iges_export_mod
        import smg_component_set as component_set_mod
        import smg_wireframe as wireframe_mod
        import smg_holecut as holecut_mod
        import smg_logger as logger

        # Initialise shared context (app, ui, handler store, etc.).
        if hasattr(ctx, "init"):
            ctx.init(app, ui)

        # Get workspace and panels.
        ws = ui.workspaces.itemById("FusionSolidEnvironment")
        if not ws:
            ui.messageBox("FusionSolidEnvironment workspace not found.")
            return

        solid_tab = ws.toolbarTabs.itemById("SolidTab")
        if solid_tab:
            create_panel = solid_tab.toolbarPanels.itemById("SolidCreatePanel")
            modify_panel = solid_tab.toolbarPanels.itemById("SolidModifyPanel")
        else:
            create_panel = ws.toolbarPanels.itemById("SolidCreatePanel")
            modify_panel = ws.toolbarPanels.itemById("SolidModifyPanel")

        panel_id = "PhilsDesignToolsPanel"
        panel = None

        # Remove any stale panel created outside the Solid tab.
        try:
            stale_panel = ws.toolbarPanels.itemById(panel_id)
            if stale_panel:
                stale_panel.deleteMe()
        except:
            pass

        if solid_tab:
            panel = solid_tab.toolbarPanels.itemById(panel_id)
            if not panel:
                panel = solid_tab.toolbarPanels.add(
                    panel_id, "PhilsDesignTools", "SolidModifyPanel", False
                )
        else:
            panel = ws.toolbarPanels.itemById(panel_id)
            if not panel:
                panel = ws.toolbarPanels.add(
                    panel_id, "PhilsDesignTools", "SolidModifyPanel", False
                )

        if not panel:
            ui.messageBox("PhilsDesignTools panel not found or created.")
            return

        logger.log("PhilsDesignTools started.")

        legacy_cmd_ids = [
            "PhilsDesignTools_EA",
            "PhilsDesignTools_SHS",
            "PhilsDesignTools_RHS",
            "PhilsDesignTools_Rotate",
            "PhilsDesignTools_EA_BatchRename",
            "PhilsDesignTools_SplitBody",
            "PhilsDesignTools_SplitBody_V2",
            "PhilsDesignTools_SplitBody_Delete",
            "PhilsDesignTools_EA_HoleExport_CSV",
            "PhilsDesignTools_IGES_Export",
            "PhilsDesignTools_ComponentSet",
            "PhilsDesignTools_WireframeFromBody",
            "PhilsDesignTools_HoleCutFromFace",
        ]

        for legacy_panel in (create_panel, modify_panel):
            if not legacy_panel:
                continue
            for cmd_id in legacy_cmd_ids:
                ctrl = legacy_panel.controls.itemById(cmd_id)
                if ctrl:
                    ctrl.deleteMe()

        # Register all commands on the PhilsDesignTools panel.
        ea_mod.register(ui, panel)
        shs_mod.register(ui, panel)
        rhs_mod.register(ui, panel)
        rot_mod.register(ui, panel)
        rename_mod.register(ui, panel)
        split_mod.register(ui, panel)
        hole_export_mod.register(ui, panel)
        iges_export_mod.register(ui, panel)
        component_set_mod.register(ui, panel)
        wireframe_mod.register(ui, panel)
        holecut_mod.register(ui, panel)

    except:
        try:
            logger.log("PhilsDesignTools run error:\n" + traceback.format_exc())
        except:
            pass
        ui.messageBox("PhilsDesignTools run error:\n" + traceback.format_exc())


def stop(context):
    app = adsk.core.Application.get()
    ui = app.userInterface

    try:
        ws = ui.workspaces.itemById("FusionSolidEnvironment")

        cmd_ids = [
            "PhilsDesignTools_EA",
            "PhilsDesignTools_SHS",
            "PhilsDesignTools_RHS",
            "PhilsDesignTools_Rotate",
            "PhilsDesignTools_EA_BatchRename",
            "PhilsDesignTools_SplitBody",
            "PhilsDesignTools_SplitBody_V2",
            "PhilsDesignTools_SplitBody_Delete",
            "PhilsDesignTools_EA_HoleExport_CSV",
            "PhilsDesignTools_IGES_Export",
            "PhilsDesignTools_ComponentSet",
            "PhilsDesignTools_WireframeFromBody",
            "PhilsDesignTools_HoleCutFromFace",
        ]

        if ws:
            panel = None
            solid_tab = ws.toolbarTabs.itemById("SolidTab")
            if solid_tab:
                panel = solid_tab.toolbarPanels.itemById("PhilsDesignToolsPanel")
                if panel:
                    for cmd_id in cmd_ids:
                        ctrl = panel.controls.itemById(cmd_id)
                        if ctrl:
                            ctrl.deleteMe()
                    panel.deleteMe()

            panel = ws.toolbarPanels.itemById("PhilsDesignToolsPanel")
            if panel:
                for cmd_id in cmd_ids:
                    ctrl = panel.controls.itemById(cmd_id)
                    if ctrl:
                        ctrl.deleteMe()
                panel.deleteMe()

            for panel_id in ("SolidCreatePanel", "SolidModifyPanel"):
                legacy_panel = ws.toolbarPanels.itemById(panel_id)
                if not legacy_panel:
                    continue
                for cmd_id in cmd_ids:
                    ctrl = legacy_panel.controls.itemById(cmd_id)
                    if ctrl:
                        ctrl.deleteMe()

        for cmd_id in cmd_ids:
            cmd_def = ui.commandDefinitions.itemById(cmd_id)
            if cmd_def:
                cmd_def.deleteMe()

        import smg_logger as logger
        logger.log("PhilsDesignTools stopped.")
    except:
        try:
            import smg_logger as logger
            logger.log("PhilsDesignTools stop error:\n" + traceback.format_exc())
        except:
            pass
        ui.messageBox("PhilsDesignTools stop error:\n" + traceback.format_exc())
