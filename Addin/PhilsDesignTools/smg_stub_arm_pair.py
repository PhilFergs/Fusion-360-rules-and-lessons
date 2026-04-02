import adsk.core
import adsk.fusion
import traceback
import os
import math
import json

import smg_context as ctx
import smg_logger as logger
import smg_stub_arms as base


CMD_ID = "PhilsDesignTools_StubArmPair"
CMD_NAME = "Stub Arm Pair To Wall"
CMD_TOOLTIP = (
    "Create one stub arm pair at a time with top-angle control and optional reference anchors."
)
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

COL_INPUT_ID = "stub_pair_col"
WALL_INPUT_ID = "stub_pair_wall"
TOP_REF_INPUT_ID = "stub_pair_top_ref"
PAIR_SPACING_ID = "stub_pair_spacing"
TOP_OFFSET_ID = "stub_pair_top"
CLEARANCE_ID = "stub_pair_clearance"
WALL_INSET_ID = "stub_pair_wall_inset"
TOP_ANGLE_ID = "stub_pair_top_angle"

PAIR_SETTINGS_ATTR_NAME = "StubArmPairSettings"
DEFAULT_TOP_ANGLE_DEG = 15.0


def _dbg(msg):
    try:
        if base.DEBUG_STUB_ARMS:
            logger.log(f"{CMD_NAME} DEBUG: {msg}")
    except:
        pass


def _default_settings():
    return {
        "pair_spacing_mm": float(base.STUB_BOTTOM_DEFAULT_MM),
        "top_mm": float(base.STUB_TOP_DEFAULT_MM),
        "clearance_mm": float(base.STUB_CLEARANCE_DEFAULT_MM),
        "wall_inset_mm": float(base.STUB_WALL_INSET_DEFAULT_MM),
        "top_angle_deg": float(DEFAULT_TOP_ANGLE_DEG),
    }


def _load_settings(root):
    settings = _default_settings()
    raw = base._get_attr_value(root, base.STUB_MEMBER_ATTR_GROUP, PAIR_SETTINGS_ATTR_NAME)
    if not raw:
        return settings
    try:
        data = json.loads(raw)
    except:
        return settings
    if not isinstance(data, dict):
        return settings
    for key in settings.keys():
        if key in data and data[key] is not None:
            try:
                settings[key] = float(data[key])
            except:
                pass
    return settings


def _save_settings(root, settings):
    try:
        payload = json.dumps(settings)
    except:
        return False
    return base._set_attr(root, base.STUB_MEMBER_ATTR_GROUP, PAIR_SETTINGS_ATTR_NAME, payload)


def _add_reference_filters(sel):
    for filt in ("Vertices", "Edges", "SketchPoints", "SketchLines"):
        try:
            sel.addSelectionFilter(filt)
        except:
            pass
    sel.setSelectionLimits(0, 1)


def _safe_length_value_mm(inputs, cid, um):
    v = adsk.core.ValueCommandInput.cast(inputs.itemById(cid))
    if not v:
        return 0.0
    return um.convert(v.value, um.internalUnits, "mm")


def _safe_angle_value_deg(inputs, cid, um):
    v = adsk.core.ValueCommandInput.cast(inputs.itemById(cid))
    if not v:
        return DEFAULT_TOP_ANGLE_DEG
    try:
        expr = getattr(v, "expression", None)
        if expr:
            return float(um.evaluateExpression(expr, "deg"))
    except:
        pass
    try:
        return float(um.convert(v.value, "rad", "deg"))
    except:
        pass
    try:
        return math.degrees(float(v.value))
    except:
        return DEFAULT_TOP_ANGLE_DEG


def _point_mid(a, b):
    return adsk.core.Point3D.create(
        (a.x + b.x) * 0.5,
        (a.y + b.y) * 0.5,
        (a.z + b.z) * 0.5,
    )


