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


def _strip_occurrence_suffix(name):
    return re.sub(r":\d+$", "", str(name or "").strip())


def _browser_leaf_name(name):
    leaf = str(name or "").strip().split("+")[-1]
    return _strip_occurrence_suffix(leaf)


def _occurrence_suffix(name):
    match = re.search(r"(:\d+)$", str(name or "").strip())
    return match.group(1) if match else ":1"


def _is_default_component_name(name):
    return bool(re.fullmatch(r"component\d+", _strip_occurrence_suffix(name), re.IGNORECASE))


def _assembly_wrapper_name(member_name):
    base = _strip_occurrence_suffix(member_name)
    if not base:
        return None
    if re.search(r"-AS$", base, re.IGNORECASE):
        return base

    # Convert names like RB6-100x100x3 or RB6-100x50x3 to RB6-AS.
    size_suffix = r"\d+(?:\.\d+)?(?:x\d+(?:\.\d+)?){1,4}"
    match = re.fullmatch(r"(.+)-" + size_suffix, base, re.IGNORECASE)
    if match and match.group(1):
        return f"{match.group(1)}-AS"

    return f"{base}-AS"


def _preferred_child_component_name(parent_name, source_body_name, body_index, body_count):
    if source_body_name and not _is_generic_body_name(source_body_name):
        return source_body_name
    if body_count <= 1:
        return parent_name
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


def _component_key(comp):
    if not comp:
        return None
    for attr in ("id", "entityToken"):
        try:
            value = getattr(comp, attr)
            if value:
                return str(value)
        except:
            pass
    return str(id(comp))


def _occurrence_name(occ):
    if not occ:
        return "<root>"
    for attr in ("fullPathName", "name"):
        try:
            value = getattr(occ, attr)
            if value:
                return str(value)
        except:
            pass
    return "<occurrence>"


def _is_linked_occurrence(occ):
    if not occ:
        return False
    for attr in ("isReferencedComponent", "isExternalReference"):
        try:
            if bool(getattr(occ, attr)):
                return True
        except:
            pass
    return False


def _occurrence_or_ancestors_linked(occ):
    current = occ
    while current is not None:
        if _is_linked_occurrence(current):
            return True
        try:
            current = current.assemblyContext
        except:
            current = None
    return False


def _body_editability_reason(body):
    if not body:
        return "body is null"
    try:
        if hasattr(body, "isValid") and not body.isValid:
            return "body is invalid"
    except:
        return "body validity could not be checked"
    for attr, label in (
        ("isTransient", "body is transient"),
        ("isTemporary", "body is temporary"),
        ("isDerived", "body is derived/read-only"),
    ):
        try:
            if bool(getattr(body, attr)):
                return label
        except:
            pass
    return None


def _build_component_contexts(design):
    root = design.rootComponent
    first_occ_by_component = {}
    first_writable_occ_by_component = {}
    linked_occ_seen = {}
    writable_occ_seen = {}

    try:
        all_occs = root.allOccurrences
        for i in range(all_occs.count):
            occ = all_occs.item(i)
            if not occ:
                continue
            try:
                comp = occ.component
            except:
                comp = None
            key = _component_key(comp)
            if not key:
                continue

            linked = _occurrence_or_ancestors_linked(occ)
            if key not in first_occ_by_component:
                first_occ_by_component[key] = occ
            if linked:
                linked_occ_seen[key] = True
            else:
                writable_occ_seen[key] = True
                if key not in first_writable_occ_by_component:
                    first_writable_occ_by_component[key] = occ
    except Exception as ex:
        logger.log(f"NORMALIZE: allOccurrences scan failed: {ex}")

    contexts = []
    all_comps = design.allComponents
    for i in range(all_comps.count):
        comp = all_comps.item(i)
        if not comp:
            continue
        key = _component_key(comp)
        occurrence = None
        if comp != root:
            occurrence = first_writable_occ_by_component.get(key) or first_occ_by_component.get(key)
        linked_only = bool(linked_occ_seen.get(key)) and not bool(writable_occ_seen.get(key))
        contexts.append(
            {
                "component": comp,
                "occurrence": occurrence,
                "linked": _is_referenced_component(comp) or linked_only,
            }
        )
    return contexts


