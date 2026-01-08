import adsk.core
import adsk.fusion
import traceback
import os
import re

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_IGES_Export"
CMD_NAME = "IGES Component Export"
CMD_TOOLTIP = "Export selected leaf components to IGES files."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

SELECTION_INPUT_ID = "iges_export_selection"


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[<>:\"/\\|?*]", "_", name).strip()
    return name if name else "Component"


def is_linked_occurrence(occ: adsk.fusion.Occurrence) -> bool:
    try:
        return occ.isReferencedComponent
    except:
        return False


def occurrence_or_ancestors_linked(occ: adsk.fusion.Occurrence) -> bool:
    current = occ
    while current is not None:
        if is_linked_occurrence(current):
            return True
        current = current.assemblyContext
    return False


def component_branch_is_linked(design: adsk.fusion.Design, comp: adsk.fusion.Component) -> bool:
    all_occs = design.rootComponent.allOccurrences
    for i in range(all_occs.count):
        occ = all_occs.item(i)
        if occ.component == comp:
            if occurrence_or_ancestors_linked(occ):
                return True
    return False


def is_parent_component(design, comp):
    root = design.rootComponent
    if comp == root:
        return True
    occs = comp.occurrences
    return bool(occs and occs.count > 0)


def extract_leaf_components(comp):
    results = []

    def walk(c):
        if c.occurrences.count == 0:
            results.append(c)
        else:
            for o in c.occurrences:
                walk(o.component)

    walk(comp)
    return results


def resolve_selection_to_leaf_components(sel_input, design):
    if not sel_input or sel_input.selectionCount == 0:
        return []

    export_list = []
    tokens = set()

    for i in range(sel_input.selectionCount):
        ent = sel_input.selection(i).entity

        occ = adsk.fusion.Occurrence.cast(ent)
        comp = adsk.fusion.Component.cast(ent)
        body = adsk.fusion.BRepBody.cast(ent)

        if body:
            comp = body.parentComponent
        if occ:
            comp = occ.component
        if not comp:
            continue

        if is_parent_component(design, comp):
            for leaf in extract_leaf_components(comp):
                if leaf.entityToken not in tokens:
                    tokens.add(leaf.entityToken)
                    export_list.append(leaf)
        else:
            if comp.entityToken not in tokens:
                tokens.add(comp.entityToken)
                export_list.append(comp)

    return export_list


def choose_export_folder(ui):
    dlg = ui.createFileDialog()
    dlg.title = "Choose export folder"
    dlg.filter = "IGES (*.iges;*.igs)"
    dlg.initialFilename = "dummy.iges"
    if dlg.showSave() != adsk.core.DialogResults.DialogOK:
        return None
    return os.path.dirname(dlg.filename)


class IGESExportCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById(SELECTION_INPUT_ID):
                return

            sel = inputs.addSelectionInput(
                SELECTION_INPUT_ID,
                "Selection",
                "Select components, occurrences, or bodies to export"
            )
            sel.addSelectionFilter("Bodies")
            sel.addSelectionFilter("Occurrences")
            sel.addSelectionFilter("Components")
            sel.setSelectionLimits(1, 0)

            on_exec = IGESExportExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)

        except:
            logger.log("IGES Export UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("IGES Export UI failed:\n" + traceback.format_exc())


class IGESExportExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log("IGES Export failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("IGES Export failed:\n" + traceback.format_exc())


def _execute(args):
    app = ctx.app()
    ui = ctx.ui()

    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("No active design.")
        return

    cmd = args.command
    inputs = cmd.commandInputs
    sel_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(SELECTION_INPUT_ID))

    comps = resolve_selection_to_leaf_components(sel_input, design)
    if not comps:
        ui.messageBox("No sub-components to export.")
        return

    linked_branches = [c for c in comps if component_branch_is_linked(design, c)]

    skip_linked = False
    if linked_branches:
        preview = ", ".join(c.name for c in linked_branches[:5])
        if len(linked_branches) > 5:
            preview += ", ..."

        result = ui.messageBox(
            "Linked components or linked parent branches detected:\n"
            f"{preview}\n\n"
            "Do you want to export linked components?\n"
            "YES = export all\nNO = skip all linked branches",
            "Linked Component Warning",
            adsk.core.MessageBoxButtonTypes.YesNoButtonType,
            adsk.core.MessageBoxIconTypes.WarningIconType,
        )

        if result == adsk.core.DialogResults.DialogNo:
            skip_linked = True

    if skip_linked:
        comps = [c for c in comps if not component_branch_is_linked(design, c)]
        if not comps:
            ui.messageBox("All candidates were in linked branches - nothing to export.")
            return

    folder = choose_export_folder(ui)
    if not folder:
        return

    export_mgr = design.exportManager
    name_count = {}
    count = 0

    for comp in comps:
        full_name = (comp.name or "").strip()
        prefix = full_name.split("-")[0] if "-" in full_name else full_name
        prefix = sanitize_filename(prefix)

        if prefix not in name_count:
            name_count[prefix] = 1
            final = prefix
        else:
            name_count[prefix] += 1
            final = f"{prefix}_{name_count[prefix]}"

        path = os.path.join(folder, final + ".iges")

        opts = export_mgr.createIGESExportOptions(path, comp)
        export_mgr.execute(opts)
        count += 1

    logger.log_command(
        CMD_NAME,
        {
            "exported": count,
            "folder": folder,
            "skip_linked": skip_linked,
        },
    )

    ui.messageBox(f"Exported {count} IGES files to:\n{folder}")


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = IGESExportCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
