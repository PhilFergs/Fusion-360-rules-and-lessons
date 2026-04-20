import adsk.core
import adsk.fusion
import os
import re
import traceback

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_NormalizeComponentStructure"
CMD_NAME = "Normalize Component Structure"
CMD_TOOLTIP = (
    "Ensure each component has either subcomponents or a single body, then match body names to component names."
)
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)


class NormalizeStructureCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if not inputs.itemById("normalize_info"):
                info = (
                    "This will:\n"
                    "- Convert bodies into child components when a component is mixed (bodies + child components)\n"
                    "- Convert bodies into child components when a component has multiple direct bodies\n"
                    "- Rename each single direct body to match its parent component name"
                )
                inputs.addTextBoxCommandInput("normalize_info", "", info, 6, True)

            on_exec = NormalizeStructureExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)
        except:
            logger.log(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} UI failed:\n" + traceback.format_exc())


class NormalizeStructureExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute()
        except:
            logger.log(f"{CMD_NAME} failed:\n" + traceback.format_exc())
            ctx.ui().messageBox(f"{CMD_NAME} failed:\n" + traceback.format_exc())


def _component_name(comp):
    try:
        return comp.name or "<unnamed>"
    except:
        return "<unknown>"


def _body_name(body):
    try:
        return body.name or "Body"
    except:
        return "Body"


def _is_generic_body_name(name):
    if not name:
        return True
    return bool(re.fullmatch(r"body(?:\s*\d+)?", str(name).strip(), re.IGNORECASE))


def _preferred_child_component_name(parent_name, source_body_name, body_index, body_count):
    if source_body_name and not _is_generic_body_name(source_body_name):
        return source_body_name
    if body_count <= 1:
        return f"{parent_name} Body"
    return f"{parent_name} Body {body_index + 1}"


def _is_referenced_component(comp):
    # Referenced (linked) component definitions are not editable in-place.
    for attr in ("isReferencedComponent", "isExternalReference"):
        try:
            if bool(getattr(comp, attr)):
                return True
        except:
            pass
    return False


def _direct_bodies(comp):
    out = []
    try:
        bodies = comp.bRepBodies
        for i in range(bodies.count):
            b = bodies.item(i)
            if b:
                out.append(b)
    except:
        pass
    return out


def _direct_child_occurrence_count(comp):
    try:
        return comp.occurrences.count
    except:
        return 0


def _needs_conversion(body_count, child_count):
    if body_count <= 0:
        return False
    return (child_count > 0) or (body_count > 1)


def _execute():
    app = ctx.app()
    ui = ctx.ui()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("No active Fusion design.")
        return

    result = ui.messageBox(
        (
            "Normalize component structure across the active design?\n\n"
            "This can create new child components by moving bodies into them,\n"
            "and will rename single bodies to match their parent component names."
        ),
        CMD_NAME,
        adsk.core.MessageBoxButtonTypes.YesNoButtonType,
        adsk.core.MessageBoxIconTypes.WarningIconType,
    )
    if result != adsk.core.DialogResults.DialogYes:
        return

    stats = {
        "components_scanned": 0,
        "components_normalized": 0,
        "bodies_detected_for_conversion": 0,
        "bodies_converted": 0,
        "body_names_renamed": 0,
        "referenced_components_skipped": 0,
        "errors": 0,
    }
    errors = []

    components_before = []
    try:
        all_comps = design.allComponents
        for i in range(all_comps.count):
            comp = all_comps.item(i)
            if comp:
                components_before.append(comp)
    except Exception as ex:
        ui.messageBox(f"Failed to enumerate components: {ex}", CMD_NAME)
        return

    for comp in components_before:
        stats["components_scanned"] += 1

        if _is_referenced_component(comp):
            stats["referenced_components_skipped"] += 1
            continue

        bodies = _direct_bodies(comp)
        body_count = len(bodies)
        child_count = _direct_child_occurrence_count(comp)

        if not _needs_conversion(body_count, child_count):
            continue

        stats["bodies_detected_for_conversion"] += body_count
        converted_here = 0

        for body_index, body in enumerate(bodies):
            source_body_name = _body_name(body)
            parent_name = _component_name(comp)
            target_component_name = _preferred_child_component_name(
                parent_name,
                source_body_name,
                body_index,
                body_count,
            )

            try:
                moved_body = body.createComponent()
                if not moved_body:
                    raise RuntimeError("createComponent returned null")

                new_component = moved_body.parentComponent
                if new_component:
                    try:
                        new_component.name = target_component_name
                    except:
                        # Non-fatal; naming pass will still align body names.
                        pass

                stats["bodies_converted"] += 1
                converted_here += 1
            except Exception as ex:
                stats["errors"] += 1
                errors.append(
                    f'Convert body "{source_body_name}" in component "{parent_name}" failed: {ex}'
                )

        if converted_here > 0:
            stats["components_normalized"] += 1

    components_after = []
    try:
        all_comps = design.allComponents
        for i in range(all_comps.count):
            comp = all_comps.item(i)
            if comp:
                components_after.append(comp)
    except:
        components_after = components_before

    for comp in components_after:
        if _is_referenced_component(comp):
            continue

        bodies = _direct_bodies(comp)
        if len(bodies) != 1:
            continue

        body = bodies[0]
        target_name = _component_name(comp)
        current_name = _body_name(body)
        if current_name == target_name:
            continue

        try:
            body.name = target_name
            stats["body_names_renamed"] += 1
        except Exception as ex:
            stats["errors"] += 1
            errors.append(
                f'Body rename in component "{target_name}" failed ("{current_name}" -> "{target_name}"): {ex}'
            )

    logger.log_command(CMD_NAME, dict(stats))

    summary = [
        "Component normalization complete.",
        "",
        f"Components scanned: {stats['components_scanned']}",
        f"Components normalized: {stats['components_normalized']}",
        f"Bodies converted to child components: {stats['bodies_converted']}"
        + f" / {stats['bodies_detected_for_conversion']}",
        f"Single-body names aligned to parent: {stats['body_names_renamed']}",
        f"Referenced components skipped: {stats['referenced_components_skipped']}",
    ]

    if errors:
        sample = "\n".join(errors[:12])
        summary.append("")
        summary.append(f"Errors: {stats['errors']}")
        summary.append(sample)

    ui.messageBox("\n".join(summary), CMD_NAME)


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID,
            CMD_NAME,
            CMD_TOOLTIP,
            RESOURCE_FOLDER,
        )

    created_handler = NormalizeStructureCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
