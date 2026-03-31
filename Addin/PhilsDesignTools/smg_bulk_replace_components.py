import adsk.core
import adsk.fusion
import traceback
import os

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_BulkReplaceComponents"
CMD_NAME = "Bulk Replace Components"
CMD_TOOLTIP = "Replace multiple external occurrences using one external replacement design."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

TARGETS_INPUT_ID = "bulk_replace_targets"
REPLACE_ALL_INPUT_ID = "bulk_replace_all_instances"


def _safe_add_selection_filter(sel, filter_name: str):
    try:
        sel.addSelectionFilter(filter_name)
        return True
    except:
        logger.log(f"{CMD_NAME}: Selection filter '{filter_name}' not supported; ignoring.")
        return False


def _resolve_occurrence_from_entity(entity, design):
    if not entity or not design:
        return None

    occ = adsk.fusion.Occurrence.cast(entity)
    if occ:
        return occ

    if hasattr(entity, "assemblyContext") and entity.assemblyContext:
        occ = entity.assemblyContext
        if occ:
            return occ

    return None


def _is_referenced_occurrence(occ):
    try:
        return bool(occ.isReferencedComponent)
    except:
        return False


def _pick_replacement_data_file(ui, app):
    dlg = None
    try:
        dlg = ui.createCloudFileDialog()
    except:
        dlg = None

    if not dlg:
        ui.messageBox(
            "Cloud file picker is not available in this Fusion build.\n"
            "Use Fusion's built-in Replace Component for this operation."
        )
        return None

    dlg.title = "Select replacement design"
    dlg.isMultiSelectEnabled = False

    try:
        active_doc = app.activeDocument
        if active_doc and active_doc.dataFile and active_doc.dataFile.parentFolder:
            dlg.dataFolder = active_doc.dataFile.parentFolder
    except:
        pass

    if dlg.showOpen() != adsk.core.DialogResults.DialogOK:
        return None

    try:
        picked = dlg.dataFile
        if not picked:
            ui.messageBox(
                "No replacement design was selected.\n\n"
                "If the list appears empty, check that the target folder contains Fusion design items "
                "and try again."
            )
            return None
        return picked
    except:
        return None


class BulkReplaceCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById(TARGETS_INPUT_ID):
                return

            targets = inputs.addSelectionInput(
                TARGETS_INPUT_ID,
                "Targets",
                "Select external occurrences to replace",
            )
            _safe_add_selection_filter(targets, "Occurrences")
            targets.setSelectionLimits(1, 0)

            inputs.addBoolValueInput(
                REPLACE_ALL_INPUT_ID,
                "Replace all instances",
                True,
                "",
                False,
            )

            on_exec = BulkReplaceExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)

        except:
            logger.log(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())


class BulkReplaceExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log(f"{CMD_NAME} failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} failed:\n" + traceback.format_exc())


def _execute(args):
    app = ctx.app()
    ui = ctx.ui()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("No active Fusion design.")
        return

    cmd = args.command
    inputs = cmd.commandInputs
    targets_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(TARGETS_INPUT_ID))
    replace_all_input = adsk.core.BoolValueCommandInput.cast(inputs.itemById(REPLACE_ALL_INPUT_ID))
    replace_all = bool(replace_all_input.value) if replace_all_input else False

    if not targets_input or targets_input.selectionCount == 0:
        ui.messageBox("Select at least one target occurrence.")
        return

    targets = []
    seen = set()
    for i in range(targets_input.selectionCount):
        entity = targets_input.selection(i).entity
        occ = _resolve_occurrence_from_entity(entity, design)
        if not occ:
            continue
        token = occ.entityToken
        if token in seen:
            continue
        seen.add(token)
        targets.append(occ)

    if not targets:
        ui.messageBox("No valid target occurrences found in selection.")
        return

    external_targets = []
    skipped_non_external = 0
    for occ in targets:
        if _is_referenced_occurrence(occ):
            external_targets.append(occ)
        else:
            skipped_non_external += 1

    if not external_targets:
        ui.messageBox(
            "None of the selected occurrences are external references.\n\n"
            "This command works with external components only."
        )
        return

    replacement_data_file = _pick_replacement_data_file(ui, app)
    if not replacement_data_file:
        return

    replacement_name = ""
    try:
        replacement_name = replacement_data_file.name or "<selected file>"
    except:
        replacement_name = "<selected file>"

    if replace_all:
        confirm_msg = (
            f"Replacement file: {replacement_name}\n\n"
            f"Selected external targets: {len(external_targets)}\n"
            f"Skipped non-external: {skipped_non_external}\n\n"
            "Replace all instances is ON.\n"
            "For each selected component type, all matching instances in this design may be replaced.\n\n"
            "Continue?"
        )
    else:
        confirm_msg = (
            f"Replacement file: {replacement_name}\n\n"
            f"Selected external targets: {len(external_targets)}\n"
            f"Skipped non-external: {skipped_non_external}\n\n"
            "Continue?"
        )

    result = ui.messageBox(
        confirm_msg,
        CMD_NAME,
        adsk.core.MessageBoxButtonTypes.YesNoButtonType,
        adsk.core.MessageBoxIconTypes.WarningIconType,
    )
    if result != adsk.core.DialogResults.DialogYes:
        return

    operations = []
    if replace_all:
        seen_components = set()
        for occ in external_targets:
            comp_token = None
            try:
                comp_token = occ.component.entityToken
            except:
                comp_token = occ.entityToken
            if comp_token in seen_components:
                continue
            seen_components.add(comp_token)
            operations.append(occ)
    else:
        operations = external_targets

    succeeded = 0
    failed = []

    for occ in operations:
        label = ""
        try:
            label = occ.name or occ.component.name
        except:
            label = "<unknown>"

        try:
            ok = occ.replace(replacement_data_file, replace_all)
            if ok:
                succeeded += 1
            else:
                failed.append(f"{label}: replace returned False")
        except Exception as ex:
            failed.append(f"{label}: {ex}")

    logger.log_command(
        CMD_NAME,
        {
            "targets_selected": len(targets),
            "external_targets": len(external_targets),
            "operations": len(operations),
            "replace_all_instances": replace_all,
            "replacement_file": replacement_name,
            "succeeded": succeeded,
            "failed": len(failed),
            "skipped_non_external": skipped_non_external,
        },
    )

    if failed:
        sample = "\n".join(failed[:10])
        ui.messageBox(
            f"Completed with issues.\n\n"
            f"Successful operations: {succeeded}\n"
            f"Failed operations: {len(failed)}\n"
            f"Skipped non-external: {skipped_non_external}\n\n"
            f"Sample failures:\n{sample}",
            CMD_NAME,
        )
        return

    ui.messageBox(
        f"Bulk replace complete.\n\n"
        f"Successful operations: {succeeded}\n"
        f"Skipped non-external: {skipped_non_external}",
        CMD_NAME,
    )


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = BulkReplaceCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
