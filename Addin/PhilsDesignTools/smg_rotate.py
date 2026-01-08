import adsk.core, adsk.fusion, traceback, math, os
import smg_context as ctx
import smg_logger as logger


CMD_ID = "PhilsDesignTools_Rotate"
CMD_NAME = "Rotate Steel Member"
CMD_TOOLTIP = "Rotate selected steel members."
DEBUG_ROTATE = True
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)


def _fmt_pt(p):
    return f"({p.x:.4f}, {p.y:.4f}, {p.z:.4f})"


def _fmt_vec(v):
    return f"({v.x:.4f}, {v.y:.4f}, {v.z:.4f})"


class RotateExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log("Rotate failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Rotate failed:\n" + traceback.format_exc())


class RotateCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById("rot_members"):
                return

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
            dd.listItems.add("90", True)
            dd.listItems.add("-90", False)

            on_exec = RotateExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)

        except:
            logger.log("Rotate UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Rotate UI failed:\n" + traceback.format_exc())


# ---------------------------------------------------------
# Hole-based pivot: line along length axis through hole centers
# ---------------------------------------------------------

def _get_hole_axis(occ, length_axis):
    """
    Return (axis_vector, pivot_point) from hole centers.
    Uses only circles whose normals are perpendicular to the member length axis.
    """
    if not occ or not length_axis:
        return None, None

    axis = adsk.core.Vector3D.create(length_axis.x, length_axis.y, length_axis.z)
    if axis.length == 0:
        return None, None
    axis.normalize()

    centers = []
    radii = []
    for body in occ.bRepBodies:
        for edge in body.edges:
            circ = adsk.core.Circle3D.cast(edge.geometry)
            if not circ:
                continue
            n = circ.normal
            if not n or n.length == 0:
                continue
            n_vec = adsk.core.Vector3D.create(n.x, n.y, n.z)
            n_vec.normalize()
            # Ignore circles whose normals are close to the length axis
            if abs(n_vec.dotProduct(axis)) > 0.2:
                continue
            centers.append(circ.center)
            radii.append(circ.radius)

    if len(centers) < 2:
        return None, None

    # Pick the most common radius cluster to isolate hole circles.
    rad_groups = []  # each item: [r_mean, [indices]]
    rad_tol = 1e-3
    for idx, r in enumerate(radii):
        found = False
        for g in rad_groups:
            if abs(r - g[0]) <= rad_tol:
                g[1].append(idx)
                g[0] = sum(radii[i] for i in g[1]) / len(g[1])
                found = True
                break
        if not found:
            rad_groups.append([r, [idx]])

    rad_groups.sort(key=lambda g: len(g[1]), reverse=True)
    keep_idx = set(rad_groups[0][1]) if rad_groups else set()

    # Keep only the bottom face circles (by world Z) to avoid mixing top/bottom.
    bottom_idx = list(keep_idx)
    if bottom_idx:
        min_z = min(centers[i].z for i in bottom_idx)
        z_tol = 1e-3
        bottom_idx = [i for i in bottom_idx if abs(centers[i].z - min_z) <= z_tol]
        # Fallback if the filter is too strict.
        if len(bottom_idx) < 2:
            bottom_idx = list(keep_idx)

    # Group duplicate circle edges into single hole centers.
    groups = []  # each item: [t_mean, [centers]]
    tol = 1e-3
    for i, c in enumerate(centers):
        if i not in bottom_idx:
            continue
        t = axis.x * c.x + axis.y * c.y + axis.z * c.z
        found = False
        for g in groups:
            if abs(t - g[0]) <= tol:
                g[1].append(c)
                # update mean t for stability
                g[0] = sum(axis.x * p.x + axis.y * p.y + axis.z * p.z for p in g[1]) / len(g[1])
                found = True
                break
        if not found:
            groups.append([t, [c]])

    hole_centers = []
    for _, pts in groups:
        sx = sy = sz = 0.0
        for p in pts:
            sx += p.x
            sy += p.y
            sz += p.z
        inv = 1.0 / len(pts)
        hole_centers.append(adsk.core.Point3D.create(sx * inv, sy * inv, sz * inv))

    if len(hole_centers) < 2:
        return None, None

    max_d2 = -1.0
    sp = ep = None
    for i in range(len(hole_centers)):
        c1 = hole_centers[i]
        for j in range(i + 1, len(hole_centers)):
            c2 = hole_centers[j]
            dx = c2.x - c1.x
            dy = c2.y - c1.y
            dz = c2.z - c1.z
            d2 = dx * dx + dy * dy + dz * dz
            if d2 > max_d2:
                max_d2 = d2
                sp = c1
                ep = c2

    if max_d2 <= 0 or sp is None or ep is None:
        return None, None

    axis_vec = adsk.core.Vector3D.create(ep.x - sp.x, ep.y - sp.y, ep.z - sp.z)
    if axis_vec.length == 0:
        return None, None
    axis_vec.normalize()

    mid = adsk.core.Point3D.create(
        (sp.x + ep.x) * 0.5,
        (sp.y + ep.y) * 0.5,
        (sp.z + ep.z) * 0.5,
    )
    return axis_vec, mid


