import adsk.core, adsk.fusion, math
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

UB_SECTIONS = [
    {"name": "150 UB 14", "depth": 150.0, "width": 75.0, "flange": 7.0, "web": 5.0},
    {"name": "150 UB 18", "depth": 155.0, "width": 75.0, "flange": 9.5, "web": 6.0},
    {"name": "180 UB 16.1", "depth": 173.0, "width": 90.0, "flange": 7.0, "web": 4.5},
    {"name": "180 UB 18.1", "depth": 175.0, "width": 90.0, "flange": 8.0, "web": 5.0},
    {"name": "180 UB 22.2", "depth": 179.0, "width": 90.0, "flange": 10.0, "web": 6.0},
    {"name": "200 UB 18.2", "depth": 198.0, "width": 99.0, "flange": 7.0, "web": 4.5},
    {"name": "200 UB 22.2", "depth": 202.0, "width": 133.0, "flange": 7.0, "web": 5.0},
    {"name": "200 UB 25.4", "depth": 203.0, "width": 133.0, "flange": 7.8, "web": 5.8},
    {"name": "200 UB 29.8", "depth": 207.0, "width": 134.0, "flange": 9.6, "web": 6.3},
    {"name": "250 UB 25.7", "depth": 248.0, "width": 124.0, "flange": 8.0, "web": 5.0},
    {"name": "250 UB 31.4", "depth": 252.0, "width": 146.0, "flange": 8.6, "web": 6.1},
    {"name": "250 UB 37.3", "depth": 256.0, "width": 146.0, "flange": 10.9, "web": 6.4},
    {"name": "310 UB 32", "depth": 298.0, "width": 149.0, "flange": 8.0, "web": 5.5},
    {"name": "310 UB 40.4", "depth": 304.0, "width": 165.0, "flange": 10.2, "web": 6.1},
    {"name": "310 UB 46.2", "depth": 307.0, "width": 166.0, "flange": 11.8, "web": 6.7},
    {"name": "360 UB 44.7", "depth": 352.0, "width": 171.0, "flange": 9.7, "web": 6.9},
    {"name": "360 UB 50.7", "depth": 356.0, "width": 171.0, "flange": 11.5, "web": 7.3},
    {"name": "360 UB 56.7", "depth": 359.0, "width": 172.0, "flange": 13.0, "web": 8.0},
    {"name": "410 UB 53.7", "depth": 403.0, "width": 178.0, "flange": 10.9, "web": 7.6},
    {"name": "410 UB 59.7", "depth": 406.0, "width": 178.0, "flange": 12.8, "web": 7.8},
    {"name": "460 UB 67.1", "depth": 454.0, "width": 190.0, "flange": 12.7, "web": 8.5},
    {"name": "460 UB 74.6", "depth": 457.0, "width": 190.0, "flange": 14.5, "web": 9.1},
    {"name": "460 UB 82.1", "depth": 460.0, "width": 191.0, "flange": 16.0, "web": 9.9},
    {"name": "530 UB 82", "depth": 528.0, "width": 209.0, "flange": 13.2, "web": 9.6},
    {"name": "530 UB 92.4", "depth": 533.0, "width": 209.0, "flange": 15.6, "web": 10.2},
    {"name": "610 UB 101", "depth": 602.0, "width": 228.0, "flange": 14.8, "web": 10.6},
    {"name": "610 UB 113", "depth": 607.0, "width": 228.0, "flange": 17.3, "web": 11.2},
    {"name": "610 UB 125", "depth": 612.0, "width": 229.0, "flange": 19.6, "web": 11.9},
]

PFC_SECTIONS = [
    {"name": "75 PFC", "depth": 75.0, "width": 40.0, "flange": 6.1, "web": 3.8},
    {"name": "100 PFC", "depth": 100.0, "width": 50.0, "flange": 6.7, "web": 4.2},
    {"name": "125 PFC", "depth": 125.0, "width": 65.0, "flange": 7.5, "web": 4.7},
    {"name": "150 PFC", "depth": 150.0, "width": 75.0, "flange": 9.5, "web": 6.0},
    {"name": "180 PFC", "depth": 180.0, "width": 75.0, "flange": 11.0, "web": 6.0},
    {"name": "200 PFC", "depth": 200.0, "width": 75.0, "flange": 12.0, "web": 6.0},
    {"name": "230 PFC", "depth": 230.0, "width": 75.0, "flange": 12.0, "web": 6.5},
    {"name": "250 PFC", "depth": 250.0, "width": 90.0, "flange": 15.0, "web": 8.0},
    {"name": "300 PFC", "depth": 300.0, "width": 90.0, "flange": 16.0, "web": 8.0},
    {"name": "380 PFC", "depth": 380.0, "width": 100.0, "flange": 17.5, "web": 10.0},
]

