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
        import smg_logger as logger

        # Initialise shared context (app, ui, handler store, etc.).
        if hasattr(ctx, "init"):
            ctx.init(app, ui)

        # Get workspace and panels.
        ws = ui.workspaces.itemById("FusionSolidEnvironment")
        if not ws:
            ui.messageBox("FusionSolidEnvironment workspace not found.")
            return

        create_panel = ws.toolbarPanels.itemById("SolidCreatePanel")
        if not create_panel:
            ui.messageBox("SolidCreatePanel not found.")
            return

        modify_panel = ws.toolbarPanels.itemById("SolidModifyPanel")
        if not modify_panel:
            ui.messageBox("SolidModifyPanel not found.")
            return

        logger.log("PhilsDesignTools started.")

        # Register generation commands on Create panel.
        ea_mod.register(ui, create_panel)
        shs_mod.register(ui, create_panel)
        rhs_mod.register(ui, create_panel)
        rot_mod.register(ui, create_panel)

        # Register batch rename on Modify panel.
        rename_mod.register(ui, modify_panel)
        split_mod.register(ui, modify_panel)

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
        ]

        panel_ids = ["SolidCreatePanel", "SolidModifyPanel"]

        if ws:
            for panel_id in panel_ids:
                panel = ws.toolbarPanels.itemById(panel_id)
                if not panel:
                    continue
                for cmd_id in cmd_ids:
                    ctrl = panel.controls.itemById(cmd_id)
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
