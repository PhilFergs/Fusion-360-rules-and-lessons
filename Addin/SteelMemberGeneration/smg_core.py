import adsk.core, adsk.fusion, math, traceback
import smg_context as ctx

# Defaults (mm)
DEFAULT_FLANGE_LENGTH_MM   = 50.0
DEFAULT_THICKNESS_MM       = 3.0
DEFAULT_EXTRA_END_MM       = 20.0
DEFAULT_HOLE_DIAMETER_MM   = 13.0
DEFAULT_HOLE_GAUGE_MM      = 25.0

DEFAULT_SHS_SIZE_MM        = 100.0
DEFAULT_SHS_THICKNESS_MM   = 3.0

DEFAULT_RHS_WIDTH_MM       = 100.0
DEFAULT_RHS_DEPTH_MM       = 50.0
DEFAULT_RHS_THICKNESS_MM   = 3.0


# ----- basic helpers ---------------------------------------------------------
def get_design():
    return adsk.fusion.Design.cast(ctx.app().activeProduct)


def get_root():
    design = get_design()
    return design.rootComponent


def units_manager():
    return get_design().unitsManager


def collect_lines_from_selection_input(sel_input):
    out = []
    if not sel_input:
        return out
    for i in range(sel_input.selectionCount):
        ent = sel_input.selection(i).entity
        sl = adsk.fusion.SketchLine.cast(ent)
        if sl:
            out.append(sl)
    return out


def find_next_index(design, prefix: str) -> int:
    max_idx = 0
    for comp in design.allComponents:
        name = comp.name
        if not name.startswith(prefix):
            continue
        digits = ''
        for ch in name[len(prefix):]:
            if ch.isdigit():
                digits += ch
            else:
                break
        if digits:
            try:
                idx = int(digits)
                max_idx = max(max_idx, idx)
            except:
                pass
    return max_idx + 1


def create_orientation_matrix(line_mid, x_base, y_axis, z_base, angle_deg, offset_x_u):
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)

    x_rot = adsk.core.Vector3D.create(
        x_base.x * c + z_base.x * s,
        x_base.y * c + z_base.y * s,
        x_base.z * c + z_base.z * s
    )
    z_rot = adsk.core.Vector3D.create(
        -x_base.x * s + z_base.x * c,
        -x_base.y * s + z_base.y * c,
        -x_base.z * s + z_base.z * c
    )
    x_rot.normalize()
    z_rot.normalize()

    origin = adsk.core.Point3D.create(
        line_mid.x - x_rot.x * offset_x_u,
        line_mid.y - x_rot.y * offset_x_u,
        line_mid.z - x_rot.z * offset_x_u
    )

    m = adsk.core.Matrix3D.create()
    m.setWithCoordinateSystem(origin, x_rot, y_axis, z_rot)
    return m


# ----- EA generation ---------------------------------------------------------
def generate_ea_from_lines(lines,
                           flange_mm, thickness_mm, extra_mm,
                           hole_d_mm, hole_g_mm, fillet_mm,
                           angle_deg):
    if not lines:
        ctx.ui().messageBox("Please select at least one sketch line.")
        return

    design = get_design()
    root = get_root()
    um = units_manager()

    next_idx = find_next_index(design, "EA")
    created = 0

    for line in lines:
        if _create_ea_for_line(design, root, um, line, next_idx,
                               flange_mm, thickness_mm, extra_mm,
                               hole_d_mm, hole_g_mm, fillet_mm,
                               angle_deg):
            created += 1
            next_idx += 1

    ctx.ui().messageBox(f"Created {created} EA components.")