C_CHANNEL_SECTIONS = [
    {"name": "C100.10", "depth": 102.0, "width": 51.0, "thickness": 1.0, "lip": 12.5},
    {"name": "C100.12", "depth": 102.0, "width": 51.0, "thickness": 1.2, "lip": 13.0},
    {"name": "C100.15", "depth": 102.0, "width": 51.0, "thickness": 1.5, "lip": 14.0},
    {"name": "C100.19", "depth": 102.0, "width": 51.0, "thickness": 1.9, "lip": 15.0},
    {"name": "C150.10", "depth": 152.0, "width": 64.0, "thickness": 1.0, "lip": 14.5},
    {"name": "C150.12", "depth": 152.0, "width": 64.0, "thickness": 1.2, "lip": 15.0},
    {"name": "C150.15", "depth": 152.0, "width": 64.0, "thickness": 1.5, "lip": 16.0},
    {"name": "C150.19", "depth": 152.0, "width": 64.0, "thickness": 1.9, "lip": 17.0},
    {"name": "C150.24", "depth": 152.0, "width": 64.0, "thickness": 2.4, "lip": 18.5},
    {"name": "C200.15", "depth": 203.0, "width": 76.0, "thickness": 1.5, "lip": 16.0},
    {"name": "C200.19", "depth": 203.0, "width": 76.0, "thickness": 1.9, "lip": 19.5},
    {"name": "C200.24", "depth": 203.0, "width": 76.0, "thickness": 2.4, "lip": 21.0},
    {"name": "C250.15", "depth": 254.0, "width": 76.0, "thickness": 1.5, "lip": 15.5},
    {"name": "C250.19", "depth": 254.0, "width": 76.0, "thickness": 1.9, "lip": 19.0},
    {"name": "C250.24", "depth": 254.0, "width": 76.0, "thickness": 2.4, "lip": 20.5},
]


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


def set_occurrence_component_name(occ, comp, target_name: str) -> bool:
    renamed = False
    for entity in (occ, comp):
        if entity is None:
            continue
        try:
            if entity.name != target_name:
                entity.name = target_name
            renamed = True
        except:
            pass
    return renamed


def _clean_description_number(value):
    try:
        num = float(value)
    except:
        return str(value)
    if abs(num - round(num)) < 1e-6:
        return str(int(round(num)))
    return f"{num:.1f}".rstrip("0").rstrip(".")


def _profile_description(family, *dims):
    return f"{family} " + " x ".join(_clean_description_number(dim) for dim in dims)


def _set_component_description(comp, description):
    if comp is None or not description:
        return
    try:
        comp.description = description
    except:
        pass


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
                           angle_deg,
                           holes_enabled=True,
                           include_profile_in_name=False):
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
                               angle_deg, holes_enabled, include_profile_in_name):
            created += 1
            next_idx += 1

    ctx.ui().messageBox(f"Created {created} EA components.")


def _create_ea_for_line(design, root, um, sk_line, idx,
                        flange_mm, thickness_mm, extra_mm,
                        hole_d_mm, hole_g_mm, fillet_mm,
                        angle_deg, holes_enabled, include_profile_in_name):
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

    comp_name = f"EA{idx}"
    if include_profile_in_name:
        comp_name += (
            f"-{int(round(flange_mm))}x{int(round(flange_mm))}x{int(round(thickness_mm))}"
        )
    set_occurrence_component_name(occ, comp, comp_name)
    _set_component_description(
        comp,
        _profile_description("EA", flange_mm, flange_mm, thickness_mm),
    )

    body = _build_ea_geometry(design, comp, um, cc_len_u,
                              flange_mm, thickness_mm, extra_mm,
                              hole_d_mm, hole_g_mm, fillet_mm,
                              holes_enabled)

    _apply_steel_material(comp, body)
    _apply_steel_color(body)
    try:
        ctx.app().activeViewport.refresh()
    except:
        pass
    return True


