import adsk.core
import adsk.fusion
import traceback
import re
import os

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_EA_BatchRename"
CMD_NAME = "Batch Rename"
CMD_TOOLTIP = "Rename steel members by selection order with length-based naming."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

SELECTION_INPUT_ID = "EA_BatchRename_Selection"
PREFIX_INPUT_ID = "EA_BatchRename_Prefix"
START_INDEX_INPUT_ID = "EA_BatchRename_StartIndex"
SIZE_SUFFIX_INPUT_ID = "EA_BatchRename_SizeSuffix"

_last_prefix = None
_last_start_index = None
_last_size_suffix = None


class RenameCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById(SELECTION_INPUT_ID):
                return

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
                _last_prefix if _last_prefix else "EA"
            )

            # Starting index input.
            inputs.addStringValueInput(
                START_INDEX_INPUT_ID,
                "Starting index",
                _last_start_index if _last_start_index else "1"
            )

            # Size suffix input (section info).
            inputs.addStringValueInput(
                SIZE_SUFFIX_INPUT_ID,
                "Size suffix",
                _last_size_suffix if _last_size_suffix else "50x50x3"
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
            start_index_input = adsk.core.StringValueCommandInput.cast(
                inputs.itemById(START_INDEX_INPUT_ID)
            )
            size_suffix_input = adsk.core.StringValueCommandInput.cast(
                inputs.itemById(SIZE_SUFFIX_INPUT_ID)
            )

            # Read user inputs.
            prefix = (prefix_input.value or "").strip()
            if prefix == "":
                prefix = "EA"

            start_index_raw = (start_index_input.value or "").strip() if start_index_input else "1"
            try:
                start_index_val = float(start_index_raw)
            except:
                ui.messageBox("Starting index must be a number (e.g. 3 or 3.1).")
                return
            use_decimal = abs(start_index_val - round(start_index_val)) > 1e-6
            step = 0.1 if use_decimal else 1.0
            start_index = start_index_val

            raw_suffix = (size_suffix_input.value or "").strip()
            if raw_suffix == "":
                raw_suffix = "50x50x3"

            global _last_prefix, _last_start_index, _last_size_suffix
            _last_prefix = prefix
            _last_start_index = start_index_raw
            _last_size_suffix = raw_suffix

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

            exclude_occ_tokens = set()
            exclude_comp_tokens = set()
            for occ in occurrences:
                _add_entity_tokens(occ, exclude_occ_tokens)
                try:
                    comp = occ.component
                    if comp:
                        _add_entity_tokens(comp, exclude_comp_tokens)
                except:
                    pass

            target_index_labels = _build_target_index_labels(
                start_index,
                step,
                len(occurrences),
                use_decimal,
            )
            target_index_set = set(target_index_labels)

            conflicts = _collect_conflicts_for_target_indices(
                design,
                prefix,
                target_index_set,
                exclude_occ_tokens,
                exclude_comp_tokens,
            )
            conflict_labels = _collect_conflict_labels(prefix, conflicts)
            overwrite_conflicts = False

            log_lines = []

            if conflict_labels:
                conflict_list = ", ".join(conflict_labels)
                msg = (
                    "Conflicting names found for the requested indices:\n\n"
                    f"{conflict_list}\n\n"
                    "Click Yes to overwrite (existing items will be renamed to "
                    "\"needs rename 1\", \"needs rename 2\", ...).\n"
                    "Click No to cancel."
                )
                result = ui.messageBox(
                    msg,
                    CMD_NAME,
                    adsk.core.MessageBoxButtonTypes.YesNoButtonType,
                    adsk.core.MessageBoxIconTypes.WarningIconType,
                )
                if result != adsk.core.DialogResults.DialogYes:
                    return
                overwrite_conflicts = True
                log_lines.append("Overwrote existing names: " + conflict_list)
                used_names = _collect_existing_names(design)
                _apply_conflict_overwrite(conflicts, used_names, log_lines)
                log_lines.append("")

            logger.log_command(
                CMD_NAME,
                {
                    "members": len(occurrences),
                    "prefix": prefix,
                    "start_index": start_index_raw,
                    "size_suffix": size_suffix,
                    "step": step,
                    "conflicts": conflict_labels,
                    "overwrite": overwrite_conflicts,
                },
            )

            # Rename in selection order.
            current_index = start_index

            for occ in occurrences:
                length_mm = _compute_length_mm_longest_edge(occ, units_mgr)
                if length_mm is None:
                    length_label = "UNKNOWN"
                else:
                    length_label = f"{int(round(length_mm))}"

                # Build final name.
                if use_decimal:
                    idx_label = f"{current_index:.1f}"
                else:
                    idx_label = f"{int(round(current_index))}"
                new_name = f"{prefix}{idx_label}-{length_label}mm-{size_suffix}"

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

                current_index = round(current_index + step, 1) if use_decimal else current_index + 1

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


def _build_target_index_labels(start_index, step, count, use_decimal):
    labels = []
    current = start_index
    for _ in range(count):
        if use_decimal:
            labels.append(f"{current:.1f}")
            current = round(current + step, 1)
        else:
            labels.append(f"{int(round(current))}")
            current = current + step
    return labels


def _collect_conflicts_for_target_indices(
    design: adsk.fusion.Design,
    prefix: str,
    target_index_set,
    exclude_occ_tokens=None,
    exclude_comp_tokens=None,
):
    conflicts = []
    if not design or not prefix or not target_index_set:
        return conflicts

    pattern = re.compile(
        r"^" + re.escape(prefix) + r"(\d+(?:\.\d+)?)\b",
        re.IGNORECASE,
    )

    # Components
    try:
        for comp in design.allComponents:
            token = _safe_entity_token(comp)
            if exclude_comp_tokens and token in exclude_comp_tokens:
                continue
            try:
                native = comp.nativeObject
            except:
                native = None
            if native:
                native_token = _safe_entity_token(native)
                if exclude_comp_tokens and native_token in exclude_comp_tokens:
                    continue
            name = comp.name or ""
            m = pattern.match(name)
            if not m:
                continue
            idx_label = m.group(1)
            if idx_label in target_index_set:
                conflicts.append({
                    "kind": "component",
                    "entity": comp,
                    "name": name,
                    "idx_label": idx_label,
                })
    except:
        pass

    # Occurrences
    try:
        for occ in design.rootComponent.allOccurrences:
            token = _safe_entity_token(occ)
            if exclude_occ_tokens and token in exclude_occ_tokens:
                continue
            try:
                native = occ.nativeObject
            except:
                native = None
            if native:
                native_token = _safe_entity_token(native)
                if exclude_occ_tokens and native_token in exclude_occ_tokens:
                    continue
            name = occ.name or ""
            m = pattern.match(name)
            if not m:
                continue
            idx_label = m.group(1)
            if idx_label in target_index_set:
                conflicts.append({
                    "kind": "occurrence",
                    "entity": occ,
                    "name": name,
                    "idx_label": idx_label,
                })
    except:
        pass

    return conflicts


def _collect_conflict_labels(prefix: str, conflicts):
    idx_labels = set()
    for item in conflicts:
        idx = item.get("idx_label")
        if idx:
            idx_labels.add(idx)

    def sort_key(val):
        try:
            return float(val)
        except:
            return val

    return [f"{prefix}{idx}" for idx in sorted(idx_labels, key=sort_key)]


def _collect_existing_names(design: adsk.fusion.Design):
    names = set()
    if not design:
        return names
    try:
        for comp in design.allComponents:
            if comp.name:
                names.add(comp.name)
    except:
        pass
    try:
        for occ in design.rootComponent.allOccurrences:
            if occ.name:
                names.add(occ.name)
    except:
        pass
    return names


def _safe_entity_token(entity):
    try:
        return entity.entityToken
    except:
        return None


def _add_entity_tokens(entity, token_set):
    if not entity:
        return
    token = _safe_entity_token(entity)
    if token:
        token_set.add(token)
    try:
        native = entity.nativeObject
    except:
        native = None
    if native:
        native_token = _safe_entity_token(native)
        if native_token:
            token_set.add(native_token)


def _safe_name(entity):
    try:
        return entity.name or ""
    except:
        return ""


def _next_needs_rename_label(used_names, counter):
    while True:
        label = f"needs rename {counter}"
        if label not in used_names:
            used_names.add(label)
            return label, counter + 1
        counter += 1


def _apply_conflict_overwrite(conflicts, used_names, log_lines):
    counter = 1
    comp_new_names = {}
    comp_entities = {}

    for item in conflicts:
        if item.get("kind") != "component":
            continue
        comp = item.get("entity")
        token = _safe_entity_token(comp)
        if not token or token in comp_new_names:
            continue
        new_name, counter = _next_needs_rename_label(used_names, counter)
        comp_new_names[token] = new_name
        comp_entities[token] = comp

    occ_new_names = {}
    occ_entities = {}

    for item in conflicts:
        if item.get("kind") != "occurrence":
            continue
        occ = item.get("entity")
        token = _safe_entity_token(occ)
        if not token or token in occ_new_names:
            continue

        comp = None
        try:
            comp = occ.component
        except:
            comp = None
        comp_token = _safe_entity_token(comp) if comp else None

        if comp_token and comp_token in comp_new_names:
            new_name = comp_new_names[comp_token]
        else:
            new_name, counter = _next_needs_rename_label(used_names, counter)

        occ_new_names[token] = new_name
        occ_entities[token] = occ

    for token, comp in comp_entities.items():
        new_name = comp_new_names[token]
        old_name = _safe_name(comp)
        try:
            comp.name = new_name
            _rename_component_bodies(comp, new_name)
            log_lines.append(f'{old_name}  ->  {new_name}  (component)')
        except Exception as ex:
            log_lines.append(f'FAILED to rename component "{old_name}": {ex}')

    for token, occ in occ_entities.items():
        new_name = occ_new_names[token]
        old_name = _safe_name(occ)
        try:
            occ.name = new_name
            log_lines.append(f'{old_name}  ->  {new_name}  (occurrence)')
        except Exception as ex:
            log_lines.append(f'FAILED to rename occurrence "{old_name}": {ex}')


def _find_max_index_for_prefix(
    design: adsk.fusion.Design,
    prefix: str,
    exclude_occ_tokens=None,
    exclude_comp_tokens=None,
):
    if not design or not prefix:
        return None

    pattern = re.compile(r"^" + re.escape(prefix) + r"(\d+)\b")
    max_index = 0

    # Components
    try:
        for comp in design.allComponents:
            try:
                token = comp.entityToken
            except:
                token = None
            if exclude_comp_tokens and token in exclude_comp_tokens:
                continue
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
            try:
                token = occ.entityToken
            except:
                token = None
            if exclude_occ_tokens and token in exclude_occ_tokens:
                continue
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
            RESOURCE_FOLDER
        )

    created_handler = RenameCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if modify_panel and not modify_panel.controls.itemById(CMD_ID):
        ctrl = modify_panel.controls.addCommand(cmd_def, CMD_ID)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = True
