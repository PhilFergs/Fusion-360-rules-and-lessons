import os
import traceback
from functools import partial

import adsk.core

from . import context as ctx
from . import core, logger
from .profile_schema import ANGLES, PROFILE_FAMILIES, profile_family

CMD_ID = "PhilsFusionTools_CreateSteelMember"
CMD_NAME = "Create Steel Member"
CMD_TOOLTIP = "Create EA, SHS, RHS, I Beam, PFC, or C Channel members."
RESOURCE_FOLDER = os.path.join(
    os.path.dirname(__file__),
    "resources",
    "PhilsDesignTools_EA",
)

FAMILY_INPUT_ID = "steel_family"
LINES_INPUT_ID = "steel_lines"


def _input_id(family_key, field):
    return f"steel_{family_key.casefold()}_{field}"


def _value_input(inputs, input_id, name, units, default_mm):
    return inputs.addValueInput(
        input_id,
        name,
        units,
        adsk.core.ValueInput.createByString(f"{default_mm} mm"),
    )


def _add_angle_input(inputs, family_key):
    dropdown = inputs.addDropDownCommandInput(
        _input_id(family_key, "angle"),
        "Orientation (deg)",
        adsk.core.DropDownStyles.TextListDropDownStyle,
    )
    for angle in ANGLES:
        dropdown.listItems.add(str(angle), angle == 0, "")


def _add_common_inputs(inputs, family_key, units, extra_mm):
    _value_input(
        inputs,
        _input_id(family_key, "extra"),
        "Extra end (each side)",
        units,
        extra_mm,
    )
    inputs.addBoolValueInput(
        _input_id(family_key, "profile_name"),
        "Add profile to name",
        True,
        "",
        False,
    )
    _add_angle_input(inputs, family_key)


def _add_ea_inputs(inputs, units):
    key = "EA"
    _value_input(inputs, _input_id(key, "flange"), "Flange length", units, 50.0)
    _value_input(inputs, _input_id(key, "thickness"), "Thickness", units, 3.0)
    _value_input(inputs, _input_id(key, "extra"), "Extra end (each side)", units, 20.0)
    _value_input(inputs, _input_id(key, "hole_diameter"), "Hole diameter", units, 13.0)
    _value_input(inputs, _input_id(key, "hole_gauge"), "Hole gauge", units, 25.0)
    _value_input(inputs, _input_id(key, "fillet"), "Root fillet radius", units, 3.0)
    inputs.addBoolValueInput(
        _input_id(key, "holes_enabled"),
        "Create holes",
        True,
        "",
        True,
    )
    inputs.addBoolValueInput(
        _input_id(key, "profile_name"),
        "Add profile to name",
        True,
        "",
        False,
    )
    _add_angle_input(inputs, key)


def _add_shs_inputs(inputs, units):
    key = "SHS"
    _value_input(inputs, _input_id(key, "size"), "Size (width = depth)", units, 100.0)
    _value_input(inputs, _input_id(key, "thickness"), "Wall thickness", units, 3.0)
    _add_common_inputs(inputs, key, units, 0.0)


def _add_rhs_inputs(inputs, units):
    key = "RHS"
    _value_input(inputs, _input_id(key, "width"), "Width", units, 100.0)
    _value_input(inputs, _input_id(key, "depth"), "Depth", units, 50.0)
    _value_input(inputs, _input_id(key, "thickness"), "Wall thickness", units, 3.0)
    _add_common_inputs(inputs, key, units, 0.0)


def _add_section_inputs(inputs, family_key, units):
    family = profile_family(family_key)
    dropdown = inputs.addDropDownCommandInput(
        _input_id(family_key, "section"),
        "Section",
        adsk.core.DropDownStyles.TextListDropDownStyle,
    )
    for section in family.sections:
        dropdown.listItems.add(section, section == family.default_section, "")
    _add_common_inputs(inputs, family_key, units, 0.0)


def _selected_family(inputs):
    dropdown = adsk.core.DropDownCommandInput.cast(inputs.itemById(FAMILY_INPUT_ID))
    if dropdown and dropdown.selectedItem:
        return dropdown.selectedItem.name.split(" | ", 1)[0]
    return PROFILE_FAMILIES[0].key


def _update_group_visibility(inputs):
    selected = _selected_family(inputs)
    for family in PROFILE_FAMILIES:
        group = inputs.itemById(_input_id(family.key, "group"))
        if group:
            group.isVisible = family.key == selected


class SteelMemberInputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            if args.input.id == FAMILY_INPUT_ID:
                _update_group_visibility(args.inputs)
        except Exception:
            logger.log("Steel Member input update failed:\n" + traceback.format_exc())


class SteelMemberExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except Exception:
            logger.log("Steel Member failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(
                "Create Steel Member failed. See the Phils Fusion Tools log for details."
            )


class SteelMemberCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, default_family=None):
        super().__init__()
        self.default_family = default_family or PROFILE_FAMILIES[0].key

    def notify(self, args):
        try:
            design = core.get_design()
            units = design.unitsManager.defaultLengthUnits or "mm"
            command = args.command
            command.isRepeatable = True
            inputs = command.commandInputs
            if inputs.itemById(FAMILY_INPUT_ID):
                return

            family_input = inputs.addDropDownCommandInput(
                FAMILY_INPUT_ID,
                "Profile family",
                adsk.core.DropDownStyles.TextListDropDownStyle,
            )
            for family in PROFILE_FAMILIES:
                family_input.listItems.add(
                    f"{family.key} | {family.label}",
                    family.key == self.default_family,
                    "",
                )

            lines = inputs.addSelectionInput(
                LINES_INPUT_ID,
                "Lines",
                "Select sketch lines for steel members",
            )
            lines.addSelectionFilter("SketchLines")
            lines.setSelectionLimits(1, 0)

            for family in PROFILE_FAMILIES:
                group = inputs.addGroupCommandInput(
                    _input_id(family.key, "group"),
                    family.label,
                )
                group.isExpanded = True
                if family.key == "EA":
                    _add_ea_inputs(group.children, units)
                elif family.key == "SHS":
                    _add_shs_inputs(group.children, units)
                elif family.key == "RHS":
                    _add_rhs_inputs(group.children, units)
                else:
                    _add_section_inputs(group.children, family.key, units)

            _update_group_visibility(inputs)

            execute_handler = SteelMemberExecuteHandler()
            command.execute.add(execute_handler)
            ctx.add_handler(execute_handler)

            changed_handler = SteelMemberInputChangedHandler()
            command.inputChanged.add(changed_handler)
            ctx.add_handler(changed_handler)
        except Exception:
            logger.log("Steel Member dialog failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(
                "Create Steel Member could not open. "
                "See the Phils Fusion Tools log for details."
            )


def _value_mm(inputs, family_key, field, units_manager):
    value_input = adsk.core.ValueCommandInput.cast(
        inputs.itemById(_input_id(family_key, field))
    )
    return units_manager.convert(value_input.value, units_manager.internalUnits, "mm")


def _bool_value(inputs, family_key, field):
    bool_input = adsk.core.BoolValueCommandInput.cast(
        inputs.itemById(_input_id(family_key, field))
    )
    return bool(bool_input.value)


def _angle_value(inputs, family_key):
    dropdown = adsk.core.DropDownCommandInput.cast(
        inputs.itemById(_input_id(family_key, "angle"))
    )
    return float(dropdown.selectedItem.name)


def _section_value(inputs, family_key):
    dropdown = adsk.core.DropDownCommandInput.cast(
        inputs.itemById(_input_id(family_key, "section"))
    )
    return dropdown.selectedItem.name


def _execute(args):
    inputs = args.command.commandInputs
    family_key = _selected_family(inputs)
    selection = adsk.core.SelectionCommandInput.cast(inputs.itemById(LINES_INPUT_ID))
    lines = core.collect_lines_from_selection_input(selection)
    if not lines:
        ctx.ui().messageBox("Select at least one sketch line.")
        return

    units_manager = core.get_design().unitsManager
    extra = _value_mm(inputs, family_key, "extra", units_manager)
    profile_name = _bool_value(inputs, family_key, "profile_name")
    angle = _angle_value(inputs, family_key)
    logger.log_command(
        CMD_NAME,
        {"family": family_key, "lines": len(lines), "angle_deg": angle},
    )

    if family_key == "EA":
        core.generate_ea_from_lines(
            lines,
            _value_mm(inputs, family_key, "flange", units_manager),
            _value_mm(inputs, family_key, "thickness", units_manager),
            extra,
            _value_mm(inputs, family_key, "hole_diameter", units_manager),
            _value_mm(inputs, family_key, "hole_gauge", units_manager),
            _value_mm(inputs, family_key, "fillet", units_manager),
            angle,
            _bool_value(inputs, family_key, "holes_enabled"),
            profile_name,
        )
    elif family_key == "SHS":
        core.generate_shs_from_lines(
            lines,
            _value_mm(inputs, family_key, "size", units_manager),
            _value_mm(inputs, family_key, "thickness", units_manager),
            extra,
            angle,
            profile_name,
        )
    elif family_key == "RHS":
        core.generate_rhs_from_lines(
            lines,
            _value_mm(inputs, family_key, "width", units_manager),
            _value_mm(inputs, family_key, "depth", units_manager),
            _value_mm(inputs, family_key, "thickness", units_manager),
            extra,
            angle,
            profile_name,
        )
    elif family_key == "I_BEAM":
        core.generate_ub_from_lines(
            lines,
            _section_value(inputs, family_key),
            extra,
            angle,
            profile_name,
        )
    elif family_key == "PFC":
        core.generate_pfc_from_lines(
            lines,
            _section_value(inputs, family_key),
            extra,
            angle,
            profile_name,
        )
    elif family_key == "C_CHANNEL":
        core.generate_c_channel_from_lines(
            lines,
            _section_value(inputs, family_key),
            extra,
            angle,
            profile_name,
        )
    else:
        raise ValueError(f"unsupported profile family: {family_key}")


def legacy_profile_handler_factories():
    return {
        family.legacy_id: partial(SteelMemberCommandCreatedHandler, family.key)
        for family in PROFILE_FAMILIES
    }
