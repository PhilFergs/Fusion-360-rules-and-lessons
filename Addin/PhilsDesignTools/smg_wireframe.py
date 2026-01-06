import adsk.core
import adsk.fusion
import traceback
import os

import smg_context as ctx
import smg_logger as logger

CMD_ID = "PhilsDesignTools_WireframeFromBody"
CMD_NAME = "Wireframe From Body"
CMD_TOOLTIP = "Create centreline sketches from selected bodies."
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources", CMD_ID)

SELECTION_INPUT_ID = "wireframe_body_selection"

TOL = 1e-6
ANGLE_TOL = 1e-3


class WireframeCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            sel = inputs.addSelectionInput(
                SELECTION_INPUT_ID,
                "Bodies",
                "Select one or more solid bodies"
            )
            sel.addSelectionFilter("Bodies")
            sel.setSelectionLimits(1, 0)

            on_exec = WireframeExecuteHandler()
            cmd.execute.add(on_exec)
            ctx.add_handler(on_exec)

        except:
            logger.log("Wireframe From Body UI failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Wireframe From Body UI failed:\n" + traceback.format_exc())


class WireframeExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _execute(args)
        except:
            logger.log("Wireframe From Body failed:\n" + traceback.format_exc())
            ctx.ui().messageBox("Wireframe From Body failed:\n" + traceback.format_exc())


def _get_body_center(body):
    try:
        props = body.physicalProperties
        if props:
            com = props.centerOfMass
            if com:
                return com
    except:
        pass

    bb = body.boundingBox
    mp = bb.minPoint
    xp = bb.maxPoint
    return adsk.core.Point3D.create(
        (mp.x + xp.x) * 0.5,
        (mp.y + xp.y) * 0.5,
        (mp.z + xp.z) * 0.5,
    )


def _normalise(v):
    out = adsk.core.Vector3D.create(v.x, v.y, v.z)
    if out.length > TOL:
        out.normalize()
    return out


def _canon_dir(v):
    v2 = _normalise(v)
    if v2.x < 0 or (abs(v2.x) < TOL and v2.y < 0) or \
       (abs(v2.x) < TOL and abs(v2.y) < TOL and v2.z < 0):
        v2.scaleBy(-1)
    return v2


def _offset_point(p, d, t):
    d2 = _normalise(d)
    return adsk.core.Point3D.create(
        p.x + d2.x * t,
        p.y + d2.y * t,
        p.z + d2.z * t,
    )


def _safe_plane_from_points(planes, p0, p1, p2):
    pl_in = planes.createInput()
    if pl_in.setByThreePoints(p0, p1, p2):
        try:
            return planes.add(pl_in)
        except:
            return None
    return None


def _fallback_plane(root):
    return root.xYConstructionPlane


def _execute(args):
    app = ctx.app()
    ui = ctx.ui()

    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox("No active design.")
        return

    root = design.rootComponent
    planes = root.constructionPlanes
    sketches = root.sketches

    cmd = args.command
    inputs = cmd.commandInputs
    sel_input = adsk.core.SelectionCommandInput.cast(inputs.itemById(SELECTION_INPUT_ID))

    if not sel_input or sel_input.selectionCount == 0:
        ui.messageBox("Select one or more bodies.")
        return

    bodies = {}
    for i in range(sel_input.selectionCount):
        ent = sel_input.selection(i).entity
        body = adsk.fusion.BRepBody.cast(ent)
        if not body:
            continue
        if not body.isSolid:
            continue

        try:
            key = body.tempId
        except:
            key = id(body)
        bodies[key] = body

    bodies = list(bodies.values())
    if not bodies:
        ui.messageBox("No valid solid bodies selected.")
        return

    created = 0
    skipped_multi = []
    processed = []

    for body in bodies:
        if body.faces.count != 6:
            skipped_multi.append(body.name or "<unnamed>")
            continue

        center = _get_body_center(body)
        if not center:
            skipped_multi.append(body.name or "<unnamed>")
            continue

        clusters = []
        for e in body.edges:
            line = adsk.core.Line3D.cast(e.geometry)
            if not line:
                continue

            sp = line.startPoint
            ep = line.endPoint
            vec = adsk.core.Vector3D.create(
                ep.x - sp.x,
                ep.y - sp.y,
                ep.z - sp.z,
            )
            length = vec.length
            if length < TOL:
                continue

            d = _canon_dir(vec)

            placed = False
            for c in clusters:
                if c["dir"].crossProduct(d).length < ANGLE_TOL:
                    c["edges"].append((sp, ep, length))
                    c["tot"] += length
                    placed = True
                    break

            if not placed:
                clusters.append({
                    "dir": d,
                    "edges": [(sp, ep, length)],
                    "tot": length,
                })

        if not clusters:
            skipped_multi.append(body.name or "<unnamed>")
            continue

        clusters.sort(key=lambda c: c["tot"], reverse=True)
        axis = clusters[0]["dir"]

        min_t = None
        max_t = None
        for v in body.vertices:
            p = v.geometry
            diff = adsk.core.Vector3D.create(
                p.x - center.x,
                p.y - center.y,
                p.z - center.z,
            )
            t = diff.dotProduct(axis)
            if min_t is None:
                min_t = max_t = t
            else:
                min_t = min(min_t, t)
                max_t = max(max_t, t)

        if min_t is None or abs(max_t - min_t) < TOL:
            skipped_multi.append(body.name or "<unnamed>")
            continue

        p0 = _offset_point(center, axis, min_t)
        p1 = _offset_point(center, axis, max_t)

        ref = adsk.core.Vector3D.create(0, 0, 1)
        if axis.crossProduct(ref).length < TOL:
            ref = adsk.core.Vector3D.create(1, 0, 0)
        perp = axis.crossProduct(ref)
        if perp.length < TOL:
            perp = adsk.core.Vector3D.create(0, 1, 0)
        perp.normalize()

        pA = _offset_point(center, axis, 1.0)
        pB = _offset_point(center, perp, 1.0)

        plane = _safe_plane_from_points(planes, center, pA, pB)
        if not plane:
            plane = _fallback_plane(root)

        sk = sketches.add(plane)
        s0 = sk.modelToSketchSpace(p0)
        s1 = sk.modelToSketchSpace(p1)
        sk.sketchCurves.sketchLines.addByTwoPoints(s0, s1)

        try:
            sk.name = f"Wireframe_{body.name}"
        except:
            pass

        created += 1
        processed.append(body)

    for b in processed:
        try:
            b.isVisible = False
        except:
            pass

    logger.log_command(
        CMD_NAME,
        {
            "selected": len(bodies),
            "created": created,
            "skipped": len(skipped_multi),
        },
    )

    msg = [f"Created {created} centreline sketch(es)."]
    if skipped_multi:
        msg.append(
            "Skipped non-6-face bodies:\n  " +
            "\n  ".join(sorted(set(skipped_multi)))
        )

    ui.messageBox("\n\n".join(msg))


def register(ui, panel):
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCE_FOLDER
        )

    created_handler = WireframeCreatedHandler()
    cmd_def.commandCreated.add(created_handler)
    ctx.add_handler(created_handler)

    if panel and not panel.controls.itemById(CMD_ID):
        ctrl = panel.controls.addCommand(cmd_def)
        ctrl.isPromoted = True
        ctrl.isPromotedByDefault = False
