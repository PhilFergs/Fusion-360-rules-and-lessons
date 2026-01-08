import adsk.core
import adsk.fusion
import traceback
import os

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_HoleCutFromFace"
CMD_NAME = "Hole Cut From Face"
CMD_TOOLTIP = "Cut a target body using a cylindrical hole face as the tool axis."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

HOLE_FACE_INPUT_ID = "holecut_hole_face"
TARGET_BODY_INPUT_ID = "holecut_target_body"


def _matrix_identity() -> adsk.core.Matrix3D:
    return adsk.core.Matrix3D.create()


def _invert_matrix(m: adsk.core.Matrix3D) -> adsk.core.Matrix3D:
    inv = m.copy()
    inv.invert()
    return inv


class HoleCutCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById(HOLE_FACE_INPUT_ID):
                return

            sel_hole = inputs.addSelectionInput(
                HOLE_FACE_INPUT_ID,
                "Hole Face",
                "Select inside cylindrical hole face"
            )
            sel_hole.addSelectionFilter("CylindricalFaces")
            sel_hole.setSelectionLimits(1, 1)

            sel_body = inputs.addSelectionInput(
                TARGET_BODY_INPUT_ID,
                "Target Body",
                "Select target body to cut"
            )
            sel_body.addSelectionFilter("Bodies")
            sel_body.setSelectionLimits(1, 1)

            on_exec = HoleCutExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)

        except:
            logger.log("Hole Cut From Face UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Hole Cut From Face UI failed:\n" + traceback.format_exc())


class HoleCutExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log("Hole Cut From Face failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Hole Cut From Face failed:\n" + traceback.format_exc())


def _execute(args):
    ui = ctx.ui()
    app = ctx.app()

    cmd = args.command
    inputs = cmd.commandInputs

    sel_hole = adsk.core.SelectionCommandInput.cast(inputs.itemById(HOLE_FACE_INPUT_ID))
    sel_body = adsk.core.SelectionCommandInput.cast(inputs.itemById(TARGET_BODY_INPUT_ID))

    if not sel_hole or sel_hole.selectionCount != 1:
        ui.messageBox("Please select exactly one cylindrical hole face.")
        return

    if not sel_body or sel_body.selectionCount != 1:
        ui.messageBox("Please select exactly one target body.")
        return

    hole_face_ctx = adsk.fusion.BRepFace.cast(sel_hole.selection(0).entity)
    target_body_ctx = adsk.fusion.BRepBody.cast(sel_body.selection(0).entity)

    if not hole_face_ctx or not target_body_ctx:
        ui.messageBox("Invalid selection. Please select a cylindrical hole face and a body.")
        return

    hole_body_ctx = hole_face_ctx.body
    hole_occ = hole_body_ctx.assemblyContext
    hole_face_native = hole_face_ctx.nativeObject or hole_face_ctx

    target_body_native = target_body_ctx.nativeObject or target_body_ctx
    target_comp = target_body_native.parentComponent
    target_occ = target_body_ctx.assemblyContext

    hole_to_world = hole_occ.transform if hole_occ else _matrix_identity()
    world_to_target = _invert_matrix(target_occ.transform) if target_occ else _matrix_identity()

    surface_native = hole_face_native.geometry
    if surface_native.surfaceType != adsk.core.SurfaceTypes.CylinderSurfaceType:
        ui.messageBox(
            "Selected face is not cylindrical.\n\n"
            "Please select the inside wall of a cylindrical hole."
        )
        return

    cylinder_native = adsk.core.Cylinder.cast(surface_native)
    if not cylinder_native:
        ui.messageBox("Failed to read cylindrical geometry from the selected face.")
        return

    axis_native = cylinder_native.axis.copy()
    radius = cylinder_native.radius

    circ_edge_native = None
    for i in range(hole_face_native.edges.count):
        e = hole_face_native.edges.item(i)
        if adsk.core.Circle3D.cast(e.geometry):
            circ_edge_native = e
            break

    if not circ_edge_native:
        ui.messageBox("Could not find a circular edge on the selected face.")
        return

    circle_native = adsk.core.Circle3D.cast(circ_edge_native.geometry)
    center_native = circle_native.center

    if axis_native.length == 0:
        ui.messageBox("Cylinder axis has zero length. Cannot proceed.")
        return

    axis_native.normalize()

    center_world = center_native.copy()
    center_world.transformBy(hole_to_world)

    axis_world = axis_native.copy()
    axis_world.transformBy(hole_to_world)
    axis_world.normalize()

    center_target = center_world.copy()
    center_target.transformBy(world_to_target)

    axis_target = axis_world.copy()
    axis_target.transformBy(world_to_target)
    axis_target.normalize()

    height = 200.0
    half = height * 0.5

    start_point = center_target.copy()
    back_vec = axis_target.copy()
    back_vec.scaleBy(-half)
    start_point.translateBy(back_vec)

    end_point = center_target.copy()
    fwd_vec = axis_target.copy()
    fwd_vec.scaleBy(half)
    end_point.translateBy(fwd_vec)

    temp_mgr = adsk.fusion.TemporaryBRepManager.get()

    tool_temp = temp_mgr.createCylinderOrCone(
        start_point,
        radius,
        end_point,
        radius,
    )

    tool_body = target_comp.bRepBodies.add(tool_temp)
    tool_body.name = "Hole Cut Tool"

    combine_feats = target_comp.features.combineFeatures
    tool_bodies = adsk.core.ObjectCollection.create()
    tool_bodies.add(tool_body)

    ci = combine_feats.createInput(target_body_native, tool_bodies)
    ci.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
    ci.isKeepToolBodies = False

    combine_feats.add(ci)

    logger.log_command(
        CMD_NAME,
        {
            "hole_body": hole_body_ctx.name if hole_body_ctx else "",
            "target_body": target_body_native.name if target_body_native else "",
            "radius": radius,
            "height": height,
        },
    )

    try:
        app.activeViewport.refresh()
    except:
        pass


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = HoleCutCommandCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
