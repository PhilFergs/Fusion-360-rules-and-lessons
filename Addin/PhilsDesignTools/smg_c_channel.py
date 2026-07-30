import adsk.core, traceback, os
import smg_context as ctx
import smg_core as core
import smg_logger as logger

CMD_ID = "PhilsDesignTools_CChannel"
CMD_NAME = "C Channel From Lines"
CMD_TOOLTIP = "Generate lipped C purlin/channel members from sketch lines."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)


class CChannelCommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log("C Channel command failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("C Channel command failed:\n" + traceback.format_exc())


class CChannelCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            design = core.get_design()
            um = design.unitsManager
            length_units = um.defaultLengthUnits or "mm"

            cmd = args.command
            cmd.isRepeatable = True
            inputs = cmd.commandInputs

            if inputs.itemById("c_channel_selLines"):
                return

            sel = inputs.addSelectionInput("c_channel_selLines", "Lines", "Select sketch lines for C channel members")
            sel.addSelectionFilter("SketchLines")
            sel.setSelectionLimits(1, 0)

            dd = inputs.addDropDownCommandInput(
                "c_channel_section",
                "Section",
                adsk.core.DropDownStyles.TextListDropDownStyle,
            )
            for i, section in enumerate(core.C_CHANNEL_SECTIONS):
                dd.listItems.add(section["name"], i == 2, "")

            inputs.addValueInput(
                "c_channel_extra",
                "Extra end (each side)",
                length_units,
                adsk.core.ValueInput.createByString("0 mm"),
            )
            inputs.addBoolValueInput("c_channel_profile_name_enabled", "Add profile to name", True, "", False)

            angle_dd = inputs.addDropDownCommandInput(
                "c_channel_angle",
                "Orientation (deg)",
                adsk.core.DropDownStyles.TextListDropDownStyle,
            )
            for ang in (0, 90, 180, 270):
                angle_dd.listItems.add(str(ang), ang == 0, "")

            on_execute = CChannelCommandExecuteHandler()
            cmd.execute.add(on_execute)
            ctx.add_handler(on_execute)
        except:
            logger.log("C Channel CommandCreated failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("C Channel CommandCreated failed:\n" + traceback.format_exc())


def _execute(args):
    cmd = args.command
    inputs = cmd.commandInputs
    design = core.get_design()
    um = design.unitsManager

    sel = adsk.core.SelectionCommandInput.cast(inputs.itemById("c_channel_selLines"))
    lines = core.collect_lines_from_selection_input(sel)
    if not lines:
        ctx.ui().messageBox("Select at least one sketch line.")
        return

    section_dd = adsk.core.DropDownCommandInput.cast(inputs.itemById("c_channel_section"))
    section_name = (
        section_dd.selectedItem.name
        if section_dd and section_dd.selectedItem
        else core.C_CHANNEL_SECTIONS[2]["name"]
    )

    extra_input = adsk.core.ValueCommandInput.cast(inputs.itemById("c_channel_extra"))
    extra = um.convert(extra_input.value, um.internalUnits, "mm") if extra_input else 0.0

    profile_name_enabled = False
    profile_name_input = adsk.core.BoolValueCommandInput.cast(inputs.itemById("c_channel_profile_name_enabled"))
    if profile_name_input:
        profile_name_enabled = bool(profile_name_input.value)

    angle_dd = adsk.core.DropDownCommandInput.cast(inputs.itemById("c_channel_angle"))
    angle = float(angle_dd.selectedItem.name) if angle_dd and angle_dd.selectedItem else 0.0

    logger.log_command(
        CMD_NAME,
        {
            "lines": len(lines),
            "section": section_name,
            "extra_mm": extra,
            "profile_name_enabled": profile_name_enabled,
            "angle_deg": angle,
        },
    )

    core.generate_c_channel_from_lines(lines, section_name, extra, angle, profile_name_enabled)


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = CChannelCommandCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
