import adsk.core, traceback
import smg_context as ctx
import smg_core as core

CMD_ID = "SteelMemberGeneration_RHS"
CMD_NAME = "RHS From Lines"
CMD_TOOLTIP = "Generate RHS members from sketch lines."


class RHSCommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            ctx.ui().messageBox("RHS command failed:\n" + traceback.format_exc())


class RHSCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            design = core.get_design()
            um = design.unitsManager
            length_units = um.defaultLengthUnits or 'mm'

            cmd = args.command
            cmd.isRepeatable = True
            inputs = cmd.commandInputs

            sel = inputs.addSelectionInput('rhs_selLines', 'Lines', 'Select sketch lines for RHS members')
            sel.addSelectionFilter('SketchLines')
            sel.setSelectionLimits(1, 0)

            def v(mm):
                return adsk.core.ValueInput.createByString(f"{mm} mm")

            inputs.addValueInput('rhs_width',     'Width',                 length_units, v(core.DEFAULT_RHS_WIDTH_MM))
            inputs.addValueInput('rhs_depth',     'Depth',                 length_units, v(core.DEFAULT_RHS_DEPTH_MM))
            inputs.addValueInput('rhs_thickness', 'Wall thickness',        length_units, v(core.DEFAULT_RHS_THICKNESS_MM))
            inputs.addValueInput('rhs_extra',     'Extra end (each side)', length_units, v(0.0))

            dd = inputs.addDropDownCommandInput(
                'rhs_angle',
                'Orientation (deg)',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            for ang in (0, 90, 180, 270):
                dd.listItems.add(str(ang), ang == 0, '')

            on_execute = RHSCommandExecuteHandler()
            cmd.execute.add(on_execute)
            ctx.add_handler(on_execute)
        except:
            ctx.ui().messageBox("RHS CommandCreated failed:\n" + traceback.format_exc())


def _execute(args):
    cmd = args.command
    inputs = cmd.commandInputs
    design = core.get_design()
    um = design.unitsManager

    sel = adsk.core.SelectionCommandInput.cast(inputs.itemById('rhs_selLines'))
    lines = core.collect_lines_from_selection_input(sel)
    if not lines:
        ctx.ui().messageBox("Select at least one sketch line.")
        return

    def mm_val(cid):
        v = adsk.core.ValueCommandInput.cast(inputs.itemById(cid))
        return um.convert(v.value, um.internalUnits, 'mm')

    width     = mm_val('rhs_width')
    depth     = mm_val('rhs_depth')
    thickness = mm_val('rhs_thickness')
    extra     = mm_val('rhs_extra')

    angle_dd = adsk.core.DropDownCommandInput.cast(inputs.itemById('rhs_angle'))
    angle = float(angle_dd.selectedItem.name) if angle_dd and angle_dd.selectedItem else 0.0

    core.generate_rhs_from_lines(
        lines,
        width, depth, thickness, extra,
        angle
    )


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_TOOLTIP)

    created_handler = RHSCommandCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = True
