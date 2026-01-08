import adsk.core, adsk.fusion, traceback, os
import smg_context as ctx
import smg_logger as logger


CMD_ID = "PhilsDesignTools_SplitBody_V2"
OLD_CMD_IDS = ["PhilsDesignTools_SplitBody"]
DELETE_CMD_ID = "PhilsDesignTools_SplitBody_Delete"
DELETE_CMD_NAME = "Split Body Delete"
DELETE_CMD_TOOLTIP = "Select a body to delete after a split."
CMD_NAME = "Split Body (Keep Side)"
CMD_TOOLTIP = "Split a body with a plane/face and keep one side or all."
SPLIT_VERSION = "2026-01-06-native"
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)
DELETE_RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", DELETE_CMD_ID)

LAST_SPLIT_BODY_TOKENS = []


class SplitExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log("Split Body failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Split Body failed:\n" + traceback.format_exc())


class SplitCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById("split_body"):
                return

            body_sel = inputs.addSelectionInput(
                "split_body",
                "Body",
                "Select a body to split"
            )
            body_sel.addSelectionFilter("Bodies")
            body_sel.setSelectionLimits(1, 1)

            tool_sel = inputs.addSelectionInput(
                "split_tool",
                "Split tool",
                "Select a planar face or construction plane"
            )
            tool_sel.addSelectionFilter("PlanarFaces")
            tool_sel.addSelectionFilter("ConstructionPlanes")
            tool_sel.setSelectionLimits(1, 1)

            inputs.addBoolValueInput(
                "split_extend",
                "Extend split tool",
                True,
                "",
                True
            )

            keep_dd = inputs.addDropDownCommandInput(
                "split_keep_mode",
                "Post-split action",
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            keep_dd.listItems.add("Select body to delete", True)
            keep_dd.listItems.add("Keep all", False)

            on_exec = SplitExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)

        except:
            logger.log("Split Body UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Split Body UI failed:\n" + traceback.format_exc())


class SplitDeleteExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute_delete(args)
        except:
            logger.log("Split Body delete failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Split Body delete failed:\n" + traceback.format_exc())


class SplitDeleteCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            if inputs.itemById("split_delete_body"):
                return

            sel = inputs.addSelectionInput(
                "split_delete_body",
                "Body to delete",
                "Select a body to delete from the last split"
            )
            sel.addSelectionFilter("Bodies")
            sel.setSelectionLimits(1, 1)

            on_exec = SplitDeleteExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)
        except:
            logger.log("Split Body delete UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Split Body delete UI failed:\n" + traceback.format_exc())


def _get_plane_from_tool(tool):
    cp = adsk.fusion.ConstructionPlane.cast(tool)
    if cp:
        plane = adsk.core.Plane.cast(cp.geometry)
        return plane

    face = adsk.fusion.BRepFace.cast(tool)
    if face:
        return adsk.core.Plane.cast(face.geometry)

    return None


def _collect_body_tokens(bodies):
    tokens = []
    try:
        for b in bodies:
            try:
                tokens.append(b.entityToken)
            except:
                pass
    except:
        pass
    return tokens


def _set_last_split_bodies(tokens):
    global LAST_SPLIT_BODY_TOKENS
    LAST_SPLIT_BODY_TOKENS = list(tokens) if tokens else []


def _get_native_entity(entity):
    if not entity:
        return None
    try:
        native = entity.nativeObject
        if native:
            return native
    except:
        pass
    return entity


def _safe_name(entity):
    try:
        return entity.name
    except:
        return ""


def _is_proxy(entity):
    try:
        return entity.assemblyContext is not None
    except:
        return False


def _get_parent_component(entity):
    try:
        return entity.parentComponent
    except:
        return None


def _get_bbox_center(bbox):
    if not bbox:
        return None
    minp = bbox.minPoint
    maxp = bbox.maxPoint
    return adsk.core.Point3D.create(
        (minp.x + maxp.x) * 0.5,
        (minp.y + maxp.y) * 0.5,
        (minp.z + maxp.z) * 0.5,
    )


def _classify_body(body, plane):
    if not body or not plane:
        return 0.0
    center = _get_bbox_center(body.boundingBox)
    if not center:
        return 0.0
    n = adsk.core.Vector3D.create(plane.normal.x, plane.normal.y, plane.normal.z)
    if n.length == 0:
        return 0.0
    n.normalize()
    v = adsk.core.Vector3D.create(
        center.x - plane.origin.x,
        center.y - plane.origin.y,
        center.z - plane.origin.z,
    )
    return n.dotProduct(v)


