import adsk.core
import adsk.fusion
import traceback
import csv
import os
import math
import json

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
STUB_BRACKET_ATTR_NAME = "StubBracketType"
STUB_BRACKET_ANCHOR_ATTR_NAME = "StubBracketAnchor"
STUB_COLUMN_ATTR_NAME = "StubColumnLabel"
STUB_BRACKET_ATTR_MAP_NAME = "StubBracketTypeMap"
STUB_BRACKET_ANCHOR_MAP_NAME = "StubBracketAnchorMap"
DEBUG_STUB_ARMS_EXPORT = True
DEBUG_STUB_ARMS_EXPORT_SAMPLE = 10


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
    attr_label = _get_line_attr_value(line, STUB_COLUMN_ATTR_NAME)
    if attr_label:
        return str(attr_label).strip()
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
        for suffix in (" - square", " - swivel"):
            if trimmed.lower().endswith(suffix):
                trimmed = trimmed[: -len(suffix)].strip()
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


def _get_line_attr_direct(line, attr_name):
    if not line or not attr_name:
        return None
    candidates = [line]
    try:
        native = line.nativeObject
        if native:
            candidates.append(native)
    except:
        pass
    for candidate in candidates:
        try:
            attrs = candidate.attributes
        except:
            attrs = None
        if not attrs:
            continue
        try:
            attr = attrs.itemByName(STUB_MEMBER_ATTR_GROUP, attr_name)
        except:
            attr = None
        if not attr:
            continue
        try:
            value = attr.value
        except:
            value = None
        if value:
            return value
    return None


def _get_line_attr_value(line, attr_name):
    val = _get_line_attr_direct(line, attr_name)
    if val:
        return val
    if attr_name == STUB_BRACKET_ATTR_NAME:
        return _get_line_map_value(line, STUB_BRACKET_ATTR_MAP_NAME)
    if attr_name == STUB_BRACKET_ANCHOR_ATTR_NAME:
        return _get_line_map_value(line, STUB_BRACKET_ANCHOR_MAP_NAME)
    return None


def _get_attr_map(entity, map_name):
    if not entity or not map_name:
        return {}
    try:
        attrs = entity.attributes
    except:
        return {}
    if not attrs:
        return {}
    try:
        attr = attrs.itemByName(STUB_MEMBER_ATTR_GROUP, map_name)
    except:
        attr = None
    if not attr:
        return {}
    try:
        raw = attr.value
    except:
        raw = None
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except:
        pass
    data = {}
    for line in str(raw).splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, val = line.split("=", 1)
        data[key] = val
    return data


def _line_map_key(entity):
    if not entity:
        return None
    tok = _safe_entity_token(entity)
    if tok:
        return tok
    return f"id:{id(entity)}"


def _get_line_map_value(line, map_name):
    if not line or not map_name:
        return None
    try:
        sk = line.parentSketch
    except:
        sk = None
    comp = None
    if sk:
        try:
            comp = sk.parentComponent
        except:
            comp = None
    owners = [sk, comp]
    for owner in owners:
        if not owner:
            continue
        data = _get_attr_map(owner, map_name)
        if not data:
            continue
        key = _line_map_key(line)
        if key and key in data:
            return data[key]
        try:
            native = line.nativeObject
        except:
            native = None
        if native:
            key = _line_map_key(native)
            if key and key in data:
                return data[key]
    return None


def _is_bracket_anchor(line):
    val = _get_line_attr_value(line, STUB_BRACKET_ANCHOR_ATTR_NAME)
    if not val:
        return False
    return str(val).strip().lower() in ("1", "true", "yes", "y")


