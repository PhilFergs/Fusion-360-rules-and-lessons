import adsk.core
import adsk.fusion
import os
import re
import traceback

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_SetComponentDescriptions"
CMD_NAME = "Set Component Descriptions"
CMD_TOOLTIP = "Set Fusion component descriptions from recognised steel profile names."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

SELECTION_INPUT_ID = "set_component_descriptions_selection"
ALL_DESIGN_INPUT_ID = "set_component_descriptions_all_design"
OVERWRITE_INPUT_ID = "set_component_descriptions_overwrite"

TOL = 1e-6
ANGLE_TOL = 1e-3
PARALLEL_DOT_TOL = 0.98
LEVEL_TOL_MM = 0.5
DIM_TOL_MM = 1.0
FLAT_BAR_MIN_LENGTH_RATIO = 3.0
FLAT_BAR_MAX_WIDTH_MM = 200.0
PURLIN_LIP_MAX_RATIO = 0.85


class SetComponentDescriptionsCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById(ALL_DESIGN_INPUT_ID):
                return

            info = (
                "Writes the Fusion component Description field and simplified material names from recognised steel profiles.\n"
                "Only leaf components are updated: exactly one direct body and no child components.\n"
                "Uses the actual body geometry to infer the profile family and size."
            )
            inputs.addTextBoxCommandInput(
                "set_component_descriptions_info",
                "",
                info,
                3,
                True,
            )

            sel = inputs.addSelectionInput(
                SELECTION_INPUT_ID,
                "Selection",
                "Select occurrences, components, or bodies to update",
            )
            sel.addSelectionFilter("Occurrences")
            sel.addSelectionFilter("Bodies")
            try:
                sel.addSelectionFilter("Components")
            except:
                logger.log(f"{CMD_NAME}: Selection filter 'Components' not supported; ignoring.")
            sel.setSelectionLimits(0, 0)

            inputs.addBoolValueInput(
                ALL_DESIGN_INPUT_ID,
                "Whole design",
                True,
                "",
                True,
            )
            inputs.addBoolValueInput(
                OVERWRITE_INPUT_ID,
                "Overwrite existing descriptions",
                True,
                "",
                True,
            )

            on_exec = SetComponentDescriptionsExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)
        except:
            logger.log(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())


class SetComponentDescriptionsExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log(f"{CMD_NAME} failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} failed:\n" + traceback.format_exc())


def _is_referenced_component(comp):
    if not comp:
        return False
    for attr in ("isReferencedComponent", "isExternalReference"):
        try:
            if bool(getattr(comp, attr)):
                return True
        except:
            pass
    return False


def _safe_token(entity):
    try:
        tok = entity.entityToken
        if tok:
            return tok
    except:
        pass
    return f"id:{id(entity)}"


def _all_components(design):
    out = []
    try:
        comps = design.allComponents
        for i in range(comps.count):
            comp = comps.item(i)
            if comp:
                out.append(comp)
    except:
        pass
    return out


def _components_from_selection(sel_input):
    out = []
    seen = set()
    if not sel_input:
        return out

    for i in range(sel_input.selectionCount):
        ent = sel_input.selection(i).entity
        if not ent:
            continue

        comp = adsk.fusion.Component.cast(ent)
        if not comp:
            occ = adsk.fusion.Occurrence.cast(ent)
            if occ:
                try:
                    comp = occ.component
                except:
                    comp = None
        if not comp:
            body = adsk.fusion.BRepBody.cast(ent)
            if body:
                try:
                    comp = body.parentComponent
                except:
                    comp = None
        if not comp:
            continue

        key = _safe_token(comp)
        if key in seen:
            continue
        seen.add(key)
        out.append(comp)

    return out


def _name_candidates(comp):
    out = []

    try:
        if comp.name:
            out.append(comp.name)
    except:
        pass

    try:
        bodies = comp.bRepBodies
    except:
        bodies = None

    if bodies:
        for i in range(bodies.count):
            try:
                body = bodies.item(i)
                if body and body.name:
                    out.append(body.name)
            except:
                continue

    return out


