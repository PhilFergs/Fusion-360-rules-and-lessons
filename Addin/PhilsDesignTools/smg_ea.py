import adsk.core, traceback
import smg_context as ctx
import smg_core as core


CMD_ID = "PhilsDesignTools_EA"
CMD_NAME = "EA From Lines"
CMD_TOOLTIP = "Generate EA members from sketch lines."


class EACommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            ctx.ui().messageBox("EA command failed:\n" + traceback.format_exc())


class EAInputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            inp = args.input
            if inp.id == 'ea_thickness':
                inputs = args.inputs
                thickness_input = adsk.core.ValueCommandInput.cast(inputs.itemById('ea_thickness'))
                fillet_input = adsk.core.ValueCommandInput.cast(inputs.itemById('ea_fillet'))
                if thickness_input and fillet_input:
                    fillet_input.expression = thickness_input.expression
        except:
            pass


class EACommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            design = core.get_design()
            um = design.unitsManager
            length_units = um.defaultLengthUnits or 'mm'

            cmd = args.command
            cmd.isRepeatable = True
            inputs = cmd.commandInputs

            sel = inputs.addSelectionInput('ea_selLines', 'Lines', 'Select sketch lines for EA members')
            sel.addSelectionFilter('SketchLines')
            sel.setSelectionLimits(1, 0)

            def v(mm):
                return adsk.core.ValueInput.createByString(f"{mm} mm")

            inputs.addValueInput('ea_flange',    'Flange length',        length_units, v(core.DEFAULT_FLANGE_LENGTH_MM))
            inputs.addValueInput('ea_thickness', 'Thickness',            length_units, v(core.DEFAULT_THICKNESS_MM))
            inputs.addValueInput('ea_extra',     'Extra end (each side)', length_units, v(core.DEFAULT_EXTRA_END_MM))
            inputs.addValueInput('ea_hole_d',    'Hole diameter',        length_units, v(core.DEFAULT_HOLE_DIAMETER_MM))
            inputs.addValueInput('ea_hole_g',    'Hole gauge',           length_units, v(core.DEFAULT_HOLE_GAUGE_MM))
            inputs.addValueInput('ea_fillet',    'Root fillet radius',   length_units, v(core.DEFAULT_THICKNESS_MM))

            dd = inputs.addDropDownCommandInput(
                'ea_angle',
                'Orientation (deg)',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            for ang in (0, 90, 180, 270):
                dd.listItems.add(str(ang), ang == 0, '')

            on_execute = EACommandExecuteHandler()
            cmd.execute.add(on_execute)
            ctx.add_handler(on_execute)

            on_changed = EAInputChangedHandler()
            cmd.inputChanged.add(on_changed)
            ctx.add_handler(on_changed)

        except:
            ctx.ui().messageBox("EA CommandCreated failed:\n" + traceback.format_exc())


def _execute(args):
    cmd = args.command
    inputs = cmd.commandInputs
    design = core.get_design()
    um = design.unitsManager

    sel = adsk.core.SelectionCommandInput.cast(inputs.itemById('ea_selLines'))
    lines = core.collect_lines_from_selection_input(sel)
    if not lines:
        ctx.ui().messageBox("Select at least one sketch line.")
        return

    def mm_val(cid):
        v = adsk.core.ValueCommandInput.cast(inputs.itemById(cid))
        return um.convert(v.value, um.internalUnits, 'mm')

    flange    = mm_val('ea_flange')
    thickness = mm_val('ea_thickness')
    extra     = mm_val('ea_extra')
    hole_d    = mm_val('ea_hole_d')
    hole_g    = mm_val('ea_hole_g')
    fillet    = mm_val('ea_fillet')

    angle_dd = adsk.core.DropDownCommandInput.cast(inputs.itemById('ea_angle'))
    angle = float(angle_dd.selectedItem.name) if angle_dd and angle_dd.selectedItem else 0.0

    core.generate_ea_from_lines(
        lines,
        flange, thickness, extra,
        hole_d, hole_g, fillet,
        angle
    )


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_TOOLTIP)

    created_handler = EACommandCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = True

