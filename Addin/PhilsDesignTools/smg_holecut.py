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
TOL = 1e-6
DEBUG_HOLECUT = True


def _matrix_identity() -> adsk.core.Matrix3D:
    return adsk.core.Matrix3D.create()


def _invert_matrix(m: adsk.core.Matrix3D) -> adsk.core.Matrix3D:
    inv = m.copy()
    inv.invert()
    return inv


def _fmt_point(p: adsk.core.Point3D) -> str:
    try:
        return f"({p.x:.4f}, {p.y:.4f}, {p.z:.4f})"
    except:
        return "<point>"


def _fmt_vec(v: adsk.core.Vector3D) -> str:
    try:
        return f"({v.x:.4f}, {v.y:.4f}, {v.z:.4f})|len={v.length:.4f}"
    except:
        return "<vec>"


def _fmt_matrix(m: adsk.core.Matrix3D) -> str:
    try:
        o = adsk.core.Point3D.create(0, 0, 0)
        x = adsk.core.Vector3D.create(1, 0, 0)
        y = adsk.core.Vector3D.create(0, 1, 0)
        z = adsk.core.Vector3D.create(0, 0, 1)
        if m.getAsCoordinateSystem(o, x, y, z):
            return f"o={_fmt_point(o)} x={_fmt_vec(x)} y={_fmt_vec(y)} z={_fmt_vec(z)}"
    except:
        pass
    try:
        arr = m.asArray()
        return f"asArray={arr}"
    except:
        pass
    return "<matrix>"


def _dbg(msg: str, details=None):
    if not DEBUG_HOLECUT:
        return
    try:
        if details is None:
            logger.log(f"HOLECUT: {msg}")
        else:
            logger.log(f"HOLECUT: {msg} | {details}")
    except:
        pass


def _plane_from_point_normal(planes, origin, normal, scale, creation_occ=None):
    n = normal.copy()
    if n.length <= TOL:
        _dbg("plane_from_point_normal: normal length too small", {"normal": _fmt_vec(n)})
        return None
    n.normalize()
    _dbg(
        "plane_from_point_normal: start",
        {
            "origin": _fmt_point(origin),
            "normal": _fmt_vec(n),
            "scale": scale,
            "creation_occ": getattr(creation_occ, "name", None),
        },
    )

    tmp = adsk.core.Vector3D.create(1, 0, 0)
    if abs(n.dotProduct(tmp)) > 0.99:
        tmp = adsk.core.Vector3D.create(0, 1, 0)
    u = n.crossProduct(tmp)
    if u.length <= TOL:
        tmp = adsk.core.Vector3D.create(0, 0, 1)
        u = n.crossProduct(tmp)
    if u.length <= TOL:
        _dbg("plane_from_point_normal: failed to build U direction", {"normal": _fmt_vec(n)})
        return None
    u.normalize()
    v = n.crossProduct(u)
    if v.length <= TOL:
        _dbg("plane_from_point_normal: failed to build V direction", {"u": _fmt_vec(u)})
        return None
    v.normalize()

    s = max(scale, 1.0)
    p1 = origin.copy()
    p2 = origin.copy()
    u.scaleBy(s)
    v.scaleBy(s)
    p1.translateBy(u)
    p2.translateBy(v)

    # setByPlane is not supported in parametric designs; use 3-point definition.
    pl_in = planes.createInput(creation_occ) if creation_occ else planes.createInput()
    if not pl_in.setByThreePoints(origin, p1, p2):
        _dbg(
            "plane_from_point_normal: setByThreePoints returned False",
            {"origin": _fmt_point(origin), "p1": _fmt_point(p1), "p2": _fmt_point(p2)},
        )
        return None
    try:
        plane = planes.add(pl_in)
        _dbg("plane_from_point_normal: setByThreePoints succeeded")
        return plane
    except Exception as ex:
        _dbg(
            "plane_from_point_normal: setByThreePoints add failed",
            {"err": str(ex), "trace": traceback.format_exc()},
        )
        return None


def _project_point_to_plane(origin, normal, point):
    n = normal.copy()
    if n.length <= TOL:
        return point.copy(), 0.0
    n.normalize()

    v = adsk.core.Vector3D.create(point.x - origin.x, point.y - origin.y, point.z - origin.z)
    dist = n.dotProduct(v)
    proj = adsk.core.Point3D.create(point.x - n.x * dist, point.y - n.y * dist, point.z - n.z * dist)
    return proj, dist