def _entity_world_point(entity):
    if not entity:
        return None

    vtx = adsk.fusion.BRepVertex.cast(entity)
    if vtx:
        try:
            return vtx.geometry
        except:
            return None

    skpt = adsk.fusion.SketchPoint.cast(entity)
    if skpt:
        try:
            wg = skpt.worldGeometry
            if wg:
                return wg
        except:
            pass
        try:
            return skpt.parentSketch.sketchToModelSpace(skpt.geometry)
        except:
            return None

    edge = adsk.fusion.BRepEdge.cast(entity)
    if edge:
        try:
            sp = edge.startVertex.geometry
            ep = edge.endVertex.geometry
            return _point_mid(sp, ep)
        except:
            pass
        try:
            line = adsk.core.Line3D.cast(edge.geometry)
            if line:
                return _point_mid(line.startPoint, line.endPoint)
        except:
            pass
        return None

    skline = adsk.fusion.SketchLine.cast(entity)
    if skline:
        try:
            sp = skline.startSketchPoint.geometry
            ep = skline.endSketchPoint.geometry
            sm = skline.parentSketch.sketchToModelSpace
            return _point_mid(sm(sp), sm(ep))
        except:
            return None

    cpoint = adsk.fusion.ConstructionPoint.cast(entity)
    if cpoint:
        try:
            return cpoint.geometry
        except:
            return None

    return None


def _selected_reference_point(sel_input):
    if not sel_input or sel_input.selectionCount < 1:
        return None
    ent = sel_input.selection(0).entity
    return _entity_world_point(ent)


def _project_point_to_axis(point, axis_origin, axis_dir):
    if not point or not axis_origin or not axis_dir:
        return None, None
    vec = adsk.core.Vector3D.create(
        point.x - axis_origin.x,
        point.y - axis_origin.y,
        point.z - axis_origin.z,
    )
    t = vec.dotProduct(axis_dir)
    proj = base._offset_point(axis_origin, axis_dir, t)
    return proj, t


def _horizontalize(vec):
    if not vec:
        return None
    out = adsk.core.Vector3D.create(vec.x, vec.y, 0.0)
    if out.length <= base.TOL:
        return None
    out.normalize()
    return out


def _build_angled_direction(horizontal_dir, angle_deg):
    h = _horizontalize(horizontal_dir)
    if not h:
        return None
    rad = math.radians(angle_deg)
    d = adsk.core.Vector3D.create(
        h.x * math.cos(rad),
        h.y * math.cos(rad),
        math.sin(rad),
    )
    if d.length <= base.TOL:
        return None
    d.normalize()
    return d


def _resolve_column_face_and_body(col_input, root, wall_faces, wall_sketches):
    if not col_input or col_input.selectionCount == 0:
        return None, None, "Select one column face or one column body."

    ent = col_input.selection(0).entity
    face = adsk.fusion.BRepFace.cast(ent)
    body = adsk.fusion.BRepBody.cast(ent)
    occ = adsk.fusion.Occurrence.cast(ent)
    comp = adsk.fusion.Component.cast(ent)

    if face:
        face = base._proxy_face(face, root)
        if not face:
            return None, None, "Could not resolve selected face in assembly context."
        return face, face.body, None

    if body:
        body = base._proxy_body(body, root)
        if not body:
            return None, None, "Could not resolve selected body in assembly context."
        side_face = base._choose_column_face(body, root, wall_faces, wall_sketches)
        if not side_face:
            return None, None, "Could not find a suitable side face on selected body."
        return side_face, body, None

    if occ or comp:
        if comp is None and occ:
            comp = occ.component
        if not comp:
            return None, None, "Selected component/occurrence has no component data."
        try:
            bodies = comp.bRepBodies
        except:
            bodies = None
        if not bodies or bodies.count == 0:
            return None, None, "Selected component/occurrence has no solid bodies."
        if bodies.count != 1:
            return None, None, "Select a single column body or face (component contains multiple bodies)."
        body_native = bodies.item(0)
        body_asm = base._proxy_body(body_native, root)
        if not body_asm:
            return None, None, "Could not resolve selected component body in assembly context."
        side_face = base._choose_column_face(body_asm, root, wall_faces, wall_sketches)
        if not side_face:
            return None, None, "Could not find a suitable side face on selected component body."
        return side_face, body_asm, None

    return None, None, "Unsupported column selection. Use a face, body, or single-body component."


