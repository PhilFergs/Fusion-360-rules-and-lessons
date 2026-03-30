import adsk.core
import adsk.fusion
import traceback
import os
import re

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_IGES_Export"
CMD_NAME = "Multi Part File Export"
CMD_TOOLTIP = "Export selected leaf components to multiple file formats."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

SELECTION_INPUT_ID = "iges_export_selection"
FORMAT_INPUT_ID = "multi_export_format"

EXPORT_FORMATS = [
    {
        "key": "step",
        "label": "STEP (.step)",
        "extension": ".step",
        "methods": ["createSTEPExportOptions"],
    },
    {
        "key": "stl",
        "label": "STL (.stl)",
        "extension": ".stl",
        "methods": ["createSTLExportOptions"],
    },
    {
        "key": "iges",
        "label": "IGES (.iges)",
        "extension": ".iges",
        "methods": ["createIGESExportOptions"],
    },
    {
        "key": "sat",
        "label": "SAT (.sat)",
        "extension": ".sat",
        "methods": ["createSATExportOptions"],
    },
    {
        "key": "smt",
        "label": "SMT (.smt)",
        "extension": ".smt",
        "methods": ["createSMTExportOptions"],
    },
    {
        "key": "f3d",
        "label": "Fusion Archive (.f3d)",
        "extension": ".f3d",
        "methods": ["createFusionArchiveExportOptions"],
    },
    {
        "key": "rhino_3dm",
        "label": "Rhino 3DM (.3dm)",
        "extension": ".3dm",
        "methods": ["create3DMExportOptions", "createRhino3DMExportOptions"],
        "show_when_unavailable": True,
        "unavailable_reason": "Rhino 3DM export is not exposed via the Fusion add-in export API in this Fusion build.",
    },
]

DEFAULT_EXPORT_FORMAT_KEY = "step"


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


def choose_export_folder(ui, export_format):
    dlg = ui.createFileDialog()
    ext = export_format["extension"]
    dlg.title = "Choose export folder"
    dlg.filter = f"{export_format['label']} (*{ext})"
    dlg.initialFilename = "dummy" + ext
    if dlg.showSave() != adsk.core.DialogResults.DialogOK:
        return None
    return os.path.dirname(dlg.filename)


def _safe_add_selection_filter(sel, filter_name: str):
    try:
        sel.addSelectionFilter(filter_name)
        return True
    except:
        logger.log(f"{CMD_NAME}: Selection filter '{filter_name}' not supported; ignoring.")
        return False


def _active_design():
    app = ctx.app()
    if not app:
        return None
    return adsk.fusion.Design.cast(app.activeProduct)


def _resolve_export_method(export_mgr, export_format):
    for method_name in export_format.get("methods", []):
        method = getattr(export_mgr, method_name, None)
        if callable(method):
            return method_name
    return None


def _available_export_formats(design):
    if not design:
        return []

    export_mgr = design.exportManager
    formats = []
    for export_format in EXPORT_FORMATS:
        resolved_method = _resolve_export_method(export_mgr, export_format)
        if resolved_method:
            fmt = dict(export_format)
            fmt["method"] = resolved_method
            formats.append(fmt)
        elif export_format.get("show_when_unavailable", False):
            fmt = dict(export_format)
            fmt["method"] = None
            formats.append(fmt)
    return formats


def _selected_export_format(inputs, available_formats):
    if not available_formats:
        return None

    default_format = next(
        (f for f in available_formats if f["key"] == DEFAULT_EXPORT_FORMAT_KEY),
        available_formats[0],
    )

    dd = adsk.core.DropDownCommandInput.cast(inputs.itemById(FORMAT_INPUT_ID))
    if not dd or not dd.selectedItem:
        return default_format

    by_label = {f["label"]: f for f in available_formats}
    return by_label.get(dd.selectedItem.name, default_format)


