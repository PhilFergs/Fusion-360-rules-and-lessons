import adsk.core, adsk.fusion, traceback, os
import smg_context as ctx
import smg_logger as logger


CMD_ID = "PhilsDesignTools_StubArms"
CMD_NAME = "Stub Arms To Wall"
CMD_TOOLTIP = "Create stub arm sketch lines from RHS columns to the wall."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)
STUB_LINES_COMPONENT_NAME = "Stub arm lines"
STUB_MEMBER_ATTR_GROUP = "PhilsDesignTools"
STUB_MEMBER_ATTR_NAME = "StubMemberType"

TOL = 1e-6
ANGLE_TOL = 1e-3
DEBUG_STUB_ARMS = True
DEBUG_WALL_MARKERS = True
DEBUG_PROFILE_TEST = False


class StubArmsExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log("Stub Arms command failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Stub Arms command failed:\n" + traceback.format_exc())


class StubArmsCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            design = adsk.fusion.Design.cast(ctx.app().activeProduct)
            if not design:
                ctx.ui().messageBox("No active design.")
                return
            um = design.unitsManager
            length_units = um.defaultLengthUnits or "mm"

            cmd = args.command
            cmd.isRepeatable = True
            inputs = cmd.commandInputs

            if inputs.itemById("stub_cols"):
                return

            sel_cols = inputs.addSelectionInput(
                "stub_cols",
                "RHS/SHS column faces",
                "Select a planar face or a column body"
            )
            sel_cols.addSelectionFilter("Faces")
            sel_cols.addSelectionFilter("Bodies")
            sel_cols.addSelectionFilter("Occurrences")
            sel_cols.setSelectionLimits(1, 0)

            sel_wall = inputs.addSelectionInput(
                "stub_wall",
                "Wall faces",
                "Select wall faces or surface bodies"
            )
            sel_wall.addSelectionFilter("Faces")
            sel_wall.addSelectionFilter("Bodies")
            sel_wall.addSelectionFilter("Occurrences")
            sel_wall.setSelectionLimits(1, 0)

            inputs.addIntegerSpinnerCommandInput(
                "stub_points",
                "Connection points",
                2,
                20,
                1,
                6
            )

            def v(mm):
                return adsk.core.ValueInput.createByString(f"{mm} mm")

            inputs.addValueInput("stub_bottom", "Bottom offset", length_units, v(500.0))
            inputs.addValueInput("stub_top", "Top offset", length_units, v(150.0))
            inputs.addValueInput("stub_clearance", "Wall clearance", length_units, v(200.0))

            on_exec = StubArmsExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)
        except:
            logger.log("Stub Arms CommandCreated failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Stub Arms CommandCreated failed:\n" + traceback.format_exc())


def _dbg(message):
    if DEBUG_STUB_ARMS:
        logger.log(f"{CMD_NAME} DEBUG: {message}")


def _normalise(v):
    out = adsk.core.Vector3D.create(v.x, v.y, v.z)
    if out.length > TOL:
        out.normalize()
    return out


def _canon_dir(v):
    v2 = _normalise(v)
    if v2.x < 0 or (abs(v2.x) < TOL and v2.y < 0) or \
       (abs(v2.x) < TOL and abs(v2.y) < TOL and v2.z < 0):
        v2.scaleBy(-1)
    return v2


def _get_body_center(body):
    try:
        props = body.physicalProperties
        if props:
            com = props.centerOfMass
            if com:
                return com
    except:
        pass

    bb = body.boundingBox
    mp = bb.minPoint
    xp = bb.maxPoint
    return adsk.core.Point3D.create(
        (mp.x + xp.x) * 0.5,
        (mp.y + xp.y) * 0.5,
        (mp.z + xp.z) * 0.5,
    )


def _get_body_axis(body):
    clusters = []
    for e in body.edges:
        line = adsk.core.Line3D.cast(e.geometry)
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
        for c in clusters:
            if c["dir"].crossProduct(d).length < ANGLE_TOL:
                c["tot"] += length
                placed = True
                break
        if not placed:
            clusters.append({"dir": d, "tot": length})

    if not clusters:
        return None

    clusters.sort(key=lambda c: c["tot"], reverse=True)
    return clusters[0]["dir"]


def _axis_endpoints(body, axis):
    center = _get_body_center(body)
    if not center or not axis:
        return None, None, None, None

    min_t = None
    max_t = None
    for v in body.vertices:
        p = v.geometry
        diff = adsk.core.Vector3D.create(
            p.x - center.x,
            p.y - center.y,
            p.z - center.z,
        )
        t = diff.dotProduct(axis)
        if min_t is None:
            min_t = max_t = t
        else:
            min_t = min(min_t, t)
            max_t = max(max_t, t)

    if min_t is None or abs(max_t - min_t) < TOL:
        return None, None, None, None

    bottom = adsk.core.Point3D.create(
        center.x + axis.x * min_t,
        center.y + axis.y * min_t,
        center.z + axis.z * min_t,
    )
    top = adsk.core.Point3D.create(
        center.x + axis.x * max_t,
        center.y + axis.y * max_t,
        center.z + axis.z * max_t,
    )

    # Ensure bottom/top follow world Z so offsets map to "down/up" consistently.
    if bottom.z > top.z:
        bottom, top = top, bottom

    axis_vec = adsk.core.Vector3D.create(
        top.x - bottom.x,
        top.y - bottom.y,
        top.z - bottom.z,
    )
    if axis_vec.length < TOL:
        return None, None, None, None
    axis_vec.normalize()
    length = bottom.distanceTo(top)
    return axis_vec, bottom, top, length


def _looks_like_rhs_shs(body, axis_dir):
    if not body or not axis_dir:
        return False
    side_faces = []
    for face in body.faces:
        plane = adsk.core.Plane.cast(face.geometry)
        if not plane:
            continue
        n = plane.normal
        if not n or n.length < TOL:
            continue
        n_vec = adsk.core.Vector3D.create(n.x, n.y, n.z)
        n_vec.normalize()
        if abs(n_vec.dotProduct(axis_dir)) > 0.2:
            continue
        side_faces.append(n_vec)

    if len(side_faces) < 4:
        return False

    clusters = []
    for n_vec in side_faces:
        d = _canon_dir(n_vec)
        placed = False
        for c in clusters:
            if c["dir"].crossProduct(d).length < ANGLE_TOL:
                c["count"] += 1
                placed = True
                break
        if not placed:
            clusters.append({"dir": d, "count": 1})

    return len(clusters) >= 2


def _offset_point(p, d, dist):
    return adsk.core.Point3D.create(
        p.x + d.x * dist,
        p.y + d.y * dist,
        p.z + d.z * dist,
    )


def _get_face_plane(face):
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
    return adsk.core.Plane.cast(face.geometry)