def _direct_body_count(comp):
    try:
        return comp.bRepBodies.count
    except:
        return 0


def _direct_child_occurrence_count(comp):
    try:
        return comp.occurrences.count
    except:
        return 0


def _is_leaf_target_component(comp):
    return _direct_body_count(comp) == 1 and _direct_child_occurrence_count(comp) == 0


def _single_body(comp):
    try:
        bodies = comp.bRepBodies
        if bodies and bodies.count == 1:
            return bodies.item(0)
    except:
        pass
    return None


def _normalise_text(text):
    txt = (text or "").upper().strip()
    txt = txt.replace("_", " ")
    txt = txt.replace("\u00D7", "X")
    txt = txt.replace("×", "X")
    txt = re.sub(r"\s+", " ", txt)
    return txt


def _clean_numeric(num_text):
    try:
        num = float(num_text)
    except:
        return num_text
    if abs(num - round(num)) < 1e-6:
        return str(int(round(num)))
    return f"{num:.1f}".rstrip("0").rstrip(".")


def _fmt_dims(*parts):
    return " x ".join(_clean_numeric(part) for part in parts if part is not None)


def _find_size_triplet(text):
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*[Xx]\s*(\d+(?:\.\d+)?)\s*[Xx]\s*(\d+(?:\.\d+)?)",
        text,
    )
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3)


def _find_size_pair(text):
    m = re.search(r"(\d+(?:\.\d+)?)\s*[Xx]\s*(\d+(?:\.\d+)?)", text)
    if not m:
        return None
    return m.group(1), m.group(2)


def _contains_family(text, token):
    return bool(
        re.search(
            rf"(?<![A-Z0-9]){re.escape(token)}(?=\d*(?:[^A-Z0-9]|$))",
            text,
        )
    )


def _vector_copy(v):
    return adsk.core.Vector3D.create(v.x, v.y, v.z)


def _point_as_vector(p):
    return adsk.core.Vector3D.create(p.x, p.y, p.z)


def _normalise_vec(v):
    out = _vector_copy(v)
    if out.length > TOL:
        out.normalize()
    return out


def _canon_dir(v):
    v2 = _normalise_vec(v)
    if v2.x < 0 or (abs(v2.x) < TOL and v2.y < 0) or \
       (abs(v2.x) < TOL and abs(v2.y) < TOL and v2.z < 0):
        v2.scaleBy(-1)
    return v2


def _is_parallel(v1, v2):
    try:
        a = _normalise_vec(v1)
        b = _normalise_vec(v2)
        return abs(a.dotProduct(b)) >= PARALLEL_DOT_TOL
    except:
        return False


def _mm_from_internal(um, value):
    try:
        return um.convert(value, um.internalUnits, "mm")
    except:
        return value


def _unique_levels_mm(values, tol_mm=LEVEL_TOL_MM):
    merged = []
    for value in sorted(values):
        if not merged or abs(value - merged[-1]) > tol_mm:
            merged.append(value)
        else:
            merged[-1] = (merged[-1] + value) * 0.5
    return merged


def _body_axis(body):
    clusters = []
    try:
        for edge in body.edges:
            line = adsk.core.Line3D.cast(edge.geometry)
            if not line:
                continue
            sp = line.startPoint
            ep = line.endPoint
            vec = adsk.core.Vector3D.create(
                ep.x - sp.x,
                ep.y - sp.y,
                ep.z - sp.z,
            )
            length = vec.length
            if length < TOL:
                continue
            d = _canon_dir(vec)

            placed = False
            for cluster in clusters:
                if cluster["dir"].crossProduct(d).length < ANGLE_TOL:
                    cluster["tot"] += length
                    placed = True
                    break
            if not placed:
                clusters.append({"dir": d, "tot": length})
    except:
        return None

    if not clusters:
        return None

    clusters.sort(key=lambda item: item["tot"], reverse=True)
    return clusters[0]["dir"]