def _body_for_context(body, occurrence):
    if not body:
        return None
    if not occurrence:
        return body
    try:
        if getattr(body, "assemblyContext", None):
            return body
    except:
        pass
    try:
        return body.createForAssemblyContext(occurrence)
    except Exception as ex:
        logger.log(
            f"NORMALIZE: body proxy failed body='{_body_name(body)}' "
            + f"occurrence='{_occurrence_name(occurrence)}': {ex}"
        )
    return None


def _occurrence_for_context(occurrence, parent_occurrence):
    if not occurrence:
        return None
    if not parent_occurrence:
        return occurrence
    try:
        if getattr(occurrence, "assemblyContext", None):
            return occurrence
    except:
        pass
    try:
        return occurrence.createForAssemblyContext(parent_occurrence)
    except Exception as ex:
        logger.log(
            f"NORMALIZE: occurrence proxy failed occurrence='{_occurrence_name(occurrence)}' "
            + f"parent='{_occurrence_name(parent_occurrence)}': {ex}"
        )
    return None


def _occurrence_component_is_empty(occurrence):
    try:
        comp = occurrence.component
        if not comp:
            return True
        if comp.bRepBodies.count > 0:
            return False
        if comp.occurrences.count > 0:
            return False
    except:
        return False
    return True


def _delete_empty_occurrence_safely(occurrence):
    if not occurrence:
        return
    if not _occurrence_component_is_empty(occurrence):
        logger.log(
            f"NORMALIZE: cleanup skipped for non-empty child occurrence='{_occurrence_name(occurrence)}'"
        )
        return
    try:
        native = getattr(occurrence, "nativeObject", None) or occurrence
        native.deleteMe()
    except Exception as ex:
        logger.log(f"NORMALIZE: cleanup empty child occurrence failed: {ex}")


def _component_from_body(body):
    if not body:
        return None
    try:
        return body.parentComponent
    except:
        return None


def _component_from_occurrence(occurrence):
    if not occurrence:
        return None
    try:
        return occurrence.component
    except:
        return None


def _occurrence_transform(occurrence):
    if not occurrence:
        return None
    for attr in ("transform2", "transform"):
        try:
            matrix = getattr(occurrence, attr)
            if matrix:
                return matrix.copy()
        except:
            pass
    return None


def _restore_occurrence_transform(design, occurrence, matrix, reason):
    if not occurrence:
        logger.log(f"NORMALIZE: occurrence transform restore skipped reason='{reason}' occurrence=null")
        return False
    if not matrix:
        logger.log(
            f"NORMALIZE: occurrence transform restore skipped reason='{reason}' "
            + f"occurrence='{_occurrence_name(occurrence)}' matrix=null"
        )
        return False

    try:
        if design and design.rootComponent:
            ok = design.rootComponent.transformOccurrences([occurrence], [matrix.copy()], True)
            if ok:
                logger.log(
                    f"NORMALIZE: occurrence transform restored reason='{reason}' "
                    + f"route='root.transformOccurrences' occurrence='{_occurrence_name(occurrence)}'"
                )
                return True
            logger.log(
                f"NORMALIZE: occurrence transform restore returned false reason='{reason}' "
                + f"route='root.transformOccurrences' occurrence='{_occurrence_name(occurrence)}'"
            )
    except Exception as ex:
        logger.log(
            f"NORMALIZE: occurrence transform restore failed reason='{reason}' "
            + f"route='root.transformOccurrences' occurrence='{_occurrence_name(occurrence)}': {ex}"
        )

    for attr in ("transform2", "transform"):
        try:
            setattr(occurrence, attr, matrix.copy())
            logger.log(
                f"NORMALIZE: occurrence transform restored reason='{reason}' "
                + f"route='{attr}' occurrence='{_occurrence_name(occurrence)}'"
            )
            return True
        except Exception as ex:
            logger.log(
                f"NORMALIZE: occurrence transform restore failed reason='{reason}' "
                + f"route='{attr}' occurrence='{_occurrence_name(occurrence)}': {ex}"
            )
    return False


def _native_object(entity):
    if not entity:
        return None
    try:
        native = entity.nativeObject
        if native and native != entity:
            return native
    except:
        pass
    return None


def _entity_name(entity):
    try:
        return entity.name or ""
    except:
        return ""