def _find_planar_face_for_axis(body, point, axis):
    axis_n = axis.copy()
    if axis_n.length <= TOL:
        return None, None
    axis_n.normalize()

    best_on = None
    best_on_proj = None
    best_on_dist = None

    best_any = None
    best_any_proj = None
    best_any_dist = None

    tol = 0.02  # internal units (cm) ~ 0.2 mm

    for face in body.faces:
        surf = face.geometry
        if surf.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
            continue

        plane = adsk.core.Plane.cast(surf)
        if not plane:
            continue

        n = plane.normal.copy()
        if n.length <= TOL:
            continue
        n.normalize()

        dot = abs(n.dotProduct(axis_n))
        if dot < 0.98:
            continue

        proj, dist = _project_point_to_plane(plane.origin, n, point)
        on_face = False
        try:
            on_face = face.isPointOnFace(proj, tol)
        except:
            on_face = False

        _dbg(
            "planar face candidate",
            {
                "face": getattr(face, "tempId", None),
                "dot": dot,
                "dist": dist,
                "on_face": on_face,
                "proj": _fmt_point(proj),
            },
        )

        adist = abs(dist)
        if on_face:
            if best_on_dist is None or adist < best_on_dist:
                best_on = face
                best_on_proj = proj
                best_on_dist = adist
        else:
            if best_any_dist is None or adist < best_any_dist:
                best_any = face
                best_any_proj = proj
                best_any_dist = adist

    if best_on:
        _dbg("planar face pick: on-face", {"dist": best_on_dist})
        return best_on, best_on_proj
    if best_any:
        _dbg("planar face pick: off-face", {"dist": best_any_dist})
        return best_any, best_any_proj
    return None, None


