import adsk.core
import adsk.fusion
import os
import traceback

import smg_context as ctx
import smg_logger as logger


CMD_ID = "PhilsDesignTools_MovePreservePosition"
CMD_NAME = "Move Preserve Position"
CMD_TOOLTIP = "Move selected component occurrences into a new parent while preserving model-space position."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

SOURCES_INPUT_ID = "move_preserve_sources"
TARGET_INPUT_ID = "move_preserve_target"

DEBUG_MOVE_PRESERVE = True


def _dbg(message):
    if DEBUG_MOVE_PRESERVE:
        logger.log(f"MOVE_PRESERVE: {message}")


def _safe_add_selection_filter(sel, filter_name):
    try:
        sel.addSelectionFilter(filter_name)
        return True
    except:
        logger.log(f"MOVE_PRESERVE: selection filter '{filter_name}' not supported; ignoring")
        return False


def _occurrence_name(occ):
    if not occ:
        return "<root>"
    for attr in ("fullPathName", "name"):
        try:
            value = getattr(occ, attr)
            if value:
                return str(value)
        except:
            pass
    return "<occurrence>"


def _occurrence_path(occ):
    try:
        return str(occ.fullPathName or occ.name or "")
    except:
        return _occurrence_name(occ)


def _occurrence_token(occ):
    if not occ:
        return ""
    for attr in ("entityToken", "fullPathName", "name"):
        try:
            value = getattr(occ, attr)
            if value:
                return str(value)
        except:
            pass
    return str(id(occ))


def _matrix_to_text(matrix):
    if not matrix:
        return "<null>"
    try:
        rows = []
        for r in range(4):
            vals = []
            for c in range(4):
                vals.append(f"{matrix.getCell(r, c):.6f}")
            rows.append("[" + ", ".join(vals) + "]")
        return " ".join(rows)
    except:
        return "<matrix>"


def _resolve_occurrence_from_entity(entity):
    if not entity:
        return None

    occ = adsk.fusion.Occurrence.cast(entity)
    if occ:
        return occ

    try:
        if hasattr(entity, "assemblyContext") and entity.assemblyContext:
            return entity.assemblyContext
    except:
        pass

    return None


def _selected_occurrences(sel_input):
    out = []
    seen = set()
    if not sel_input:
        return out

    for i in range(sel_input.selectionCount):
        try:
            entity = sel_input.selection(i).entity
        except:
            continue
        occ = _resolve_occurrence_from_entity(entity)
        if not occ:
            continue
        token = _occurrence_token(occ)
        if token in seen:
            continue
        seen.add(token)
        out.append(occ)

    return out


def _selected_single_occurrence(sel_input):
    if not sel_input or sel_input.selectionCount < 1:
        return None
    try:
        return _resolve_occurrence_from_entity(sel_input.selection(0).entity)
    except:
        return None


def _root_context_occurrence(design, occ):
    if not design or not occ:
        return occ

    path = _occurrence_path(occ)
    token = _occurrence_token(occ)
    try:
        all_occs = design.rootComponent.allOccurrences
        for i in range(all_occs.count):
            candidate = all_occs.item(i)
            if not candidate:
                continue
            if path and _occurrence_path(candidate) == path:
                return candidate
            if token and _occurrence_token(candidate) == token:
                return candidate
    except Exception as ex:
        logger.log(
            f"MOVE_PRESERVE: root occurrence lookup failed "
            + f"occurrence='{_occurrence_name(occ)}': {ex}"
        )

    return occ


def _is_linked_occurrence(occ):
    if not occ:
        return False
    for attr in ("isReferencedComponent", "isExternalReference"):
        try:
            if bool(getattr(occ, attr)):
                return True
        except:
            pass
    try:
        comp = occ.component
        for attr in ("isReferencedComponent", "isExternalReference"):
            try:
                if bool(getattr(comp, attr)):
                    return True
            except:
                pass
    except:
        pass
    return False


