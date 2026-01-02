import adsk.core
import adsk.fusion
import traceback
import re

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_EA_BatchRename"
CMD_NAME = "EA Batch Rename"
CMD_TOOLTIP = "Rename EA/steel members by selection order with length-based naming."

SELECTION_INPUT_ID = "EA_BatchRename_Selection"
PREFIX_INPUT_ID = "EA_BatchRename_Prefix"
START_INDEX_INPUT_ID = "EA_BatchRename_StartIndex"
SIZE_SUFFIX_INPUT_ID = "EA_BatchRename_SizeSuffix"


class RenameCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            # Selection input - user can select occurrences to rename.
            sel_input = inputs.addSelectionInput(
                SELECTION_INPUT_ID,
                "Members",
                "Select steel member occurrences to rename"
            )
            # Only allow occurrences - no sketches, faces, edges, etc.
            sel_input.addSelectionFilter("Occurrences")
            sel_input.setSelectionLimits(1, 0)  # At least 1, unlimited max.

            # Prefix input.
            inputs.addStringValueInput(
                PREFIX_INPUT_ID,
                "Name prefix",
                "EA"
            )

            # Starting index input.
            inputs.addIntegerSpinnerCommandInput(
                START_INDEX_INPUT_ID,
                "Starting index",
                1, 1000000, 1, 1
            )

            # Size suffix input (section info).
            inputs.addStringValueInput(
                SIZE_SUFFIX_INPUT_ID,
                "Size suffix",
                "50x50x3"
            )

            on_execute = RenameExecuteHandler()
            cmd.execute.add(on_execute)
            ctx.add_handler(on_execute)

        except:
            logger.log(
                "Error in EA Batch Rename CommandCreated:\n" + traceback.format_exc()
            )
            ctx.ui().messageBox(
                "Error in EA Batch Rename CommandCreated:\n" + traceback.format_exc()
            )


class RenameExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args: adsk.core.CommandEventArgs):
        try:
            ui = ctx.ui()
            design = _get_active_design()
            if not design:
                return

            units_mgr = design.unitsManager

            cmd = args.command
            inputs = cmd.commandInputs

            sel_input = adsk.core.SelectionCommandInput.cast(
                inputs.itemById(SELECTION_INPUT_ID)
            )
            prefix_input = adsk.core.StringValueCommandInput.cast(
                inputs.itemById(PREFIX_INPUT_ID)
            )
            start_index_input = adsk.core.IntegerSpinnerCommandInput.cast(
                inputs.itemById(START_INDEX_INPUT_ID)
            )
            size_suffix_input = adsk.core.StringValueCommandInput.cast(
                inputs.itemById(SIZE_SUFFIX_INPUT_ID)
            )

            # Read user inputs.
            prefix = (prefix_input.value or "").strip()
            if prefix == "":
                prefix = "EA"

            start_index = start_index_input.value if start_index_input else 1

            raw_suffix = (size_suffix_input.value or "").strip()
            if raw_suffix == "":
                raw_suffix = "50x50x3"

            # Auto-normalise suffix based on prefix/type (EA compression 50x50x3 -> 50x3).
            size_suffix = _normalise_size_suffix(prefix, raw_suffix)

            # Collect occurrences strictly from the dialog selection.
            occurrences = []
            seen_tokens = set()

            if not sel_input or sel_input.selectionCount == 0:
                ui.messageBox(
                    "No members selected.\n\n"
                    "Select one or more component occurrences in the command dialog."
                )
                return

            for i in range(sel_input.selectionCount):
                sel = sel_input.selection(i)
                entity = sel.entity
                occ = _resolve_occurrence_from_entity(entity, design)
                if not occ:
                    # If it isn't an occurrence/component, just skip it quietly.
                    continue
                token = occ.entityToken
                if token in seen_tokens:
                    continue
                seen_tokens.add(token)
                occurrences.append(occ)

            if not occurrences:
                ui.messageBox(
                    "No valid component occurrences found in the selection.\n\n"
                    "Only components/occurrences are supported."
                )
                return

            # Auto-bump start index based on existing names.
            max_existing = _find_max_index_for_prefix(design, prefix)
            effective_start = start_index
            note_line = ""
            if max_existing is not None and max_existing >= start_index:
                effective_start = max_existing + 1
                note_line = (
                    f"Existing {prefix} indices up to {max_existing} found - "
                    f"starting from {effective_start} instead of {start_index}."
                )

            # Rename in selection order.
            log_lines = []
            if note_line:
                log_lines.append(note_line)
                log_lines.append("")

            current_index = effective_start

            for occ in occurrences:
                length_mm = _compute_length_mm_longest_edge(occ, units_mgr)
                if length_mm is None:
                    length_label = "UNKNOWN"
                else:
                    length_label = f"{int(round(length_mm))}"

                # Build final name.
                new_name = f"{prefix}{current_index}-{length_label}mm-{size_suffix}"

                renamed = False
                old_label = ""
                comp_for_bodies = None

                try:
                    # Try renaming occurrence first.
                    try:
                        old_label = occ.name
                        occ.name = new_name
                        comp_for_bodies = occ.component
                        renamed = True
                        log_lines.append(f'{old_label}  ->  {new_name}  (occurrence)')
                    except Exception:
                        comp = occ.component
                        if comp:
                            old_label = comp.name
                            comp.name = new_name
                            comp_for_bodies = comp
                            renamed = True
                            log_lines.append(f'{old_label}  ->  {new_name}  (component)')

                    if not renamed:
                        safe_name = ""
                        try:
                            safe_name = occ.name
                        except Exception:
                            safe_name = "<unknown occurrence>"
                        log_lines.append(
                            f'FAILED to rename occurrence "{safe_name}" (index {current_index}).'
                        )

                    # Also rename all bodies in that component to match.
                    if comp_for_bodies:
                        _rename_component_bodies(comp_for_bodies, new_name)

                except Exception as ex:
                    safe_name = ""
                    try:
                        safe_name = occ.name
                    except Exception:
                        safe_name = "<unknown occurrence>"
                    log_lines.append(
                        f'ERROR renaming \"{safe_name}\" (index {current_index}): {ex}'
                    )

                current_index += 1

            summary = (
                "EA Batch Rename results:\n\n" + "\n".join(log_lines)
                if log_lines else
                "No occurrences were renamed."
            )
            ui.messageBox(summary, CMD_NAME)

        except:
            logger.log(
                "Error in EA Batch Rename Execute:\n" + traceback.format_exc()
            )
            ctx.ui().messageBox(
                "Error in EA Batch Rename Execute:\n" + traceback.format_exc()
            )


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------