def _call_export_method(export_mgr, method_name, arg_sets):
    method = getattr(export_mgr, method_name, None)
    if not callable(method):
        return None, f"Export method '{method_name}' is not available in this Fusion build."

    last_err = None
    for args in arg_sets:
        try:
            opts = method(*args)
            if opts:
                return opts, None
        except TypeError as ex:
            last_err = ex
        except Exception as ex:
            last_err = ex
            break

    if last_err:
        return None, str(last_err)
    return None, "Fusion did not return export options for this format."


def _create_export_options(export_mgr, export_format, out_path, comp):
    key = export_format["key"]
    method_name = export_format.get("method")

    if not method_name:
        reason = export_format.get("unavailable_reason") or "Export method is not available in this Fusion build."
        return None, reason

    if key == "stl":
        opts, err = _call_export_method(
            export_mgr,
            method_name,
            [
                (comp, out_path),
                (out_path, comp),
                (comp,),
            ],
        )
        if opts and hasattr(opts, "filename"):
            try:
                opts.filename = out_path
            except:
                pass
        return opts, err

    return _call_export_method(
        export_mgr,
        method_name,
        [
            (out_path, comp),
            (out_path,),
            (comp, out_path),
        ],
    )


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
                "Select components, occurrences, or bodies to export",
            )
            _safe_add_selection_filter(sel, "Bodies")
            _safe_add_selection_filter(sel, "Occurrences")
            _safe_add_selection_filter(sel, "Components")
            sel.setSelectionLimits(1, 0)

            design = _active_design()
            available_formats = _available_export_formats(design)
            if not available_formats:
                ui = ctx.ui()
                if ui:
                    ui.messageBox("No supported export formats were found in this Fusion build.")
                return

            dd = inputs.addDropDownCommandInput(
                FORMAT_INPUT_ID,
                "File type",
                adsk.core.DropDownStyles.TextListDropDownStyle,
            )
            default_key = DEFAULT_EXPORT_FORMAT_KEY if any(
                f["key"] == DEFAULT_EXPORT_FORMAT_KEY for f in available_formats
            ) else available_formats[0]["key"]
            for fmt in available_formats:
                dd.listItems.add(fmt["label"], fmt["key"] == default_key, "")

            on_exec = IGESExportExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)

        except:
            logger.log(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())


class IGESExportExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log(f"{CMD_NAME} failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} failed:\n" + traceback.format_exc())


def _execute(args):
    app = ctx.app()
    ui = ctx.ui()

    design = _active_design()
    if not design:
        ui.messageBox("No active design.")
        return

    cmd = args.command
    inputs = cmd.commandInputs
    sel_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(SELECTION_INPUT_ID))
    available_formats = _available_export_formats(design)
    if not available_formats:
        ui.messageBox("No supported export formats were found in this Fusion build.")
        return
    export_format = _selected_export_format(inputs, available_formats)

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

    folder = choose_export_folder(ui, export_format)
    if not folder:
        return

    export_mgr = design.exportManager
    name_count = {}
    count = 0
    failures = []

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

        path = os.path.join(folder, final + export_format["extension"])

        opts, err = _create_export_options(export_mgr, export_format, path, comp)
        if not opts:
            failures.append(f"{comp.name}: {err}")
            continue

        try:
            export_mgr.execute(opts)
            count += 1
        except Exception as ex:
            failures.append(f"{comp.name}: {ex}")

    logger.log_command(
        CMD_NAME,
        {
            "format": export_format["key"],
            "exported": count,
            "failed": len(failures),
            "folder": folder,
            "skip_linked": skip_linked,
        },
    )

    if count == 0 and failures:
        sample = "\n".join(failures[:5])
        ui.messageBox(
            f"No files exported for {export_format['label']}.\n\n"
            f"Sample errors:\n{sample}"
        )
        return

    if failures:
        sample = "\n".join(failures[:5])
        ui.messageBox(
            f"Exported {count} {export_format['label']} files to:\n{folder}\n\n"
            f"{len(failures)} item(s) failed.\nSample:\n{sample}"
        )
        return

    ui.messageBox(f"Exported {count} {export_format['label']} files to:\n{folder}")


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
