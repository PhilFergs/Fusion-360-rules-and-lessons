import adsk.core
import adsk.fusion
import traceback
import csv
import os

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_EA_HoleExport_CSV"
CMD_NAME = "EA Hole Export CSV"
CMD_TOOLTIP = "Export EA hole locations to CSV."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

SELECTION_INPUT_ID = "ea_hole_export_selection"


class HoleExportCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            sel = inputs.addSelectionInput(
                SELECTION_INPUT_ID,
                "Selection",
                "Select EA components, occurrences, or bodies"
            )
            sel.addSelectionFilter("Bodies")
            sel.addSelectionFilter("Occurrences")
            sel.addSelectionFilter("Components")
            sel.setSelectionLimits(1, 0)

            on_exec = HoleExportExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)

        except:
            logger.log("EA Hole Export CSV UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("EA Hole Export CSV UI failed:\n" + traceback.format_exc())


class HoleExportExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log("EA Hole Export CSV failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("EA Hole Export CSV failed:\n" + traceback.format_exc())


def _iterate_selected_bodies(sel_input):
    if not sel_input or sel_input.selectionCount == 0:
        raise RuntimeError("No entities selected. Select components or bodies first.")

    bodies = []
    tokens = set()

    for i in range(sel_input.selectionCount):
        ent = sel_input.selection(i).entity
        if not ent:
            continue

        occ = adsk.fusion.Occurrence.cast(ent)
        comp = adsk.fusion.Component.cast(ent)
        body = adsk.fusion.BRepBody.cast(ent)

        if occ:
            comp_name = occ.component.name if occ.component else occ.name
            for b in occ.bRepBodies:
                if not b.isSolid:
                    continue
                try:
                    tok = b.entityToken
                except:
                    tok = None
                if tok and tok in tokens:
                    continue
                if tok:
                    tokens.add(tok)
                bodies.append((comp_name, b))
        elif comp:
            comp_name = comp.name
            for b in comp.bRepBodies:
                if not b.isSolid:
                    continue
                try:
                    tok = b.entityToken
                except:
                    tok = None
                if tok and tok in tokens:
                    continue
                if tok:
                    tokens.add(tok)
                bodies.append((comp_name, b))
        elif body:
            if body.isSolid:
                comp = body.parentComponent
                comp_name = comp.name if comp else "UnknownComponent"
                try:
                    tok = body.entityToken
                except:
                    tok = None
                if tok and tok in tokens:
                    continue
                if tok:
                    tokens.add(tok)
                bodies.append((comp_name, body))

    if not bodies:
        raise RuntimeError("No solid bodies found in selection.")

    return bodies


def _get_cylindrical_faces(body):
    cyl_faces = []
    for face in body.faces:
        geom = face.geometry
        if not geom:
            continue
        try:
            st = geom.surfaceType
        except:
            continue
        if st == adsk.core.SurfaceTypes.CylinderSurfaceType:
            cyl_faces.append(face)
    return cyl_faces


def _get_longest_edge_dir(body):
    longest_len = 0.0
    best_vec = None
    for edge in body.edges:
        geom = edge.geometry
        line = adsk.core.Line3D.cast(geom)
        if not line:
            continue
        sp = line.startPoint
        ep = line.endPoint
        v = sp.vectorTo(ep)
        length = v.length
        if length > longest_len:
            longest_len = length
            best_vec = v
    if best_vec and longest_len > 1e-6:
        best_vec.normalize()
        return best_vec
    return None


def _get_body_axes(body):
    bbox = body.boundingBox
    if not bbox:
        raise RuntimeError("Body '{}' has no bounding box.".format(body.name))

    min_p = bbox.minPoint
    max_p = bbox.maxPoint

    length_dir = _get_longest_edge_dir(body)
    if not length_dir:
        diag = min_p.vectorTo(max_p)
        if diag.length <= 1e-6:
            raise RuntimeError("Body '{}' has negligible size.".format(body.name))
        diag.normalize()
        length_dir = diag

    min_proj = None
    for v in body.vertices:
        p = v.geometry
        vec = adsk.core.Vector3D.create(p.x, p.y, p.z)
        proj = vec.dotProduct(length_dir)
        if min_proj is None or proj < min_proj:
            min_proj = proj

    if min_proj is None:
        raise RuntimeError("Failed to determine length extent for body '{}'".format(body.name))

    return {
        "length_dir": length_dir,
        "min_proj": min_proj,
        "min_p": min_p,
        "max_p": max_p,
    }


def _normalize(v):
    out = adsk.core.Vector3D.create(v.x, v.y, v.z)
    if out.length > 1e-6:
        out.normalize()
    return out


def _cluster_normal(normals, n, tol=0.01):
    for idx, info in enumerate(normals):
        d = info["dir"]
        if abs(d.dotProduct(n)) >= 1.0 - tol:
            return idx
    dir_copy = adsk.core.Vector3D.create(n.x, n.y, n.z)
    normals.append({
        "dir": dir_copy,
        "count": 0,
        "plane_origin": None,
        "v_dir": None,
        "min_s": None,
        "max_s": None,
    })
    return len(normals) - 1


def _execute(args):
    cmd = args.command
    inputs = cmd.commandInputs
    sel_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(SELECTION_INPUT_ID))

    bodies = _iterate_selected_bodies(sel_input)

    ui = ctx.ui()
    app = ctx.app()

    file_dlg = ui.createFileDialog()
    file_dlg.isMultiSelectEnabled = False
    file_dlg.title = "Export EA Hole Locations to CSV"
    file_dlg.filter = "CSV files (*.csv)"
    file_dlg.initialFilename = "EA_HoleExport.csv"

    if file_dlg.showSave() != adsk.core.DialogResults.DialogOK:
        return

    out_path = file_dlg.filename

    logger.log_command(
        CMD_NAME,
        {
            "selected_bodies": len(bodies),
            "output": out_path,
        },
    )

    CM_TO_MM = 10.0

    rows = [[
        "EAComponent",
        "HoleIndex",
        "Flange",
        "DistanceFromLeft_mm",
        "HoleInset_mm",
        "HoleDiameter_mm",
    ]]

    total_holes = 0

    for comp_name, body in bodies:
        try:
            axes = _get_body_axes(body)
        except Exception as ex_body:
            ui.messageBox("Skipping body '{}':\n{}".format(body.name, str(ex_body)))
            continue

        length_dir = axes["length_dir"]
        min_proj = axes["min_proj"]

        cyl_faces = _get_cylindrical_faces(body)
        if not cyl_faces:
            continue

        hole_data = []
        flange_clusters = []

        for face in cyl_faces:
            geom = face.geometry
            cyl = adsk.core.Cylinder.cast(geom)
            if not cyl:
                continue

            center = cyl.origin
            radius = cyl.radius

            center_vec = adsk.core.Vector3D.create(center.x, center.y, center.z)
            proj_center = center_vec.dotProduct(length_dir)
            cL = proj_center - min_proj

            best_plane = None
            best_area = 0.0
            for edge in face.edges:
                for af in edge.faces:
                    if af == face:
                        continue
                    g2 = af.geometry
                    if not g2:
                        continue
                    try:
                        st2 = g2.surfaceType
                    except:
                        continue
                    if st2 == adsk.core.SurfaceTypes.PlaneSurfaceType:
                        area = af.area
                        if area > best_area:
                            best_area = area
                            best_plane = g2

            if not best_plane:
                continue

            n = _normalize(best_plane.normal)
            plane_origin = best_plane.origin

            cluster_idx = _cluster_normal(flange_clusters, n)
            cluster = flange_clusters[cluster_idx]
            cluster["count"] += 1
            if cluster["plane_origin"] is None:
                cluster["plane_origin"] = plane_origin

            hole_data.append({
                "radius": radius,
                "center": center,
                "cL": cL,
                "cluster": cluster_idx,
            })

        if not hole_data or not flange_clusters:
            continue

        plane_tol = 0.01

        for cluster in flange_clusters:
            n = cluster["dir"]
            p0 = cluster["plane_origin"]
            if p0 is None:
                continue

            u = adsk.core.Vector3D.create(length_dir.x, length_dir.y, length_dir.z)
            dot_un = u.dotProduct(n)
            normal_component = adsk.core.Vector3D.create(n.x, n.y, n.z)
            normal_component.scaleBy(dot_un)
            u.subtract(normal_component)
            if u.length <= 1e-6:
                if abs(n.x) < 0.9:
                    u = adsk.core.Vector3D.create(1, 0, 0)
                else:
                    u = adsk.core.Vector3D.create(0, 1, 0)
                dot_un = u.dotProduct(n)
                normal_component = adsk.core.Vector3D.create(n.x, n.y, n.z)
                normal_component.scaleBy(dot_un)
                u.subtract(normal_component)
            u.normalize()

            v_dir = n.crossProduct(u)
            if v_dir.length <= 1e-6:
                v_dir = u.crossProduct(n)
            v_dir.normalize()
            cluster["v_dir"] = v_dir

            min_s = None
            max_s = None

            for vtx in body.vertices:
                p = vtx.geometry
                r = adsk.core.Vector3D.create(p.x - p0.x, p.y - p0.y, p.z - p0.z)
                dist_plane = r.dotProduct(n)
                if abs(dist_plane) > plane_tol:
                    continue

                s = r.dotProduct(v_dir)
                if min_s is None or s < min_s:
                    min_s = s
                if max_s is None or s > max_s:
                    max_s = s

            cluster["min_s"] = min_s
            cluster["max_s"] = max_s

        horiz_cluster = max(
            range(len(flange_clusters)),
            key=lambda i: flange_clusters[i]["count"],
        )

        valid_holes = []
        for h in hole_data:
            cl = flange_clusters[h["cluster"]]
            if cl["v_dir"] is None or cl["min_s"] is None or cl["max_s"] is None:
                continue
            valid_holes.append(h)

        if not valid_holes:
            continue

        valid_holes.sort(key=lambda h: h["cL"])

        hole_index = 0
        for h in valid_holes:
            radius = h["radius"]
            center = h["center"]
            cL_cm = h["cL"]
            cluster_idx = h["cluster"]

            cl = flange_clusters[cluster_idx]
            n = cl["dir"]
            p0 = cl["plane_origin"]
            vdir = cl["v_dir"]
            min_s = cl["min_s"]
            max_s = cl["max_s"]

            distance_from_left_mm = round(cL_cm * CM_TO_MM)

            r_h = adsk.core.Vector3D.create(
                center.x - p0.x,
                center.y - p0.y,
                center.z - p0.z,
            )
            s_h = r_h.dotProduct(vdir)
            inset_cm = min(abs(s_h - min_s), abs(s_h - max_s))
            inset_mm = round(inset_cm * CM_TO_MM)

            diameter_mm = round((2.0 * radius) * CM_TO_MM)

            flange_label = "Horizontal" if cluster_idx == horiz_cluster else "Vertical"

            hole_index += 1
            total_holes += 1

            rows.append([
                comp_name,
                hole_index,
                flange_label,
                distance_from_left_mm,
                inset_mm,
                diameter_mm,
            ])

    with open(out_path, "w", newline="") as f:
        csv.writer(f).writerows(rows)

    logger.log_command(
        CMD_NAME,
        {
            "result": "export_complete",
            "total_holes": total_holes,
            "output": out_path,
        },
    )

    ui.messageBox(
        "EA hole CSV export complete.\n"
        f"File: {out_path}\n"
        f"Total holes found: {total_holes}"
    )


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = HoleExportCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