def _body_length_mm(body, axis_dir, um):
    if not body or not axis_dir:
        return None

    min_proj = None
    max_proj = None
    try:
        for vertex in body.vertices:
            p = vertex.geometry
            proj = _point_as_vector(p).dotProduct(axis_dir)
            if min_proj is None or proj < min_proj:
                min_proj = proj
            if max_proj is None or proj > max_proj:
                max_proj = proj
    except:
        return None

    if min_proj is None or max_proj is None:
        return None
    return _mm_from_internal(um, max_proj - min_proj)


def _project_point_mm(point, axis_dir, um):
    try:
        return _mm_from_internal(um, _point_as_vector(point).dotProduct(axis_dir))
    except:
        return None


def _face_plane(face):
    if not face:
        return None
    try:
        res = face.evaluator.getPlane()
        if isinstance(res, tuple):
            if res[0]:
                return res[1]
        elif res:
            return res
    except:
        pass
    try:
        return adsk.core.Plane.cast(face.geometry)
    except:
        return None


def _line_dir_in_plane(face, plane_normal):
    try:
        for edge in face.edges:
            line = adsk.core.Line3D.cast(edge.geometry)
            if not line:
                continue
            sp = line.startPoint
            ep = line.endPoint
            vec = adsk.core.Vector3D.create(ep.x - sp.x, ep.y - sp.y, ep.z - sp.z)
            if vec.length < TOL:
                continue
            d = _normalise_vec(vec)
            if abs(d.dotProduct(plane_normal)) < 0.2:
                return d
    except:
        pass
    return None


def _loop_points(loop):
    out = []
    try:
        for edge in loop.edges:
            for attr in ("startVertex", "endVertex"):
                try:
                    vertex = getattr(edge, attr)
                except:
                    vertex = None
                if not vertex:
                    continue
                try:
                    point = vertex.geometry
                except:
                    point = None
                if point:
                    out.append(point)
    except:
        pass
    return out


def _levels_from_points_mm(points, axis_dir, um):
    values = []
    for point in points:
        value = _project_point_mm(point, axis_dir, um)
        if value is not None:
            values.append(value)
    return _unique_levels_mm(values)


def _loop_box(loop, u_dir, v_dir, um):
    points = _loop_points(loop)
    if len(points) < 2:
        return None

    u_levels = _levels_from_points_mm(points, u_dir, um)
    v_levels = _levels_from_points_mm(points, v_dir, um)
    if len(u_levels) < 2 or len(v_levels) < 2:
        return None

    width = u_levels[-1] - u_levels[0]
    height = v_levels[-1] - v_levels[0]
    if width <= 0 or height <= 0:
        return None

    edge_count = 0
    curved_edges = 0
    try:
        for edge in loop.edges:
            edge_count += 1
            if not adsk.core.Line3D.cast(edge.geometry):
                curved_edges += 1
    except:
        pass

    return {
        "u_levels": u_levels,
        "v_levels": v_levels,
        "width": width,
        "height": height,
        "area": width * height,
        "edge_count": edge_count,
        "curved_edges": curved_edges,
        "rectangular_like": edge_count == 4 and curved_edges == 0 and len(u_levels) == 2 and len(v_levels) == 2,
    }


def _end_face_profile(body, axis_dir, um):
    best = None
    try:
        for face in body.faces:
            plane = _face_plane(face)
            if not plane:
                continue
            normal = _normalise_vec(plane.normal)
            if abs(normal.dotProduct(axis_dir)) < PARALLEL_DOT_TOL:
                continue

            u_dir = _line_dir_in_plane(face, normal)
            if not u_dir:
                continue
            v_dir = normal.crossProduct(u_dir)
            if v_dir.length < TOL:
                continue
            v_dir.normalize()

            loop_boxes = []
            try:
                for loop in face.loops:
                    box = _loop_box(loop, u_dir, v_dir, um)
                    if box:
                        loop_boxes.append(box)
            except:
                continue

            if not loop_boxes:
                continue

            loop_boxes.sort(key=lambda item: item["area"], reverse=True)
            candidate = {
                "loop_boxes": loop_boxes,
                "outer_area": loop_boxes[0]["area"],
            }
            if not best or candidate["outer_area"] > best["outer_area"]:
                best = candidate
    except:
        return None

    return best