def _get_ea_hole_axis(occ):
    """
    Return (axis_vector, pivot_point) from two EA hole circles on the outer face.
    The face is chosen by circular edges (preferred) or smallest area (fallback).
    """
    if not occ:
        return None, None

    bbox = occ.boundingBox
    center = None
    if bbox:
        minp = bbox.minPoint
        maxp = bbox.maxPoint
        center = adsk.core.Point3D.create(
            (minp.x + maxp.x) * 0.5,
            (minp.y + maxp.y) * 0.5,
            (minp.z + maxp.z) * 0.5,
        )

    best_face = None
    best_circles = None
    best_dist = None
    best_area = None
    face_min_area = None
    min_area = None

    for body in occ.bRepBodies:
        for face in body.faces:
            plane = adsk.core.Plane.cast(face.geometry)
            if not plane:
                continue
            circles = []
            for edge in face.edges:
                circ = adsk.core.Circle3D.cast(edge.geometry)
                if circ:
                    circles.append(circ)
            if len(circles) >= 2:
                try:
                    area = face.areaProperties().area
                except:
                    area = None
                dist = None
                if center:
                    n = plane.normal
                    if n and n.length > 0:
                        n_vec = adsk.core.Vector3D.create(n.x, n.y, n.z)
                        n_vec.normalize()
                        v = adsk.core.Vector3D.create(
                            center.x - plane.origin.x,
                            center.y - plane.origin.y,
                            center.z - plane.origin.z,
                        )
                        dist = abs(n_vec.dotProduct(v))
                if not best_face:
                    best_face = face
                    best_circles = circles
                    best_dist = dist
                    best_area = area
                else:
                    if dist is not None and best_dist is not None:
                        if dist > best_dist + 1e-6:
                            best_face = face
                            best_circles = circles
                            best_dist = dist
                            best_area = area
                        elif abs(dist - best_dist) <= 1e-6:
                            if len(circles) > len(best_circles or []):
                                best_face = face
                                best_circles = circles
                                best_dist = dist
                                best_area = area
                            elif area is not None and best_area is not None and area < best_area:
                                best_face = face
                                best_circles = circles
                                best_dist = dist
                                best_area = area
                    elif dist is not None and best_dist is None:
                        best_face = face
                        best_circles = circles
                        best_dist = dist
                        best_area = area
                    elif dist is None and best_dist is None:
                        if len(circles) > len(best_circles or []):
                            best_face = face
                            best_circles = circles
                            best_area = area
                        elif area is not None and best_area is not None and area < best_area:
                            best_face = face
                            best_circles = circles
                            best_area = area
            else:
                try:
                    area = face.areaProperties().area
                except:
                    area = None
                if area is not None and (min_area is None or area < min_area):
                    min_area = area
                    face_min_area = face

    hole_face = best_face if best_face else face_min_area
    if not hole_face:
        if DEBUG_ROTATE:
            logger.log("EA rotate: no suitable planar face found.")
        return None, None

    plane = adsk.core.Plane.cast(hole_face.geometry)
    if not plane:
        return None, None

    # Collect unique circles on the chosen face.
    circles = []
    tol = 1e-4
    if best_face and hole_face == best_face and best_circles:
        source_circles = best_circles
    else:
        source_circles = []
        for edge in hole_face.edges:
            circ = adsk.core.Circle3D.cast(edge.geometry)
            if circ:
                source_circles.append(circ)
    for circ in source_circles:
        found = False
        for existing in circles:
            if existing.center.distanceTo(circ.center) <= tol:
                found = True
                break
        if not found:
            circles.append(circ)

    if len(circles) < 2:
        if DEBUG_ROTATE:
            logger.log(f"EA rotate: only {len(circles)} circle(s) on face, need 2.")
        return None, None

    # Pick the two farthest holes.
    max_d2 = -1.0
    c1 = c2 = None
    r1 = r2 = None
    for i in range(len(circles)):
        a = circles[i]
        for j in range(i + 1, len(circles)):
            b = circles[j]
            dx = b.center.x - a.center.x
            dy = b.center.y - a.center.y
            dz = b.center.z - a.center.z
            d2 = dx * dx + dy * dy + dz * dz
            if d2 > max_d2:
                max_d2 = d2
                c1, c2 = a.center, b.center
                r1, r2 = a.radius, b.radius

    if max_d2 <= 0 or not c1 or not c2:
        if DEBUG_ROTATE:
            logger.log("EA rotate: failed to find two distinct hole circles.")
        return None, None

    # Axis direction: line between centers projected onto face plane.
    v = adsk.core.Vector3D.create(c2.x - c1.x, c2.y - c1.y, c2.z - c1.z)
    n = plane.normal
    if n and n.length > 0:
        n_vec = adsk.core.Vector3D.create(n.x, n.y, n.z)
        n_vec.normalize()
        proj = v.dotProduct(n_vec)
        v = adsk.core.Vector3D.create(
            v.x - n_vec.x * proj,
            v.y - n_vec.y * proj,
            v.z - n_vec.z * proj,
        )
    if v.length == 0:
        if DEBUG_ROTATE:
            logger.log("EA rotate: hole axis vector length is 0.")
        return None, None
    v.normalize()

    # Closest points on the two circles (on the chosen face plane).
    p1 = adsk.core.Point3D.create(
        c1.x + v.x * r1, c1.y + v.y * r1, c1.z + v.z * r1
    )
    p2 = adsk.core.Point3D.create(
        c2.x - v.x * r2, c2.y - v.y * r2, c2.z - v.z * r2
    )

    mid = adsk.core.Point3D.create(
        (p1.x + p2.x) * 0.5,
        (p1.y + p2.y) * 0.5,
        (p1.z + p2.z) * 0.5,
    )

    if DEBUG_ROTATE:
        try:
            area = hole_face.areaProperties().area
        except:
            area = None
        dist_msg = f"{best_dist:.4f}" if best_dist is not None else "n/a"
        logger.log(
            "EA rotate: hole face area="
            + (f"{area:.4f}" if area is not None else "n/a")
            + f", dist={dist_msg}, circles={len(circles)}, axis={_fmt_vec(v)}, pivot={_fmt_pt(mid)}"
        )
    return v, mid


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
    angle_name = dd.selectedItem.name if dd and dd.selectedItem else "90"
    angle_sign = -1.0 if angle_name.startswith("-") else 1.0
    angle_rad = angle_sign * math.radians(90.0)

    if not sel or sel.selectionCount == 0:
        ctx.ui().messageBox("Select at least one steel member occurrence.")
        return

    logger.log_command(
        CMD_NAME,
        {
            "members": sel.selectionCount,
            "angle_deg": angle_sign * 90.0,
        },
    )

    if DEBUG_ROTATE:
        logger.log(f"Rotate: angle_deg={angle_sign * 90.0:.1f}, members={sel.selectionCount}")

    for i in range(sel.selectionCount):
        occ = adsk.fusion.Occurrence.cast(sel.selection(i).entity)
        if not occ:
            continue

        # ---------- Spin about length axis, pivoting through EA hole line if present ----------
        axis, center = _get_length_axis_and_center(occ)
        if not axis or not center:
            continue

        use_axis = axis
        use_pivot = center

        comp_name = occ.component.name if occ.component else ""
        if comp_name.startswith("EA"):
            ea_axis, ea_pivot = _get_ea_hole_axis(occ)
            if ea_axis and ea_pivot:
                use_axis = ea_axis
                use_pivot = ea_pivot
        else:
            hole_axis, pivot = _get_hole_axis(occ, axis)
            if hole_axis and pivot:
                use_axis = hole_axis
                use_pivot = pivot
        if DEBUG_ROTATE:
            logger.log(
                f"Rotate: {comp_name} axis={_fmt_vec(use_axis)} pivot={_fmt_pt(use_pivot)}"
            )

        rot = adsk.core.Matrix3D.create()
        rot.setToRotation(angle_rad, use_axis, use_pivot)
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
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    handler = RotateCreatedHandler()
    cmd_def.commandCreated.add(handler)
    ctx.add_handler(handler)

    if not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = True
