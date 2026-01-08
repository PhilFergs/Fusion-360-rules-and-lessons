import adsk.core, traceback, os
import smg_context as ctx
import smg_core as core
import smg_logger as logger

CMD_ID = "PhilsDesignTools_SHS"
CMD_NAME = "SHS From Lines"
CMD_TOOLTIP = "Generate SHS members from sketch lines."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)


class SHSCommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log("SHS command failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("SHS command failed:\n" + traceback.format_exc())


class SHSCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            design = core.get_design()
            um = design.unitsManager
            length_units = um.defaultLengthUnits or 'mm'

            cmd = args.command
            cmd.isRepeatable = True
            inputs = cmd.commandInputs

            if inputs.itemById('shs_selLines'):
                return

            sel = inputs.addSelectionInput('shs_selLines', 'Lines', 'Select sketch lines for SHS members')
            sel.addSelectionFilter('SketchLines')
            sel.setSelectionLimits(1, 0)

            def v(mm):
                return adsk.core.ValueInput.createByString(f"{mm} mm")

            inputs.addValueInput('shs_size',      'Size (width = depth)',   length_units, v(core.DEFAULT_SHS_SIZE_MM))
            inputs.addValueInput('shs_thickness', 'Wall thickness',         length_units, v(core.DEFAULT_SHS_THICKNESS_MM))
            inputs.addValueInput('shs_extra',     'Extra end (each side)',  length_units, v(0.0))

            dd = inputs.addDropDownCommandInput(
                'shs_angle',
                'Orientation (deg)',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            for ang in (0, 90, 180, 270):
                dd.listItems.add(str(ang), ang == 0, '')

            on_execute = SHSCommandExecuteHandler()
            cmd.execute.add(on_execute)
            ctx.add_handler(on_execute)
        except:
            logger.log("SHS CommandCreated failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("SHS CommandCreated failed:\n" + traceback.format_exc())


def _execute(args):
    cmd = args.command
    inputs = cmd.commandInputs
    design = core.get_design()
    um = design.unitsManager

    sel = adsk.core.SelectionCommandInput.cast(inputs.itemById('shs_selLines'))
    lines = core.collect_lines_from_selection_input(sel)
    if not lines:
        ctx.ui().messageBox("Select at least one sketch line.")
        return

    def mm_val(cid):
        v = adsk.core.ValueCommandInput.cast(inputs.itemById(cid))
        return um.convert(v.value, um.internalUnits, 'mm')

    size      = mm_val('shs_size')
    thickness = mm_val('shs_thickness')
    extra     = mm_val('shs_extra')

    angle_dd = adsk.core.DropDownCommandInput.cast(inputs.itemById('shs_angle'))
    angle = float(angle_dd.selectedItem.name) if angle_dd and angle_dd.selectedItem else 0.0

    logger.log_command(
        CMD_NAME,
        {
            "lines": len(lines),
            "size_mm": size,
            "thickness_mm": thickness,
            "extra_mm": extra,
            "angle_deg": angle,
        },
    )

    core.generate_shs_from_lines(
        lines,
        size, thickness, extra,
        angle
    )


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = SHSCommandCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = True