def _build_ea_geometry(design, comp, um, cc_len_u,
                       flange_mm, thickness_mm, extra_mm,
                       hole_d_mm, hole_g_mm, fillet_mm,
                       holes_enabled):
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
    if holes_enabled:
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
                            angle_deg,
                            include_profile_in_name=False):
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
                                angle_deg, include_profile_in_name):
            created += 1
            next_idx += 1

    ctx.ui().messageBox(f"Created {created} SHS components.")


def _create_shs_for_line(design, root, um, sk_line, idx,
                         size_mm, thickness_mm, extra_mm,
                         angle_deg, include_profile_in_name):
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

    comp_name = f"SHS{idx}"
    if include_profile_in_name:
        comp_name += (
            f"-{int(round(size_mm))}x{int(round(size_mm))}x{int(round(thickness_mm))}"
        )
    set_occurrence_component_name(occ, comp, comp_name)
    _set_component_description(
        comp,
        _profile_description("SHS", size_mm, size_mm, thickness_mm),
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
                            angle_deg,
                            include_profile_in_name=False):
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
                                angle_deg, include_profile_in_name):
            created += 1
            next_idx += 1

    ctx.ui().messageBox(f"Created {created} RHS components.")


def _create_rhs_for_line(design, root, um, sk_line, idx,
                         width_mm, depth_mm, thickness_mm, extra_mm,
                         angle_deg, include_profile_in_name):
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

    comp_name = f"RHS{idx}"
    if include_profile_in_name:
        comp_name += (
            f"-{int(round(width_mm))}x{int(round(depth_mm))}x{int(round(thickness_mm))}"
        )
    set_occurrence_component_name(occ, comp, comp_name)
    _set_component_description(
        comp,
        _profile_description("RHS", width_mm, depth_mm, thickness_mm),
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


# ----- UB / PFC / C channel generation ---------------------------------------
def _section_by_name(sections, name):
    for section in sections:
        if section.get("name") == name:
            return dict(section)
    return dict(sections[0]) if sections else None


def _compact_section_name(name):
    return (name or "").replace(" ", "")


def _pick_largest_profile(sketch):
    prof = None
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


def _create_polyline_profile(sketch, points_u):
    lines = sketch.sketchCurves.sketchLines
    count = len(points_u)
    for i in range(count):
        x1, z1 = points_u[i]
        x2, z2 = points_u[(i + 1) % count]
        lines.addByTwoPoints(
            adsk.core.Point3D.create(x1, z1, 0),
            adsk.core.Point3D.create(x2, z2, 0),
        )


def _ub_profile_points_mm(section):
    depth = section["depth"]
    width = section["width"]
    flange = section["flange"]
    web = section["web"]
    half_d = depth / 2.0
    half_w = width / 2.0
    half_web = web / 2.0
    return [
        (-half_w, -half_d),
        (half_w, -half_d),
        (half_w, -half_d + flange),
        (half_web, -half_d + flange),
        (half_web, half_d - flange),
        (half_w, half_d - flange),
        (half_w, half_d),
        (-half_w, half_d),
        (-half_w, half_d - flange),
        (-half_web, half_d - flange),
        (-half_web, -half_d + flange),
        (-half_w, -half_d + flange),
    ]


def _pfc_profile_points_mm(section):
    depth = section["depth"]
    width = section["width"]
    flange = section["flange"]
    web = section["web"]
    half_d = depth / 2.0
    half_w = width / 2.0
    left = -half_w
    right = half_w
    web_inner = left + web
    return [
        (left, -half_d),
        (right, -half_d),
        (right, -half_d + flange),
        (web_inner, -half_d + flange),
        (web_inner, half_d - flange),
        (right, half_d - flange),
        (right, half_d),
        (left, half_d),
    ]


def _c_channel_profile_points_mm(section):
    depth = section["depth"]
    width = section["width"]
    thickness = section["thickness"]
    lip = section["lip"]
    half_d = depth / 2.0
    half_w = width / 2.0
    raw = [
        (0.0, -half_d),
        (width, -half_d),
        (width, -half_d + lip),
        (width - thickness, -half_d + lip),
        (width - thickness, -half_d + thickness),
        (thickness, -half_d + thickness),
        (thickness, half_d - thickness),
        (width - thickness, half_d - thickness),
        (width - thickness, half_d - lip),
        (width, half_d - lip),
        (width, half_d),
        (0.0, half_d),
    ]
    return [(x - half_w, z) for x, z in raw]


def _build_section_geometry(comp, um, cc_len_u, points_mm, extra_mm):
    sketches = comp.sketches
    extrudes = comp.features.extrudeFeatures

    points_u = [
        (
            um.convert(x, "mm", um.internalUnits),
            um.convert(z, "mm", um.internalUnits),
        )
        for x, z in points_mm
    ]
    extra_u = um.convert(extra_mm, "mm", um.internalUnits)
    length_total_u = cc_len_u + 2 * extra_u

    sk = sketches.add(comp.xZConstructionPlane)
    _create_polyline_profile(sk, points_u)

    prof = _pick_largest_profile(sk)
    if not prof:
        raise RuntimeError("Failed to find section profile.")

    ext_in = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setSymmetricExtent(adsk.core.ValueInput.createByReal(length_total_u), True)
    ext = extrudes.add(ext_in)
    return ext.bodies.item(0)


def _create_section_for_line(design, root, um, sk_line, idx,
                             prefix, section, description, points_mm,
                             extra_mm, angle_deg, include_profile_in_name):
    sp = sk_line.startSketchPoint.worldGeometry
    ep = sk_line.endSketchPoint.worldGeometry
    cc_len_u = sp.distanceTo(ep)
    if cc_len_u <= 0:
        return False

    mid = adsk.core.Point3D.create(
        (sp.x + ep.x) / 2.0,
        (sp.y + ep.y) / 2.0,
        (sp.z + ep.z) / 2.0,
    )
    y_axis = adsk.core.Vector3D.create(
        ep.x - sp.x, ep.y - sp.y, ep.z - sp.z,
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

    comp_name = f"{prefix}{idx}"
    if include_profile_in_name:
        comp_name += f"-{_compact_section_name(section.get('name', prefix))}"
    set_occurrence_component_name(occ, comp, comp_name)
    _set_component_description(comp, description)

    body = _build_section_geometry(comp, um, cc_len_u, points_mm, extra_mm)
    _apply_steel_material(comp, body)
    _apply_steel_color(body)
    try:
        ctx.app().activeViewport.refresh()
    except:
        pass
    return True


def _generate_section_from_lines(lines, section, extra_mm, angle_deg,
                                 include_profile_in_name, prefix,
                                 message_family, description, points_mm):
    if not lines:
        ctx.ui().messageBox("Please select at least one sketch line.")
        return

    design = get_design()
    root = get_root()
    um = units_manager()
    next_idx = find_next_index(design, prefix)
    created = 0

    for line in lines:
        if _create_section_for_line(
            design, root, um, line, next_idx,
            prefix, section, description, points_mm,
            extra_mm, angle_deg, include_profile_in_name,
        ):
            created += 1
            next_idx += 1

    ctx.ui().messageBox(f"Created {created} {message_family} components.")


def generate_ub_from_lines(lines, section_name, extra_mm, angle_deg,
                           include_profile_in_name=False):
    section = _section_by_name(UB_SECTIONS, section_name)
    if not section:
        ctx.ui().messageBox("No UB section selected.")
        return
    description = _profile_description(
        "UB",
        section["depth"],
        section["width"],
        section["web"],
        section["flange"],
    )
    _generate_section_from_lines(
        lines,
        section,
        extra_mm,
        angle_deg,
        include_profile_in_name,
        "UB",
        "UB",
        description,
        _ub_profile_points_mm(section),
    )


def generate_pfc_from_lines(lines, section_name, extra_mm, angle_deg,
                            include_profile_in_name=False):
    section = _section_by_name(PFC_SECTIONS, section_name)
    if not section:
        ctx.ui().messageBox("No PFC section selected.")
        return
    description = _profile_description(
        "PFC",
        section["depth"],
        section["width"],
        section["web"],
        section["flange"],
    )
    _generate_section_from_lines(
        lines,
        section,
        extra_mm,
        angle_deg,
        include_profile_in_name,
        "PFC",
        "PFC",
        description,
        _pfc_profile_points_mm(section),
    )


def generate_c_channel_from_lines(lines, section_name, extra_mm, angle_deg,
                                  include_profile_in_name=False):
    section = _section_by_name(C_CHANNEL_SECTIONS, section_name)
    if not section:
        ctx.ui().messageBox("No C channel section selected.")
        return
    description = _profile_description(
        "C PURLIN",
        section["depth"],
        section["width"],
        section["lip"],
        section["thickness"],
    )
    _generate_section_from_lines(
        lines,
        section,
        extra_mm,
        angle_deg,
        include_profile_in_name,
        "C",
        "C channel",
        description,
        _c_channel_profile_points_mm(section),
    )


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

