Stub Arms To Wall - Step By Step Workflow

Purpose
Create a pair of sketch lines from a RHS/SHS column to a wall, where each line:
- Starts on a column side face.
- Is perpendicular to the column long axis.
- Hits the selected wall surface.

Inputs
- Column selection: body or occurrence. Must be RHS/SHS.
- Wall selection: any face or body (surface or solid). If a body is selected, use all its faces.
- Parameters: connection points, bottom offset, top offset, inboard offset.

Workflow
1) Collect selections in assembly context.
   - Convert column bodies and wall faces to assembly context proxies.
   - If the wall selection is a body, add all of its faces.

2) For each column body:
   - Find the long axis by clustering edge directions and picking the longest cluster.
   - Compute bottom/top endpoints by projecting all vertices onto the axis.
   - Identify side faces:
     - Keep planar faces with normals roughly perpendicular to the axis.
     - Group by normal direction and keep the largest face per direction.
     - From those, keep the two largest outer faces.
   - For each side face, define:
     - Side face plane (origin + normal).
     - Inboard direction = face normal pointing toward the body center.
     - Outward direction = opposite of inboard direction.

3) Build connection points along the axis.
   - Start at bottom offset, end at top offset, evenly spaced.
   - Each adjacent pair (upper/lower) is a "pair" that will share one wall point.

4) For each pair:
   - Compute the mid point between upper and lower along the axis.
   - Create a slice plane through the mid point, perpendicular to the axis.
   - For each candidate side face:
     - Project upper/lower points onto the side face plane.
     - Offset both by the inboard distance along the inboard direction.
     - Define line direction in the side face plane:
       - line_dir = axis_dir cross side_face_normal (normalize).
     - Find the wall hit:
       - Intersect the wall face with the slice plane to get an intersection curve.
       - Find the closest point on that curve to the mid point (in the slice plane).
       - If no curve exists, try the next side face.
   - Use the first valid wall hit as the wall point.
   - Draw two lines: upper_start -> wall_point, lower_start -> wall_point.

5) Errors and reporting:
   - If no side faces or no wall hit, skip the pair and log it.
   - Summarize created lines, skipped bodies, and missed pairs.

Notes
- This method avoids ray length and direction issues by using plane/curve intersections.
- It stays faithful to the manual workflow: draw a line on the side face, perpendicular to the axis, until it hits the wall.