def _get_wall_center_sketch(root, entry, cache):
    if not root or not entry or cache is None:
        return None
    face = entry.get("asm") if isinstance(entry, dict) else entry
    if not face:
        return None
    try:
        key = face.entityToken
    except:
        key = id(face)
    if key in cache:
        return cache[key]
    try:
        sk = root.sketches.add(face)
    except:
        return None
    try:
        sk.name = _next_sketch_name(root, "WallCenter")
    except:
        pass
    try:
        edges = adsk.core.ObjectCollection.create()
        loop_edges = None
        try:
            loops = face.loops
            for li in range(loops.count):
                loop = loops.item(li)
                try:
                    if not loop.isOuter:
                        continue
                except:
                    continue
                try:
                    loop_edges = loop.edges
                except:
                    loop_edges = None
                break
        except:
            loop_edges = None
        if loop_edges:
            for i in range(loop_edges.count):
                edges.add(loop_edges.item(i))
        else:
            for i in range(face.edges.count):
                edges.add(face.edges.item(i))
        proj = sk.project(edges)
        try:
            for i in range(proj.count):
                curve = proj.item(i)
                try:
                    curve.isConstruction = False
                except:
                    pass
                try:
                    curve.isReference = False
                except:
                    pass
                if DEBUG_STUB_ARMS:
                    try:
                        _dbg(
                            f"WallCenter proj curve {i}: "
                            f"construction={getattr(curve, 'isConstruction', None)} "
                            f"reference={getattr(curve, 'isReference', None)}"
                        )
                    except:
                        pass
        except:
            pass
        if DEBUG_STUB_ARMS:
            try:
                _dbg(f"WallCenter profiles={sk.profiles.count}")
            except:
                pass
    except:
        pass
    cache[key] = sk
    return sk


def _disable_sketch_profiles(sketch):
    if not sketch:
        return
    for attr in (
        "areProfilesVisible",
        "isProfilesVisible",
        "areProfilesShown",
        "isProfileShown",
    ):
        try:
            setattr(sketch, attr, False)
        except:
            pass


def _tag_stub_line(line, member_type):
    if not line or not member_type:
        return
    try:
        attrs = line.attributes
    except:
        attrs = None
    if not attrs:
        return
    try:
        existing = attrs.itemByName(STUB_MEMBER_ATTR_GROUP, STUB_MEMBER_ATTR_NAME)
        if existing:
            existing.value = member_type
        else:
            attrs.add(STUB_MEMBER_ATTR_GROUP, STUB_MEMBER_ATTR_NAME, member_type)
    except:
        pass