def _create_ea_for_line(design, root, um, sk_line, idx,
                        flange_mm, thickness_mm, extra_mm,
                        hole_d_mm, hole_g_mm, fillet_mm,
                        angle_deg):
    sp = sk_line.startSketchPoint.worldGeometry
    ep = sk_line.endSketchPoint.worldGeometry
    cc_len_u = sp.distanceTo(ep)
    if cc_len_u <= 0:
        return False

    mid = adsk.core.Point3D.create(
        (sp.x + ep.x) / 2.0,
        (sp.y + ep.y) / 2.0,
        (sp.z + ep.z) / 2.0
    )

    y_axis = adsk.core.Vector3D.create(
        ep.x - sp.x, ep.y - sp.y, ep.z - sp.z
    )
    y_axis.normalize()

    tmp = adsk.core.Vector3D.create(1, 0, 0)
    if abs(tmp.dotProduct(y_axis)) > 0.99:
        tmp = adsk.core.Vector3D.create(0, 1, 0)
    x_base = y_axis.crossProduct(tmp)
    x_base.normalize()
    z_base = x_base.crossProduct(y_axis)
    z_base.normalize()

    hole_g_u = um.convert(hole_g_mm, "mm", um.internalUnits)
    mat = create_orientation_matrix(mid, x_base, y_axis, z_base, angle_deg, hole_g_u)
    occ = root.occurrences.addNewComponent(mat)
    comp = occ.component

    cc_mm = um.convert(cc_len_u, um.internalUnits, "mm")
    comp.name = (
        f"EA{idx}-{int(round(cc_mm))}mm-"
        f"{int(round(flange_mm))}x{int(round(flange_mm))}x{int(round(thickness_mm))}"
    )

    body = _build_ea_geometry(design, comp, um, cc_len_u,
                              flange_mm, thickness_mm, extra_mm,
                              hole_d_mm, hole_g_mm, fillet_mm)

    _apply_steel_material(comp, body)
    _apply_steel_color(body)
    try:
        ctx.app().activeViewport.refresh()
    except:
        pass
    return True


def _build_ea_geometry(design, comp, um, cc_len_u,
                       flange_mm, thickness_mm, extra_mm,
                       hole_d_mm, hole_g_mm, fillet_mm):
    sketches = comp.sketches
    extrudes = comp.features.extrudeFeatures

    flange_u = um.convert(flange_mm, "mm", um.internalUnits)
    thk_u    = um.convert(thickness_mm, "mm", um.internalUnits)
    extra_u  = um.convert(extra_mm, "mm", um.internalUnits)
    hole_d_u = um.convert(hole_d_mm, "mm", um.internalUnits)
    hole_g_u = um.convert(hole_g_mm, "mm", um.internalUnits)
    fillet_u = um.convert(fillet_mm, "mm", um.internalUnits)

    length_total_u = cc_len_u + 2 * extra_u

    xz = comp.xZConstructionPlane
    sk = sketches.add(xz)
    lines = sk.sketchCurves.sketchLines

    A = adsk.core.Point3D.create(0,        0,      0)
    B = adsk.core.Point3D.create(flange_u, 0,      0)
    C = adsk.core.Point3D.create(flange_u, thk_u,  0)
    D = adsk.core.Point3D.create(thk_u,    thk_u,  0)
    E = adsk.core.Point3D.create(thk_u,    flange_u, 0)
    F = adsk.core.Point3D.create(0,        flange_u, 0)

    lines.addByTwoPoints(A, B)
    lines.addByTwoPoints(B, C)
    lines.addByTwoPoints(C, D)
    lines.addByTwoPoints(D, E)
    lines.addByTwoPoints(E, F)
    lines.addByTwoPoints(F, A)

    prof = sk.profiles.item(0)
    ext_in = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setSymmetricExtent(adsk.core.ValueInput.createByReal(length_total_u), True)
    ext = extrudes.add(ext_in)
    body = ext.bodies.item(0)

    _apply_root_fillet(comp, body, thk_u, fillet_u)
    _cut_ea_holes(comp, body, cc_len_u, hole_d_u, hole_g_u, flange_u)
    return body