def _find_angled_wall_hit(origin, ground_dir, angle_deg, wall_faces, wall_sketches):
    best_hit = None
    best_entry = None
    best_dist = None
    best_dir = None
    for sign in (1.0, -1.0):
        gd = adsk.core.Vector3D.create(ground_dir.x, ground_dir.y, ground_dir.z)
        gd.scaleBy(sign)
        ray_dir = _build_angled_direction(gd, angle_deg)
        if not ray_dir:
            continue
        hit, entry = base._intersect_ray_with_faces_onface(origin, ray_dir, wall_faces, wall_sketches)
        if not hit:
            continue
        dist = origin.distanceTo(hit)
        if best_dist is None or dist < best_dist:
            best_hit = hit
            best_entry = entry
            best_dist = dist
            best_dir = ray_dir
    return best_hit, best_entry, best_dir


class StubArmPairCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            design = adsk.fusion.Design.cast(ctx.app().activeProduct)
            if not design:
                ctx.ui().messageBox("No active design.")
                return
            root = design.rootComponent
            um = design.unitsManager
            length_units = um.defaultLengthUnits or "mm"
            settings = _load_settings(root)

            cmd = args.command
            cmd.isRepeatable = True
            inputs = cmd.commandInputs

            if inputs.itemById(COL_INPUT_ID):
                return

            col_sel = inputs.addSelectionInput(
                COL_INPUT_ID,
                "Column",
                "Select one RHS/SHS face, body, or single-body component",
            )
            for filt in ("Faces", "Bodies", "Occurrences", "Components"):
                try:
                    col_sel.addSelectionFilter(filt)
                except:
                    pass
            col_sel.setSelectionLimits(1, 1)

            wall_sel = inputs.addSelectionInput(
                WALL_INPUT_ID,
                "Wall faces",
                "Select wall faces or wall bodies",
            )
            for filt in ("Faces", "Bodies", "Occurrences", "Components"):
                try:
                    wall_sel.addSelectionFilter(filt)
                except:
                    pass
            wall_sel.setSelectionLimits(1, 0)

            top_ref_sel = inputs.addSelectionInput(
                TOP_REF_INPUT_ID,
                "Top reference (optional)",
                "Pick point/vertex/edge/line used as anchor for top offset",
            )
            _add_reference_filters(top_ref_sel)

            def v_mm(mm):
                return adsk.core.ValueInput.createByString(f"{mm} mm")

            inputs.addValueInput(
                PAIR_SPACING_ID,
                "Bottom line distance from top",
                length_units,
                v_mm(settings.get("pair_spacing_mm", base.STUB_BOTTOM_DEFAULT_MM)),
            )
            inputs.addValueInput(
                TOP_OFFSET_ID,
                "Top offset",
                length_units,
                v_mm(settings.get("top_mm", base.STUB_TOP_DEFAULT_MM)),
            )
            inputs.addValueInput(
                CLEARANCE_ID,
                "Wall clearance",
                length_units,
                v_mm(settings.get("clearance_mm", base.STUB_CLEARANCE_DEFAULT_MM)),
            )
            inputs.addValueInput(
                WALL_INSET_ID,
                "Wall inset",
                length_units,
                v_mm(settings.get("wall_inset_mm", base.STUB_WALL_INSET_DEFAULT_MM)),
            )
            inputs.addValueInput(
                TOP_ANGLE_ID,
                "Top line angle to ground",
                "deg",
                adsk.core.ValueInput.createByString(
                    f"{settings.get('top_angle_deg', DEFAULT_TOP_ANGLE_DEG)} deg"
                ),
            )

            on_exec = StubArmPairExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)
        except:
            logger.log(f"{CMD_NAME} CommandCreated failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} CommandCreated failed:\n" + traceback.format_exc())


class StubArmPairExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log(f"{CMD_NAME} failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} failed:\n" + traceback.format_exc())


