import adsk.core, adsk.fusion, traceback, os
import smg_context as ctx
import smg_logger as logger


CMD_ID = "PhilsDesignTools_StubArms"
CMD_NAME = "Stub Arms To Wall"
CMD_TOOLTIP = "Create stub arm sketch lines from RHS columns to the wall."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

TOL = 1e-6
ANGLE_TOL = 1e-3
FACE_TOL = 1e-3
DEBUG_STUB_ARMS = True


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
                "RHS columns",
                "Select RHS column bodies"
            )
            sel_cols.addSelectionFilter("Bodies")
            sel_cols.setSelectionLimits(1, 0)

            sel_wall = inputs.addSelectionInput(
                "stub_wall",
                "Wall",
                "Select wall faces or bodies"
            )
            sel_wall.addSelectionFilter("Faces")
            sel_wall.addSelectionFilter("Bodies")
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
            inputs.addValueInput("stub_inboard", "Inboard offset", length_units, v(25.0))

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


def _offset_point(p, d, dist):
    return adsk.core.Point3D.create(
        p.x + d.x * dist,
        p.y + d.y * dist,
        p.z + d.z * dist,
    )


def _closest_face_point(face, point):
    try:
        if hasattr(face.evaluator, "getClosestPointTo"):
            res = face.evaluator.getClosestPointTo(point)
        else:
            res = face.evaluator.getClosestPoint(point)
    except:
        return None
    if isinstance(res, tuple):
        if not res[0]:
            return None
        return res[1]
    return res


def _point_on_face(face, point):
    cp = _closest_face_point(face, point)
    if not cp:
        return False
    return cp.distanceTo(point) <= FACE_TOL


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


def _project_vector_to_plane(vec, plane_normal):
    n_vec = adsk.core.Vector3D.create(plane_normal.x, plane_normal.y, plane_normal.z)
    if n_vec.length < TOL:
        return None
    n_vec.normalize()
    proj = vec.dotProduct(n_vec)
    out = adsk.core.Vector3D.create(
        vec.x - n_vec.x * proj,
        vec.y - n_vec.y * proj,
        vec.z - n_vec.z * proj,
    )
    if out.length < TOL:
        return None
    return out


def _ray_plane_intersection(origin, direction, plane):
    if not plane:
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
    if t <= TOL:
        return None, None
    hit = adsk.core.Point3D.create(
        origin.x + direction.x * t,
        origin.y + direction.y * t,
        origin.z + direction.z * t,
    )
    return hit, t


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


def _intersect_ray_with_face(face, origin, direction):
    if direction.length < TOL:
        return None
    direction = _normalise(direction)

    line = adsk.core.Line3D.create(
        origin,
        adsk.core.Point3D.create(
            origin.x + direction.x,
            origin.y + direction.y,
            origin.z + direction.z,
        )
    )

    hit_pts = []
    try:
        if hasattr(face.evaluator, "intersectWithLine"):
            res = face.evaluator.intersectWithLine(line)
            hit_pts = _extract_points(res)
    except:
        hit_pts = []

    if not hit_pts:
        plane = adsk.core.Plane.cast(face.geometry)
        if plane:
            hit, _ = _ray_plane_intersection(origin, direction, plane)
            if hit and _point_on_face(face, hit):
                hit_pts = [hit]

    best_pt = None
    best_t = None
    for hit in hit_pts:
        if not hit:
            continue
        vec = adsk.core.Vector3D.create(
            hit.x - origin.x,
            hit.y - origin.y,
            hit.z - origin.z,
        )
        t = vec.dotProduct(direction)
        if t <= TOL:
            continue
        if best_t is None or t < best_t:
            best_t = t
            best_pt = hit
    return best_pt


def _intersect_ray_with_faces(origin, direction, faces):
    if direction.length < TOL:
        return None
    direction = _normalise(direction)
    best_pt = None
    best_t = None
    for face in faces:
        hit = _intersect_ray_with_face(face, origin, direction)
        if not hit:
            continue
        vec = adsk.core.Vector3D.create(
            hit.x - origin.x,
            hit.y - origin.y,
            hit.z - origin.z,
        )
        t = vec.dotProduct(direction)
        if t <= TOL:
            continue
        if best_t is None or t < best_t:
            best_t = t
            best_pt = hit
    return best_pt


def _faces_from_body(body):
    faces = []
    try:
        for i in range(body.faces.count):
            faces.append(body.faces.item(i))
    except:
        pass
    return faces


