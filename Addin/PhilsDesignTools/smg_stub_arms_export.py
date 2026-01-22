import adsk.core
import adsk.fusion
import traceback
import csv
import os
import math

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_StubArms_Export_CSV"
CMD_NAME = "Stub Arms Export CSV"
CMD_TOOLTIP = "Export stub arm line lengths and stock quantities to CSV."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

SELECTION_INPUT_ID = "stub_arms_export_selection"
INCLUDE_SUBCOMPONENTS_ID = "stub_arms_export_include_subcomponents"
VISIBLE_ONLY_ID = "stub_arms_export_visible_only"
DETAIL_BY_COLUMN_ID = "stub_arms_export_detail_by_column"

STOCK_MIN_MM = 300
STOCK_MAX_MM = 1800
STOCK_STEP_MM = 200
STUB_MEMBER_ATTR_GROUP = "PhilsDesignTools"
STUB_MEMBER_ATTR_NAME = "StubMemberType"


class StubArmsExportCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById(SELECTION_INPUT_ID):
                return

            sel = inputs.addSelectionInput(
                SELECTION_INPUT_ID,
                "Selection",
                "Select stub arm sketch lines, sketches, or components"
            )
            sel.addSelectionFilter("SketchLines")
            try:
                sel.addSelectionFilter("Sketches")
            except:
                pass
            sel.addSelectionFilter("Occurrences")
            try:
                sel.addSelectionFilter("Components")
            except:
                logger.log("Selection filter 'Components' not supported; ignoring.")
            sel.setSelectionLimits(1, 0)

            inputs.addBoolValueInput(
                INCLUDE_SUBCOMPONENTS_ID,
                "Include subcomponents",
                True,
                "",
                True,
            )
            inputs.addBoolValueInput(
                VISIBLE_ONLY_ID,
                "Visible lines only",
                True,
                "",
                True,
            )
            inputs.addBoolValueInput(
                DETAIL_BY_COLUMN_ID,
                "Include per-line breakdown",
                True,
                "",
                False,
            )

            on_exec = StubArmsExportExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)
        except:
            logger.log("Stub Arms Export UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Stub Arms Export UI failed:\n" + traceback.format_exc())


class StubArmsExportExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log("Stub Arms Export failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Stub Arms Export failed:\n" + traceback.format_exc())


def _safe_entity_token(entity):
    try:
        return entity.entityToken
    except:
        return None


def _is_entity_visible(ent):
    try:
        return ent.isVisible
    except:
        return True


def _is_line_visible(line):
    if not line:
        return False
    try:
        if hasattr(line, "isConstruction") and line.isConstruction:
            return False
    except:
        pass
    if not _is_entity_visible(line):
        return False
    try:
        sk = line.parentSketch
        if sk and not _is_entity_visible(sk):
            return False
    except:
        pass
    try:
        occ = line.assemblyContext
        if occ and not _is_entity_visible(occ):
            return False
    except:
        pass
    return True


def _append_line(line, tokens, lines, visible_only):
    if not line:
        return
    if visible_only and not _is_line_visible(line):
        return
    tok = _safe_entity_token(line)
    if tok and tok in tokens:
        return
    if tok:
        tokens.add(tok)
    lines.append(line)


def _collect_lines_from_sketch(sketch, tokens, lines, visible_only):
    if not sketch:
        return
    if visible_only and not _is_entity_visible(sketch):
        return
    try:
        sk_lines = sketch.sketchCurves.sketchLines
        for i in range(sk_lines.count):
            _append_line(sk_lines.item(i), tokens, lines, visible_only)
    except:
        pass


def _collect_lines_from_occurrence(occ, include_children, tokens, lines, visible_only):
    if not occ or not occ.component:
        return
    if visible_only and not _is_entity_visible(occ):
        return
    _collect_lines_from_component(occ.component, False, tokens, lines, visible_only)
    if not include_children:
        return
    try:
        children = occ.childOccurrences
    except:
        children = None
    if not children:
        return
    for child in children:
        _collect_lines_from_occurrence(child, include_children, tokens, lines, visible_only)