def _component_occurrences_in_context(comp, parent_occurrence):
    out = []
    if not comp:
        return out
    try:
        occs = comp.occurrences
        for i in range(occs.count):
            child_occ = occs.item(i)
            if not child_occ:
                continue
            if parent_occurrence:
                try:
                    child_occ = child_occ.createForAssemblyContext(parent_occurrence)
                except Exception as ex:
                    logger.log(
                        f"NORMALIZE: child occurrence context failed "
                        + f"child='{_occurrence_name(child_occ)}' "
                        + f"parent='{_occurrence_name(parent_occurrence)}': {ex}"
                    )
                    continue
            out.append(child_occ)
    except Exception as ex:
        logger.log(f"NORMALIZE: enumerate child occurrences failed component='{_component_name(comp)}': {ex}")
    return out


def _delete_occurrence_object(occurrence, reason):
    if not occurrence:
        return False
    candidates = []
    native = _native_object(occurrence)
    if native:
        candidates.append(("native occurrence", native))
    candidates.append(("occurrence", occurrence))

    for label, candidate in candidates:
        try:
            old_name = _occurrence_name(candidate)
            candidate.deleteMe()
            logger.log(
                f"NORMALIZE: occurrence delete ok reason='{reason}' "
                + f"route='{label}' occurrence='{old_name}'"
            )
            return True
        except Exception as ex:
            logger.log(
                f"NORMALIZE: occurrence delete failed reason='{reason}' "
                + f"route='{label}' occurrence='{_occurrence_name(candidate)}': {ex}"
            )
    return False


def _set_component_name(comp, target_name, reason):
    if not comp or not target_name:
        return False

    candidates = []
    native = _native_object(comp)
    if native:
        candidates.append(("native component", native))
    candidates.append(("component", comp))

    for label, candidate in candidates:
        try:
            current_name = _component_name(candidate)
            if current_name != target_name:
                candidate.name = target_name
            logger.log(
                f"NORMALIZE: component rename ok reason='{reason}' "
                + f"route='{label}' from='{current_name}' to='{target_name}'"
            )
            return True
        except Exception as ex:
            logger.log(
                f"NORMALIZE: component rename failed reason='{reason}' route='{label}' "
                + f"current='{_component_name(candidate)}' target='{target_name}': {ex}"
            )
    return False


def _set_occurrence_name(occurrence, target_name, reason):
    if not occurrence or not target_name:
        return False

    candidates = []
    native = _native_object(occurrence)
    if native:
        candidates.append(("native occurrence", native))
    candidates.append(("occurrence", occurrence))

    for label, candidate in candidates:
        try:
            current_name = _occurrence_name(candidate)
            current_base = _browser_leaf_name(current_name)
            if current_base != target_name:
                candidate.name = target_name
            logger.log(
                f"NORMALIZE: occurrence rename ok reason='{reason}' "
                + f"route='{label}' from='{current_name}' to='{target_name}'"
            )
            return True
        except Exception as ex:
            logger.log(
                f"NORMALIZE: occurrence rename failed reason='{reason}' route='{label}' "
                + f"current='{_occurrence_name(candidate)}' target='{target_name}': {ex}"
            )
    return False


def _set_component_name_from_refs(target_name, reason, *refs):
    renamed = False
    for ref in refs:
        occ = adsk.fusion.Occurrence.cast(ref)
        if occ:
            occurrence_ok = _set_occurrence_name(occ, target_name, reason)
            renamed = occurrence_ok or renamed
            if not occurrence_ok:
                _set_component_name(_component_from_occurrence(occ), target_name, reason)
            continue

        body = adsk.fusion.BRepBody.cast(ref)
        if body:
            renamed = _set_component_name(_component_from_body(body), target_name, reason) or renamed
            continue

        comp = adsk.fusion.Component.cast(ref)
        if comp:
            renamed = _set_component_name(comp, target_name, reason) or renamed
            continue

    return renamed


def _set_component_and_occurrence_name(comp, occurrence, target_name, reason):
    return _set_component_name_from_refs(target_name, reason, occurrence, comp)


def _add_named_root_occurrence(design, target_name, reason):
    if not design or not target_name:
        return None
    try:
        root = design.rootComponent
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        if not occ:
            return None

        named = _set_component_name_from_refs(
            target_name,
            reason,
            occ,
            _component_from_occurrence(occ),
        )
        if named:
            return occ

        logger.log(
            f"NORMALIZE: named root occurrence aborted name blocked "
            + f"reason='{reason}' created='{_occurrence_name(occ)}' target='{target_name}'"
        )
        _delete_occurrence_object(occ, "cleanup unnamed root component")
    except Exception as ex:
        logger.log(
            f"NORMALIZE: add named root occurrence failed "
            + f"reason='{reason}' target='{target_name}': {ex}"
        )
    return None