def _profile_face_data(body, axis_dir, um):
    cyl_radii = []
    try:
        for face in body.faces:
            try:
                cyl = adsk.core.Cylinder.cast(face.geometry)
            except:
                cyl = None
            if not cyl:
                continue

            try:
                cyl_axis = _normalise_vec(cyl.axis)
                if abs(cyl_axis.dotProduct(axis_dir)) >= PARALLEL_DOT_TOL:
                    cyl_radii.append(_mm_from_internal(um, cyl.radius))
            except:
                continue
    except:
        pass

    return _unique_levels_mm(cyl_radii, tol_mm=0.1)


def _face_area_value(face):
    try:
        return float(face.area)
    except:
        return 0.0


def _planar_face_clusters(body):
    clusters = []
    try:
        for face in body.faces:
            plane = _face_plane(face)
            if not plane:
                continue
            normal = _canon_dir(plane.normal)
            area = _face_area_value(face)
            placed = False
            for cluster in clusters:
                if cluster["dir"].crossProduct(normal).length < ANGLE_TOL:
                    cluster["faces"].append(face)
                    cluster["area"] += area
                    placed = True
                    break
            if not placed:
                clusters.append({"dir": normal, "faces": [face], "area": area})
    except:
        pass
    clusters.sort(key=lambda item: item["area"], reverse=True)
    return clusters


def _largest_outer_loop_box(face, u_dir, v_dir, um):
    best = None
    try:
        for loop in face.loops:
            box = _loop_box(loop, u_dir, v_dir, um)
            if not box:
                continue
            if not best or box["area"] > best["area"]:
                best = box
    except:
        return None
    return best


def _description_from_planar_stock(body, um):
    clusters = _planar_face_clusters(body)
    if not clusters:
        return None

    cluster = clusters[0]
    normal = cluster["dir"]
    faces = cluster["faces"]
    if len(faces) < 2:
        return None

    levels = []
    for face in faces:
        plane = _face_plane(face)
        if not plane:
            continue
        level = _project_point_mm(plane.origin, normal, um)
        if level is not None:
            levels.append(level)
    levels = _unique_levels_mm(levels)
    if len(levels) < 2:
        return None

    thickness = levels[-1] - levels[0]
    if thickness <= 0:
        return None

    face = max(faces, key=_face_area_value)
    u_dir = _line_dir_in_plane(face, normal)
    if not u_dir:
        return None
    v_dir = normal.crossProduct(u_dir)
    if v_dir.length < TOL:
        return None
    v_dir.normalize()

    outer = _largest_outer_loop_box(face, u_dir, v_dir, um)
    if not outer:
        return None

    width = max(outer["width"], outer["height"])
    height = min(outer["width"], outer["height"])

    if outer["rectangular_like"]:
        return f"FLAT BAR {_fmt_dims(height, thickness)}"

    return f"PLATE {_clean_numeric(thickness)}"


def _profile_basis(side_faces):
    clusters = []
    for face in side_faces:
        d = face["normal"]
        placed = False
        for cluster in clusters:
            if cluster["dir"].crossProduct(d).length < ANGLE_TOL:
                cluster["count"] += 1
                placed = True
                break
        if not placed:
            clusters.append({"dir": d, "count": 1})

    if len(clusters) < 2:
        return None, None

    clusters.sort(key=lambda item: item["count"], reverse=True)
    first = clusters[0]["dir"]
    second = None
    for cluster in clusters[1:]:
        if not _is_parallel(first, cluster["dir"]):
            second = cluster["dir"]
            break

    if not second:
        return None, None
    return first, second


def _axis_levels_mm(side_faces, axis_dir, um):
    levels = []
    for face in side_faces:
        if not _is_parallel(face["normal"], axis_dir):
            continue
        try:
            levels.append(_mm_from_internal(um, _point_as_vector(face["origin"]).dotProduct(axis_dir)))
        except:
            continue
    return _unique_levels_mm(levels)


