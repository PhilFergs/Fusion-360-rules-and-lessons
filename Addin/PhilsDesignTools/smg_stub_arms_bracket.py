import adsk.core
import adsk.fusion
import traceback
import os

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_StubArms_SetBracket"
CMD_NAME = "Stub Arms Set Bracket"
CMD_TOOLTIP = "Move selected stub arm lines into Square/Swivel sketches for export."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

SELECTION_INPUT_ID = "stub_arms_setbracket_lines"
TYPE_INPUT_ID = "stub_arms_setbracket_type"
INCLUDE_PAIR_ID = "stub_arms_setbracket_include_pair"
DELETE_ORIG_ID = "stub_arms_setbracket_delete_original"

POINT_TOL = 1e-4


class StubArmsBracketCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById(SELECTION_INPUT_ID):
                return

            sel = inputs.addSelectionInput(
                SELECTION_INPUT_ID,
                "Stub arm lines",
                "Select stub arm sketch lines to set bracket type"
            )
            sel.addSelectionFilter("SketchLines")
            sel.setSelectionLimits(1, 0)

            type_input = inputs.addDropDownCommandInput(
                TYPE_INPUT_ID,
                "Bracket type",
                adsk.core.DropDownStyles.TextListDropDownStyle,
            )
            type_input.listItems.add("Square", True, "")
            type_input.listItems.add("Swivel", False, "")

            inputs.addBoolValueInput(
                INCLUDE_PAIR_ID,
                "Include paired line",
                True,
                "",
                True,
            )
            inputs.addBoolValueInput(
                DELETE_ORIG_ID,
                "Delete original lines",
                True,
                "",
                True,
            )

            on_exec = StubArmsBracketExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)
        except:
            logger.log("Stub Arms Set Bracket UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Stub Arms Set Bracket UI failed:\n" + traceback.format_exc())


class StubArmsBracketExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log("Stub Arms Set Bracket failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Stub Arms Set Bracket failed:\n" + traceback.format_exc())


def _safe_entity_token(entity):
    try:
        return entity.entityToken
    except:
        return None


def _line_key(line):
    tok = _safe_entity_token(line)
    if tok:
        return tok
    return f"id:{id(line)}"


def _endpoint_tokens(line):
    tokens = []
    if not line:
        return tokens
    try:
        sp = line.startSketchPoint
        ep = line.endSketchPoint
    except:
        return tokens
    for pt in (sp, ep):
        if not pt:
            continue
        tok = _safe_entity_token(pt)
        tokens.append(tok if tok else f"id:{id(pt)}")
    return tokens


def _lines_share_endpoint(line_a, line_b):
    if not line_a or not line_b:
        return False
    toks_a = _endpoint_tokens(line_a)
    toks_b = _endpoint_tokens(line_b)
    if toks_a and toks_b:
        for ta in toks_a:
            if ta in toks_b:
                return True
    try:
        sp_a = line_a.startSketchPoint.worldGeometry
        ep_a = line_a.endSketchPoint.worldGeometry
        sp_b = line_b.startSketchPoint.worldGeometry
        ep_b = line_b.endSketchPoint.worldGeometry
    except:
        return False
    for pa in (sp_a, ep_a):
        for pb in (sp_b, ep_b):
            try:
                if pa.distanceTo(pb) <= POINT_TOL:
                    return True
            except:
                continue
    return False


def _collect_selected_lines(sel_input):
    lines = []
    seen = set()
    if not sel_input:
        return lines
    for i in range(sel_input.selectionCount):
        ent = sel_input.selection(i).entity
        line = adsk.fusion.SketchLine.cast(ent)
        if not line:
            continue
        key = _line_key(line)
        if key in seen:
            continue
        seen.add(key)
        lines.append(line)
    return lines


def _expand_with_pairs(lines):
    expanded = []
    seen = set()
    for line in lines:
        if not line:
            continue
        key = _line_key(line)
        if key in seen:
            continue
        seen.add(key)
        expanded.append(line)

        try:
            sk = line.parentSketch
        except:
            sk = None
        if not sk:
            continue
        try:
            sk_lines = sk.sketchCurves.sketchLines
        except:
            sk_lines = None
        if not sk_lines:
            continue
        for i in range(sk_lines.count):
            other = sk_lines.item(i)
            if not other or other == line:
                continue
            if not _lines_share_endpoint(line, other):
                continue
            other_key = _line_key(other)
            if other_key in seen:
                continue
            seen.add(other_key)
            expanded.append(other)
    return expanded


def _column_label_from_sketch_name(name):
    if not name:
        return "Unknown"
    prefix = "Stub Arms - "
    if name.startswith(prefix):
        trimmed = name[len(prefix):].strip()
        for suffix in (" - square", " - swivel"):
            if trimmed.lower().endswith(suffix):
                trimmed = trimmed[: -len(suffix)].strip()
        return trimmed if trimmed else name
    return name