def _add_sibling_wrapper_occurrence(design, old_occurrence, wrapper_name):
    if not wrapper_name:
        return None, None

    assembly_context = None
    try:
        assembly_context = old_occurrence.assemblyContext if old_occurrence else None
    except:
        assembly_context = None

    try:
        root_occ = _add_named_root_occurrence(design, wrapper_name, "new rebuilt wrapper")
        if not root_occ:
            return None, None

        if assembly_context:
            try:
                root_transform = _occurrence_transform(root_occ)
                moved_occ = root_occ.moveToComponent(assembly_context)
                if moved_occ:
                    _restore_occurrence_transform(
                        design,
                        moved_occ,
                        root_transform,
                        "preserve rebuilt wrapper world transform",
                    )
                    logger.log(
                        f"NORMALIZE: moved named rebuilt wrapper into context "
                        + f"wrapper='{_occurrence_name(moved_occ)}' "
                        + f"context='{_occurrence_name(assembly_context)}'"
                    )
                    return moved_occ, moved_occ
            except Exception as ex:
                logger.log(
                    f"NORMALIZE: rebuilt wrapper move into context failed "
                    + f"wrapper='{_occurrence_name(root_occ)}' "
                    + f"context='{_occurrence_name(assembly_context)}': {ex}"
                )
                _delete_occurrence_object(root_occ, "cleanup unmoved rebuilt wrapper")
                return None, None
        return root_occ, root_occ
    except Exception as ex:
        logger.log(
            f"NORMALIZE: add rebuilt wrapper failed old='{_occurrence_name(old_occurrence)}' "
            + f"target='{wrapper_name}': {ex}"
        )
    return None, None


def _rebuild_mixed_wrapper(design, comp, parent_occurrence, wrapper_name):
    if not design or not comp or not parent_occurrence or not wrapper_name:
        return False

    old_name = _component_name(comp)
    child_occurrences = _component_occurrences_in_context(comp, parent_occurrence)
    if not child_occurrences:
        logger.log(f"NORMALIZE: rebuild wrapper skipped no children component='{old_name}'")
        return False

    wrapper_occurrence, wrapper_native = _add_sibling_wrapper_occurrence(
        design,
        parent_occurrence,
        wrapper_name,
    )
    if not wrapper_occurrence:
        return False

    moved_count = 0
    for child_occ in child_occurrences:
        try:
            child_name = _occurrence_name(child_occ)
            child_transform = _occurrence_transform(child_occ)
            moved = child_occ.moveToComponent(wrapper_occurrence)
            if moved:
                _restore_occurrence_transform(
                    design,
                    moved,
                    child_transform,
                    "preserve child world transform after wrapper rebuild",
                )
                moved_count += 1
                logger.log(
                    f"NORMALIZE: moved child into rebuilt wrapper "
                    + f"child='{child_name}' wrapper='{_occurrence_name(wrapper_occurrence)}'"
                )
            else:
                logger.log(
                    f"NORMALIZE: move child into rebuilt wrapper returned null "
                    + f"child='{child_name}' wrapper='{_occurrence_name(wrapper_occurrence)}'"
                )
        except Exception as ex:
            logger.log(
                f"NORMALIZE: move child into rebuilt wrapper failed "
                + f"child='{_occurrence_name(child_occ)}' "
                + f"wrapper='{_occurrence_name(wrapper_occurrence)}': {ex}"
            )

    if moved_count <= 0:
        _delete_occurrence_object(wrapper_native or wrapper_occurrence, "cleanup empty rebuilt wrapper")
        return False

    deleted_old = _delete_occurrence_object(parent_occurrence, "remove old mixed wrapper after rebuild")
    if not deleted_old:
        logger.log(
            f"NORMALIZE: rebuilt wrapper kept but old wrapper could not be deleted "
            + f"old='{_occurrence_name(parent_occurrence)}' new='{_occurrence_name(wrapper_occurrence)}'"
        )

    logger.log(
        f"NORMALIZE: rebuilt mixed wrapper from='{old_name}' to='{wrapper_name}' "
        + f"children_moved={moved_count} old_deleted={deleted_old}"
    )
    return True