def _get_active_design():
    app = ctx.app()
    ui = ctx.ui()

    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    if not design:
        ui.messageBox(
            "The active product is not a Fusion 360 design.\n"
            "Switch to a design workspace and try again."
        )
    return design


def _resolve_occurrence_from_entity(entity, design: adsk.fusion.Design):
    """
    Resolve an occurrence from whatever Fusion hands us.
    Must NOT throw - return None if we can't resolve a clean occurrence.
    """
    if not entity or not design:
        return None

    # Direct occurrence selection.
    occ = adsk.fusion.Occurrence.cast(entity)
    if occ:
        return occ

    # Entity in an assembly context (face/edge/body in an occurrence).
    if hasattr(entity, "assemblyContext") and entity.assemblyContext:
        occ = entity.assemblyContext
        if occ:
            return occ

    # Direct component selection: find an occurrence that references this component.
    comp = adsk.fusion.Component.cast(entity)
    if comp:
        try:
            all_occs = design.rootComponent.allOccurrences
            for o in all_occs:
                if o.component == comp:
                    return o
        except:
            pass

    # Anything else (sketch, face, edge, etc.) is ignored.
    return None


def _compute_length_mm_longest_edge(
    occ: adsk.fusion.Occurrence,
    units_mgr: adsk.fusion.FusionUnitsManager
):
    """
    Compute the member length as the length of the longest straight edge
    in the occurrence (true overall member length), independent of orientation.
    """
    if not occ:
        return None

    try:
        bodies = occ.bRepBodies
        if not bodies or bodies.count == 0:
            return None

        xform = occ.transform
        has_xform = xform is not None

        max_len_internal = 0.0

        for body in bodies:
            for edge in body.edges:
                # Only consider edges with two endpoints (line-like edges).
                try:
                    v1 = edge.startVertex.geometry
                    v2 = edge.endVertex.geometry
                except:
                    continue

                p1 = v1.copy()
                p2 = v2.copy()

                if has_xform:
                    p1.transformBy(xform)
                    p2.transformBy(xform)

                dx = p2.x - p1.x
                dy = p2.y - p1.y
                dz = p2.z - p1.z
                d = (dx * dx + dy * dy + dz * dz) ** 0.5
                if d > max_len_internal:
                    max_len_internal = d

        if max_len_internal <= 0.0:
            return None

        internal_units = units_mgr.internalUnits
        return units_mgr.convert(max_len_internal, internal_units, "mm")

    except:
        return None


def _find_max_index_for_prefix(design: adsk.fusion.Design, prefix: str):
    if not design or not prefix:
        return None

    pattern = re.compile(r"^" + re.escape(prefix) + r"(\d+)\b")
    max_index = 0

    # Components
    try:
        for comp in design.allComponents:
            name = comp.name or ""
            m = pattern.match(name)
            if m:
                idx = int(m.group(1))
                if idx > max_index:
                    max_index = idx
    except:
        pass

    # Occurrences
    try:
        for occ in design.rootComponent.allOccurrences:
            name = occ.name or ""
            m = pattern.match(name)
            if m:
                idx = int(m.group(1))
                if idx > max_index:
                    max_index = idx
    except:
        pass

    return max_index if max_index > 0 else None


def _normalise_size_suffix(prefix: str, suffix: str) -> str:
    """
    If prefix suggests EA and suffix is of form AxBxT with A == B,
    compress to AxT (e.g. 50x50x3 -> 50x3). Otherwise, return suffix unchanged.
    """
    s = suffix.strip()
    if s == "":
        return s

    if prefix.upper().startswith("EA"):
        m = re.match(
            r"^\s*(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)\s*$",
            s
        )
        if m:
            a, b, t = m.groups()
            if a == b:
                return f"{a}x{t}"

    return s


def _rename_component_bodies(comp: adsk.fusion.Component, new_name: str):
    """
    Rename all bodies in the component to match the new component/occurrence name.
    Assumes single-body members, but safely handles multi-body.
    """
    try:
        bodies = comp.bRepBodies
        if not bodies:
            return
        for body in bodies:
            try:
                body.name = new_name
            except:
                # Don't let a bad body name kill the whole rename.
                continue
    except:
        pass


# -------------------------------------------------------------------------
# Registration
# -------------------------------------------------------------------------


def register(ui: adsk.core.UserInterface, modify_panel: adsk.core.ToolbarPanel):
    """
    Register EA Batch Rename command on the Solid > Modify panel.
    """
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID,
            CMD_NAME,
            CMD_TOOLTIP,
            ""  # no custom icon for now
        )

    created_handler = RenameCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if modify_panel and not modify_panel.controls.itemById(CMD_ID):
        ctrl = modify_panel.controls.addCommand(cmd_def, CMD_ID)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = True



