import adsk.core
import adsk.fusion
import traceback
import re
import os

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_RemoveLengthNames"
CMD_NAME = "Remove Length From Names"
CMD_TOOLTIP = "Remove only the -####mm- segment from selected component/body/sketch names."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)
INPUT_COMPONENTS_ID = "removeLength_components"
INPUT_BODIES_ID = "removeLength_bodies"
INPUT_SKETCHES_ID = "removeLength_sketches"

LENGTH_SEGMENT_RE = re.compile(r"-(\d+(?:\.\d+)?)mm-", re.IGNORECASE)


def _strip_length_segment(name: str) -> str:
    if not name:
        return name
    return LENGTH_SEGMENT_RE.sub("-", name)


class RemoveLengthNamesCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            inputs.addBoolValueInput(INPUT_COMPONENTS_ID, "Components", True, "", True)
            inputs.addBoolValueInput(INPUT_BODIES_ID, "Bodies", True, "", True)
            inputs.addBoolValueInput(INPUT_SKETCHES_ID, "Sketches", True, "", True)
            on_exec = RemoveLengthNamesExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)
        except:
            logger.log(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())


class RemoveLengthNamesExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            rename_components = _get_checkbox_value(cmd, INPUT_COMPONENTS_ID, True)
            rename_bodies = _get_checkbox_value(cmd, INPUT_BODIES_ID, True)
            rename_sketches = _get_checkbox_value(cmd, INPUT_SKETCHES_ID, True)
            _execute(rename_components, rename_bodies, rename_sketches)
        except:
            logger.log(f"{CMD_NAME} failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} failed:\n" + traceback.format_exc())


def _get_checkbox_value(command, input_id, default=False):
    try:
        inp = adsk.core.BoolValueCommandInput.cast(command.commandInputs.itemById(input_id))
        if inp:
            return bool(inp.value)
    except Exception:
        pass
    return default


def _execute(rename_components, rename_bodies, rename_sketches):
    app = ctx.app()
    ui = ctx.ui()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("No active Fusion design.")
        return

    targets = []
    if rename_components:
        targets.append("component")
    if rename_bodies:
        targets.append("body")
    if rename_sketches:
        targets.append("sketch")
    if not targets:
        ui.messageBox("Select at least one target type: Components, Bodies, or Sketches.", CMD_NAME)
        return

    confirm = ui.messageBox(
        (
            "This will remove only the '-####mm-' segment from existing {} names.\n\n".format(
                ", ".join(targets)
            )
            + "Nothing else in each name will be changed.\n\n"
            + "Continue?"
        ),
        CMD_NAME,
        adsk.core.MessageBoxButtonTypes.YesNoButtonType,
        adsk.core.MessageBoxIconTypes.WarningIconType,
    )
    if confirm != adsk.core.DialogResults.DialogYes:
        return

    renamed_components = 0
    renamed_bodies = 0
    renamed_sketches = 0
    errors = []

    if rename_components:
        for comp in design.allComponents:
            if comp == design.rootComponent:
                continue
            old_name = comp.name or ""
            new_name = _strip_length_segment(old_name)
            if new_name == old_name:
                continue
            try:
                comp.name = new_name
                renamed_components += 1
            except Exception as ex:
                errors.append(f'Component "{old_name}": {ex}')

    if rename_bodies:
        for comp in design.allComponents:
            bodies = comp.bRepBodies
            for i in range(bodies.count):
                body = bodies.item(i)
                old_name = body.name or ""
                new_name = _strip_length_segment(old_name)
                if new_name == old_name:
                    continue
                try:
                    body.name = new_name
                    renamed_bodies += 1
                except Exception as ex:
                    errors.append(f'Body "{old_name}" in "{comp.name}": {ex}')

    if rename_sketches:
        for comp in design.allComponents:
            sketches = comp.sketches
            for i in range(sketches.count):
                sketch = sketches.item(i)
                old_name = sketch.name or ""
                new_name = _strip_length_segment(old_name)
                if new_name == old_name:
                    continue
                try:
                    sketch.name = new_name
                    renamed_sketches += 1
                except Exception as ex:
                    errors.append(f'Sketch "{old_name}" in "{comp.name}": {ex}')

    logger.log_command(
        CMD_NAME,
        {
            "selected_components": bool(rename_components),
            "selected_bodies": bool(rename_bodies),
            "selected_sketches": bool(rename_sketches),
            "components_renamed": renamed_components,
            "bodies_renamed": renamed_bodies,
            "sketches_renamed": renamed_sketches,
            "errors": len(errors),
        },
    )

    summary_lines = ["Length segment cleanup complete.", ""]
    if rename_components:
        summary_lines.append(f"Components renamed: {renamed_components}")
    if rename_bodies:
        summary_lines.append(f"Bodies renamed: {renamed_bodies}")
    if rename_sketches:
        summary_lines.append(f"Sketches renamed: {renamed_sketches}")
    summary = "\n".join(summary_lines)
    if errors:
        sample = "\n".join(errors[:10])
        summary += f"\n\nErrors: {len(errors)}\n{sample}"
    ui.messageBox(summary, CMD_NAME)


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = RemoveLengthNamesCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