def _smallest_positive_gap(levels):
    gaps = []
    for i in range(len(levels) - 1):
        gap = levels[i + 1] - levels[i]
        if gap > LEVEL_TOL_MM * 0.25:
            gaps.append(gap)
    if not gaps:
        return None
    return min(gaps)


def _positive_gaps(levels):
    out = []
    for i in range(len(levels) - 1):
        gap = levels[i + 1] - levels[i]
        if gap > LEVEL_TOL_MM * 0.25:
            out.append(gap)
    return sorted(out)


def _description_from_rect_hollow(u_levels, v_levels):
    outer_u = u_levels[-1] - u_levels[0]
    outer_v = v_levels[-1] - v_levels[0]
    candidates = []
    if len(u_levels) >= 4:
        candidates.append((outer_u - (u_levels[-2] - u_levels[1])) * 0.5)
    if len(v_levels) >= 4:
        candidates.append((outer_v - (v_levels[-2] - v_levels[1])) * 0.5)
    candidates = [gap for gap in candidates if gap and gap > 0]
    if not candidates:
        return None

    thickness = min(candidates)
    width = max(outer_u, outer_v)
    depth = min(outer_u, outer_v)
    family = "SHS" if abs(width - depth) <= DIM_TOL_MM else "RHS"
    return f"{family} {_fmt_dims(width, depth, thickness)}"


def _description_from_angle(u_levels, v_levels):
    if min(len(u_levels), len(v_levels)) < 3:
        return None

    outer_u = u_levels[-1] - u_levels[0]
    outer_v = v_levels[-1] - v_levels[0]
    thk_u = _smallest_positive_gap(u_levels)
    thk_v = _smallest_positive_gap(v_levels)
    candidates = [gap for gap in (thk_u, thk_v) if gap]
    if not candidates:
        return None

    thickness = min(candidates)
    if thickness >= min(outer_u, outer_v) - DIM_TOL_MM:
        return None
    width = max(outer_u, outer_v)
    depth = min(outer_u, outer_v)
    return f"EA {_fmt_dims(width, depth, thickness)}"


def _channel_lip_mm(levels, thickness, flange_mm):
    for gap in _positive_gaps(levels):
        if gap <= thickness + DIM_TOL_MM:
            continue
        if gap >= flange_mm * PURLIN_LIP_MAX_RATIO:
            continue
        return gap
    return None


def _description_from_c_purlin(u_levels, v_levels, outer_box):
    if not outer_box:
        return None

    dims = _section_axis_levels(u_levels, v_levels)
    depth_levels = dims["depth_levels"]
    width_levels = dims["width_levels"]
    depth = dims["depth"]
    flange = dims["width"]

    if len(depth_levels) < 4 or len(width_levels) != 3:
        return None

    outer_u = u_levels[-1] - u_levels[0]
    outer_v = v_levels[-1] - v_levels[0]
    thk_u = _smallest_positive_gap(u_levels)
    thk_v = _smallest_positive_gap(v_levels)
    candidates = [gap for gap in (thk_u, thk_v) if gap]
    if not candidates:
        return None

    thickness = min(candidates)
    if thickness >= flange - DIM_TOL_MM:
        return None
    if depth <= flange * 1.15:
        return None

    lip = _channel_lip_mm(depth_levels, thickness, flange)
    if not lip:
        return None
    return f"C PURLIN {_fmt_dims(depth, flange, lip, thickness)}"


def _section_axis_levels(u_levels, v_levels):
    outer_u = u_levels[-1] - u_levels[0]
    outer_v = v_levels[-1] - v_levels[0]
    if outer_u >= outer_v:
        return {
            "depth_levels": u_levels,
            "width_levels": v_levels,
            "depth": outer_u,
            "width": outer_v,
        }
    return {
        "depth_levels": v_levels,
        "width_levels": u_levels,
        "depth": outer_v,
        "width": outer_u,
    }