def _execute(args):
    cmd = args.command
    inputs = cmd.commandInputs

    body_sel = adsk.core.SelectionCommandInput.cast(inputs.itemById("split_body"))
    tool_sel = adsk.core.SelectionCommandInput.cast(inputs.itemById("split_tool"))
    extend_in = adsk.core.BoolValueCommandInput.cast(inputs.itemById("split_extend"))
    keep_dd = adsk.core.DropDownCommandInput.cast(inputs.itemById("split_keep_mode"))

    if not body_sel or body_sel.selectionCount == 0:
        ctx.ui().messageBox("Select a body to split.")
        return
    if not tool_sel or tool_sel.selectionCount == 0:
        ctx.ui().messageBox("Select a planar face or construction plane.")
        return

    body = adsk.fusion.BRepBody.cast(body_sel.selection(0).entity)
    tool = tool_sel.selection(0).entity
    if not body:
        ctx.ui().messageBox("Selected body is not valid.")
        return

    body_native = _get_native_entity(body)
    comp = _get_parent_component(body)
    if not comp:
        comp = _get_parent_component(body_native)
    if not comp:
        ctx.ui().messageBox("Failed to resolve the target component.")
        return

    split_feats = comp.features.splitBodyFeatures
    is_extend = extend_in.value if extend_in else True
    split_feat = None
    split_mode = "direct"
    occ = None
    try:
        occ = body.assemblyContext
    except:
        occ = None

    bodies_before_comp = 0
    bodies_before_occ = 0
    try:
        bodies_before_comp = comp.bRepBodies.count
    except:
        bodies_before_comp = 0
    try:
        bodies_before_occ = occ.bRepBodies.count if occ else 0
    except:
        bodies_before_occ = 0
    feat_before = 0
    try:
        feat_before = split_feats.count
    except:
        feat_before = 0
    tokens_before = []
    try:
        tokens_before = _collect_body_tokens(occ.bRepBodies if occ else comp.bRepBodies)
    except:
        tokens_before = []

    logger.log_command(
        CMD_NAME,
        {
            "version": SPLIT_VERSION,
            "body": _safe_name(body),
            "body_comp": _safe_name(_get_parent_component(body_native)),
            "body_proxy": _is_proxy(body),
            "tool": type(tool).__name__,
            "tool_name": _safe_name(tool),
            "tool_comp": _safe_name(_get_parent_component(_get_native_entity(tool))),
            "tool_proxy": _is_proxy(tool),
            "extend": is_extend,
            "action": keep_dd.selectedItem.name if keep_dd and keep_dd.selectedItem else "Keep all",
        },
    )

    try:
        split_in = split_feats.createInput(body, tool, is_extend)
        split_feat = split_feats.add(split_in)
    except Exception as ex:
        logger.log_command(
            CMD_NAME,
            {
                "version": SPLIT_VERSION,
                "body": _safe_name(body),
                "tool": type(tool).__name__,
                "extend": is_extend,
                "result": "split_exception",
                "error": str(ex),
            },
        )
        split_feat = None
    feat_after = feat_before
    try:
        feat_after = split_feats.count
    except:
        feat_after = feat_before
    if not split_feat and feat_after > feat_before:
        try:
            split_feat = split_feats.item(feat_after - 1)
            split_mode = "feature_count"
        except:
            split_feat = None

    if not split_feat:
        bodies_after_comp = bodies_before_comp
        bodies_after_occ = bodies_before_occ
        try:
            bodies_after_comp = comp.bRepBodies.count
        except:
            bodies_after_comp = bodies_before_comp
        try:
            bodies_after_occ = occ.bRepBodies.count if occ else bodies_before_occ
        except:
            bodies_after_occ = bodies_before_occ
        if (bodies_after_comp > bodies_before_comp) or (bodies_after_occ > bodies_before_occ):
            split_feat = "implicit"
            split_mode = "implicit"
            logger.log_command(
                CMD_NAME,
                {
                    "version": SPLIT_VERSION,
                    "body": _safe_name(body),
                    "tool": type(tool).__name__,
                    "extend": is_extend,
                    "result": "split_implicit",
                    "bodies_before_comp": bodies_before_comp,
                    "bodies_after_comp": bodies_after_comp,
                    "bodies_before_occ": bodies_before_occ,
                    "bodies_after_occ": bodies_after_occ,
                    "feat_before": feat_before,
                    "feat_after": feat_after,
                },
            )

    if not split_feat or split_feat == "implicit":
        logger.log_command(
            CMD_NAME,
            {
                "version": SPLIT_VERSION,
                "body": body.name,
                "tool": type(tool).__name__,
                "extend": is_extend,
                "result": "split_failed" if not split_feat else "split_implicit",
                "split_mode": split_mode,
            },
        )
        if not split_feat:
            ctx.ui().messageBox(
                "Split failed. Ensure the split tool intersects the body "
                "and try again (Extend does not move the plane)."
            )
            return

    if split_mode != "implicit":
        bodies = split_feat.bodies
    else:
        bodies = occ.bRepBodies if occ else comp.bRepBodies
    if not bodies or bodies.count < 2:
        ctx.ui().messageBox("Split did not create multiple bodies.")
        return

    tokens_after = _collect_body_tokens(bodies)
    candidate_tokens = []
    if len(tokens_before) <= 1:
        candidate_tokens = tokens_after
    else:
        after_set = set(tokens_after)
        before_set = set(tokens_before)
        new_tokens = [t for t in tokens_after if t not in before_set]
        candidate_tokens = new_tokens
        try:
            orig_token = body.entityToken
            if orig_token in after_set and orig_token not in candidate_tokens:
                candidate_tokens.append(orig_token)
        except:
            pass
    if not candidate_tokens:
        candidate_tokens = tokens_after
    _set_last_split_bodies(candidate_tokens)

    keep_choice = keep_dd.selectedItem.name if keep_dd and keep_dd.selectedItem else "Keep all"
    if keep_choice.startswith("Select body"):
        keep_mode = "select_delete"
    else:
        keep_mode = "all"

    logger.log_command(
        CMD_NAME,
        {
            "version": SPLIT_VERSION,
            "body": body.name,
            "tool": type(tool).__name__,
            "extend": is_extend,
            "keep": keep_mode,
        },
    )

    if keep_mode == "select_delete":
        cmd_def = ctx.ui().commandDefinitions.itemById(DELETE_CMD_ID)
        if cmd_def:
            cmd_def.execute()

    try:
        ctx.app().activeViewport.refresh()
    except:
        pass


