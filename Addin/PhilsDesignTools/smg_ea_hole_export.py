import adsk.core
import adsk.fusion
import traceback
import csv
import os
import re
import zipfile

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_EA_HoleExport_CSV"
CMD_NAME = "EA Hole Export"
CMD_TOOLTIP = "Export EA holes as detailed rows or summary rows in CSV/XLSX."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

SELECTION_INPUT_ID = "ea_hole_export_selection"
FILTER_NON_STANDARD_ID = "ea_hole_export_non_standard"
INCLUDE_SUBCOMPONENTS_ID = "ea_hole_export_include_subcomponents"
EXPORT_MODE_ID = "ea_hole_export_mode"
FILETYPE_ID = "ea_hole_export_filetype"

EXPORT_MODE_DETAILED = "Detailed (one row per hole)"
EXPORT_MODE_SUMMARY = "Summary (one row per member)"
EXPORT_MODE_OPTIONS = [EXPORT_MODE_DETAILED, EXPORT_MODE_SUMMARY]

FILETYPE_CSV = "CSV (.csv)"
FILETYPE_XLSX = "XLSX (.xlsx)"
FILETYPE_OPTIONS = [FILETYPE_XLSX, FILETYPE_CSV]
FILETYPE_DEFAULT = FILETYPE_XLSX

FUSION_INSERT_RE = re.compile(r"\([0-9]+\)", re.IGNORECASE)
PROFILE_FROM_NAME_RE = re.compile(
    r"^(?P<base>.+?)-(?P<profile>\d+(?:\.\d+)?(?:x\d+(?:\.\d+)?){1,3})$",
    re.IGNORECASE,
)


class HoleExportCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById(SELECTION_INPUT_ID):
                return

            sel = inputs.addSelectionInput(
                SELECTION_INPUT_ID,
                "Selection",
                "Select EA occurrences or bodies"
            )
            sel.addSelectionFilter("Bodies")
            sel.addSelectionFilter("Occurrences")
            try:
                sel.addSelectionFilter("Components")
            except:
                logger.log("Selection filter 'Components' not supported; ignoring.")
            sel.setSelectionLimits(1, 0)

            mode_input = inputs.addDropDownCommandInput(
                EXPORT_MODE_ID,
                "Export Mode",
                adsk.core.DropDownStyles.TextListDropDownStyle,
            )
            mode_items = mode_input.listItems
            for option in EXPORT_MODE_OPTIONS:
                mode_items.add(option, option == EXPORT_MODE_SUMMARY, "")

            filetype_input = inputs.addDropDownCommandInput(
                FILETYPE_ID,
                "File Type",
                adsk.core.DropDownStyles.TextListDropDownStyle,
            )
            filetype_items = filetype_input.listItems
            for option in FILETYPE_OPTIONS:
                filetype_items.add(option, option == FILETYPE_DEFAULT, "")

            inputs.addBoolValueInput(
                FILTER_NON_STANDARD_ID,
                "Non Standard Only (>2 holes)",
                True,
                "",
                False,
            )
            inputs.addBoolValueInput(
                INCLUDE_SUBCOMPONENTS_ID,
                "Include subcomponents",
                True,
                "",
                True,
            )

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


def _safe_entity_token(entity):
    try:
        return entity.entityToken
    except:
        return None


def _append_body(comp_name, body, tokens, bodies):
    if not body or not body.isSolid:
        return
    tok = _safe_entity_token(body)
    if tok and tok in tokens:
        return
    if tok:
        tokens.add(tok)
    bodies.append((comp_name, body))


def _collect_occurrence_bodies(occ, include_children, tokens, bodies):
    if not occ:
        return
    comp_name = occ.component.name if occ.component else occ.name
    try:
        for b in occ.bRepBodies:
            _append_body(comp_name, b, tokens, bodies)
    except:
        pass

    if not include_children:
        return
    try:
        children = occ.childOccurrences
    except:
        children = None
    if not children:
        return
    for child in children:
        _collect_occurrence_bodies(child, include_children, tokens, bodies)


def _collect_component_bodies(comp, include_children, tokens, bodies):
    if not comp:
        return
    comp_name = comp.name
    try:
        for b in comp.bRepBodies:
            _append_body(comp_name, b, tokens, bodies)
    except:
        pass

    if not include_children:
        return
    try:
        occs = comp.occurrences
    except:
        occs = None
    if not occs:
        return
    for occ in occs:
        _collect_occurrence_bodies(occ, include_children, tokens, bodies)