def _approx_equal(a, b, tol_mm=DIM_TOL_MM):
    return abs(a - b) <= tol_mm


def _description_from_ub(u_levels, v_levels, outer_box):
    if not outer_box:
        return None

    dims = _section_axis_levels(u_levels, v_levels)
    depth_levels = dims["depth_levels"]
    width_levels = dims["width_levels"]
    depth = dims["depth"]
    width = dims["width"]

    if len(depth_levels) < 4 or len(width_levels) < 4:
        return None
    if outer_box["edge_count"] < 10:
        return None

    flange_thickness = _smallest_positive_gap(depth_levels)
    web_thickness = _smallest_positive_gap(width_levels)
    if not flange_thickness or not web_thickness:
        return None
    if flange_thickness >= depth - DIM_TOL_MM or web_thickness >= width - DIM_TOL_MM:
        return None

    lower_flange = depth_levels[1] - depth_levels[0]
    upper_flange = depth_levels[-1] - depth_levels[-2]
    left_outstand = width_levels[1] - width_levels[0]
    right_outstand = width_levels[-1] - width_levels[-2]

    if not _approx_equal(lower_flange, upper_flange):
        return None
    if not _approx_equal(left_outstand, right_outstand):
        return None

    return f"UB {_fmt_dims(depth, width, web_thickness, flange_thickness)}"


def _description_from_pfc(u_levels, v_levels, outer_box):
    if not outer_box:
        return None

    dims = _section_axis_levels(u_levels, v_levels)
    depth_levels = dims["depth_levels"]
    width_levels = dims["width_levels"]
    depth = dims["depth"]
    width = dims["width"]

    if len(depth_levels) != 4 or len(width_levels) != 3:
        return None
    if outer_box["edge_count"] < 8:
        return None

    flange_thickness = _smallest_positive_gap(depth_levels)
    web_thickness = _smallest_positive_gap(width_levels)
    if not flange_thickness or not web_thickness:
        return None
    if flange_thickness >= depth - DIM_TOL_MM or web_thickness >= width - DIM_TOL_MM:
        return None

    lower_flange = depth_levels[1] - depth_levels[0]
    upper_flange = depth_levels[-1] - depth_levels[-2]
    if not _approx_equal(lower_flange, upper_flange):
        return None

    return f"PFC {_fmt_dims(depth, width, web_thickness, flange_thickness)}"


def _description_from_solid_rect(u_levels, v_levels, length_mm):
    outer_u = u_levels[-1] - u_levels[0]
    outer_v = v_levels[-1] - v_levels[0]
    width = max(outer_u, outer_v)
    thickness = min(outer_u, outer_v)
    if thickness <= 0:
        return None
    if width <= FLAT_BAR_MAX_WIDTH_MM and length_mm and length_mm >= width * FLAT_BAR_MIN_LENGTH_RATIO:
        return f"FLAT BAR {_fmt_dims(width, thickness)}"
    return f"PLATE {_clean_numeric(thickness)}"


