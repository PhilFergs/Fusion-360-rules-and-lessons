import adsk.core
import adsk.fusion
import traceback
import re
import os

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_ComponentSet"
CMD_NAME = "New Component Set"
CMD_TOOLTIP = "Create a range of new components by prefix and index."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

PREFIX_INPUT_ID = "component_set_prefix"
RANGE_INPUT_ID = "component_set_range"
SUFFIX_INPUT_ID = "component_set_suffix"


def _parse_range(text: str):
    m = re.match(r"^\s*(-?\d+)\s*-\s*(-?\d+)\s*$", text)
    if not m:
        return None
    a = int(m.group(1))
    b = int(m.group(2))
    if a > b:
        return None
    return a, b


class ComponentSetCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById(PREFIX_INPUT_ID):
                return

            inputs.addStringValueInput(PREFIX_INPUT_ID, "Prefix", "SC")
            inputs.addStringValueInput(RANGE_INPUT_ID, "Number range", "1-18")
            inputs.addStringValueInput(SUFFIX_INPUT_ID, "Suffix", "-AS")

            on_exec = ComponentSetExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)

        except:
            logger.log("New Component Set UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("New Component Set UI failed:\n" + traceback.format_exc())


class ComponentSetExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log("New Component Set failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("New Component Set failed:\n" + traceback.format_exc())


def _execute(args):
    ui = ctx.ui()
    app = ctx.app()

    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("No active Fusion design.")
        return

    cmd = args.command
    inputs = cmd.commandInputs

    prefix_input = adsk.core.StringValueCommandInput.cast(inputs.itemById(PREFIX_INPUT_ID))
    range_input = adsk.core.StringValueCommandInput.cast(inputs.itemById(RANGE_INPUT_ID))
    suffix_input = adsk.core.StringValueCommandInput.cast(inputs.itemById(SUFFIX_INPUT_ID))

    prefix = (prefix_input.value or "").strip()
    if not prefix:
        prefix = "SC"

    range_text = (range_input.value or "").strip()
    suffix = (suffix_input.value or "").strip()

    rng = _parse_range(range_text)
    if not rng:
        ui.messageBox("Invalid range. Use format like: 1-40 (start must be <= end).")
        return

    start_num, end_num = rng
    count = (end_num - start_num) + 1

    root = design.rootComponent
    occs = root.occurrences

    logger.log_command(
        CMD_NAME,
        {
            "prefix": prefix,
            "range": range_text,
            "suffix": suffix,
            "count": count,
        },
    )

    for n in range(start_num, end_num + 1):
        occ = occs.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = f"{prefix}{n}{suffix}"

    ui.messageBox(
        f"Created {count} components: {prefix}{start_num}{suffix} - {prefix}{end_num}{suffix}"
    )


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = ComponentSetCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