def _execute(args):
    design = adsk.fusion.Design.cast(ctx.app().activeProduct)
    if not design:
        ctx.ui().messageBox("No active design.")
        return
    root = design.rootComponent
    um = design.unitsManager

    cmd = args.command
    inputs = cmd.commandInputs
    col_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(COL_INPUT_ID))
    wall_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(WALL_INPUT_ID))
    top_ref_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(TOP_REF_INPUT_ID))

    if not col_input or col_input.selectionCount < 1:
        ctx.ui().messageBox("Select one column face/body/component.")
        return
    if not wall_input or wall_input.selectionCount < 1:
        ctx.ui().messageBox("Select at least one wall face/body.")
        return

    pair_spacing_mm = _safe_length_value_mm(inputs, PAIR_SPACING_ID, um)
    top_mm = _safe_length_value_mm(inputs, TOP_OFFSET_ID, um)
    clearance_mm = _safe_length_value_mm(inputs, CLEARANCE_ID, um)
    wall_inset_mm = max(0.0, _safe_length_value_mm(inputs, WALL_INSET_ID, um))
    top_angle_deg = _safe_angle_value_deg(inputs, TOP_ANGLE_ID, um)
    if pair_spacing_mm <= 0:
        ctx.ui().messageBox("Bottom line distance from top must be greater than 0 mm.")
        return
    if top_angle_deg < -80.0 or top_angle_deg > 80.0:
        ctx.ui().messageBox("Top angle must be between -80 and +80 degrees.")
        return

    pair_spacing_u = um.convert(pair_spacing_mm, "mm", um.internalUnits)
    top_u = um.convert(top_mm, "mm", um.internalUnits)
    clearance_u = um.convert(clearance_mm, "mm", um.internalUnits)
    wall_inset_u = um.convert(wall_inset_mm, "mm", um.internalUnits)

    wall_faces = base._collect_wall_faces(wall_input, root)
    if not wall_faces:
        ctx.ui().messageBox("No valid wall faces found in the selection.")
        return

    wall_sketches = {} if (base.USE_SKETCH_FALLBACK or base.DEBUG_WALL_MARKERS) else None
    col_face, body, err = _resolve_column_face_and_body(col_input, root, wall_faces, wall_sketches)
    if err:
        ctx.ui().messageBox(err)
        return

    axis = base._get_body_axis(body)
    axis_dir, bottom, top, length = base._axis_endpoints(body, axis) if axis else (None, None, None, None)
    if not axis_dir or not bottom or not top or not length:
        ctx.ui().messageBox("Could not determine column axis/length from selection.")
        return
    if not base._looks_like_rhs_shs(body, axis_dir):
        ctx.ui().messageBox("Selected column does not look like RHS/SHS.")
        return

    plane = base._get_face_plane(col_face)
    if not plane:
        ctx.ui().messageBox("Selected/derived column face is not planar.")
        return

    comp_axes = base._component_axes(body, root)
    line_dir = base._line_dir_for_face(plane.normal, axis_dir, comp_axes)
    if not line_dir:
        ctx.ui().messageBox("Failed to determine wall direction from selected face.")
        return

    ground_dir = _horizontalize(line_dir)
    if not ground_dir:
        if wall_faces:
            wf = wall_faces[0]["asm"]
            wplane = base._get_face_plane(wf)
            if wplane and wplane.normal:
                ground_dir = _horizontalize(adsk.core.Vector3D.create(-wplane.normal.x, -wplane.normal.y, 0.0))
    if not ground_dir:
        ctx.ui().messageBox("Could not determine ground-reference direction for angled top line.")
        return

    top_ref_p = _selected_reference_point(top_ref_input)
    top_anchor = top
    if top_ref_p:
        proj, _ = _project_point_to_axis(top_ref_p, bottom, axis_dir)
        if proj:
            top_anchor = proj

    upper_start = base._offset_point(top_anchor, axis_dir, -top_u)
    lower_start = base._offset_point(upper_start, axis_dir, -pair_spacing_u)
    if lower_start.distanceTo(upper_start) <= base.TOL * 10.0:
        ctx.ui().messageBox("Top/bottom start points collapsed. Adjust top offset or pair spacing.")
        return

    lower = base._project_point_to_plane(lower_start, plane.origin, plane.normal)
    upper = base._project_point_to_plane(upper_start, plane.origin, plane.normal)
    if not lower or not upper:
        ctx.ui().messageBox("Failed to project start points onto the column face.")
        return

    hit, hit_entry, used_ray_dir = _find_angled_wall_hit(
        upper,
        ground_dir,
        top_angle_deg,
        wall_faces,
        wall_sketches,
    )
    if not hit or not hit_entry:
        ctx.ui().messageBox(
            "No wall hit found for the top line at the requested angle.\n"
            "Try changing the angle or selecting different wall faces."
        )
        return

    hit_before_inset = hit
    hit = base._offset_hit_from_wall(hit, upper, hit_entry, wall_inset_u)
    if base.DEBUG_STUB_ARMS and hit_before_inset and hit:
        inset_applied_mm = um.convert(hit_before_inset.distanceTo(hit), um.internalUnits, "mm")
        _dbg(f"Inset applied mm={inset_applied_mm:.2f}")

    lower_adj, draw_lower = base._adjust_lower_for_clearance(
        lower,
        upper,
        hit,
        axis_dir,
        wall_faces,
        wall_sketches,
        clearance_u,
    )

    arm_dir = adsk.core.Vector3D.create(hit.x - upper.x, hit.y - upper.y, hit.z - upper.z)
    bracket_type = base._bracket_type_for_faces(hit_entry, arm_dir, used_ray_dir or line_dir)

    stub_comp = base._get_or_create_stub_component(root)
    if not stub_comp:
        ctx.ui().messageBox("Failed to create/find 'stub arm lines' component.")
        return

    sk = base._create_stub_sketch(stub_comp, col_face, root)
    if not sk:
        ctx.ui().messageBox("Failed to create sketch for stub arm pair.")
        return
    try:
        label = base._component_label_for_body(body)
        sk.name = base._next_sketch_name(stub_comp, f"Stub Arm Pair - {label}")
    except:
        pass
    base._disable_sketch_profiles(sk)

    try:
        upper_sk = sk.modelToSketchSpace(upper)
        lower_sk = sk.modelToSketchSpace(lower_adj)
        hit_sk = sk.modelToSketchSpace(hit)
    except:
        upper_sk = upper
        lower_sk = lower_adj
        hit_sk = hit

    lines = sk.sketchCurves.sketchLines
    upper_line = lines.addByTwoPoints(upper_sk, hit_sk)
    base._tag_stub_line(upper_line, "FlatBar")
    base._tag_stub_bracket(upper_line, bracket_type, True)

    lines_created = 1
    if draw_lower:
        lower_line = lines.addByTwoPoints(lower_sk, hit_sk)
        base._tag_stub_line(lower_line, "EA")
        lines_created += 1

    _save_settings(
        root,
        {
            "pair_spacing_mm": pair_spacing_mm,
            "top_mm": top_mm,
            "clearance_mm": clearance_mm,
            "wall_inset_mm": wall_inset_mm,
            "top_angle_deg": top_angle_deg,
        },
    )

    logger.log_command(
        CMD_NAME,
        {
            "lines_created": lines_created,
            "top_angle_deg": top_angle_deg,
            "pair_spacing_mm": pair_spacing_mm,
            "top_ref_used": bool(top_ref_p),
            "bracket_type": bracket_type,
        },
    )

    try:
        ctx.app().activeViewport.refresh()
    except:
        pass

    msg = [
        f"Created {lines_created} line(s).",
        f"Top line angle to ground: {top_angle_deg:.1f} deg",
        f"Bottom line distance from top: {pair_spacing_mm:.1f} mm",
        f"Top reference used: {'Yes' if top_ref_p else 'No'}",
    ]
    if not draw_lower:
        msg.append("Lower line skipped due to wall-clearance check.")
    ctx.ui().messageBox("\n".join(msg), CMD_NAME)


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = StubArmPairCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