def _collect_lines_from_component(comp, include_children, tokens, lines, visible_only):
    if not comp:
        return
    try:
        sketches = comp.sketches
        for i in range(sketches.count):
            _collect_lines_from_sketch(sketches.item(i), tokens, lines, visible_only)
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
        _collect_lines_from_occurrence(occ, include_children, tokens, lines, visible_only)


def _iterate_selected_lines(sel_input, include_subcomponents, visible_only):
    if not sel_input or sel_input.selectionCount == 0:
        raise RuntimeError("No entities selected. Select stub arm lines or a component.")

    lines = []
    tokens = set()

    for i in range(sel_input.selectionCount):
        ent = sel_input.selection(i).entity
        if not ent:
            continue

        line = adsk.fusion.SketchLine.cast(ent)
        sketch = adsk.fusion.Sketch.cast(ent)
        occ = adsk.fusion.Occurrence.cast(ent)
        comp = adsk.fusion.Component.cast(ent)

        if line:
            _append_line(line, tokens, lines, visible_only)
        elif sketch:
            _collect_lines_from_sketch(sketch, tokens, lines, visible_only)
        elif occ:
            _collect_lines_from_occurrence(occ, include_subcomponents, tokens, lines, visible_only)
        elif comp:
            _collect_lines_from_component(comp, include_subcomponents, tokens, lines, visible_only)

    if not lines:
        raise RuntimeError("No sketch lines found in the selection.")
    return lines


def _round_to_stock(mm_val):
    if mm_val <= STOCK_MIN_MM:
        return STOCK_MIN_MM
    steps = int(math.ceil((mm_val - STOCK_MIN_MM) / float(STOCK_STEP_MM)))
    size = STOCK_MIN_MM + steps * STOCK_STEP_MM
    if size > STOCK_MAX_MM:
        return None
    return size


def _round_to_stock_oversize(mm_val):
    if mm_val <= STOCK_MIN_MM:
        return STOCK_MIN_MM
    steps = int(math.ceil((mm_val - STOCK_MIN_MM) / float(STOCK_STEP_MM)))
    return STOCK_MIN_MM + steps * STOCK_STEP_MM


def _column_label_for_line(line):
    try:
        sk = line.parentSketch
    except:
        sk = None
    if not sk:
        return "Unknown"
    try:
        name = sk.name or ""
    except:
        name = ""
    prefix = "Stub Arms - "
    if name.startswith(prefix):
        trimmed = name[len(prefix):].strip()
        return trimmed if trimmed else name
    return name if name else "Unknown"


def _point_key(point, um, decimals=1):
    if not point or not um:
        return None
    try:
        x_mm = um.convert(point.x, um.internalUnits, "mm")
        y_mm = um.convert(point.y, um.internalUnits, "mm")
        z_mm = um.convert(point.z, um.internalUnits, "mm")
    except:
        return None
    return (round(x_mm, decimals), round(y_mm, decimals), round(z_mm, decimals))


def _sketch_key(sketch):
    if not sketch:
        return "sk:none"
    tok = _safe_entity_token(sketch)
    if tok:
        return f"sk:{tok}"
    return f"sk:{id(sketch)}"


def _line_key(line):
    if not line:
        return None
    tok = _safe_entity_token(line)
    if tok:
        return f"ln:{tok}"
    return f"ln:{id(line)}"


def _line_endpoint_keys(line, um, decimals=1):
    if not line or not um:
        return None, None
    try:
        sp = line.startSketchPoint.worldGeometry
        ep = line.endSketchPoint.worldGeometry
    except:
        return None, None
    return _point_key(sp, um, decimals), _point_key(ep, um, decimals)


def _lines_share_endpoint(line_a, line_b, um, decimals=1):
    if not line_a or not line_b:
        return False
    a1, a2 = _line_endpoint_keys(line_a, um, decimals)
    b1, b2 = _line_endpoint_keys(line_b, um, decimals)
    if a1 is None or a2 is None or b1 is None or b2 is None:
        return False
    return a1 == b1 or a1 == b2 or a2 == b1 or a2 == b2