def _occurrence_or_ancestors_linked(occ):
    current = occ
    while current is not None:
        if _is_linked_occurrence(current):
            return True
        try:
            current = current.assemblyContext
        except:
            current = None
    return False


def _occurrence_transform(occ):
    if not occ:
        return None
    for attr in ("transform2", "transform"):
        try:
            matrix = getattr(occ, attr)
            if matrix:
                return matrix.copy()
        except:
            pass
    return None


def _restore_occurrence_transform(design, occurrence, matrix, reason):
    if not occurrence:
        logger.log(f"MOVE_PRESERVE: transform restore skipped reason='{reason}' occurrence=null")
        return False
    if not matrix:
        logger.log(
            f"MOVE_PRESERVE: transform restore skipped reason='{reason}' "
            + f"occurrence='{_occurrence_name(occurrence)}' matrix=null"
        )
        return False

    try:
        if design and design.rootComponent:
            ok = design.rootComponent.transformOccurrences([occurrence], [matrix.copy()], True)
            if ok:
                logger.log(
                    f"MOVE_PRESERVE: transform restored reason='{reason}' "
                    + f"route='root.transformOccurrences' occurrence='{_occurrence_name(occurrence)}'"
                )
                return True
            logger.log(
                f"MOVE_PRESERVE: transform restore returned false reason='{reason}' "
                + f"route='root.transformOccurrences' occurrence='{_occurrence_name(occurrence)}'"
            )
    except Exception as ex:
        logger.log(
            f"MOVE_PRESERVE: transform restore failed reason='{reason}' "
            + f"route='root.transformOccurrences' occurrence='{_occurrence_name(occurrence)}': {ex}"
        )

    for attr in ("transform2", "transform"):
        try:
            setattr(occurrence, attr, matrix.copy())
            logger.log(
                f"MOVE_PRESERVE: transform restored reason='{reason}' "
                + f"route='{attr}' occurrence='{_occurrence_name(occurrence)}'"
            )
            return True
        except Exception as ex:
            logger.log(
                f"MOVE_PRESERVE: transform restore failed reason='{reason}' "
                + f"route='{attr}' occurrence='{_occurrence_name(occurrence)}': {ex}"
            )
    return False


def _is_same_occurrence(a, b):
    if not a or not b:
        return False
    return _occurrence_path(a) == _occurrence_path(b)


def _is_target_inside_source(source_occ, target_parent_occ):
    source_path = _occurrence_path(source_occ)
    target_path = _occurrence_path(target_parent_occ)
    if not source_path or not target_path:
        return False
    return target_path == source_path or target_path.startswith(source_path + "+")


def _current_parent_occurrence(occ):
    try:
        return occ.assemblyContext
    except:
        return None


def _move_one(design, source_occ, target_parent_occ):
    source_occ = _root_context_occurrence(design, source_occ)
    target_parent_occ = _root_context_occurrence(design, target_parent_occ)
    source_name = _occurrence_name(source_occ)
    target_name = _occurrence_name(target_parent_occ)

    if not source_occ:
        return False, "selection did not resolve to an occurrence", None
    if not target_parent_occ:
        return False, "target parent did not resolve to an occurrence", None
    if _is_same_occurrence(source_occ, target_parent_occ):
        return False, "source is the target parent", None
    if _is_target_inside_source(source_occ, target_parent_occ):
        return False, "target parent is inside the source occurrence", None
    if _occurrence_or_ancestors_linked(source_occ):
        return False, "source occurrence or one of its parents is linked/read-only", None
    if _occurrence_or_ancestors_linked(target_parent_occ):
        return False, "target parent or one of its parents is linked/read-only", None

    current_parent = _current_parent_occurrence(source_occ)
    if current_parent and _is_same_occurrence(current_parent, target_parent_occ):
        return False, "source is already directly under the target parent", None

    saved_matrix = _occurrence_transform(source_occ)
    if not saved_matrix:
        return False, "could not capture source model-space transform", None

    _dbg(
        "captured "
        + f"source='{source_name}' target_parent='{target_name}' "
        + f"matrix={_matrix_to_text(saved_matrix)}"
    )

    try:
        moved_occ = source_occ.moveToComponent(target_parent_occ)
    except Exception as ex:
        return False, f"moveToComponent failed: {ex}", None

    if not moved_occ:
        return False, "moveToComponent returned null", None

    restored = _restore_occurrence_transform(
        design,
        moved_occ,
        saved_matrix,
        "preserve world transform after reparent",
    )
    if not restored:
        return False, "moved but transform restore failed", moved_occ

    _dbg(
        "moved "
        + f"source='{source_name}' result='{_occurrence_name(moved_occ)}' "
        + f"target_parent='{target_name}'"
    )
    return True, "", moved_occ


class MovePreserveExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log(f"{CMD_NAME} failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} failed:\n" + traceback.format_exc())


class MovePreserveCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById(SOURCES_INPUT_ID):
                return

            info = (
                "Moves selected component occurrences into the selected target parent occurrence, "
                "then restores their root/model-space transform so they do not visually shift."
            )
            inputs.addTextBoxCommandInput("move_preserve_info", "", info, 3, True)

            sources = inputs.addSelectionInput(
                SOURCES_INPUT_ID,
                "Components to move",
                "Select one or more component occurrences to move",
            )
            _safe_add_selection_filter(sources, "Occurrences")
            sources.setSelectionLimits(1, 0)

            target = inputs.addSelectionInput(
                TARGET_INPUT_ID,
                "Target parent",
                "Select the occurrence that should become the new parent",
            )
            _safe_add_selection_filter(target, "Occurrences")
            target.setSelectionLimits(1, 1)

            on_exec = MovePreserveExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)

        except:
            logger.log(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())


def _execute(args):
    ui = ctx.ui()
    app = ctx.app()
    design = adsk.fusion.Design.cast(app.activeProduct) if app else None
    if not design:
        ui.messageBox("No active Fusion design.")
        return

    cmd = args.command
    inputs = cmd.commandInputs
    sources_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(SOURCES_INPUT_ID))
    target_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(TARGET_INPUT_ID))

    sources = _selected_occurrences(sources_input)
    target_parent = _selected_single_occurrence(target_input)

    if not sources:
        ui.messageBox("Select at least one component occurrence to move.", CMD_NAME)
        return
    if not target_parent:
        ui.messageBox("Select a target parent occurrence.", CMD_NAME)
        return

    logger.log(
        f"MOVE_PRESERVE: execute sources={len(sources)} "
        + f"target_parent='{_occurrence_name(target_parent)}'"
    )

    moved_count = 0
    skipped = []
    failed = []

    for source_occ in sources:
        source_name = _occurrence_name(source_occ)
        try:
            ok, reason, moved_occ = _move_one(design, source_occ, target_parent)
            if ok:
                moved_count += 1
            else:
                item = f"{source_name}: {reason}"
                if moved_occ:
                    failed.append(item)
                else:
                    skipped.append(item)
                logger.log(f"MOVE_PRESERVE: skipped source='{source_name}' reason='{reason}'")
        except Exception as ex:
            failed.append(f"{source_name}: {ex}")
            logger.log(
                f"MOVE_PRESERVE: failed source='{source_name}' "
                + f"target_parent='{_occurrence_name(target_parent)}': {ex}"
            )

    logger.log(
        f"MOVE_PRESERVE: complete moved={moved_count} skipped={len(skipped)} failed={len(failed)}"
    )

    if skipped or failed:
        details = []
        if skipped:
            details.append("Skipped:\n" + "\n".join(skipped[:10]))
        if failed:
            details.append("Failed:\n" + "\n".join(failed[:10]))
        ui.messageBox(
            f"Move complete with issues.\n\n"
            f"Moved: {moved_count}\n"
            f"Skipped: {len(skipped)}\n"
            f"Failed: {len(failed)}\n\n"
            + "\n\n".join(details),
            CMD_NAME,
        )
        return

    ui.messageBox(f"Move complete.\n\nMoved: {moved_count}", CMD_NAME)


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = MovePreserveCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