def _cut_ea_holes(comp, body, cc_len_u, hole_d_u, hole_g_u, flange_u):
    sketches = comp.sketches
    extrudes = comp.features.extrudeFeatures

    xy = comp.xYConstructionPlane
    sk = sketches.add(xy)
    circles = sk.sketchCurves.sketchCircles

    half = cc_len_u / 2.0
    r = hole_d_u / 2.0
    circles.addByCenterRadius(adsk.core.Point3D.create(hole_g_u, -half, 0), r)
    circles.addByCenterRadius(adsk.core.Point3D.create(hole_g_u,  half, 0), r)

    profs = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        profs.add(sk.profiles.item(i))

    cut_in = extrudes.createInput(profs, adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut_in.participantBodies = [body]
    cut_in.setSymmetricExtent(adsk.core.ValueInput.createByReal(flange_u * 2.0), True)
    extrudes.add(cut_in)


def _apply_root_fillet(comp, body, thk_u, rad_u):
    fillets = comp.features.filletFeatures
    root_v = None
    for v in body.vertices:
        p = v.geometry
        if abs(p.x) < 1e-6 and abs(p.z) < 1e-6 and abs(p.y) < thk_u * 0.5:
            root_v = v
            break
    if not root_v:
        return

    tol_dir = 1e-6
    tol_pos = thk_u * 0.5
    edges = adsk.core.ObjectCollection.create()
    for e in root_v.edges:
        sv = e.startVertex.geometry
        ev = e.endVertex.geometry
        vertical = (
            abs(sv.x) < tol_pos and
            abs(ev.x) < tol_pos and
            abs(sv.z) < tol_pos and
            abs(ev.z) < tol_pos and
            abs(sv.y - ev.y) > tol_dir
        )
        if vertical:
            edges.add(e)

    if not edges.count:
        return

    fi = fillets.createInput()
    rad = adsk.core.ValueInput.createByReal(rad_u)
    if hasattr(fi, "edgeSets"):
        fi.edgeSets.addConstantRadiusEdgeSet(edges, rad, True)
    else:
        fi.addConstantRadiusEdgeSet(edges, rad, True)
    fillets.add(fi)


# ----- SHS / RHS generation ---------------------------------------------------
def _pick_ring_profile(sketch):
    prof = None
    for p in sketch.profiles:
        loops = getattr(p, "profileLoops", None)
        if loops and loops.count > 1:
            prof = p
            break
    if prof:
        return prof

    max_area = -1.0
    for p in sketch.profiles:
        try:
            area = p.areaProperties().area
        except:
            continue
        if area > max_area:
            max_area = area
            prof = p
    return prof


def _compute_corner_radii_from_thickness(thickness_mm, thk_u):
    # AS/NZS 1163-ish: outer radius ~2t or 2.5t, inner ~1t
    if thickness_mm <= 3.0:
        outer = 2.0 * thk_u
    else:
        outer = 2.5 * thk_u
    inner = 1.0 * thk_u
    return outer, inner


def _apply_shs_corner_fillets(comp, body, size_u, inner_u, thk_u, thickness_mm):
    fillets = comp.features.filletFeatures
    outer_r, inner_r = _compute_corner_radii_from_thickness(thickness_mm, thk_u)

    half = size_u / 2.0
    tol = thk_u * 0.1

    edges_outer = adsk.core.ObjectCollection.create()
    edges_inner = adsk.core.ObjectCollection.create()

    for e in body.edges:
        sv = e.startVertex.geometry
        ev = e.endVertex.geometry
        if abs(sv.x - ev.x) > 1e-6 or abs(sv.z - ev.z) > 1e-6:
            continue
        if abs(sv.y - ev.y) < 1e-6:
            continue
        x = sv.x
        z = sv.z
        if abs(abs(x) - half) < tol and abs(abs(z) - half) < tol:
            edges_outer.add(e)
        elif abs(abs(x) - inner_u) < tol and abs(abs(z) - inner_u) < tol:
            edges_inner.add(e)

    if edges_outer.count:
        fi = fillets.createInput()
        rad = adsk.core.ValueInput.createByReal(outer_r)
        if hasattr(fi, "edgeSets"):
            fi.edgeSets.addConstantRadiusEdgeSet(edges_outer, rad, True)
        else:
            fi.addConstantRadiusEdgeSet(edges_outer, rad, True)
        fillets.add(fi)

    if edges_inner.count:
        fi = fillets.createInput()
        rad = adsk.core.ValueInput.createByReal(inner_r)
        if hasattr(fi, "edgeSets"):
            fi.edgeSets.addConstantRadiusEdgeSet(edges_inner, rad, True)
        else:
            fi.addConstantRadiusEdgeSet(edges_inner, rad, True)
        fillets.add(fi)


def _apply_rhs_corner_fillets(comp, body,
                              half_w_u, half_d_u,
                              inner_w_u, inner_d_u,
                              thk_u, thickness_mm):
    fillets = comp.features.filletFeatures
    outer_r, inner_r = _compute_corner_radii_from_thickness(thickness_mm, thk_u)

    tol = thk_u * 0.1
    edges_outer = adsk.core.ObjectCollection.create()
    edges_inner = adsk.core.ObjectCollection.create()

    for e in body.edges:
        sv = e.startVertex.geometry
        ev = e.endVertex.geometry
        if abs(sv.x - ev.x) > 1e-6 or abs(sv.z - ev.z) > 1e-6:
            continue
        if abs(sv.y - ev.y) < 1e-6:
            continue
        x = sv.x
        z = sv.z
        if abs(abs(x) - half_w_u) < tol and abs(abs(z) - half_d_u) < tol:
            edges_outer.add(e)
        elif abs(abs(x) - inner_w_u) < tol and abs(abs(z) - inner_d_u) < tol:
            edges_inner.add(e)

    if edges_outer.count:
        fi = fillets.createInput()
        rad = adsk.core.ValueInput.createByReal(outer_r)
        if hasattr(fi, "edgeSets"):
            fi.edgeSets.addConstantRadiusEdgeSet(edges_outer, rad, True)
        else:
            fi.addConstantRadiusEdgeSet(edges_outer, rad, True)
        fillets.add(fi)

    if edges_inner.count:
        fi = fillets.createInput()
        rad = adsk.core.ValueInput.createByReal(inner_r)
        if hasattr(fi, "edgeSets"):
            fi.edgeSets.addConstantRadiusEdgeSet(edges_inner, rad, True)
        else:
            fi.addConstantRadiusEdgeSet(edges_inner, rad, True)
        fillets.add(fi)


def generate_shs_from_lines(lines,
                            size_mm, thickness_mm, extra_mm,
                            angle_deg):
    if not lines:
        ctx.ui().messageBox("Please select at least one sketch line.")
        return

    design = get_design()
    root = get_root()
    um = units_manager()
    next_idx = find_next_index(design, "SHS")
    created = 0

    for line in lines:
        if _create_shs_for_line(design, root, um, line, next_idx,
                                size_mm, thickness_mm, extra_mm,
                                angle_deg):
            created += 1
            next_idx += 1

    ctx.ui().messageBox(f"Created {created} SHS components.")


def _create_shs_for_line(design, root, um, sk_line, idx,
                         size_mm, thickness_mm, extra_mm,
                         angle_deg):
    sp = sk_line.startSketchPoint.worldGeometry
    ep = sk_line.endSketchPoint.worldGeometry
    cc_len_u = sp.distanceTo(ep)
    if cc_len_u <= 0:
        return False

    mid = adsk.core.Point3D.create(
        (sp.x + ep.x) / 2.0,
        (sp.y + ep.y) / 2.0,
        (sp.z + ep.z) / 2.0
    )
    y_axis = adsk.core.Vector3D.create(
        ep.x - sp.x, ep.y - sp.y, ep.z - sp.z
    )
    y_axis.normalize()

    tmp = adsk.core.Vector3D.create(1, 0, 0)
    if abs(tmp.dotProduct(y_axis)) > 0.99:
        tmp = adsk.core.Vector3D.create(0, 1, 0)
    x_base = y_axis.crossProduct(tmp)
    x_base.normalize()
    z_base = x_base.crossProduct(y_axis)
    z_base.normalize()

    mat = create_orientation_matrix(mid, x_base, y_axis, z_base, angle_deg, 0.0)
    occ = root.occurrences.addNewComponent(mat)
    comp = occ.component

    cc_mm = um.convert(cc_len_u, um.internalUnits, "mm")
    comp.name = (
        f"SHS{idx}-{int(round(cc_mm))}mm-"
        f"{int(round(size_mm))}x{int(round(size_mm))}x{int(round(thickness_mm))}"
    )

    body = _build_shs_geometry(design, comp, um, cc_len_u,
                               size_mm, thickness_mm, extra_mm)
    _apply_steel_material(comp, body)
    _apply_steel_color(body)
    try:
        ctx.app().activeViewport.refresh()
    except:
        pass
    return True


def _build_shs_geometry(design, comp, um, cc_len_u,
                        size_mm, thickness_mm, extra_mm):
    sketches = comp.sketches
    extrudes = comp.features.extrudeFeatures

    size_u  = um.convert(size_mm, "mm", um.internalUnits)
    thk_u   = um.convert(thickness_mm, "mm", um.internalUnits)
    extra_u = um.convert(extra_mm, "mm", um.internalUnits)
    length_total_u = cc_len_u + 2 * extra_u

    half  = size_u / 2.0
    inner = half - thk_u

    xz = comp.xZConstructionPlane
    sk = sketches.add(xz)
    lines = sk.sketchCurves.sketchLines

    A = adsk.core.Point3D.create(-half, -half, 0)
    B = adsk.core.Point3D.create( half, -half, 0)
    C = adsk.core.Point3D.create( half,  half, 0)
    D = adsk.core.Point3D.create(-half,  half, 0)
    lines.addByTwoPoints(A, B)
    lines.addByTwoPoints(B, C)
    lines.addByTwoPoints(C, D)
    lines.addByTwoPoints(D, A)

    Ai = adsk.core.Point3D.create(-inner, -inner, 0)
    Bi = adsk.core.Point3D.create( inner, -inner, 0)
    Ci = adsk.core.Point3D.create( inner,  inner, 0)
    Di = adsk.core.Point3D.create(-inner,  inner, 0)
    lines.addByTwoPoints(Ai, Bi)
    lines.addByTwoPoints(Bi, Ci)
    lines.addByTwoPoints(Ci, Di)
    lines.addByTwoPoints(Di, Ai)

    prof = _pick_ring_profile(sk)
    if not prof:
        raise RuntimeError("Failed to find SHS wall profile.")

    ext_in = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setSymmetricExtent(adsk.core.ValueInput.createByReal(length_total_u), True)
    ext = extrudes.add(ext_in)
    body = ext.bodies.item(0)

    _apply_shs_corner_fillets(comp, body, size_u, inner, thk_u, thickness_mm)
    return body


def generate_rhs_from_lines(lines,
                            width_mm, depth_mm, thickness_mm, extra_mm,
                            angle_deg):
    if not lines:
        ctx.ui().messageBox("Please select at least one sketch line.")
        return

    design = get_design()
    root = get_root()
    um = units_manager()
    next_idx = find_next_index(design, "RHS")
    created = 0

    for line in lines:
        if _create_rhs_for_line(design, root, um, line, next_idx,
                                width_mm, depth_mm, thickness_mm, extra_mm,
                                angle_deg):
            created += 1
            next_idx += 1

    ctx.ui().messageBox(f"Created {created} RHS components.")


def _create_rhs_for_line(design, root, um, sk_line, idx,
                         width_mm, depth_mm, thickness_mm, extra_mm,
                         angle_deg):
    sp = sk_line.startSketchPoint.worldGeometry
    ep = sk_line.endSketchPoint.worldGeometry
    cc_len_u = sp.distanceTo(ep)
    if cc_len_u <= 0:
        return False

    mid = adsk.core.Point3D.create(
        (sp.x + ep.x) / 2.0,
        (sp.y + ep.y) / 2.0,
        (sp.z + ep.z) / 2.0
    )

    y_axis = adsk.core.Vector3D.create(
        ep.x - sp.x, ep.y - sp.y, ep.z - sp.z
    )
    y_axis.normalize()

    tmp = adsk.core.Vector3D.create(1, 0, 0)
    if abs(tmp.dotProduct(y_axis)) > 0.99:
        tmp = adsk.core.Vector3D.create(0, 1, 0)
    x_base = y_axis.crossProduct(tmp)
    x_base.normalize()
    z_base = x_base.crossProduct(y_axis)
    z_base.normalize()

    mat = create_orientation_matrix(mid, x_base, y_axis, z_base, angle_deg, 0.0)
    occ = root.occurrences.addNewComponent(mat)
    comp = occ.component

    cc_mm = um.convert(cc_len_u, um.internalUnits, "mm")
    comp.name = (
        f"RHS{idx}-{int(round(cc_mm))}mm-"
        f"{int(round(width_mm))}x{int(round(depth_mm))}x{int(round(thickness_mm))}"
    )

    body = _build_rhs_geometry(design, comp, um, cc_len_u,
                               width_mm, depth_mm, thickness_mm, extra_mm)
    _apply_steel_material(comp, body)
    _apply_steel_color(body)
    try:
        ctx.app().activeViewport.refresh()
    except:
        pass
    return True


def _build_rhs_geometry(design, comp, um, cc_len_u,
                        width_mm, depth_mm, thickness_mm, extra_mm):
    sketches = comp.sketches
    extrudes = comp.features.extrudeFeatures

    width_u = um.convert(width_mm, "mm", um.internalUnits)
    depth_u = um.convert(depth_mm, "mm", um.internalUnits)
    thk_u   = um.convert(thickness_mm, "mm", um.internalUnits)
    extra_u = um.convert(extra_mm, "mm", um.internalUnits)
    length_total_u = cc_len_u + 2 * extra_u

    half_w  = width_u / 2.0
    half_d  = depth_u / 2.0
    inner_w = half_w - thk_u
    inner_d = half_d - thk_u

    xz = comp.xZConstructionPlane
    sk = sketches.add(xz)
    lines = sk.sketchCurves.sketchLines

    A = adsk.core.Point3D.create(-half_w, -half_d, 0)
    B = adsk.core.Point3D.create( half_w, -half_d, 0)
    C = adsk.core.Point3D.create( half_w,  half_d, 0)
    D = adsk.core.Point3D.create(-half_w,  half_d, 0)
    lines.addByTwoPoints(A, B)
    lines.addByTwoPoints(B, C)
    lines.addByTwoPoints(C, D)
    lines.addByTwoPoints(D, A)

    Ai = adsk.core.Point3D.create(-inner_w, -inner_d, 0)
    Bi = adsk.core.Point3D.create( inner_w, -inner_d, 0)
    Ci = adsk.core.Point3D.create( inner_w,  inner_d, 0)
    Di = adsk.core.Point3D.create(-inner_w,  inner_d, 0)
    lines.addByTwoPoints(Ai, Bi)
    lines.addByTwoPoints(Bi, Ci)
    lines.addByTwoPoints(Ci, Di)
    lines.addByTwoPoints(Di, Ai)

    prof = _pick_ring_profile(sk)
    if not prof:
        raise RuntimeError("Failed to find RHS wall profile.")

    ext_in = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setSymmetricExtent(adsk.core.ValueInput.createByReal(length_total_u), True)
    ext = extrudes.add(ext_in)
    body = ext.bodies.item(0)

    _apply_rhs_corner_fillets(comp, body, half_w, half_d, inner_w, inner_d, thk_u, thickness_mm)
    return body


# ----- material & appearance --------------------------------------------------
def _apply_steel_material(comp, body):
    try:
        design = get_design()
        mats = design.materials
        steel = mats.itemByName("Steel")
        if not steel:
            lib = ctx.app().materialLibraries.item(0)
            for i in range(lib.materials.count):
                m = lib.materials.item(i)
                if "steel" in m.name.lower():
                    steel = m
                    break
        if steel:
            body.material = steel
    except:
        pass


def _apply_steel_color(body):
    try:
        design = get_design()
        apps = design.appearances
        app = apps.itemByName("EA Steel Color")
        if not app:
            lib = ctx.app().materialLibraries.item(0)
            app = apps.addByColor("EA Steel Color", lib, adsk.core.Color.create(40, 60, 85))
        body.appearance = app
    except:
        pass