def _iterate_selected_bodies(sel_input, include_subcomponents):
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
            _collect_occurrence_bodies(occ, include_subcomponents, tokens, bodies)
        elif comp:
            _collect_component_bodies(comp, include_subcomponents, tokens, bodies)
        elif body:
            comp = body.parentComponent
            comp_name = comp.name if comp else "UnknownComponent"
            _append_body(comp_name, body, tokens, bodies)

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
    max_proj = None
    for v in body.vertices:
        p = v.geometry
        vec = adsk.core.Vector3D.create(p.x, p.y, p.z)
        proj = vec.dotProduct(length_dir)
        if min_proj is None or proj < min_proj:
            min_proj = proj
        if max_proj is None or proj > max_proj:
            max_proj = proj

    if min_proj is None or max_proj is None:
        raise RuntimeError("Failed to determine length extent for body '{}'".format(body.name))

    return {
        "length_dir": length_dir,
        "min_proj": min_proj,
        "max_proj": max_proj,
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


def _clean_fusion_name(name):
    return FUSION_INSERT_RE.sub("", str(name or "")).strip()


def _split_name_profile(name):
    clean_name = _clean_fusion_name(name)
    if not clean_name:
        return "", ""
    match = PROFILE_FROM_NAME_RE.match(clean_name)
    if not match:
        return clean_name, ""
    return match.group("base").strip(), match.group("profile").strip()


def _get_body_material_name(body):
    try:
        mat = body.material
        if mat and mat.name:
            return mat.name
    except:
        pass
    return ""


def _extension_for_filetype(filetype):
    return ".csv" if filetype == FILETYPE_CSV else ".xlsx"


def _filter_for_filetype(filetype):
    return "CSV files (*.csv)" if filetype == FILETYPE_CSV else "XLSX files (*.xlsx)"


def _ensure_file_extension(path, extension):
    root, ext = os.path.splitext(path)
    if ext.lower() == extension.lower():
        return path
    return root + extension


def _escape_xml_text(value):
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&apos;")
    )


def _xlsx_col_name(col_idx):
    letters = ""
    n = col_idx
    while n > 0:
        n, rem = divmod(n - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _write_rows_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


def _write_rows_xlsx(path, rows):
    rows_xml = []
    for row_idx, row in enumerate(rows, start=1):
        cells_xml = []
        for col_idx, value in enumerate(row, start=1):
            cell_ref = f"{_xlsx_col_name(col_idx)}{row_idx}"
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                cell_xml = f'<c r="{cell_ref}"><v>{value}</v></c>'
            else:
                txt = _escape_xml_text(value)
                cell_xml = f'<c r="{cell_ref}" t="inlineStr"><is><t>{txt}</t></is></c>'
            cells_xml.append(cell_xml)
        rows_xml.append(f'<row r="{row_idx}">{"".join(cells_xml)}</row>')

    worksheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(rows_xml)}</sheetData></worksheet>'
    )
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
    <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
    <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
    <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""
    rels_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
    <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
    workbook_xml = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    core_xml = """<?xml version="1.0" encoding="UTF-8"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>EA Hole Export</dc:title>
  <dc:creator>PhilsDesignTools</dc:creator>
</cp:coreProperties>"""
    app_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>PhilsDesignTools</Application>