def _find_axis_hit_face(comp, body, origin, axis):
    axis_n = axis.copy()
    if axis_n.length <= TOL:
        return None, None
    axis_n.normalize()

    try:
        body_key = body.tempId
    except:
        body_key = id(body)

    def _scan(dir_vec):
        hits = adsk.core.ObjectCollection.create()
        ents = comp.findBRepUsingRay(
            origin,
            dir_vec,
            adsk.fusion.BRepEntityTypes.BRepFaceEntityType,
            0.02,
            True,
            hits,
        )
        if not ents:
            return None, None
        for i in range(ents.count):
            face = adsk.fusion.BRepFace.cast(ents.item(i))
            hit = adsk.core.Point3D.cast(hits.item(i)) if i < hits.count else None
            if not face or not hit:
                continue
            try:
                face_body_key = face.body.tempId
            except:
                face_body_key = id(face.body)
            if face_body_key != body_key:
                continue
            surf = face.geometry
            if surf.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
                continue
            plane = adsk.core.Plane.cast(surf)
            if not plane:
                continue
            n = plane.normal.copy()
            if n.length <= TOL:
                continue
            n.normalize()
            dot = abs(n.dotProduct(axis_n))
            _dbg(
                "ray face candidate",
                {"face": getattr(face, "tempId", None), "dot": dot, "hit": _fmt_point(hit)},
            )
            if dot < 0.98:
                continue
            return face, hit
        return None, None

    face_fwd, hit_fwd = _scan(axis_n)
    if face_fwd:
        _dbg("ray face pick: forward", {"hit": _fmt_point(hit_fwd)})
        return face_fwd, hit_fwd

    axis_back = axis_n.copy()
    axis_back.scaleBy(-1.0)
    face_back, hit_back = _scan(axis_back)
    if face_back:
        _dbg("ray face pick: backward", {"hit": _fmt_point(hit_back)})
        return face_back, hit_back

    return None, None


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
            sel_hole.setSelectionLimits(1, 0)

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
    design = adsk.fusion.Design.cast(app.activeProduct)
    _dbg(
        "execute: start",
        {
            "designType": getattr(design, "designType", None),
            "activeComponent": getattr(getattr(design, "activeComponent", None), "name", None),
        },
    )

    cmd = args.command
    inputs = cmd.commandInputs

    sel_hole = adsk.core.SelectionCommandInput.cast(inputs.itemById(HOLE_FACE_INPUT_ID))
    sel_body = adsk.core.SelectionCommandInput.cast(inputs.itemById(TARGET_BODY_INPUT_ID))

    if not sel_hole or sel_hole.selectionCount < 1:
        ui.messageBox("Please select one or more cylindrical hole faces.")
        return

    if not sel_body or sel_body.selectionCount != 1:
        ui.messageBox("Please select exactly one target body.")
        return

    target_body_ctx = adsk.fusion.BRepBody.cast(sel_body.selection(0).entity)

    if not target_body_ctx:
        ui.messageBox("Invalid selection. Please select a cylindrical hole face and a body.")
        return

    hole_faces_ctx = []
    for i in range(sel_hole.selectionCount):
        try:
            ent = sel_hole.selection(i).entity
        except:
            continue
        face = adsk.fusion.BRepFace.cast(ent)
        if face:
            hole_faces_ctx.append(face)

    if not hole_faces_ctx:
        ui.messageBox("No valid cylindrical hole faces were found in the selection.")
        return

    target_body_native = target_body_ctx.nativeObject or target_body_ctx
    target_comp = target_body_native.parentComponent
    target_occ = target_body_ctx.assemblyContext
    first_hole_body_ctx = hole_faces_ctx[0].body if hole_faces_ctx else None
    first_hole_body_native = (first_hole_body_ctx.nativeObject or first_hole_body_ctx) if first_hole_body_ctx else None
    first_hole_occ = first_hole_body_ctx.assemblyContext if first_hole_body_ctx else None
    _dbg(
        "execute: selections",
        {
            "hole_count": len(hole_faces_ctx),
            "hole_body_first": getattr(first_hole_body_native, "name", None),
            "hole_occ_first": getattr(first_hole_occ, "name", None),
            "target_body": getattr(target_body_native, "name", None),
            "target_comp": getattr(target_comp, "name", None),
            "target_occ": getattr(target_occ, "name", None),
            "target_occ_ref": getattr(target_occ, "isReferencedComponent", None) if target_occ else None,
        },
    )
    if target_occ and getattr(target_occ, "isReferencedComponent", False):
        ui.messageBox(
            "Target body is in a linked (referenced) component occurrence.\n\n"
            "Please break the link/make it local, then run the cut."
        )
        _dbg("execute: target occurrence is referenced; aborting")
        return

    world_to_target = _invert_matrix(target_occ.transform2) if target_occ else _matrix_identity()
    if target_occ:
        _dbg("execute: target_occ.transform2", _fmt_matrix(target_occ.transform2))
        _dbg("execute: world_to_target", _fmt_matrix(world_to_target))

    bb = target_body_native.boundingBox
    diag = bb.minPoint.distanceTo(bb.maxPoint)
    height = max(diag * 2.0, 20.0)
    _dbg(
        "execute: target bounds",
        {
            "bb_min": _fmt_point(bb.minPoint),
            "bb_max": _fmt_point(bb.maxPoint),
            "diag": diag,
            "height": height,
        },
    )

    sketches = target_comp.sketches

    prev_occ = design.activeOccurrence if design else None
    if target_occ and not target_occ.isActive:
        ok = target_occ.activate()
        _dbg("execute: target occurrence activate", {"ok": ok, "occ": target_occ.name})

    cut_count = 0
    skip_count = 0
    last_radius = None

    try:
        for hole_face_ctx in hole_faces_ctx:
            hole_body_ctx = hole_face_ctx.body
            hole_occ = hole_body_ctx.assemblyContext
            hole_face_native = hole_face_ctx.nativeObject or hole_face_ctx
            hole_to_world = hole_occ.transform2 if hole_occ else _matrix_identity()
            if hole_occ:
                _dbg("execute: hole_to_world", _fmt_matrix(hole_to_world))

            surface_native = hole_face_native.geometry
            if surface_native.surfaceType != adsk.core.SurfaceTypes.CylinderSurfaceType:
                _dbg("execute: selected face not cylindrical", {"surfaceType": surface_native.surfaceType})
                skip_count += 1
                continue

            cylinder_native = adsk.core.Cylinder.cast(surface_native)
            if not cylinder_native:
                _dbg("execute: Cylinder.cast failed")
                skip_count += 1
                continue

            axis_native = cylinder_native.axis.copy()
            radius = cylinder_native.radius
            last_radius = radius
            _dbg("execute: cylinder native", {"axis": _fmt_vec(axis_native), "radius": radius})

            circ_edge_native = None
            for i in range(hole_face_native.edges.count):
                e = hole_face_native.edges.item(i)
                if adsk.core.Circle3D.cast(e.geometry):
                    circ_edge_native = e
                    break

            if not circ_edge_native:
                _dbg("execute: no circular edge found on cylindrical face")
                skip_count += 1
                continue

            circle_native = adsk.core.Circle3D.cast(circ_edge_native.geometry)
            center_native = circle_native.center
            _dbg("execute: circle native", {"center": _fmt_point(center_native)})

            if axis_native.length == 0:
                _dbg("execute: cylinder axis has zero length")
                skip_count += 1
                continue

            axis_native.normalize()

            center_world = center_native.copy()
            center_world.transformBy(hole_to_world)

            axis_world = axis_native.copy()
            axis_world.transformBy(hole_to_world)
            axis_world.normalize()
            _dbg(
                "execute: world geometry",
                {"center_world": _fmt_point(center_world), "axis_world": _fmt_vec(axis_world)},
            )

            center_target = center_world.copy()
            center_target.transformBy(world_to_target)

            axis_target = axis_world.copy()
            axis_target.transformBy(world_to_target)
            axis_target.normalize()
            _dbg(
                "execute: target geometry",
                {"center_target": _fmt_point(center_target), "axis_target": _fmt_vec(axis_target)},
            )

            face, center_on_face = _find_axis_hit_face(target_comp, target_body_native, center_target, axis_target)
            if not face or not center_on_face:
                _dbg("execute: ray face search failed; falling back to planar scan")
                face, center_on_face = _find_planar_face_for_axis(target_body_native, center_target, axis_target)
            if not face or not center_on_face:
                _dbg(
                    "execute: planar face search failed",
                    {"center_target": _fmt_point(center_target), "axis_target": _fmt_vec(axis_target)},
                )
                skip_count += 1
                continue

            if hasattr(sketches, "addWithoutEdges"):
                sk = sketches.addWithoutEdges(face)
                _dbg("execute: sketch created on face (no edges)", {"face": getattr(face, "tempId", None)})
            else:
                sk = sketches.add(face)
                _dbg("execute: sketch created on face", {"face": getattr(face, "tempId", None)})
            sk_center = sk.modelToSketchSpace(center_on_face)
            sk.sketchCurves.sketchCircles.addByCenterRadius(sk_center, radius)
            _dbg(
                "execute: circle added to sketch",
                {
                    "sk_center": _fmt_point(sk_center),
                    "radius": radius,
                    "center_on_face": _fmt_point(center_on_face),
                },
            )

            if sk.profiles.count < 1:
                _dbg("execute: no profiles found on sketch")
                skip_count += 1
                continue

            prof = None
            best_score = None
            for i in range(sk.profiles.count):
                p = sk.profiles.item(i)
                try:
                    props = p.areaProperties(adsk.fusion.CalculationAccuracy.LowCalculationAccuracy)
                    area = props.area
                    cen = props.centroid
                    d = cen.distanceTo(sk_center)
                    score = d + area * 0.01
                    _dbg("execute: profile candidate", {"i": i, "area": area, "d": d})
                except:
                    score = float(i)
                if best_score is None or score < best_score:
                    best_score = score
                    prof = p

            if not prof:
                _dbg("execute: profile selection failed")
                skip_count += 1
                continue

            hole_height = max(height, radius * 8.0, 20.0)
            extrudes = target_comp.features.extrudeFeatures
            cut_in = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
            cut_in.participantBodies = [target_body_native]
            cut_in.setSymmetricExtent(adsk.core.ValueInput.createByReal(hole_height), True)
            _dbg(
                "execute: extrude cut input ready",
                {"participant": getattr(target_body_native, "name", None), "hole_height": hole_height},
            )
            extrudes.add(cut_in)
            _dbg("execute: extrude cut added")
            cut_count += 1
    finally:
        try:
            if design:
                ok_root = design.activateRootComponent()
                _dbg("execute: activate root component", {"ok": ok_root})
            elif prev_occ and prev_occ.isValid and not prev_occ.isActive:
                prev_occ.activate()
                _dbg("execute: restored previous active occurrence", {"occ": prev_occ.name})
        except:
            pass

    logger.log_command(
        CMD_NAME,
        {
            "hole_faces": len(hole_faces_ctx),
            "target_body": target_body_native.name if target_body_native else "",
            "radius": last_radius,
            "height": height,
            "cuts": cut_count,
            "skipped": skip_count,
        },
    )

    if skip_count > 0:
        ui.messageBox(f"Cut {cut_count} holes. Skipped {skip_count}. See log for details.")

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
