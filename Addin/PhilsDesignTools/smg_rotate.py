import adsk.core, adsk.fusion, traceback, math
import smg_context as ctx


CMD_ID = "PhilsDesignTools_Rotate"
CMD_NAME = "Rotate Steel Member"
CMD_TOOLTIP = "Rotate selected steel members."


class RotateExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            ctx.ui().messageBox("Rotate failed:\n" + traceback.format_exc())


class RotateCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            sel = inputs.addSelectionInput(
                "rot_members",
                "Members",
                "Select steel member occurrences to rotate"
            )
            sel.addSelectionFilter("Occurrences")
            sel.setSelectionLimits(1, 0)

            dd = inputs.addDropDownCommandInput(
                "rot_angle",
                "Rotation",
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            dd.listItems.add("90°", True)
            dd.listItems.add("-90°", False)

            on_exec = RotateExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)

        except:
            ctx.ui().messageBox("Rotate UI failed:\n" + traceback.format_exc())


# ---------------------------------------------------------
# EA axis: line through hole centres (from EA_AddIn_v4_0_0)
# ---------------------------------------------------------

def _get_ea_hole_axis(occ):
    """Return (sp, ep, mid) for EA rotation axis based on hole centres."""
    centers = []

    for body in occ.bRepBodies:
        for edge in body.edges:
            circ = adsk.core.Circle3D.cast(edge.geometry)
            if circ:
                centers.append(circ.center)

    if len(centers) < 2:
        return None, None, None

    max_d2 = -1.0
    sp = ep = None

    for i in range(len(centers)):
        c1 = centers[i]
        for j in range(i + 1, len(centers)):
            c2 = centers[j]
            dx = c2.x - c1.x
            dy = c2.y - c1.y
            dz = c2.z - c1.z
            d2 = dx * dx + dy * dy + dz * dz
            if d2 > max_d2:
                max_d2 = d2
                sp = c1
                ep = c2

    if max_d2 <= 0 or sp is None or ep is None:
        return None, None, None

    mid = adsk.core.Point3D.create(
        (sp.x + ep.x) * 0.5,
        (sp.y + ep.y) * 0.5,
        (sp.z + ep.z) * 0.5,
    )
    return sp, ep, mid


# ---------------------------------------------------------
# SHS/RHS logic: length axis (local Y) + bbox centre pivot
# ---------------------------------------------------------

def _get_length_axis_and_center(occ):
    """
    Returns (axis_vector_world, center_point_world) for members whose
    length is along local Y (SHS/RHS generation logic).
    """
    bbox = occ.boundingBox
    if not bbox:
        return None, None

    minp = bbox.minPoint
    maxp = bbox.maxPoint
    center = adsk.core.Point3D.create(
        (minp.x + maxp.x) * 0.5,
        (minp.y + maxp.y) * 0.5,
        (minp.z + maxp.z) * 0.5,
    )

    # local Y axis -> world
    axis = adsk.core.Vector3D.create(0, 1, 0)
    t = occ.transform
    axis.transformBy(t)
    if axis.length == 0:
        return None, None
    axis.normalize()

    return axis, center


# ---------------------------------------------------------
# Central execute
# ---------------------------------------------------------

def _execute(args):
    cmd = args.command
    inputs = cmd.commandInputs
    sel = adsk.core.SelectionCommandInput.cast(inputs.itemById("rot_members"))

    dd = adsk.core.DropDownCommandInput.cast(inputs.itemById("rot_angle"))
    # FIX: ListItem has .name, not .text
    angle_name = dd.selectedItem.name if dd and dd.selectedItem else "90°"
    angle_sign = -1.0 if angle_name.startswith("-") else 1.0
    angle_rad = angle_sign * math.radians(90.0)

    if not sel or sel.selectionCount == 0:
        ctx.ui().messageBox("Select at least one steel member occurrence.")
        return

    for i in range(sel.selectionCount):
        occ = adsk.fusion.Occurrence.cast(sel.selection(i).entity)
        if not occ:
            continue

        comp_name = occ.component.name if occ.component else ""

        # ---------- EA: use hole-centre axis (hinge along bolt line) ----------
        if comp_name.startswith("EA"):
            sp, ep, mid = _get_ea_hole_axis(occ)
            if sp and ep:
                axis_vec = adsk.core.Vector3D.create(
                    ep.x - sp.x, ep.y - sp.y, ep.z - sp.z
                )
                if axis_vec.length != 0:
                    axis_vec.normalize()
                    rot = adsk.core.Matrix3D.create()
                    rot.setToRotation(angle_rad, axis_vec, mid)
                    t = occ.transform
                    t.transformBy(rot)
                    occ.transform = t
                    continue  # EA done, go to next

        # ---------- SHS / RHS (and any others): spin about length axis ----------
        axis, center = _get_length_axis_and_center(occ)
        if not axis or not center:
            continue

        rot = adsk.core.Matrix3D.create()
        rot.setToRotation(angle_rad, axis, center)
        t = occ.transform
        t.transformBy(rot)
        occ.transform = t

    try:
        ctx.app().activeViewport.refresh()
    except:
        pass


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP
        )

    handler = RotateCreatedHandler()
    cmd_def.commandCreated.add(handler)
    ctx.add_handler(handler)

    if not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = True