def _closest_wall_point(point, faces):
    best = None
    best_d2 = None
    for face in faces:
        cp = None
        try:
            ev = face.evaluator
            if hasattr(ev, "getClosestPointTo"):
                res = ev.getClosestPointTo(point)
            else:
                res = ev.getClosestPoint(point)
        except:
            res = None
        if res:
            if isinstance(res, tuple):
                if res[0]:
                    cp = res[1]
            else:
                cp = res
        if not cp:
            try:
                plane = adsk.core.Plane.cast(face.geometry)
            except:
                plane = None
            if plane:
                cp = _project_point_to_plane(point, plane.origin, plane.normal)
        if not cp:
            try:
                bb = face.boundingBox
            except:
                bb = None
            if bb:
                minp = bb.minPoint
                maxp = bb.maxPoint
                cp = adsk.core.Point3D.create(
                    (minp.x + maxp.x) * 0.5,
                    (minp.y + maxp.y) * 0.5,
                    (minp.z + maxp.z) * 0.5,
                )
        if not cp:
            continue
        dx = cp.x - point.x
        dy = cp.y - point.y
        dz = cp.z - point.z
        d2 = dx * dx + dy * dy + dz * dz
        if best_d2 is None or d2 < best_d2:
            best_d2 = d2
            best = cp
    return best


def _direction_to_wall(point, axis_dir, wall_faces):
    cp = _closest_wall_point(point, wall_faces)
    if not cp:
        return None
    vec = adsk.core.Vector3D.create(
        cp.x - point.x,
        cp.y - point.y,
        cp.z - point.z,
    )
    if vec.length < TOL:
        return None
    proj = vec.dotProduct(axis_dir)
    dir_vec = adsk.core.Vector3D.create(
        vec.x - axis_dir.x * proj,
        vec.y - axis_dir.y * proj,
        vec.z - axis_dir.z * proj,
    )
    if dir_vec.length < TOL:
        tmp = adsk.core.Vector3D.create(1, 0, 0)
        if abs(tmp.dotProduct(axis_dir)) > 0.9:
            tmp = adsk.core.Vector3D.create(0, 1, 0)
        dir_vec = axis_dir.crossProduct(tmp)
    if dir_vec.length < TOL:
        return None
    dir_vec.normalize()
    if dir_vec.dotProduct(vec) < 0:
        dir_vec.scaleBy(-1)
    return dir_vec


def _pick_front_face(body_faces, axis_dir, wall_dir):
    best_face = None
    best_n = None
    best_dot = -1.0
    for face in body_faces:
        plane = adsk.core.Plane.cast(face.geometry)
        if not plane:
            continue
        n = plane.normal
        if not n or n.length < TOL:
            continue
        n_vec = adsk.core.Vector3D.create(n.x, n.y, n.z)
        n_vec.normalize()
        # Ignore end faces (normal ~ axis).
        if abs(n_vec.dotProduct(axis_dir)) > 0.2:
            continue
        dot = n_vec.dotProduct(wall_dir)
        if dot > best_dot:
            best_dot = dot
            best_face = face
            best_n = n_vec
    if not best_face or not best_n:
        return None, None
    if best_dot < 0:
        best_n.scaleBy(-1)
    return best_face, best_n


def _pick_side_face(body_faces, axis_dir, front_n, wall_point):
    best_face = None
    best_n = None
    best_d = None
    for face in body_faces:
        plane = adsk.core.Plane.cast(face.geometry)
        if not plane:
            continue
        n = plane.normal
        if not n or n.length < TOL:
            continue
        n_vec = adsk.core.Vector3D.create(n.x, n.y, n.z)
        n_vec.normalize()
        # Ignore end faces (normal ~ axis).
        if abs(n_vec.dotProduct(axis_dir)) > 0.2:
            continue
        # Side faces are ~perpendicular to the front face normal.
        if abs(n_vec.dotProduct(front_n)) > 0.2:
            continue
        v = adsk.core.Vector3D.create(
            wall_point.x - plane.origin.x,
            wall_point.y - plane.origin.y,
            wall_point.z - plane.origin.z,
        )
        dist = abs(n_vec.dotProduct(v))
        if best_d is None or dist < best_d:
            best_d = dist
            best_face = face
            best_n = n_vec
    return best_face, best_n


def _collect_bodies(sel_input):
    bodies = {}
    for i in range(sel_input.selectionCount):
        ent = sel_input.selection(i).entity
        body = adsk.fusion.BRepBody.cast(ent)
        if not body:
            continue
        if not body.isSolid:
            continue
        try:
            key = body.entityToken
        except:
            key = None
        if not key:
            try:
                key = body.tempId
            except:
                key = id(body)
        bodies[key] = body
    return list(bodies.values())