def _find_sketch_by_name(comp, name):
    if not comp or not name:
        return None
    try:
        sketches = comp.sketches
    except:
        sketches = None
    if not sketches:
        return None
    name_lower = name.lower()
    for i in range(sketches.count):
        sk = sketches.item(i)
        try:
            if (sk.name or "").lower() == name_lower:
                return sk
        except:
            continue
    return None


def _unique_sketch_name(comp, base):
    if not comp:
        return base
    existing = set()
    try:
        sketches = comp.sketches
    except:
        sketches = None
    if sketches:
        for i in range(sketches.count):
            try:
                existing.add(sketches.item(i).name)
            except:
                pass
    if base not in existing:
        return base
    idx = 2
    while True:
        candidate = f"{base} ({idx})"
        if candidate not in existing:
            return candidate
        idx += 1


def _create_sketch_like(source_sketch, comp):
    if not source_sketch or not comp:
        return None
    try:
        sketches = comp.sketches
    except:
        return None
    ref = None
    try:
        ref = source_sketch.referencePlane
    except:
        ref = None
    if ref:
        try:
            return sketches.add(ref)
        except:
            pass
    try:
        ref = source_sketch.referenceGeometry
    except:
        ref = None
    if ref:
        try:
            return sketches.add(ref)
        except:
            pass
    try:
        ref = source_sketch.sketchPlane
    except:
        ref = None
    if ref:
        try:
            return sketches.add(ref)
        except:
            pass
    try:
        ref = source_sketch.plane
    except:
        ref = None
    if ref:
        try:
            return sketches.add(ref)
        except:
            pass
    return None


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


def _copy_line_to_sketch(line, target_sketch):
    if not line or not target_sketch:
        return None
    try:
        sp = line.startSketchPoint.worldGeometry
        ep = line.endSketchPoint.worldGeometry
    except:
        return None
    if not sp or not ep:
        return None
    try:
        sp_sk = target_sketch.modelToSketchSpace(sp)
        ep_sk = target_sketch.modelToSketchSpace(ep)
    except:
        sp_sk = sp
        ep_sk = ep
    try:
        return target_sketch.sketchCurves.sketchLines.addByTwoPoints(sp_sk, ep_sk)
    except:
        return None


def _execute(args):
    ui = ctx.ui()

    cmd = args.command
    inputs = cmd.commandInputs
    sel_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(SELECTION_INPUT_ID))
    type_input = adsk.core.DropDownCommandInput.cast(inputs.itemById(TYPE_INPUT_ID))
    include_pair_in = adsk.core.BoolValueCommandInput.cast(inputs.itemById(INCLUDE_PAIR_ID))
    delete_orig_in = adsk.core.BoolValueCommandInput.cast(inputs.itemById(DELETE_ORIG_ID))

    if not sel_input or sel_input.selectionCount == 0:
        ui.messageBox("Select one or more stub arm lines.")
        return

    bracket_type = "Square"
    if type_input:
        try:
            if type_input.selectedItem and type_input.selectedItem.name:
                bracket_type = type_input.selectedItem.name
        except:
            pass
    bracket_type = "Square" if bracket_type.lower().startswith("squ") else "Swivel"

    include_pairs = include_pair_in.value if include_pair_in else True
    delete_original = delete_orig_in.value if delete_orig_in else True

    lines = _collect_selected_lines(sel_input)
    if include_pairs:
        lines = _expand_with_pairs(lines)
    if not lines:
        ui.messageBox("No valid sketch lines found.")
        return

    moved = 0
    skipped = 0
    created = 0
    deleted = 0

    for line in lines:
        try:
            sk = line.parentSketch
        except:
            sk = None
        if not sk:
            skipped += 1
            continue

        try:
            comp = sk.parentComponent
        except:
            comp = None
        if not comp:
            skipped += 1
            continue

        try:
            sk_name = sk.name or ""
        except:
            sk_name = ""
        label = _column_label_from_sketch_name(sk_name)
        target_name = f"Stub Arms - {label} - {bracket_type}"

        if sk_name.lower() == target_name.lower():
            skipped += 1
            continue

        target_sk = _find_sketch_by_name(comp, target_name)
        if not target_sk:
            target_sk = _create_sketch_like(sk, comp)
            if not target_sk:
                skipped += 1
                continue
            try:
                target_sk.name = _unique_sketch_name(comp, target_name)
            except:
                pass
            _disable_sketch_profiles(target_sk)
            created += 1

        new_line = _copy_line_to_sketch(line, target_sk)
        if not new_line:
            skipped += 1
            continue
        moved += 1
        if delete_original:
            try:
                line.deleteMe()
                deleted += 1
            except:
                pass

    logger.log_command(
        CMD_NAME,
        {
            "selected": len(lines),
            "moved": moved,
            "created_sketches": created,
            "deleted": deleted,
            "skipped": skipped,
            "bracket_type": bracket_type,
            "include_pairs": include_pairs,
            "delete_original": delete_original,
        },
    )

    ui.messageBox(
        f"{CMD_NAME} complete.\n"
        f"Moved: {moved}\n"
        f"Created sketches: {created}\n"
        f"Deleted originals: {deleted}\n"
        f"Skipped: {skipped}"
    )


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = StubArmsBracketCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