def _dist2_2d(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy


def _point_on_segment_2d(px, py, ax, ay, bx, by, tol):
    cross = (px - ax) * (by - ay) - (py - ay) * (bx - ax)
    if abs(cross) > tol:
        return False
    dot = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
    if dot < -tol:
        return False
    len_sq = (bx - ax) * (bx - ax) + (by - ay) * (by - ay)
    if dot - len_sq > tol:
        return False
    return True


def _point_in_poly_2d(px, py, poly, tol):
    inside = False
    n = len(poly)
    if n < 3:
        return False
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        if _point_on_segment_2d(px, py, ax, ay, bx, by, tol):
            return True
        if (ay > py) != (by > py):
            x_int = ax + (py - ay) * (bx - ax) / (by - ay)
            if x_int >= px - tol:
                inside = not inside
    return inside


def _profile_outer_loop_points(profile, tol):
    if not profile:
        return []
    loops = None
    try:
        loops = profile.profileLoops
    except:
        loops = None
    if not loops or loops.count == 0:
        return []
    loop = None
    for li in range(loops.count):
        l = loops.item(li)
        try:
            if l.isOuter:
                loop = l
                break
        except:
            continue
    if not loop:
        loop = loops.item(0)
    try:
        curves = loop.profileCurves
    except:
        return []
    pts = []
    last = None
    tol_sq = tol * tol
    for i in range(curves.count):
        pc = curves.item(i)
        ent = None
        try:
            ent = pc.sketchEntity
        except:
            ent = None
        if not ent:
            continue
        try:
            sp = ent.startSketchPoint.geometry
            ep = ent.endSketchPoint.geometry
        except:
            continue
        s = (sp.x, sp.y)
        e = (ep.x, ep.y)
        if not pts:
            pts.append(s)
            pts.append(e)
            last = e
            continue
        if _dist2_2d(last, s) <= tol_sq:
            pts.append(e)
            last = e
        elif _dist2_2d(last, e) <= tol_sq:
            pts.append(s)
            last = s
        else:
            pts.append(s)
            pts.append(e)
            last = e
    cleaned = []
    for p in pts:
        if not cleaned or _dist2_2d(cleaned[-1], p) > tol_sq:
            cleaned.append(p)
    if len(cleaned) > 1 and _dist2_2d(cleaned[0], cleaned[-1]) <= tol_sq:
        cleaned.pop()
    return cleaned


def _is_point_inside_sketch_profile(sketch, point):
    if not sketch or not point:
        return False
    try:
        p_sk = sketch.modelToSketchSpace(point)
    except:
        p_sk = point
    p2d = None
    try:
        p2d = adsk.core.Point2D.create(p_sk.x, p_sk.y)
    except:
        p2d = None
    p_sk_flat = None
    try:
        p_sk_flat = adsk.core.Point3D.create(p_sk.x, p_sk.y, 0)
    except:
        p_sk_flat = None
    p_model = None
    try:
        p_model = sketch.sketchToModelSpace(p_sk)
    except:
        p_model = None
    try:
        profiles = sketch.profiles
    except:
        return False
    if not profiles or profiles.count == 0:
        if DEBUG_STUB_ARMS:
            _dbg("WallCenter profiles=0 (no closed profile)")
        return False
    for i in range(profiles.count):
        prof = profiles.item(i)
        if DEBUG_PROFILE_TEST:
            try:
                bb = prof.boundingBox
                area_val = ""
                try:
                    area_val = f" area={prof.area:.3f}"
                except:
                    area_val = ""
                loops_val = ""
                try:
                    loops = prof.profileLoops
                    loop_counts = []
                    for li in range(loops.count):
                        loop = loops.item(li)
                        try:
                            loop_counts.append(str(loop.profileCurves.count))
                        except:
                            loop_counts.append("?")
                    loops_val = " loops=" + ",".join(loop_counts) if loop_counts else ""
                except:
                    loops_val = ""
                if bb and bb.minPoint and bb.maxPoint:
                    _dbg(
                        "WallCenter profile idx="
                        f"{i} bb=({bb.minPoint.x:.3f},{bb.minPoint.y:.3f})"
                        f"-({bb.maxPoint.x:.3f},{bb.maxPoint.y:.3f}){area_val}{loops_val}"
                    )
            except:
                pass
        try:
            if hasattr(prof, "isPointInside"):
                if p2d and prof.isPointInside(p2d):
                    if DEBUG_PROFILE_TEST:
                        _dbg(f"WallCenter hit inside profile idx={i} via=2d")
                    return True
                if prof.isPointInside(p_sk):
                    if DEBUG_PROFILE_TEST:
                        _dbg(f"WallCenter hit inside profile idx={i} via=sketch")
                    return True
                if p_sk_flat and prof.isPointInside(p_sk_flat):
                    if DEBUG_PROFILE_TEST:
                        _dbg(f"WallCenter hit inside profile idx={i} via=flat")
                    return True
                if p_model and prof.isPointInside(p_model):
                    if DEBUG_PROFILE_TEST:
                        _dbg(f"WallCenter hit inside profile idx={i} via=model")
                    return True
        except:
            pass
    tol = TOL * 100.0
    for i in range(profiles.count):
        prof = profiles.item(i)
        poly = _profile_outer_loop_points(prof, tol)
        if DEBUG_PROFILE_TEST:
            try:
                _dbg(f"WallCenter poly idx={i} pts={len(poly)}")
            except:
                pass
        if poly and _point_in_poly_2d(p_sk.x, p_sk.y, poly, tol):
            if DEBUG_PROFILE_TEST:
                _dbg(f"WallCenter hit inside profile idx={i} via=poly")
            return True
    if DEBUG_STUB_ARMS:
        bb_msg = ""
        counts_msg = ""
        curves_total_msg = ""
        p_model_msg = ""
        try:
            if profiles.count > 0:
                bb = profiles.item(0).boundingBox
                if bb and bb.minPoint and bb.maxPoint:
                    bb_msg = (
                        f" bb_min=({bb.minPoint.x:.3f},{bb.minPoint.y:.3f})"
                        f" bb_max=({bb.maxPoint.x:.3f},{bb.maxPoint.y:.3f})"
                    )
        except:
            pass
        min_dist = None
        eval_hits = 0
        if not p_model:
            try:
                p_model = point
            except:
                p_model = None
        try:
            if p_model:
                p_model_msg = (
                    f" p_model=({p_model.x:.3f},{p_model.y:.3f},{p_model.z:.3f})"
                )
        except:
            pass
        try:
            curves = sketch.sketchCurves
            if DEBUG_STUB_ARMS:
                try:
                    counts = [
                        str(getattr(curves, "sketchLines", None).count),
                        str(getattr(curves, "sketchArcs", None).count),
                        str(getattr(curves, "sketchCircles", None).count),
                        str(getattr(curves, "sketchEllipses", None).count),
                        str(getattr(curves, "sketchFittedSplines", None).count),
                        str(getattr(curves, "sketchFixedSplines", None).count),
                        str(getattr(curves, "sketchConics", None).count),
                    ]
                    counts_msg = (
                        " curve_counts=[lines,arcs,circles,ellipses,"
                        "fitted,fix,conics]=" + ",".join(counts)
                    )
                except:
                    pass
                try:
                    curves_total_msg = f" curves_total={curves.count}"
                except:
                    curves_total_msg = " curves_total=?"
            try:
                total = curves.count
            except:
                total = 0
            for i in range(total):
                geo = None
                try:
                    geo = curves.item(i).geometry
                except:
                    geo = None
                if not geo:
                    continue
                obj_type = ""
                try:
                    obj_type = getattr(geo, "objectType", "") or ""
                except:
                    obj_type = ""
                if DEBUG_STUB_ARMS and i < 5:
                    try:
                        has_eval = hasattr(geo, "evaluator")
                        _dbg(f"WallCenter curve[{i}] type={obj_type} has_eval={has_eval}")
                    except:
                        pass
                try:
                    cp = None
                    is_3d = "3D" in obj_type if obj_type else False
                    if is_3d and p_model:
                        try:
                            res = geo.evaluator.getClosestPointTo(p_model)
                            cp = res[1] if isinstance(res, tuple) else res
                        except:
                            cp = None
                    if not cp and p2d:
                        try:
                            res = geo.evaluator.getClosestPointTo(p2d)
                            cp = res[1] if isinstance(res, tuple) else res
                        except:
                            cp = None
                    if not cp:
                        try:
                            res = geo.evaluator.getClosestPointTo(p_sk)
                            cp = res[1] if isinstance(res, tuple) else res
                        except:
                            cp = None
                    if not cp and p_model and not is_3d:
                        try:
                            res = geo.evaluator.getClosestPointTo(p_model)
                            cp = res[1] if isinstance(res, tuple) else res
                        except:
                            cp = None
                    if cp:
                        d = None
                        if p_model:
                            try:
                                d = cp.distanceTo(p_model)
                            except:
                                d = None
                        if d is None:
                            try:
                                d = cp.distanceTo(p2d or p_sk)
                            except:
                                d = None
                        if d is not None:
                            if min_dist is None or d < min_dist:
                                min_dist = d
                        eval_hits += 1
                except:
                    pass
        except:
            pass
        dist_msg = f" min_dist={min_dist:.3f}" if min_dist is not None else ""
        eval_msg = f" eval_hits={eval_hits}" if eval_hits else " eval_hits=0"
        _dbg(
            "WallCenter hit outside all profiles "
            f"p=({p_sk.x:.3f},{p_sk.y:.3f},{p_sk.z:.3f}){p_model_msg}"
            f"{bb_msg}{dist_msg}{eval_msg}"
            f"{counts_msg}{curves_total_msg}"
        )
    return False


def _add_wall_hit_marker(root, entry, point, radius_u, cache):
    if not root or not entry or not point or radius_u <= 0:
        return None
    sk = _get_wall_center_sketch(root, entry, cache)
    if not sk:
        return None
    if not _is_point_inside_sketch_profile(sk, point):
        if DEBUG_STUB_ARMS:
            try:
                _dbg(f"WallCenter hit world=({point.x:.3f},{point.y:.3f},{point.z:.3f})")
            except:
                pass
        return None
    try:
        p_sk = sk.modelToSketchSpace(point)
    except:
        p_sk = point
    try:
        sk.sketchCurves.sketchCircles.addByCenterRadius(p_sk, radius_u)
    except:
        pass
    return sk


def _project_point_to_plane(point, plane_origin, plane_normal):
    n_vec = adsk.core.Vector3D.create(plane_normal.x, plane_normal.y, plane_normal.z)
    if n_vec.length < TOL:
        return None
    n_vec.normalize()
    v = adsk.core.Vector3D.create(
        point.x - plane_origin.x,
        point.y - plane_origin.y,
        point.z - plane_origin.z,
    )
    dist = n_vec.dotProduct(v)
    return adsk.core.Point3D.create(
        point.x - n_vec.x * dist,
        point.y - n_vec.y * dist,
        point.z - n_vec.z * dist,
    )


def _component_axes(body, root):
    occ = None
    try:
        occ = getattr(body, "assemblyContext", None)
    except:
        pass
    if not occ:
        try:
            comp = body.parentComponent
        except:
            comp = None
        occ = _find_occurrence_for_component(root, comp) if comp else None

    x = adsk.core.Vector3D.create(1, 0, 0)
    y = adsk.core.Vector3D.create(0, 1, 0)
    z = adsk.core.Vector3D.create(0, 0, 1)
    if occ:
        try:
            tr = occ.transform
            tr.transformVector(x)
            tr.transformVector(y)
            tr.transformVector(z)
        except:
            pass
    return [_normalise(x), _normalise(y), _normalise(z)]


def _extract_points(res):
    if not res:
        return []
    if isinstance(res, tuple):
        if len(res) >= 2 and isinstance(res[0], bool):
            if not res[0]:
                return []
            return _extract_points(res[1])
        pts = []
        for item in res:
            pts.extend(_extract_points(item))
        return pts
    if hasattr(res, "count") and hasattr(res, "item"):
        pts = []
        for i in range(res.count):
            pts.append(res.item(i))
        return pts
    return [res]


def _line_plane_intersection(origin, direction, plane):
    if not plane or direction.length < TOL:
        return None, None
    n = plane.normal
    if not n or n.length < TOL:
        return None, None
    denom = n.dotProduct(direction)
    if abs(denom) < TOL:
        return None, None
    v = adsk.core.Vector3D.create(
        plane.origin.x - origin.x,
        plane.origin.y - origin.y,
        plane.origin.z - origin.z,
    )
    t = n.dotProduct(v) / denom
    hit = adsk.core.Point3D.create(
        origin.x + direction.x * t,
        origin.y + direction.y * t,
        origin.z + direction.z * t,
    )
    return hit, t


def _is_point_on_face(face, point):
    try:
        ev = face.evaluator
        if hasattr(ev, "isPointOnFace"):
            res = ev.isPointOnFace(point)
            if isinstance(res, tuple):
                return bool(res[0])
            return bool(res)
    except:
        pass
    try:
        if hasattr(face.evaluator, "getClosestPointTo"):
            res = face.evaluator.getClosestPointTo(point)
        else:
            res = face.evaluator.getClosestPoint(point)
    except:
        return False
    if isinstance(res, tuple):
        if not res[0]:
            return False
        cp = res[1]
    else:
        cp = res
    if not cp:
        return False
    return cp.distanceTo(point) <= 1e-3


def _to_local_point(point, occ):
    if not point or not occ:
        return point
    try:
        inv = occ.transform.copy()
        inv.invert()
        p = adsk.core.Point3D.create(point.x, point.y, point.z)
        p.transformBy(inv)
        return p
    except:
        return point


def _to_local_vector(vec, occ):
    if not vec or not occ:
        return vec
    try:
        inv = occ.transform.copy()
        inv.invert()
        v = adsk.core.Vector3D.create(vec.x, vec.y, vec.z)
        inv.transformVector(v)
        return v
    except:
        return vec


def _to_world_point(point, occ):
    if not point or not occ:
        return point
    try:
        p = adsk.core.Point3D.create(point.x, point.y, point.z)
        p.transformBy(occ.transform)
        return p
    except:
        return point


def _intersect_ray_with_face(face, origin, direction):
    if direction.length < TOL:
        return None
    d = _normalise(direction)
    plane = _get_face_plane(face)
    if not plane:
        return None
    hit, t = _line_plane_intersection(origin, d, plane)
    if not hit or t <= TOL:
        return None
    return hit


def _intersect_ray_with_faces(origin, direction, faces):
    best = None
    best_t = None
    best_entry = None
    for entry in faces:
        face = entry.get("asm") if isinstance(entry, dict) else entry
        if not face:
            continue
        hit = _intersect_ray_with_face(face, origin, direction)
        if not hit:
            continue
        v = adsk.core.Vector3D.create(
            hit.x - origin.x,
            hit.y - origin.y,
            hit.z - origin.z,
        )
        t = v.dotProduct(direction)
        if t <= TOL:
            continue
        if best_t is None or t < best_t:
            best_t = t
            best = hit
            best_entry = entry
    return best, best_entry


def _intersect_ray_with_faces_onface(origin, direction, faces, sk_cache):
    best = None
    best_t = None
    best_entry = None
    if not faces:
        return None, None
    for entry in faces:
        face = entry.get("asm") if isinstance(entry, dict) else entry
        if not face:
            continue
        hit = _intersect_ray_with_face(face, origin, direction)
        if not hit:
            continue
        sk = _get_wall_center_sketch(ctx.app().activeProduct.rootComponent, entry, sk_cache)
        if not sk or not _is_point_inside_sketch_profile(sk, hit):
            continue
        v = adsk.core.Vector3D.create(
            hit.x - origin.x,
            hit.y - origin.y,
            hit.z - origin.z,
        )
        t = v.dotProduct(direction)
        if t <= TOL:
            continue
        if best_t is None or t < best_t:
            best_t = t
            best = hit
            best_entry = entry
    return best, best_entry


def _segment_hits_wall_before_hit(origin, target, faces, sk_cache, clearance_u):
    if not origin or not target:
        return False
    v = adsk.core.Vector3D.create(
        target.x - origin.x,
        target.y - origin.y,
        target.z - origin.z,
    )
    dist = v.length
    if dist < TOL:
        return False
    d = _normalise(v)
    hit, _ = _intersect_ray_with_faces_onface(origin, d, faces, sk_cache)
    if not hit:
        return False
    t_near = adsk.core.Vector3D.create(
        hit.x - origin.x,
        hit.y - origin.y,
        hit.z - origin.z,
    ).dotProduct(d)
    if t_near <= TOL:
        return False
    if t_near < dist - max(clearance_u, TOL * 10.0):
        return True
    return False


def _adjust_lower_for_clearance(lower, upper, hit, axis_dir, faces, sk_cache, clearance_u):
    if not lower or not upper or not hit:
        return lower, True
    if clearance_u <= TOL:
        return lower, True
    axis = _normalise(axis_dir)
    if not axis:
        return lower, True
    v = adsk.core.Vector3D.create(
        upper.x - lower.x,
        upper.y - lower.y,
        upper.z - lower.z,
    )
    max_shift = v.dotProduct(axis)
    if max_shift <= clearance_u + TOL:
        return lower, False
    cur = lower
    max_steps = int(max_shift / clearance_u) + 2
    for _ in range(max_steps):
        if not _segment_hits_wall_before_hit(cur, hit, faces, sk_cache, clearance_u):
            return cur, True
        cur = _offset_point(cur, axis, clearance_u)
        rem = adsk.core.Vector3D.create(
            upper.x - cur.x,
            upper.y - cur.y,
            upper.z - cur.z,
        ).dotProduct(axis)
        if rem <= clearance_u:
            break
    return lower, False


def _line_dir_for_face(face_normal, axis_dir, comp_axes):
    n = _normalise(face_normal)
    axis_n = _normalise(axis_dir)
    for axis in comp_axes:
        if abs(axis.dotProduct(n)) > 0.2:
            continue
        if abs(axis.dotProduct(axis_n)) > 0.2:
            continue
        return _normalise(axis)
    d = axis_n.crossProduct(n)
    if d.length < TOL:
        return None
    d.normalize()
    return d


def _face_span_along_dir(face, direction):
    if not face or direction.length < TOL:
        return None
    d = _normalise(direction)
    min_t = None
    max_t = None
    try:
        verts = face.vertices
    except:
        verts = None
    if not verts or verts.count == 0:
        return None
    for i in range(verts.count):
        p = verts.item(i).geometry
        t = p.x * d.x + p.y * d.y + p.z * d.z
        if min_t is None:
            min_t = max_t = t
        else:
            min_t = min(min_t, t)
            max_t = max(max_t, t)
    if min_t is None:
        return None
    return max_t - min_t




def _find_occurrence_for_component(root, comp):
    if not root or not comp:
        return None
    try:
        occs = root.allOccurrences
        for i in range(occs.count):
            occ = occs.item(i)
            if occ.component == comp:
                return occ
    except:
        pass
    return None


def _proxy_body(body, root):
    if not body:
        return None
    try:
        if getattr(body, "assemblyContext", None):
            return body
    except:
        pass
    try:
        comp = body.parentComponent
    except:
        comp = None
    occ = _find_occurrence_for_component(root, comp) if comp else None
    if occ:
        try:
            return body.createForAssemblyContext(occ)
        except:
            return None
    return body


def _proxy_face(face, root):
    if not face:
        return None
    try:
        if getattr(face, "assemblyContext", None):
            return face
    except:
        pass
    try:
        comp = face.body.parentComponent
    except:
        comp = None
    occ = _find_occurrence_for_component(root, comp) if comp else None
    if occ:
        try:
            return face.createForAssemblyContext(occ)
        except:
            return None
    return face


def _collect_column_faces(sel_input, root):
    faces = {}
    bodies = []
    for i in range(sel_input.selectionCount):
        ent = sel_input.selection(i).entity
        face = adsk.fusion.BRepFace.cast(ent)
        if face:
            asm = _proxy_face(face, root)
            if not asm:
                continue
            try:
                key = asm.entityToken
            except:
                key = id(asm)
            if key not in faces:
                faces[key] = asm
            continue
        body = adsk.fusion.BRepBody.cast(ent)
        if body:
            body = _proxy_body(body, root)
            if body:
                bodies.append(body)
            continue
        occ = adsk.fusion.Occurrence.cast(ent)
        if occ:
            try:
                bodies_coll = occ.component.bRepBodies
            except:
                bodies_coll = None
            if not bodies_coll:
                continue
            for j in range(bodies_coll.count):
                b = bodies_coll.item(j)
                try:
                    b_asm = b.createForAssemblyContext(occ)
                except:
                    b_asm = None
                if b_asm:
                    bodies.append(b_asm)
            continue
    return list(faces.values()), bodies


def _collect_wall_faces(sel_input, root):
    faces = {}
    for i in range(sel_input.selectionCount):
        ent = sel_input.selection(i).entity
        face = adsk.fusion.BRepFace.cast(ent)
        if face:
            occ = getattr(face, "assemblyContext", None)
            native = getattr(face, "nativeObject", None) or face
            asm = face if occ else _proxy_face(face, root)
            if not asm:
                continue
            try:
                key = asm.entityToken
            except:
                key = id(asm)
            faces[key] = {
                "asm": asm,
                "native": native,
                "occ": occ,
            }
            continue
        body = adsk.fusion.BRepBody.cast(ent)
        if body:
            body = _proxy_body(body, root)
            if not body:
                continue
            for j in range(body.faces.count):
                f = body.faces.item(j)
                occ = getattr(f, "assemblyContext", None)
                native = getattr(f, "nativeObject", None) or f
                asm = f if occ else _proxy_face(f, root)
                if not asm:
                    continue
                try:
                    key = asm.entityToken
                except:
                    key = id(asm)
                faces[key] = {
                    "asm": asm,
                    "native": native,
                    "occ": occ,
                }
            continue
        occ = adsk.fusion.Occurrence.cast(ent)
        if occ:
            try:
                bodies = occ.component.bRepBodies
            except:
                bodies = None
            if not bodies:
                continue
            for j in range(bodies.count):
                b = bodies.item(j)
                try:
                    fcount = b.faces.count
                except:
                    fcount = 0
                if fcount == 0:
                    continue
                b_asm = b.createForAssemblyContext(occ)
                for k in range(b_asm.faces.count):
                    f = b_asm.faces.item(k)
                    occ_f = getattr(f, "assemblyContext", None)
                    native_f = getattr(f, "nativeObject", None) or f
                    asm_f = f if occ_f else _proxy_face(f, root)
                    if not asm_f:
                        continue
                    try:
                        key = asm_f.entityToken
                    except:
                        key = id(asm_f)
                    faces[key] = {
                        "asm": asm_f,
                        "native": native_f,
                        "occ": occ_f,
                    }
            continue
        comp = adsk.fusion.Component.cast(ent)
        if comp:
            occ = _find_occurrence_for_component(root, comp)
            if not occ:
                continue
            try:
                bodies = comp.bRepBodies
            except:
                bodies = None
            if not bodies:
                continue
            for j in range(bodies.count):
                b = bodies.item(j)
                try:
                    fcount = b.faces.count
                except:
                    fcount = 0
                if fcount == 0:
                    continue
                b_asm = b.createForAssemblyContext(occ)
                for k in range(b_asm.faces.count):
                    f = b_asm.faces.item(k)
                    occ_f = getattr(f, "assemblyContext", None)
                    native_f = getattr(f, "nativeObject", None) or f
                    asm_f = f if occ_f else _proxy_face(f, root)
                    if not asm_f:
                        continue
                    try:
                        key = asm_f.entityToken
                    except:
                        key = id(asm_f)
                    faces[key] = {
                        "asm": asm_f,
                        "native": native_f,
                        "occ": occ_f,
                    }
    return list(faces.values())


def _next_sketch_name(comp, base):
    existing = set()
    sketches = getattr(comp, "sketches", None)
    if not sketches:
        return base
    for i in range(sketches.count):
        try:
            existing.add(sketches.item(i).name)
        except:
            pass
    if base not in existing:
        return base
    idx = 2
    while f"{base} {idx}" in existing:
        idx += 1
    return f"{base} {idx}"


def _face_area(face):
    if not face:
        return 0.0
    try:
        return face.area
    except:
        pass
    try:
        ap = face.areaProperties
        if ap:
            return ap.area
    except:
        pass
    return 0.0


def _face_is_side(face, axis_dir):
    if not face or not axis_dir:
        return False
    plane = _get_face_plane(face)
    if not plane or not plane.normal:
        return False
    n = _normalise(plane.normal)
    a = _normalise(axis_dir)
    if not n or not a:
        return False
    return abs(n.dotProduct(a)) < 0.3


def _get_or_create_stub_component(root):
    if not root:
        return None
    target = None
    try:
        occs = root.occurrences
        for i in range(occs.count):
            occ = occs.item(i)
            try:
                if occ.component and occ.component.name.lower() == STUB_LINES_COMPONENT_NAME.lower():
                    target = occ.component
                    break
            except:
                continue
    except:
        pass
    if target:
        return target
    try:
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = STUB_LINES_COMPONENT_NAME
        return comp
    except:
        return None


def _component_label_for_body(body):
    if not body:
        return "<unnamed>"
    try:
        occ = getattr(body, "assemblyContext", None)
        if occ and occ.component and occ.component.name:
            return occ.component.name
    except:
        pass
    try:
        comp = body.parentComponent
        if comp and comp.name:
            return comp.name
    except:
        pass
    try:
        name = body.name
        if name:
            return name
    except:
        pass
    return "<unnamed>"


def _create_stub_sketch(stub_comp, face, root):
    if not stub_comp:
        return None
    sk = None
    plane = _get_face_plane(face)
    if plane:
        try:
            sk = stub_comp.sketches.add(plane)
        except:
            sk = None
    if not sk:
        try:
            sk = stub_comp.sketches.add(face)
        except:
            sk = None
    if not sk:
        try:
            sk = root.sketches.add(face)
        except:
            sk = None
    return sk


def _choose_column_face(body, root, wall_faces, wall_sketches):
    if not body:
        return None
    axis = _get_body_axis(body)
    axis_dir, bottom, top, length = _axis_endpoints(body, axis) if axis else (None, None, None, None)
    if not axis_dir or not bottom or not top:
        return None
    comp_axes = _component_axes(body, root)
    candidates = []
    try:
        faces = body.faces
    except:
        faces = None
    if not faces:
        return None
    max_area = 0.0
    for i in range(faces.count):
        f = faces.item(i)
        if not _face_is_side(f, axis_dir):
            continue
        area = _face_area(f)
        if area > max_area:
            max_area = area
        candidates.append((f, area))
    if not candidates:
        return None
    area_tol = max_area * 0.01
    top_faces = [f for f, a in candidates if a >= max_area - area_tol]
    if len(top_faces) == 1:
        return top_faces[0]
    best = None
    best_hits = -1
    best_avg = None
    for f in top_faces:
        plane = _get_face_plane(f)
        if not plane:
            continue
        line_dir = _line_dir_for_face(plane.normal, axis_dir, comp_axes)
        if not line_dir:
            continue
        wall_dir = _normalise(line_dir)
        hits = 0
        dist_sum = 0.0
        for t in (0.2, 0.5, 0.8):
            p = _offset_point(bottom, axis_dir, length * t)
            hit, _ = _intersect_ray_with_faces_onface(p, wall_dir, wall_faces, wall_sketches)
            if not hit:
                neg_dir = adsk.core.Vector3D.create(-wall_dir.x, -wall_dir.y, -wall_dir.z)
                hit, _ = _intersect_ray_with_faces_onface(p, neg_dir, wall_faces, wall_sketches)
            if hit:
                v = adsk.core.Vector3D.create(hit.x - p.x, hit.y - p.y, hit.z - p.z)
                hits += 1
                dist_sum += abs(v.dotProduct(wall_dir))
        if hits > 0:
            avg = dist_sum / float(hits)
            if hits > best_hits or (hits == best_hits and (best_avg is None or avg < best_avg)):
                best_hits = hits
                best_avg = avg
                best = f
    if best:
        return best
    return top_faces[0]


def _execute(args):
    design = adsk.fusion.Design.cast(ctx.app().activeProduct)
    if not design:
        ctx.ui().messageBox("No active design.")
        return
    root = design.rootComponent
    um = design.unitsManager

    cmd = args.command
    inputs = cmd.commandInputs

    sel_cols = adsk.core.SelectionCommandInput.cast(inputs.itemById("stub_cols"))
    sel_wall = adsk.core.SelectionCommandInput.cast(inputs.itemById("stub_wall"))
    count_in = adsk.core.IntegerSpinnerCommandInput.cast(inputs.itemById("stub_points"))

    if not sel_cols or sel_cols.selectionCount == 0:
        ctx.ui().messageBox("Select at least one RHS column face.")
        return
    if not sel_wall or sel_wall.selectionCount == 0:
        ctx.ui().messageBox("Select at least one wall face or body.")
        return

    def mm_val(cid):
        v = adsk.core.ValueCommandInput.cast(inputs.itemById(cid))
        return um.convert(v.value, um.internalUnits, "mm")

    bottom_mm = mm_val("stub_bottom")
    top_mm = mm_val("stub_top")
    count = count_in.value if count_in else 6

    bottom_u = um.convert(bottom_mm, "mm", um.internalUnits)
    top_u = um.convert(top_mm, "mm", um.internalUnits)
    clearance_mm = mm_val("stub_clearance")
    clearance_u = um.convert(clearance_mm, "mm", um.internalUnits)
    default_line_len = um.convert(100.0, "mm", um.internalUnits)

    faces, bodies = _collect_column_faces(sel_cols, root)
    if not faces and not bodies:
        ctx.ui().messageBox("No valid RHS/SHS faces selected.")
        return
    wall_faces = _collect_wall_faces(sel_wall, root)
    if not wall_faces:
        ctx.ui().messageBox("No valid wall faces selected.")
        return

    _dbg(f"Selected faces={len(faces)}, wall_faces={len(wall_faces)}, points={count}")

    logger.log_command(
        CMD_NAME,
        {
            "faces": len(faces),
            "wall_faces": len(wall_faces),
            "points": count,
            "bottom_mm": bottom_mm,
            "top_mm": top_mm,
        },
    )

    wall_center_sketches = {}
    stub_comp = _get_or_create_stub_component(root)
    if not stub_comp:
        ctx.ui().messageBox("Failed to create or find 'stub arm lines' component.")
        return
    hit_marker_radius_u = None
    if DEBUG_WALL_MARKERS:
        hit_marker_radius_u = um.convert(6.0, "mm", um.internalUnits)
        for entry in wall_faces:
            sk = _get_wall_center_sketch(root, entry, wall_center_sketches)
            if sk and DEBUG_STUB_ARMS:
                _dbg(f"Wall marker sketch='{sk.name}'")

    lines_created = 0
    cols_skipped = []
    pair_missed = 0

    for face in faces:
        body = face.body
        label = _component_label_for_body(body)
        plane = _get_face_plane(face)
        if not plane:
            _dbg(f"Skip body='{label}': selected face not planar")
            cols_skipped.append(label)
            continue

        axis = _get_body_axis(body)
        axis_dir, bottom, top, length = _axis_endpoints(body, axis) if axis else (None, None, None, None)
        if not axis_dir or not bottom or not top or not length:
            _dbg(f"Skip body='{label}': axis/length invalid")
            cols_skipped.append(label)
            continue

        if not _looks_like_rhs_shs(body, axis_dir):
            _dbg(f"Skip body='{label}': not RHS/SHS (name/geometry check failed)")
            cols_skipped.append(label)
            continue

        comp_axes = _component_axes(body, root)

        span = length - bottom_u - top_u
        if count < 2 or span <= TOL:
            _dbg(f"Skip body='{label}': span={span:.4f} count={count}")
            cols_skipped.append(label)
            continue
        spacing = span / float(count - 1)
        if spacing <= TOL:
            _dbg(f"Skip body='{label}': spacing={spacing:.4f}")
            cols_skipped.append(label)
            continue

        points = []
        for i in range(count):
            dist = bottom_u + spacing * i
            points.append(_offset_point(bottom, axis_dir, dist))

        _dbg(
            f"Body='{label}' axis=({axis_dir.x:.4f},{axis_dir.y:.4f},{axis_dir.z:.4f}) "
            f"len={length:.4f} bottom=({bottom.x:.4f},{bottom.y:.4f},{bottom.z:.4f}) "
            f"top=({top.x:.4f},{top.y:.4f},{top.z:.4f}) spacing={spacing:.4f}"
        )
        line_dir = _line_dir_for_face(plane.normal, axis_dir, comp_axes)
        if not line_dir:
            _dbg(f"Skip body='{label}': line dir invalid")
            cols_skipped.append(label)
            continue
        wall_dir = _normalise(line_dir)

        span = _face_span_along_dir(face, line_dir)
        line_len = span * 0.9 if span and span > TOL else default_line_len
        half_len = line_len * 0.5

        face_points = []
        for p in points:
            p_on = _project_point_to_plane(p, plane.origin, plane.normal)
            if not p_on:
                continue
            face_points.append(p_on)

        pair_hits = []

        for i in range(len(face_points) - 1):
            lower = face_points[i]
            upper = face_points[i + 1]
            mid = adsk.core.Point3D.create(
                (upper.x + lower.x) * 0.5,
                (upper.y + lower.y) * 0.5,
                (upper.z + lower.z) * 0.5,
            )

            hit = None
            hit_entry = None
            hit_from = "upper"
            hit, hit_entry = _intersect_ray_with_faces_onface(
                upper, wall_dir, wall_faces, wall_center_sketches
            )
            if not hit:
                hit_from = "lower"
                hit, hit_entry = _intersect_ray_with_faces_onface(
                    lower, wall_dir, wall_faces, wall_center_sketches
                )
            if not hit:
                hit_from = "mid"
                hit, hit_entry = _intersect_ray_with_faces_onface(
                    mid, wall_dir, wall_faces, wall_center_sketches
                )
            if not hit:
                neg_dir = adsk.core.Vector3D.create(-wall_dir.x, -wall_dir.y, -wall_dir.z)
                hit_from = "upper_neg"
                hit, hit_entry = _intersect_ray_with_faces_onface(
                    upper, neg_dir, wall_faces, wall_center_sketches
                )
                if not hit:
                    hit_from = "lower_neg"
                    hit, hit_entry = _intersect_ray_with_faces_onface(
                        lower, neg_dir, wall_faces, wall_center_sketches
                    )
                if not hit:
                    hit_from = "mid_neg"
                    hit, hit_entry = _intersect_ray_with_faces_onface(
                        mid, neg_dir, wall_faces, wall_center_sketches
                    )
            if not hit:
                if DEBUG_STUB_ARMS and wall_faces:
                    wf = wall_faces[0]
                    asm_face = wf["asm"]
                    native_face = wf["native"]
                    occ = wf["occ"]
                    plane_w = _get_face_plane(asm_face)
                    n_w = _normalise(plane_w.normal) if plane_w and plane_w.normal else None
                    if occ:
                        mid_l = _to_local_point(mid, occ)
                        dir_l = _to_local_vector(line_dir, occ)
                        plane_l = _get_face_plane(native_face)
                        n_l = _normalise(plane_l.normal) if plane_l and plane_l.normal else None
                        _dbg(
                            f"Missed pair {i}: mid_w=({mid.x:.3f},{mid.y:.3f},{mid.z:.3f}) "
                            f"dir_w=({wall_dir.x:.3f},{wall_dir.y:.3f},{wall_dir.z:.3f}) "
                            f"wall_n_w=({n_w.x:.3f},{n_w.y:.3f},{n_w.z:.3f}) "
                            f"mid_l=({mid_l.x:.3f},{mid_l.y:.3f},{mid_l.z:.3f}) "
                            f"dir_l=({dir_l.x:.3f},{dir_l.y:.3f},{dir_l.z:.3f}) "
                            f"wall_n_l=({n_l.x:.3f},{n_l.y:.3f},{n_l.z:.3f})"
                        )
                    else:
                        _dbg(
                            f"Missed pair {i}: mid=({mid.x:.3f},{mid.y:.3f},{mid.z:.3f}) "
                            f"dir=({wall_dir.x:.3f},{wall_dir.y:.3f},{wall_dir.z:.3f}) "
                            f"wall_n=({n_w.x:.3f},{n_w.y:.3f},{n_w.z:.3f})"
                        )
                pair_missed += 1
                continue
            if DEBUG_STUB_ARMS:
                _dbg(f"Pair {i}: wall hit from {hit_from}")
            if DEBUG_WALL_MARKERS and wall_center_sketches and hit_entry and hit_marker_radius_u:
                _add_wall_hit_marker(root, hit_entry, hit, hit_marker_radius_u, wall_center_sketches)
            lower_adj, draw_lower = _adjust_lower_for_clearance(
                lower, upper, hit, axis_dir, wall_faces, wall_center_sketches, clearance_u
            )
            pair_hits.append((i, lower_adj, upper, hit, draw_lower))

        if not pair_hits:
            continue

        sk = _create_stub_sketch(stub_comp, face, root)
        if not sk:
            _dbg(f"Skip body='{label}': failed to create stub sketch")
            cols_skipped.append(label)
            continue
        try:
            sk.name = _next_sketch_name(stub_comp, f"Stub Arms - {label}")
        except:
            pass
        _disable_sketch_profiles(sk)
        lines = sk.sketchCurves.sketchLines

        for _, lower, upper, hit, draw_lower in pair_hits:
            try:
                upper_sk = sk.modelToSketchSpace(upper)
                lower_sk = sk.modelToSketchSpace(lower)
                hit_sk = sk.modelToSketchSpace(hit)
            except:
                upper_sk = upper
                lower_sk = lower
                hit_sk = hit
            upper_line = lines.addByTwoPoints(upper_sk, hit_sk)
            _tag_stub_line(upper_line, "FlatBar")
            if draw_lower:
                lower_line = lines.addByTwoPoints(lower_sk, hit_sk)
                _tag_stub_line(lower_line, "EA")
                lines_created += 2
            else:
                lines_created += 1

    for body in bodies:
        label = _component_label_for_body(body)
        face = _choose_column_face(body, root, wall_faces, wall_center_sketches)
        if not face:
            _dbg(f"Skip body='{label}': no suitable side face")
            cols_skipped.append(label)
            continue
        plane = _get_face_plane(face)
        if not plane:
            _dbg(f"Skip body='{label}': selected face not planar")
            cols_skipped.append(label)
            continue
        axis = _get_body_axis(body)
        axis_dir, bottom, top, length = _axis_endpoints(body, axis) if axis else (None, None, None, None)
        if not axis_dir or not bottom or not top or not length:
            _dbg(f"Skip body='{label}': axis/length invalid")
            cols_skipped.append(label)
            continue
        if not _looks_like_rhs_shs(body, axis_dir):
            _dbg(f"Skip body='{label}': not RHS/SHS (name/geometry check failed)")
            cols_skipped.append(label)
            continue

        comp_axes = _component_axes(body, root)
        span = length - bottom_u - top_u
        if count < 2 or span <= TOL:
            _dbg(f"Skip body='{label}': span={span:.4f} count={count}")
            cols_skipped.append(label)
            continue
        spacing = span / float(count - 1)
        if spacing <= TOL:
            _dbg(f"Skip body='{label}': spacing={spacing:.4f}")
            cols_skipped.append(label)
            continue

        points = []
        for i in range(count):
            dist = bottom_u + spacing * i
            points.append(_offset_point(bottom, axis_dir, dist))

        _dbg(
            f"Body='{label}' axis=({axis_dir.x:.4f},{axis_dir.y:.4f},{axis_dir.z:.4f}) "
            f"len={length:.4f} bottom=({bottom.x:.4f},{bottom.y:.4f},{bottom.z:.4f}) "
            f"top=({top.x:.4f},{top.y:.4f},{top.z:.4f}) spacing={spacing:.4f}"
        )
        line_dir = _line_dir_for_face(plane.normal, axis_dir, comp_axes)
        if not line_dir:
            _dbg(f"Skip body='{label}': line dir invalid")
            cols_skipped.append(label)
            continue
        wall_dir = _normalise(line_dir)

        span = _face_span_along_dir(face, line_dir)
        line_len = span * 0.9 if span and span > TOL else default_line_len
        half_len = line_len * 0.5

        face_points = []
        for p in points:
            p_on = _project_point_to_plane(p, plane.origin, plane.normal)
            if not p_on:
                continue
            face_points.append(p_on)

        pair_hits = []
        for i in range(len(face_points) - 1):
            lower = face_points[i]
            upper = face_points[i + 1]
            mid = adsk.core.Point3D.create(
                (upper.x + lower.x) * 0.5,
                (upper.y + lower.y) * 0.5,
                (upper.z + lower.z) * 0.5,
            )

            hit = None
            hit_entry = None
            hit_from = "upper"
            hit, hit_entry = _intersect_ray_with_faces_onface(
                upper, wall_dir, wall_faces, wall_center_sketches
            )
            if not hit:
                hit_from = "lower"
                hit, hit_entry = _intersect_ray_with_faces_onface(
                    lower, wall_dir, wall_faces, wall_center_sketches
                )
            if not hit:
                hit_from = "mid"
                hit, hit_entry = _intersect_ray_with_faces_onface(
                    mid, wall_dir, wall_faces, wall_center_sketches
                )
            if not hit:
                neg_dir = adsk.core.Vector3D.create(-wall_dir.x, -wall_dir.y, -wall_dir.z)
                hit_from = "upper_neg"
                hit, hit_entry = _intersect_ray_with_faces_onface(
                    upper, neg_dir, wall_faces, wall_center_sketches
                )
                if not hit:
                    hit_from = "lower_neg"
                    hit, hit_entry = _intersect_ray_with_faces_onface(
                        lower, neg_dir, wall_faces, wall_center_sketches
                    )
                if not hit:
                    hit_from = "mid_neg"
                    hit, hit_entry = _intersect_ray_with_faces_onface(
                        mid, neg_dir, wall_faces, wall_center_sketches
                    )
            if not hit:
                pair_missed += 1
                continue
            if DEBUG_STUB_ARMS:
                _dbg(f"Pair {i}: wall hit from {hit_from}")
            if DEBUG_WALL_MARKERS and wall_center_sketches and hit_entry and hit_marker_radius_u:
                _add_wall_hit_marker(root, hit_entry, hit, hit_marker_radius_u, wall_center_sketches)
            lower_adj, draw_lower = _adjust_lower_for_clearance(
                lower, upper, hit, axis_dir, wall_faces, wall_center_sketches, clearance_u
            )
            pair_hits.append((i, lower_adj, upper, hit, draw_lower))

        if not pair_hits:
            continue

        sk = _create_stub_sketch(stub_comp, face, root)
        if not sk:
            _dbg(f"Skip body='{label}': failed to create stub sketch")
            cols_skipped.append(label)
            continue
        try:
            sk.name = _next_sketch_name(stub_comp, f"Stub Arms - {label}")
        except:
            pass
        _disable_sketch_profiles(sk)
        lines = sk.sketchCurves.sketchLines

        for _, lower, upper, hit, draw_lower in pair_hits:
            try:
                upper_sk = sk.modelToSketchSpace(upper)
                lower_sk = sk.modelToSketchSpace(lower)
                hit_sk = sk.modelToSketchSpace(hit)
            except:
                upper_sk = upper
                lower_sk = lower
                hit_sk = hit
            upper_line = lines.addByTwoPoints(upper_sk, hit_sk)
            _tag_stub_line(upper_line, "FlatBar")
            if draw_lower:
                lower_line = lines.addByTwoPoints(lower_sk, hit_sk)
                _tag_stub_line(lower_line, "EA")
                lines_created += 2
            else:
                lines_created += 1

    for sk in wall_center_sketches.values():
        try:
            sk.deleteMe()
        except:
            pass

    try:
        ctx.app().activeViewport.refresh()
    except:
        pass

    msg = [f"Created {lines_created} stub arm line(s)."]
    if cols_skipped:
        msg.append("Skipped columns:\n  " + "\n  ".join(sorted(set(cols_skipped))))
    if pair_missed:
        msg.append(f"Missed {pair_missed} pair(s) (no wall hit).")
    ctx.ui().messageBox("\n\n".join(msg))


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = StubArmsCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = True