def _collect_wall_faces(sel_input):
    faces = {}
    for i in range(sel_input.selectionCount):
        ent = sel_input.selection(i).entity
        face = adsk.fusion.BRepFace.cast(ent)
        if face:
            try:
                key = face.entityToken
            except:
                key = id(face)
            faces[key] = face
            continue
        body = adsk.fusion.BRepBody.cast(ent)
        if body:
            for j in range(body.faces.count):
                f = body.faces.item(j)
                try:
                    key = f.entityToken
                except:
                    key = id(f)
                faces[key] = f
    return list(faces.values())


def _next_sketch_name(root, base):
    existing = set()
    for i in range(root.sketches.count):
        try:
            existing.add(root.sketches.item(i).name)
        except:
            pass
    if base not in existing:
        return base
    idx = 2
    while f"{base} {idx}" in existing:
        idx += 1
    return f"{base} {idx}"


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
        ctx.ui().messageBox("Select at least one RHS column body.")
        return
    if not sel_wall or sel_wall.selectionCount == 0:
        ctx.ui().messageBox("Select one or more wall faces or bodies.")
        return

    def mm_val(cid):
        v = adsk.core.ValueCommandInput.cast(inputs.itemById(cid))
        return um.convert(v.value, um.internalUnits, "mm")

    bottom_mm = mm_val("stub_bottom")
    top_mm = mm_val("stub_top")
    inboard_mm = mm_val("stub_inboard")
    count = count_in.value if count_in else 6

    bottom_u = um.convert(bottom_mm, "mm", um.internalUnits)
    top_u = um.convert(top_mm, "mm", um.internalUnits)
    inboard_u = um.convert(inboard_mm, "mm", um.internalUnits)

    bodies = _collect_bodies(sel_cols)
    faces = _collect_wall_faces(sel_wall)
    if not bodies:
        ctx.ui().messageBox("No valid RHS bodies selected.")
        return
    if not faces:
        ctx.ui().messageBox("No valid wall faces found.")
        return

    _dbg(f"Selected bodies={len(bodies)}, wall_faces={len(faces)}, points={count}")

    logger.log_command(
        CMD_NAME,
        {
            "bodies": len(bodies),
            "wall_faces": len(faces),
            "points": count,
            "bottom_mm": bottom_mm,
            "top_mm": top_mm,
            "inboard_mm": inboard_mm,
        },
    )

    sk = root.sketches.add(root.xYConstructionPlane)
    sk.is3D = True
    try:
        sk.name = _next_sketch_name(root, "StubArms")
    except:
        pass
    lines = sk.sketchCurves.sketchLines

    lines_created = 0
    cols_skipped = []
    pair_missed = 0

    for body in bodies:
        axis = _get_body_axis(body)
        axis_dir, bottom, top, length = _axis_endpoints(body, axis) if axis else (None, None, None, None)
        if not axis_dir or not bottom or not top or not length:
            _dbg(f"Skip body='{body.name if body else ''}': axis/length invalid")
            cols_skipped.append(body.name or "<unnamed>")
            continue
        body_faces = _faces_from_body(body)
        if not body_faces:
            _dbg(f"Skip body='{body.name if body else ''}': no faces")
            cols_skipped.append(body.name or "<unnamed>")
            continue

        center = _get_body_center(body)
        if not center:
            _dbg(f"Skip body='{body.name if body else ''}': no center")
            cols_skipped.append(body.name or "<unnamed>")
            continue
        wall_cp = _closest_wall_point(center, faces)
        if not wall_cp:
            _dbg(f"Skip body='{body.name if body else ''}': no wall point")
            cols_skipped.append(body.name or "<unnamed>")
            continue
        wall_vec = adsk.core.Vector3D.create(
            wall_cp.x - center.x,
            wall_cp.y - center.y,
            wall_cp.z - center.z,
        )
        if wall_vec.length < TOL:
            _dbg(f"Skip body='{body.name if body else ''}': wall point too close")
            cols_skipped.append(body.name or "<unnamed>")
            continue
        wall_proj = wall_vec.dotProduct(axis_dir)
        wall_dir = adsk.core.Vector3D.create(
            wall_vec.x - axis_dir.x * wall_proj,
            wall_vec.y - axis_dir.y * wall_proj,
            wall_vec.z - axis_dir.z * wall_proj,
        )
        if wall_dir.length < TOL:
            wall_dir = _normalise(wall_vec)
        else:
            wall_dir.normalize()

        front_face, front_n = _pick_front_face(body_faces, axis_dir, wall_dir)
        if not front_face or not front_n:
            _dbg(f"Skip body='{body.name if body else ''}': no front face")
            cols_skipped.append(body.name or "<unnamed>")
            continue

        side_face, side_n = _pick_side_face(body_faces, axis_dir, front_n, wall_cp)
        if not side_face or not side_n:
            _dbg(f"Skip body='{body.name if body else ''}': no side face")
            cols_skipped.append(body.name or "<unnamed>")
            continue

        side_plane = adsk.core.Plane.cast(side_face.geometry)
        if not side_plane:
            _dbg(f"Skip body='{body.name if body else ''}': side face not planar")
            cols_skipped.append(body.name or "<unnamed>")
            continue

        front_dir = _project_vector_to_plane(front_n, side_n)
        if not front_dir:
            _dbg(f"Skip body='{body.name if body else ''}': front dir not in side plane")
            cols_skipped.append(body.name or "<unnamed>")
            continue
        front_dir.normalize()
        if front_dir.dotProduct(wall_dir) < 0:
            front_dir.scaleBy(-1)

        inboard_dir = adsk.core.Vector3D.create(-front_dir.x, -front_dir.y, -front_dir.z)

        span = length - bottom_u - top_u
        if count < 2 or span <= TOL:
            _dbg(f"Skip body='{body.name if body else ''}': span={span:.4f} count={count}")
            cols_skipped.append(body.name or "<unnamed>")
            continue
        spacing = span / float(count - 1)
        if spacing <= TOL:
            _dbg(f"Skip body='{body.name if body else ''}': spacing={spacing:.4f}")
            cols_skipped.append(body.name or "<unnamed>")
            continue

        points = []
        for i in range(count):
            dist = bottom_u + spacing * i
            points.append(_offset_point(bottom, axis_dir, dist))

        _dbg(
            f"Body='{body.name if body else ''}' axis=({axis_dir.x:.4f},{axis_dir.y:.4f},{axis_dir.z:.4f}) "
            f"len={length:.4f} bottom=({bottom.x:.4f},{bottom.y:.4f},{bottom.z:.4f}) "
            f"top=({top.x:.4f},{top.y:.4f},{top.z:.4f}) spacing={spacing:.4f}"
        )
        _dbg(
            f"Body='{body.name if body else ''}' wall_dir=({wall_dir.x:.4f},{wall_dir.y:.4f},{wall_dir.z:.4f})"
        )
        _dbg(
            f"Body='{body.name if body else ''}' front_n=({front_n.x:.4f},{front_n.y:.4f},{front_n.z:.4f})"
        )
        _dbg(
            f"Body='{body.name if body else ''}' side_n=({side_n.x:.4f},{side_n.y:.4f},{side_n.z:.4f})"
        )
        _dbg(
            f"Body='{body.name if body else ''}' front_dir=({front_dir.x:.4f},{front_dir.y:.4f},{front_dir.z:.4f})"
        )

        test_pt = _project_point_to_plane(center, side_plane.origin, side_n)
        if test_pt:
            test_start = _offset_point(test_pt, inboard_dir, inboard_u)
            test_hit = _intersect_ray_with_faces(test_start, front_dir, faces)
            if not test_hit:
                front_dir.scaleBy(-1)
                inboard_dir.scaleBy(-1)
                _dbg(f"Body='{body.name if body else ''}': flipped front_dir to hit wall")

        for i in range(len(points) - 1):
            upper = points[i]
            lower = points[i + 1]

            upper_on = _project_point_to_plane(upper, side_plane.origin, side_n)
            lower_on = _project_point_to_plane(lower, side_plane.origin, side_n)
            if not upper_on or not lower_on:
                _dbg(f"Pair {i}: no column plane projection body='{body.name if body else ''}'")
                pair_missed += 1
                continue

            upper_start = _offset_point(upper_on, inboard_dir, inboard_u)
            lower_start = _offset_point(lower_on, inboard_dir, inboard_u)

            wall_hit = _intersect_ray_with_faces(upper_start, front_dir, faces)
            if not wall_hit:
                _dbg(f"Pair {i}: no wall hit along front_dir body='{body.name if body else ''}'")
                pair_missed += 1
                continue

            lines.addByTwoPoints(upper_start, wall_hit)
            lines.addByTwoPoints(lower_start, wall_hit)
            lines_created += 2

    try:
        ctx.app().activeViewport.refresh()
    except:
        pass

    msg = [f"Created {lines_created} stub arm line(s) in sketch '{sk.name}'."]
    if cols_skipped:
        msg.append("Skipped columns:\n  " + "\n  ".join(sorted(set(cols_skipped))))
    if pair_missed:
        msg.append(f"Missed {pair_missed} pair(s) (no wall hit or body hit).")
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