</Properties>"""

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as xlsx:
        xlsx.writestr("[Content_Types].xml", content_types)
        xlsx.writestr("_rels/.rels", rels_rels)
        xlsx.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        xlsx.writestr("xl/workbook.xml", workbook_xml)
        xlsx.writestr("xl/worksheets/sheet1.xml", worksheet_xml)
        xlsx.writestr("docProps/core.xml", core_xml)
        xlsx.writestr("docProps/app.xml", app_xml)


def _write_rows(path, rows, filetype):
    if filetype == FILETYPE_CSV:
        _write_rows_csv(path, rows)
        return
    _write_rows_xlsx(path, rows)


def _execute(args):
    cmd = args.command
    inputs = cmd.commandInputs
    sel_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(SELECTION_INPUT_ID))
    mode_in = adsk.core.DropDownCommandInput.cast(inputs.itemById(EXPORT_MODE_ID))
    filetype_in = adsk.core.DropDownCommandInput.cast(inputs.itemById(FILETYPE_ID))
    non_standard_in = adsk.core.BoolValueCommandInput.cast(
        inputs.itemById(FILTER_NON_STANDARD_ID)
    )
    include_sub_in = adsk.core.BoolValueCommandInput.cast(
        inputs.itemById(INCLUDE_SUBCOMPONENTS_ID)
    )
    export_mode = (
        mode_in.selectedItem.name
        if mode_in and mode_in.selectedItem
        else EXPORT_MODE_SUMMARY
    )
    filetype = (
        filetype_in.selectedItem.name
        if filetype_in and filetype_in.selectedItem
        else FILETYPE_DEFAULT
    )
    non_standard_only = non_standard_in.value if non_standard_in else False
    include_subcomponents = include_sub_in.value if include_sub_in else True

    bodies = _iterate_selected_bodies(sel_input, include_subcomponents)

    ui = ctx.ui()

    file_dlg = ui.createFileDialog()
    file_dlg.isMultiSelectEnabled = False
    file_dlg.title = "Export EA Hole Data"
    file_dlg.filter = _filter_for_filetype(filetype)
    default_stem = "EA_HoleExport_Summary" if export_mode == EXPORT_MODE_SUMMARY else "EA_HoleExport_Detailed"
    file_dlg.initialFilename = default_stem + _extension_for_filetype(filetype)

    if file_dlg.showSave() != adsk.core.DialogResults.DialogOK:
        return

    out_path = _ensure_file_extension(file_dlg.filename, _extension_for_filetype(filetype))

    logger.log_command(
        CMD_NAME,
        {
            "selected_bodies": len(bodies),
            "output": out_path,
            "filetype": filetype,
            "export_mode": export_mode,
            "non_standard_only": non_standard_only,
            "include_subcomponents": include_subcomponents,
        },
    )

    CM_TO_MM = 10.0
    total_holes = 0
    total_members = 0

    if export_mode == EXPORT_MODE_SUMMARY:
        rows = [[
            "PartName",
            "Material/Profile",
            "TotalLength_mm",
            "Standard2Hole",
        ]]
    else:
        header = [
            "EAComponent",
            "HoleIndex",
            "Flange",
            "DistanceFromLeft_mm",
            "DistanceFromRight_mm",
            "MemberLength_mm",
            "HoleInset_mm",
            "HoleDiameter_mm",
        ]
        padding = [""] * (len(header) - 1)
        rows = []
        how_to = [
            "How to use this export",
            "Each row describes one hole in one EA member. All units are millimeters.",
            "EAComponent is the member name; use it to identify the EA profile in your system.",
            "MemberLength_mm is the total member length; cut the member to this length.",
            "Flange tells which face the hole is on (Horizontal or Vertical).",
            "DistanceFromLeft_mm is measured along the member length from the left end to the hole center.",
            "DistanceFromRight_mm is measured along the member length from the right end to the hole center.",
            "Left/Right are based on the member's longest axis; left = the end with the smaller coordinate along that axis.",
            "HoleInset_mm is the distance from the hole center to the nearest flange edge (across the flange width).",
            "HoleDiameter_mm is the hole diameter to drill.",
        ]
        for line in how_to:
            rows.append([line] + padding)
        rows.append([""] + padding)
        rows.append(header)

    for comp_name, body in bodies:
        try:
            axes = _get_body_axes(body)
        except Exception as ex_body:
            ui.messageBox("Skipping body '{}':\n{}".format(body.name, str(ex_body)))
            continue

        length_dir = axes["length_dir"]
        min_proj = axes["min_proj"]
        max_proj = axes["max_proj"]
        total_length_cm = max_proj - min_proj
        if total_length_cm <= 1e-6:
            ui.messageBox("Skipping body '{}':\nInvalid member length.".format(body.name))
            continue

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
            # Hole axes align with the face normal; fillets/rounded profiles do not.
            axis = _normalize(cyl.axis)
            if axis.length <= 1e-6 or abs(axis.dotProduct(n)) < 0.8:
                continue

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
        member_length_mm = round(total_length_cm * CM_TO_MM)
        is_standard_2_hole = len(valid_holes) == 2

        if export_mode == EXPORT_MODE_SUMMARY:
            if non_standard_only and is_standard_2_hole:
                continue

            part_name, profile = _split_name_profile(comp_name)
            if not part_name:
                part_name = _clean_fusion_name(comp_name)
            if not profile:
                _, profile = _split_name_profile(body.name)
            if not profile:
                profile = _get_body_material_name(body)

            rows.append([
                part_name,
                profile,
                member_length_mm,
                "Yes" if is_standard_2_hole else "No",
            ])
            total_members += 1
            total_holes += len(valid_holes)
            continue

        if non_standard_only and len(valid_holes) <= 2:
            continue

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
            distance_from_right_mm = round((total_length_cm - cL_cm) * CM_TO_MM)

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
                distance_from_right_mm,
                member_length_mm,
                inset_mm,
                diameter_mm,
            ])

    _write_rows(out_path, rows, filetype)

    logger.log_command(
        CMD_NAME,
        {
            "result": "export_complete",
            "total_holes": total_holes,
            "total_members": total_members,
            "filetype": filetype,
            "export_mode": export_mode,
            "output": out_path,
        },
    )

    if export_mode == EXPORT_MODE_SUMMARY:
        ui.messageBox(
            "EA hole summary export complete.\n"
            f"File: {out_path}\n"
            f"Members exported: {total_members}\n"
            f"Total holes found: {total_holes}"
        )
    else:
        ui.messageBox(
            "EA hole detailed export complete.\n"
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
