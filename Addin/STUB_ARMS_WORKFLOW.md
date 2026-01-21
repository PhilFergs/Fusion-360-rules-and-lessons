Stub Arms To Wall - Step By Step Workflow

Purpose
Create stub arm sketch lines from RHS/SHS columns to selected wall faces. Lines are only drawn when the hit lands on a selected face boundary, and the lower line can be shifted up to clear the wall.

Inputs
- Column selection: face (manual override), body, or occurrence. Body/occurrence auto-picks a side face.
- Wall selection: face, body, or occurrence. Body/occurrence uses all faces.
- Parameters: connection points, bottom offset, top offset, wall clearance.

Workflow
1) Collect selections in assembly context.
   - Wall faces are expanded from bodies/occurrences.
   - Column faces are used directly; column bodies/occurrences are queued for auto face selection.

2) For each column body:
   - Find the long axis and bottom/top endpoints.
   - Candidate side faces are planar faces with normals roughly perpendicular to the axis.
   - Keep the largest faces; tie-break by most valid on-face hits along the stub-arm direction.

3) For each column face:
   - Compute the line direction in the face plane:
     - line_dir = axis_dir cross face_normal (normalized).
   - Build connection points along the axis (bottom offset to top offset).

4) For each pair (adjacent points):
   - Cast rays along line_dir and -line_dir to the selected wall faces.
   - Accept only hits that land inside the face boundary (projected boundary polygon).

5) Clearance adjustment:
   - Keep the wall hit fixed.
   - Move the lower point up by the wall clearance step until the lower line no longer intersects a wall face before the hit.
   - If it cannot clear before reaching the upper point, skip the lower line (keep upper).

6) Output:
   - Stub arm sketches are created in the root component subcomponent "stub arm lines".
   - Profiles are hidden; only stub-arm lines remain.
   - Temporary wall boundary sketches are deleted.

Errors and reporting
- If no valid hit, the pair is skipped and counted as missed.
- If no valid pairs for a column, no sketch is created.

Notes
- Selecting a column face always overrides auto-pick.
- Selecting many wall faces is supported; the closest valid on-face hit is chosen.