def _move_body_to_new_child_component(design, parent_comp, body, parent_occurrence, target_component_name):
    child_occ = None
    try:
        child_occ = _add_named_root_occurrence(design, target_component_name, "new child before body move")
        if not child_occ:
            raise RuntimeError(f"could not name new child component '{target_component_name}'")

        if parent_occurrence:
            child_transform = _occurrence_transform(child_occ)
            moved_child_occ = child_occ.moveToComponent(parent_occurrence)
            if not moved_child_occ:
                raise RuntimeError("move named child occurrence into parent returned null")
            child_occ = moved_child_occ
            _restore_occurrence_transform(
                design,
                child_occ,
                child_transform,
                "preserve new child world transform after parent move",
            )
            logger.log(
                f"NORMALIZE: moved named child into parent "
                + f"child='{_occurrence_name(child_occ)}' parent='{_occurrence_name(parent_occurrence)}'"
            )

        target_occ = _occurrence_for_context(child_occ, parent_occurrence)
        if not target_occ:
            raise RuntimeError("could not resolve new child occurrence in assembly context")

        body_in_context = _body_for_context(body, parent_occurrence)
        if not body_in_context:
            raise RuntimeError("could not resolve body in assembly context")

        moved_body = body_in_context.moveToComponent(target_occ)
        if not moved_body:
            raise RuntimeError("moveToComponent returned null")

        moved_component = _component_from_body(moved_body) or _component_from_occurrence(child_occ)
        _set_component_name_from_refs(
            target_component_name,
            "new child after body move",
            child_occ,
            target_occ,
            moved_component,
            moved_body,
        )

        try:
            moved_body.name = target_component_name
        except:
            pass

        return moved_body, moved_component, child_occ
    except:
        _delete_empty_occurrence_safely(child_occ)
        raise


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