def _description_from_body_geometry(body, um):
    if not body or not um:
        return None

    axis_dir = _body_axis(body)
    if not axis_dir:
        return None

    end_profile = _end_face_profile(body, axis_dir, um)
    if end_profile:
        loop_boxes = end_profile["loop_boxes"]
        outer = loop_boxes[0]
        u_levels = outer["u_levels"]
        v_levels = outer["v_levels"]

        if len(loop_boxes) >= 2:
            inner = loop_boxes[1]
            if len(u_levels) >= 2 and len(v_levels) >= 2 and len(inner["u_levels"]) >= 2 and len(inner["v_levels"]) >= 2:
                hollow_u = [u_levels[0], inner["u_levels"][0], inner["u_levels"][-1], u_levels[-1]]
                hollow_v = [v_levels[0], inner["v_levels"][0], inner["v_levels"][-1], v_levels[-1]]
                return _description_from_rect_hollow(hollow_u, hollow_v)

        ub_desc = _description_from_ub(u_levels, v_levels, outer)
        if ub_desc:
            return ub_desc

        pfc_desc = _description_from_pfc(u_levels, v_levels, outer)
        if pfc_desc:
            return pfc_desc

        c_purlin_desc = _description_from_c_purlin(u_levels, v_levels, outer)
        if c_purlin_desc:
            return c_purlin_desc

        if len(u_levels) >= 3 and len(v_levels) >= 3:
            return _description_from_angle(u_levels, v_levels)

        if len(u_levels) == 2 and len(v_levels) == 2:
            stock_desc = _description_from_planar_stock(body, um)
            if stock_desc:
                return stock_desc
            length_mm = _body_length_mm(body, axis_dir, um)
            return _description_from_solid_rect(u_levels, v_levels, length_mm)

    cyl_radii = _profile_face_data(body, axis_dir, um)
    if len(cyl_radii) >= 2:
        outer_radius = max(cyl_radii)
        inner_radius = min(cyl_radii)
        thickness = outer_radius - inner_radius
        if thickness > 0:
            return f"CHS {_fmt_dims(outer_radius * 2.0, thickness)}"

    return None


def _description_from_text(text):
    # Name-driven profile recognition has been retired.
    return None


def _build_description(comp, um):
    body = _single_body(comp)
    if body:
        desc = _description_from_body_geometry(body, um)
        if desc:
            return desc, "geometry"

    return None, None


def _material_name_from_description(desc):
    norm = _normalise_text(desc)
    if norm.startswith("SHS "):
        return "Steel - SHS"
    if norm.startswith("RHS "):
        return "Steel - RHS"
    if norm.startswith("CHS "):
        return "Steel - CHS"
    if norm.startswith("EA "):
        return "Steel - EA"
    if norm.startswith("UB "):
        return "Steel - UB"
    if norm.startswith("PFC "):
        return "Steel - PFC"
    if norm.startswith("C PURLIN "):
        return "Steel - C Purlin"
    if norm.startswith("FLAT BAR "):
        return "Steel - Flat Bar"
    if norm.startswith("PLATE "):
        return "Steel - Plate"
    return None


def _iter_materials(materials):
    try:
        for i in range(materials.count):
            mat = materials.item(i)
            if mat:
                yield mat
    except:
        return


def _first_steel_material(materials):
    if not materials:
        return None
    try:
        mat = materials.itemByName("Steel")
        if mat:
            return mat
    except:
        pass
    for mat in _iter_materials(materials):
        try:
            if "steel" in (mat.name or "").lower():
                return mat
        except:
            continue
    return None


def _material_seed(design, body):
    if body:
        try:
            mat = body.material
            if mat:
                return mat
        except:
            pass

    try:
        mat = _first_steel_material(design.materials)
        if mat:
            return mat
    except:
        pass

    try:
        libs = ctx.app().materialLibraries
        for i in range(libs.count):
            lib = libs.item(i)
            if not lib:
                continue
            mat = _first_steel_material(lib.materials)
            if mat:
                return mat
    except:
        pass

    return None


def _ensure_named_material(design, source_material, target_name):
    if not design or not source_material or not target_name:
        return None

    try:
        existing = design.materials.itemByName(target_name)
        if existing:
            return existing
    except:
        pass

    try:
        return design.materials.addByCopy(source_material, target_name)
    except:
        return None


def _body_material_name(body):
    if not body:
        return ""
    try:
        mat = body.material
        if mat and mat.name:
            return mat.name
    except:
        pass
    return ""


