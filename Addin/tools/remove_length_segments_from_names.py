import re
import traceback

import adsk.core
import adsk.fusion


LENGTH_SEGMENT_RE = re.compile(r"-(\d+(?:\.\d+)?)mm-", re.IGNORECASE)


def _strip_length_segment(name: str) -> str:
    if not name:
        return name
    return LENGTH_SEGMENT_RE.sub("-", name)


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface if app else None

    try:
        design = adsk.fusion.Design.cast(app.activeProduct) if app else None
        if not design:
            if ui:
                ui.messageBox("No active Fusion design found.")
            return

        renamed_components = 0
        renamed_occurrences = 0
        errors = []

        # Rename component names (skip root component).
        for comp in design.allComponents:
            if comp == design.rootComponent:
                continue
            old_name = comp.name or ""
            new_name = _strip_length_segment(old_name)
            if new_name == old_name:
                continue
            try:
                comp.name = new_name
                renamed_components += 1
            except Exception as ex:
                errors.append(f'Component "{old_name}": {ex}')

        # Rename occurrence names that still contain length text.
        # This catches any manually renamed/custom occurrence labels.
        all_occs = design.rootComponent.allOccurrences
        for i in range(all_occs.count):
            occ = all_occs.item(i)
            old_name = occ.name or ""
            new_name = _strip_length_segment(old_name)
            if new_name == old_name:
                continue
            try:
                occ.name = new_name
                renamed_occurrences += 1
            except Exception as ex:
                errors.append(f'Occurrence "{old_name}": {ex}')

        summary = (
            "Length segment cleanup complete.\n\n"
            f"Components renamed: {renamed_components}\n"
            f"Occurrences renamed: {renamed_occurrences}"
        )

        if errors:
            sample = "\n".join(errors[:10])
            summary += f"\n\nErrors: {len(errors)}\n{sample}"

        if ui:
            ui.messageBox(summary)

    except:
        if ui:
            ui.messageBox("Script failed:\n" + traceback.format_exc())


def stop(context):
    pass