def _get_bracket_type(line):
    val = _get_line_attr_value(line, STUB_BRACKET_ATTR_NAME)
    if not val:
        try:
            sk = line.parentSketch
        except:
            sk = None
        name = ""
        if sk:
            try:
                name = sk.name or ""
            except:
                name = ""
        name = name.lower()
        if "square" in name:
            return "square"
        if "swivel" in name:
            return "swivel"
        return None
    val = str(val).strip().lower()
    if val in ("square", "sq"):
        return "square"
    if val in ("swivel", "swivel_bracket", "swivel bracket", "sw"):
        return "swivel"
    if val == "unknown":
        return "swivel"
    return "unknown"


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
    bracket_square = 0
    bracket_swivel = 0
    bracket_unknown = 0
    bracket_total = 0
    flatbar_lines = 0
    missing_bracket_type = 0
    missing_bracket_anchor = 0
    map_type_hits = 0
    map_anchor_hits = 0
    direct_type_hits = 0
    direct_anchor_hits = 0
    missing_samples = []

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
        line_type = line_types.get(line_key, "flat")
        if DEBUG_STUB_ARMS_EXPORT:
            raw_type_direct = _get_line_attr_direct(line, STUB_BRACKET_ATTR_NAME)
            raw_anchor_direct = _get_line_attr_direct(line, STUB_BRACKET_ANCHOR_ATTR_NAME)
            map_type = _get_line_map_value(line, STUB_BRACKET_ATTR_MAP_NAME)
            map_anchor = _get_line_map_value(line, STUB_BRACKET_ANCHOR_MAP_NAME)
            if raw_type_direct is not None:
                direct_type_hits += 1
            if raw_anchor_direct is not None:
                direct_anchor_hits += 1
            if map_type is not None:
                map_type_hits += 1
            if map_anchor is not None:
                map_anchor_hits += 1
            raw_type = _get_line_attr_value(line, STUB_BRACKET_ATTR_NAME)
            raw_anchor = _get_line_attr_value(line, STUB_BRACKET_ANCHOR_ATTR_NAME)
            if raw_type is None:
                missing_bracket_type += 1
            if raw_anchor is None:
                missing_bracket_anchor += 1
            if (
                (raw_type is None or raw_anchor is None)
                and len(missing_samples) < DEBUG_STUB_ARMS_EXPORT_SAMPLE
            ):
                missing_samples.append(
                    f"{line_key}|col={_column_label_for_line(line)}"
                    f"|type={raw_type}|anchor={raw_anchor}"
                )
        btype = _get_bracket_type(line)
        is_anchor = _is_bracket_anchor(line)
        if is_anchor and btype is None:
            btype = "swivel"
        if line_type == "flat":
            flatbar_lines += 1
            if btype is not None or is_anchor:
                bracket_total += 1
                if btype == "square":
                    bracket_square += 1
                elif btype == "swivel":
                    bracket_swivel += 1
                else:
                    bracket_unknown += 1
        stock = _round_to_stock(mm)
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
            label = "50x3" if stock_len > STOCK_MAX_MM else "40x3"
            bracket_label = ""
            if line_type == "flat":
                if btype in ("square", "swivel"):
                    bracket_label = btype.title()
                else:
                    bracket_label = "Unknown"
            detail_entries.append(
                (_column_label_for_line(line), z_mid, stock_len, label, member_type, bracket_label)
            )

    if bracket_total == 0 and flatbar_lines > 0:
        bracket_unknown = flatbar_lines
        bracket_total = flatbar_lines

    if total == 0:
        ctx.ui().messageBox("No valid stub arm lines found.")
        return

    if DEBUG_STUB_ARMS_EXPORT:
        sample = "; ".join(missing_samples) if missing_samples else "none"
        logger.log(
            f"{CMD_NAME} DEBUG: lines={total} missing_bracket_type={missing_bracket_type} "
            f"missing_bracket_anchor={missing_bracket_anchor} direct_type_hits={direct_type_hits} "
            f"direct_anchor_hits={direct_anchor_hits} map_type_hits={map_type_hits} "
            f"map_anchor_hits={map_anchor_hits} sample_missing={sample}"
        )

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
    rows.append(["EA 40x3 Stock lengths (mm)", "Quantity"])
    for size in sorted(stock_counts_ea.keys()):
        rows.append([size, stock_counts_ea[size]])
    rows.append([])
    rows.append(["EA Larger 50x3 required (mm)", "Quantity"])
    for length in sorted(manual_counts_ea.keys()):
        rows.append([length, manual_counts_ea[length]])
    rows.append([])
    rows.append(["Flat bar 40x3 Stock lengths (mm)", "Quantity"])
    for size in sorted(stock_counts_flat.keys()):
        rows.append([size, stock_counts_flat[size]])
    rows.append([])
    rows.append(["Flat bar Larger 50x3 required (mm)", "Quantity"])
    for length in sorted(manual_counts_flat.keys()):
        rows.append([length, manual_counts_flat[length]])
    rows.append([])
    rows.append(["Brackets", "Quantity"])
    rows.append(["Square bracket", bracket_square])
    rows.append(["Swivel bracket", bracket_swivel])
    if bracket_unknown:
        rows.append(["Unknown bracket (no angle tag)", bracket_unknown])
    rows.append([])
    rows.append(["Spacer blocks", bracket_total])
    rows.append(["Bracket bolts + nylock nuts (M10x40)", bracket_total])
    rows.append(["Block screws (40mm timber)", bracket_total * 4])
    rows.append(["Stub arm screws (S500)", total * 3])
    if include_details:
        rows.append([])
        rows.append(["Column", "Position", "Stock length (mm)", "Profile size", "Member", "Bracket"])
        by_column = {}
        for col, z_mid, stock_len, label, member_type, bracket_label in detail_entries:
            by_column.setdefault(col, []).append(
                (z_mid, stock_len, label, member_type, bracket_label)
            )
        for col in sorted(by_column.keys()):
            rows.append([f"Column {col}"])
            entries = sorted(by_column[col], key=lambda item: item[0])
            for idx, entry in enumerate(entries, start=1):
                rows.append([col, idx, int(round(entry[1])), entry[2], entry[3], entry[4]])

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
            "brackets_square": bracket_square,
            "brackets_swivel": bracket_swivel,
            "brackets_unknown": bracket_unknown,
            "brackets_total": bracket_total,
            "stub_arm_screws": total * 3,
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