def _execute_delete(args):
    cmd = args.command
    inputs = cmd.commandInputs
    sel = adsk.core.SelectionCommandInput.cast(inputs.itemById("split_delete_body"))

    if not sel or sel.selectionCount == 0:
        ctx.ui().messageBox("Select one body to delete.")
        return

    body = adsk.fusion.BRepBody.cast(sel.selection(0).entity)
    if not body:
        ctx.ui().messageBox("Selected entity is not a body.")
        return

    try:
        token = body.entityToken
    except:
        token = None

    if token and LAST_SPLIT_BODY_TOKENS and token not in LAST_SPLIT_BODY_TOKENS:
        logger.log_command(
            CMD_NAME,
            {
                "version": SPLIT_VERSION,
                "result": "delete_not_in_last_split",
                "body": _safe_name(body),
            },
        )

    try:
        body.deleteMe()
    except:
        ctx.ui().messageBox("Failed to delete the selected body.")
        return

    try:
        ctx.app().activeViewport.refresh()
    except:
        pass


def register(ui, panel):
    for old_id in OLD_CMD_IDS:
        old_ctrl = panel.controls.itemById(old_id) if panel else None
        if old_ctrl:
            old_ctrl.deleteMe()
        old_def = ui.commandDefinitions.itemById(old_id)
        if old_def:
            old_def.deleteMe()

    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    handler = SplitCreatedHandler()
    cmd_def.commandCreated.add(handler)
    ctx.add_handler(handler)

    if not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = True

    del_def = ui.commandDefinitions.itemById(DELETE_CMD_ID)
    if not del_def:
        del_def = ui.commandDefinitions.addButtonDefinition(
            DELETE_CMD_ID, DELETE_CMD_NAME, DELETE_CMD_TOOLTIP, DELETE_RESOURCE_FOLDER
        )

    del_handler = SplitDeleteCreatedHandler()
    del_def.commandCreated.add(del_handler)
    ctx.add_handler(del_handler)

    if panel and not panel.controls.itemById(DELETE_CMD_ID):
        del_ctrl = panel.controls.addCommand(del_def)
        del_ctrl.isPromoted = True
        del_ctrl.isPromotedByDefault = False