def _get_line_member_attr(line):
    if not line:
        return None
    candidates = [line]
    try:
        native = line.nativeObject
        if native:
            candidates.append(native)
    except:
        pass
    value = None
    for candidate in candidates:
        try:
            attrs = candidate.attributes
        except:
            attrs = None
        if not attrs:
            continue
        try:
            attr = attrs.itemByName(STUB_MEMBER_ATTR_GROUP, STUB_MEMBER_ATTR_NAME)
        except:
            attr = None
        if not attr:
            continue
        try:
            value = attr.value
        except:
            value = None
        if value:
            break
    if not value:
        return None
    val = value.strip().lower()
    if val == "ea":
        return "ea"
    if val in ("flatbar", "flat", "flat_bar", "flat bar"):
        return "flat"
    return None


def _classify_lines(lines, um):
    line_types = {}
    line_by_key = {}
    for line in lines:
        line_key = _line_key(line)
        if not line_key:
            continue
        line_by_key[line_key] = line
        attr_type = _get_line_member_attr(line)
        if attr_type:
            line_types[line_key] = attr_type

    by_sketch = {}
    for line in lines:
        line_key = _line_key(line)
        if not line_key or line_key in line_types:
            continue
        try:
            sk = line.parentSketch
        except:
            sk = None
        sk_key = _sketch_key(sk)
        entry = by_sketch.get(sk_key)
        if not entry:
            entry = {"sketch": sk, "lines": []}
            by_sketch[sk_key] = entry
        entry["lines"].append(line)

    for entry in by_sketch.values():
        sk = entry["sketch"]
        try:
            ordered = sk.sketchCurves.sketchLines if sk else None
        except:
            ordered = None
        if not ordered:
            for line in entry["lines"]:
                line_key = _line_key(line)
                if line_key and line_key not in line_types:
                    line_types[line_key] = "flat"
            continue

        ordered_keys = []
        for i in range(ordered.count):
            line = ordered.item(i)
            line_key = _line_key(line)
            if not line_key or line_key not in line_by_key:
                continue
            ordered_keys.append(line_key)

        i = 0
        while i < len(ordered_keys):
            key = ordered_keys[i]
            if key in line_types:
                i += 1
                continue
            line_types[key] = "flat"
            j = i + 1
            while j < len(ordered_keys) and ordered_keys[j] in line_types:
                j += 1
            if j < len(ordered_keys):
                key_next = ordered_keys[j]
                line_a = line_by_key.get(key)
                line_b = line_by_key.get(key_next)
                if _lines_share_endpoint(line_a, line_b, um):
                    line_types[key_next] = "ea"
                    i = j + 1
                    continue
            i += 1

    return line_types


