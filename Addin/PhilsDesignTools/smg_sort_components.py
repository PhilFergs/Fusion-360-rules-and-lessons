import adsk.core
import adsk.fusion
import traceback
import os
import re

import smg_context as ctx
import smg_logger as logger


CMD_ID = "PhilsDesignTools_SortComponents"
CMD_NAME = "Sort Components"
CMD_TOOLTIP = "Sort child occurrences by name under selected parent components."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

SELECTION_INPUT_ID = "sort_components_selection"
WHOLE_INPUT_ID = "sort_components_whole"
RECURSIVE_INPUT_ID = "sort_components_recursive"

DEBUG_SORT = False


def _dbg(message):
    if DEBUG_SORT:
        logger.log(f"{CMD_NAME} DEBUG: {message}")


def _safe_add_selection_filter(sel, filter_name: str):
    try:
        sel.addSelectionFilter(filter_name)
        return True
    except:
        logger.log(f"{CMD_NAME}: Selection filter '{filter_name}' not supported; ignoring.")
        return False


def _natural_key(name: str):
    parts = re.split(r"(\d+)", name or "")
    key = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part.lower())
    return key


def _iter_parent_components_from_selection(sel_input):
    comps = []
    tokens = set()
    if not sel_input:
        return comps
    for i in range(sel_input.selectionCount):
        ent = sel_input.selection(i).entity
        occ = adsk.fusion.Occurrence.cast(ent)
        comp = adsk.fusion.Component.cast(ent)
        if occ:
            comp = occ.component
        if not comp:
            continue
        token = comp.entityToken
        if token in tokens:
            continue
        tokens.add(token)
        comps.append(comp)
    return comps


def _collect_components_recursive(root_comp):
    out = []

    def walk(comp):
        out.append(comp)
        for occ in comp.occurrences:
            if occ.component:
                walk(occ.component)

    walk(root_comp)
    return out


def _sort_occurrences_in_component(comp, timeline):
    occs = [occ for occ in comp.occurrences]
    if len(occs) < 2:
        return 0, 0, 0

    items = []
    for occ in occs:
        try:
            tl = occ.timelineObject
        except:
            tl = None
        if not tl or tl.index < 0:
            continue
        items.append((occ, tl))

    if len(items) < 2:
        return 0, 0, 0

    anchor = min(tl.index for _, tl in items)
    items_sorted = sorted(items, key=lambda it: _natural_key(it[0].name or it[0].component.name))

    moved = 0
    skipped = 0
    failed = 0

    # Reorder in reverse, placing each item before the anchor index.
    for occ, tl in reversed(items_sorted):
        try:
            if not tl.canReorder(anchor):
                skipped += 1
                continue
            ok = tl.reorder(anchor)
            if ok:
                moved += 1
            else:
                failed += 1
        except:
            failed += 1

    _dbg(f"Sorted '{comp.name}': moved={moved} skipped={skipped} failed={failed}")
    return moved, skipped, failed


class SortComponentsExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log(f"{CMD_NAME} failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} failed:\n" + traceback.format_exc())


class SortComponentsInputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            inp = args.input
            if inp.id == WHOLE_INPUT_ID:
                inputs = args.inputs
                sel = adsk.core.SelectionCommandInput.cast(inputs.itemById(SELECTION_INPUT_ID))
                if sel:
                    sel.isEnabled = not inp.value
        except:
            pass


class SortComponentsCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById(SELECTION_INPUT_ID):
                return

            whole = inputs.addBoolValueInput(WHOLE_INPUT_ID, "Sort entire design", True, "", False)
            inputs.addBoolValueInput(RECURSIVE_INPUT_ID, "Include nested components", True, "", True)

            sel = inputs.addSelectionInput(
                SELECTION_INPUT_ID,
                "Parents",
                "Select parent components or occurrences to sort"
            )
            _safe_add_selection_filter(sel, "Occurrences")
            _safe_add_selection_filter(sel, "Components")
            sel.setSelectionLimits(0, 0)
            sel.isEnabled = not whole.value

            on_exec = SortComponentsExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)

            on_changed = SortComponentsInputChangedHandler()
            cmd.inputChanged.add(on_changed)
            ctx.add_handler(on_changed)

        except:
            logger.log(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())


def _execute(args):
    app = ctx.app()
    ui = ctx.ui()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("No active design.")
        return

    if design.designType == adsk.fusion.DesignTypes.DirectDesignType:
        result = ui.messageBox(
            "Design history is off (Direct Modeling).\n\n"
            "To sort components, Fusion needs the timeline. "
            "Enable history and continue?\n\n"
            "This converts the design to Parametric.",
            "Enable Design History?",
            adsk.core.MessageBoxButtonTypes.YesNoButtonType,
            adsk.core.MessageBoxIconTypes.WarningIconType,
        )
        if result != adsk.core.DialogResults.DialogYes:
            return
        try:
            ok = design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            if ok is False:
                ui.messageBox("Failed to enable design history.")
                return
        except:
            ui.messageBox("Failed to enable design history.")
            return

    timeline = design.timeline
    if not timeline:
        ui.messageBox("No timeline available.")
        return

    # Ensure the marker is at the end (required for reorder).
    try:
        timeline.moveToEnd()
    except:
        pass

    cmd = args.command
    inputs = cmd.commandInputs
    whole = adsk.core.BoolValueCommandInput.cast(inputs.itemById(WHOLE_INPUT_ID))
    recursive = adsk.core.BoolValueCommandInput.cast(inputs.itemById(RECURSIVE_INPUT_ID))
    sel_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(SELECTION_INPUT_ID))

    sort_all = bool(whole.value) if whole else False
    include_nested = bool(recursive.value) if recursive else True

    parents = []
    if sort_all:
        parents = [design.rootComponent]
    else:
        parents = _iter_parent_components_from_selection(sel_input)
        if not parents:
            ui.messageBox("Select at least one parent component, or enable 'Sort entire design'.")
            return

    targets = []
    if include_nested:
        tokens = set()
        for comp in parents:
            for c in _collect_components_recursive(comp):
                if c.entityToken not in tokens:
                    tokens.add(c.entityToken)
                    targets.append(c)
    else:
        targets = parents

    moved_total = 0
    skipped_total = 0
    failed_total = 0

    for comp in targets:
        moved, skipped, failed = _sort_occurrences_in_component(comp, timeline)
        moved_total += moved
        skipped_total += skipped
        failed_total += failed

    logger.log_command(
        CMD_NAME,
        {
            "parents": len(parents),
            "targets": len(targets),
            "moved": moved_total,
            "skipped": skipped_total,
            "failed": failed_total,
            "whole_design": sort_all,
            "recursive": include_nested,
        },
    )

    ui.messageBox(
        "Sort complete.\n\n"
        f"Moved: {moved_total}\n"
        f"Skipped: {skipped_total}\n"
        f"Failed: {failed_total}"
    )


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = SortComponentsCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