def _component_has_direct_child_named(comp, target_name):
    if not comp or not target_name:
        return False
    try:
        occs = comp.occurrences
        for i in range(occs.count):
            occ = occs.item(i)
            child_comp = _component_from_occurrence(occ)
            if not child_comp:
                continue
            if _component_name(child_comp) == target_name:
                return True

            child_bodies = _direct_bodies(child_comp)
            if len(child_bodies) == 1 and _body_name(child_bodies[0]) == target_name:
                return True
    except:
        pass
    return False


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
        "components_without_context_skipped": 0,
        "bodies_skipped_read_only": 0,
        "body_names_skipped_no_context": 0,
        "assembly_wrappers_renamed": 0,
        "errors": 0,
    }
    errors = []
    converted_component_targets = {}

    try:
        components_before = _build_component_contexts(design)
    except Exception as ex:
        ui.messageBox(f"Failed to enumerate components: {ex}", CMD_NAME)
        return

    logger.log(
        f"NORMALIZE: start components={len(components_before)} "
        + "strategy=contextual_move_to_child_component"
    )

    for comp_context in components_before:
        comp = comp_context["component"]
        parent_occurrence = comp_context["occurrence"]
        stats["components_scanned"] += 1

        if comp_context["linked"]:
            stats["referenced_components_skipped"] += 1
            logger.log(f"NORMALIZE: skip linked component='{_component_name(comp)}'")
            continue

        if comp != design.rootComponent and not parent_occurrence:
            stats["components_without_context_skipped"] += 1
            errors.append(
                f'Component "{_component_name(comp)}" skipped: no editable occurrence context found'
            )
            continue

        bodies = _direct_bodies(comp)
        body_count = len(bodies)
        child_count = _direct_child_occurrence_count(comp)
        parent_original_name = _component_name(comp)

        if not _needs_conversion(body_count, child_count):
            continue

        stats["bodies_detected_for_conversion"] += body_count
        converted_here = 0

        for body_index, body in enumerate(bodies):
            source_body_name = _body_name(body)
            parent_name = parent_original_name
            target_component_name = _preferred_child_component_name(
                parent_name,
                source_body_name,
                body_index,
                body_count,
            )

            try:
                readonly_reason = _body_editability_reason(body)
                if readonly_reason:
                    stats["bodies_skipped_read_only"] += 1
                    logger.log(
                        f"NORMALIZE: skip body component='{parent_name}' "
                        + f"body='{source_body_name}' reason='{readonly_reason}'"
                    )
                    continue

                logger.log(
                    f"NORMALIZE: convert body component='{parent_name}' "
                    + f"body='{source_body_name}' occurrence='{_occurrence_name(parent_occurrence)}' "
                    + f"target='{target_component_name}'"
                )

                moved_body, moved_component, child_occ = _move_body_to_new_child_component(
                    design,
                    comp,
                    body,
                    parent_occurrence,
                    target_component_name,
                )
                moved_component = moved_component or _component_from_body(moved_body)
                moved_component_key = _component_key(moved_component)
                if moved_component_key:
                    converted_component_targets[moved_component_key] = target_component_name
                if child_occ:
                    child_occ_comp = _component_from_occurrence(child_occ)
                    child_occ_comp_key = _component_key(child_occ_comp)
                    if child_occ_comp_key:
                        converted_component_targets[child_occ_comp_key] = target_component_name

                stats["bodies_converted"] += 1
                converted_here += 1
            except Exception as ex:
                stats["errors"] += 1
                logger.log(
                    f"NORMALIZE: convert failed component='{parent_name}' "
                    + f"body='{source_body_name}' target='{target_component_name}': {ex}"
                )
                errors.append(
                    f'Convert body "{source_body_name}" in component "{parent_name}" failed: {ex}'
                )

        if converted_here > 0:
            stats["components_normalized"] += 1

    try:
        components_after = _build_component_contexts(design)
    except:
        components_after = components_before

    for comp_context in components_after:
        comp = comp_context["component"]
        parent_occurrence = comp_context["occurrence"]

        if comp_context["linked"]:
            continue

        if comp != design.rootComponent and not parent_occurrence:
            continue

        parent_name = _component_name(comp)
        if _direct_bodies(comp):
            continue

        if _direct_child_occurrence_count(comp) <= 0:
            continue

        wrapper_name = _assembly_wrapper_name(parent_name)
        if not wrapper_name or wrapper_name == parent_name:
            continue

        if not _component_has_direct_child_named(comp, parent_name):
            continue

        if _rebuild_mixed_wrapper(design, comp, parent_occurrence, wrapper_name):
            stats["assembly_wrappers_renamed"] += 1
            logger.log(
                f"NORMALIZE: parent wrapper rebuilt "
                + f"from='{parent_name}' to='{wrapper_name}'"
            )

    try:
        components_after = _build_component_contexts(design)
    except:
        pass

    for comp_context in components_after:
        comp = comp_context["component"]
        parent_occurrence = comp_context["occurrence"]

        if comp_context["linked"]:
            continue

        if comp != design.rootComponent and not parent_occurrence:
            stats["body_names_skipped_no_context"] += 1
            continue

        bodies = _direct_bodies(comp)
        if len(bodies) != 1:
            continue

        body = bodies[0]
        comp_key = _component_key(comp)
        intended_name = converted_component_targets.get(comp_key)

        body_in_context = _body_for_context(body, parent_occurrence)
        if not body_in_context:
            stats["body_names_skipped_no_context"] += 1
            continue

        component_name = _component_name(comp)
        current_name = _body_name(body_in_context)
        if intended_name:
            target_name = intended_name
        elif _is_default_component_name(component_name) and not _is_generic_body_name(current_name):
            target_name = current_name
        else:
            target_name = component_name

        if component_name != target_name or (
            parent_occurrence and _browser_leaf_name(_occurrence_name(parent_occurrence)) != target_name
        ):
            _set_component_and_occurrence_name(
                comp,
                parent_occurrence,
                target_name,
                "repair single-body leaf in rename pass",
            )

        if current_name == target_name:
            continue

        try:
            body_in_context.name = target_name
            stats["body_names_renamed"] += 1
        except Exception as ex:
            stats["errors"] += 1
            logger.log(
                f"NORMALIZE: rename failed component='{target_name}' "
                + f"body='{current_name}': {ex}"
            )
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
        f"Components skipped without editable context: {stats['components_without_context_skipped']}",
        f"Bodies skipped read-only/unsupported: {stats['bodies_skipped_read_only']}",
        f"Body names skipped without context: {stats['body_names_skipped_no_context']}",
        f"Assembly wrapper names changed: {stats['assembly_wrappers_renamed']}",
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