def _execute(args):
    cmd = args.command
    inputs = cmd.commandInputs
    sel_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(SELECTION_INPUT_ID))
    include_sub_in = adsk.core.BoolValueCommandInput.cast(
        inputs.itemById(INCLUDE_SUBCOMPONENTS_ID)
    )
    visible_only_in = adsk.core.BoolValueCommandInput.cast(
        inputs.itemById(VISIBLE_ONLY_ID)
    )
    detail_in = adsk.core.BoolValueCommandInput.cast(
        inputs.itemById(DETAIL_BY_COLUMN_ID)
    )
    include_subcomponents = include_sub_in.value if include_sub_in else True
    visible_only = visible_only_in.value if visible_only_in else True
    include_details = detail_in.value if detail_in else False

    lines = _iterate_selected_lines(sel_input, include_subcomponents, visible_only)

    design = adsk.fusion.Design.cast(ctx.app().activeProduct)
    um = design.unitsManager

    stock_counts_ea = {}
    manual_counts_ea = {}
    stock_counts_flat = {}
    manual_counts_flat = {}
    detail_entries = []
    total = 0
    line_types = _classify_lines(lines, um)

    for line in lines:
        try:
            sp = line.startSketchPoint.worldGeometry
            ep = line.endSketchPoint.worldGeometry
        except:
            continue
        if not sp or not ep:
            continue
        length_u = sp.distanceTo(ep)
        if length_u <= 1e-6:
            continue
        mm = um.convert(length_u, um.internalUnits, "mm")
        if mm <= 0:
            continue
        total += 1
        line_key = _line_key(line)
        stock = _round_to_stock(mm)
        line_type = line_types.get(line_key, "flat")
        if line_type == "ea":
            stock_counts = stock_counts_ea
            manual_counts = manual_counts_ea
            member_type = "EA"
        else:
            stock_counts = stock_counts_flat
            manual_counts = manual_counts_flat
            member_type = "FlatBar"
        if stock is None:
            mm_key = int(round(_round_to_stock_oversize(mm)))
            manual_counts[mm_key] = manual_counts.get(mm_key, 0) + 1
        else:
            stock_counts[stock] = stock_counts.get(stock, 0) + 1
        if include_details:
            z_mid = (sp.z + ep.z) * 0.5
            stock_len = _round_to_stock_oversize(mm)
            label = "larger" if mm > STOCK_MAX_MM else "standard"
            detail_entries.append(
                (_column_label_for_line(line), z_mid, stock_len, label, member_type)
            )

    if total == 0:
        ctx.ui().messageBox("No valid stub arm lines found.")
        return

    ui = ctx.ui()
    file_dlg = ui.createFileDialog()
    file_dlg.isMultiSelectEnabled = False
    file_dlg.title = "Export Stub Arms to CSV"
    file_dlg.filter = "CSV files (*.csv)"
    file_dlg.initialFilename = "Stub_Arms_Export.csv"

    if file_dlg.showSave() != adsk.core.DialogResults.DialogOK:
        return

    out_path = file_dlg.filename

    rows = []
    rows.append(["EA stock length (mm)", "Quantity"])
    for size in sorted(stock_counts_ea.keys()):
        rows.append([size, stock_counts_ea[size]])
    rows.append([])
    rows.append(["EA Larger profile required (mm)", "Quantity"])
    for length in sorted(manual_counts_ea.keys()):
        rows.append([length, manual_counts_ea[length]])
    rows.append([])
    rows.append(["Flat bar stock length (mm)", "Quantity"])
    for size in sorted(stock_counts_flat.keys()):
        rows.append([size, stock_counts_flat[size]])
    rows.append([])
    rows.append(["Flat bar Larger profile required (mm)", "Quantity"])
    for length in sorted(manual_counts_flat.keys()):
        rows.append([length, manual_counts_flat[length]])
    if include_details:
        rows.append([])
        rows.append(["Column", "Position", "Stock length (mm)", "Profile size", "Member"])
        by_column = {}
        for col, z_mid, stock_len, label, member_type in detail_entries:
            by_column.setdefault(col, []).append((z_mid, stock_len, label, member_type))
        for col in sorted(by_column.keys()):
            rows.append([f"Column {col}"])
            entries = sorted(by_column[col], key=lambda item: item[0])
            for idx, entry in enumerate(entries, start=1):
                rows.append([col, idx, int(round(entry[1])), entry[2], entry[3]])

    with open(out_path, "w", newline="") as f:
        csv.writer(f).writerows(rows)

    logger.log_command(
        CMD_NAME,
        {
            "selected_lines": len(lines),
            "total_used": total,
            "stock_sizes_ea": len(stock_counts_ea),
            "manual_sizes_ea": len(manual_counts_ea),
            "stock_sizes_flat": len(stock_counts_flat),
            "manual_sizes_flat": len(manual_counts_flat),
            "visible_only": visible_only,
            "detail_breakdown": include_details,
            "output": out_path,
        },
    )

    ui.messageBox(
        "Stub arms CSV export complete.\n"
        f"File: {out_path}\n"
        f"Total stub arm lines: {total}"
    )


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = StubArmsExportCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