def _execute(args):
    app = ctx.app()
    ui = ctx.ui()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("No active Fusion design.")
        return

    cmd = args.command
    inputs = cmd.commandInputs
    sel_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(SELECTION_INPUT_ID))
    all_design_in = adsk.core.BoolValueCommandInput.cast(inputs.itemById(ALL_DESIGN_INPUT_ID))
    overwrite_in = adsk.core.BoolValueCommandInput.cast(inputs.itemById(OVERWRITE_INPUT_ID))

    use_whole_design = all_design_in.value if all_design_in else True
    overwrite_existing = overwrite_in.value if overwrite_in else True

    if use_whole_design:
        components = _all_components(design)
    else:
        components = _components_from_selection(sel_input)

    if not components:
        ui.messageBox("No components found. Select components/occurrences/bodies or enable Whole design.")
        return

    stats = {
        "components_scanned": 0,
        "descriptions_set": 0,
        "already_matched": 0,
        "existing_kept": 0,
        "materials_set": 0,
        "material_already_matched": 0,
        "material_failed": 0,
        "geometry_recognized": 0,
        "non_leaf_skipped": 0,
        "unknown_profile": 0,
        "referenced_skipped": 0,
        "errors": 0,
    }
    unknown = []
    errors = []

    for comp in components:
        stats["components_scanned"] += 1

        if _is_referenced_component(comp):
            stats["referenced_skipped"] += 1
            continue

        if not _is_leaf_target_component(comp):
            stats["non_leaf_skipped"] += 1
            continue

        desc, source = _build_description(comp, design.unitsManager)
        if not desc:
            stats["unknown_profile"] += 1
            try:
                unknown.append(comp.name)
            except:
                unknown.append("<unnamed>")
            continue

        if source == "geometry":
            stats["geometry_recognized"] += 1

        body = _single_body(comp)
        current = ""
        try:
            current = comp.description or ""
        except:
            current = ""

        desc_blocked = False
        if current == desc:
            stats["already_matched"] += 1
        elif current and not overwrite_existing:
            stats["existing_kept"] += 1
            desc_blocked = True
        else:
            try:
                comp.description = desc
                stats["descriptions_set"] += 1
            except Exception as ex:
                stats["errors"] += 1
                try:
                    comp_name = comp.name
                except:
                    comp_name = "<unnamed>"
                errors.append(f'Failed to set description on "{comp_name}": {ex}')

        target_material_name = _material_name_from_description(desc)
        if body and target_material_name:
            current_material_name = _body_material_name(body)
            if current_material_name == target_material_name:
                stats["material_already_matched"] += 1
            else:
                source_material = _material_seed(design, body)
                target_material = _ensure_named_material(design, source_material, target_material_name)
                if target_material:
                    try:
                        body.material = target_material
                        stats["materials_set"] += 1
                    except Exception as ex:
                        stats["material_failed"] += 1
                        stats["errors"] += 1
                        try:
                            comp_name = comp.name
                        except:
                            comp_name = "<unnamed>"
                        errors.append(f'Failed to set material on "{comp_name}": {ex}')
                elif not desc_blocked:
                    stats["material_failed"] += 1
                    stats["errors"] += 1
                    try:
                        comp_name = comp.name
                    except:
                        comp_name = "<unnamed>"
                    errors.append(f'Failed to create material "{target_material_name}" for "{comp_name}".')

    logger.log_command(CMD_NAME, dict(stats))

    summary = [
        "Component description update complete.",
        "",
        f"Components scanned: {stats['components_scanned']}",
        f"Descriptions set: {stats['descriptions_set']}",
        f"Already matched: {stats['already_matched']}",
        f"Existing kept: {stats['existing_kept']}",
        f"Materials set: {stats['materials_set']}",
        f"Material already matched: {stats['material_already_matched']}",
        f"Recognised by geometry: {stats['geometry_recognized']}",
        f"Non-leaf skipped: {stats['non_leaf_skipped']}",
        f"Unknown profile: {stats['unknown_profile']}",
        f"Referenced skipped: {stats['referenced_skipped']}",
    ]

    if unknown:
        summary.append("")
        summary.append("Unknown examples:")
        summary.extend(sorted(set(unknown))[:12])

    if errors:
        summary.append("")
        summary.append(f"Errors: {stats['errors']}")
        summary.extend(errors[:12])

    ui.messageBox("\n".join(summary), CMD_NAME)


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID,
            CMD_NAME,
            CMD_TOOLTIP,
            RESOURCE_FOLDER,
        )

    created_handler = SetComponentDescriptionsCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
