# DEVLOG

Ongoing development notes for the Phils Design Tools add-in.

## Update checklist
- Add a brief entry to this DEVLOG for each change set.
- Update CHANGELOG.md under Unreleased for user-facing changes.

## 2026-01-02
- Added add-in scoped CHANGELOG.md, DEVLOG.md, and README.md for development tracking.
- Added WORKFLOW.md capturing the workflow map and agreed rules.
- Renamed the add-in to Phils Design Tools and updated IDs/paths.
- Added logger usage across command handlers and startup/shutdown.
- Added USER_GUIDE.rtf for onboarding users to the workflow.
- Added USER_GUIDE.docx for Word-native distribution.
- Fixed EA rotate axis drift by selecting the planar face with hole circles farthest from the body center and deriving the axis from closest points on the two holes; added debug logging to capture axis/pivot values.
- Note to self: always bind face geometry (e.g., `plane`) in loops before using it, and avoid mixing edges from multiple faces when defining rotation axes.
- Added `VERSION_LOG.md` and `tools/deploy_addin.ps1` to log uploads and back up the active add-in before deployment.
- Documented versioning and deployment steps in WORKFLOW.md.

## 2026-01-06
- Added Split Body (Keep Side) command with post-split keep selection (positive, negative, or all).
- Added auto-deploy watcher script and optional no-backup deploy flag for faster iteration.
- Logged usage details for all existing commands via smg_logger.log_command.
- Exposed Extend split tool option and added guardrails for split failures.
- Reworked Split Body delete flow to use a follow-up command and improved implicit split detection.
- Added Split Body Delete as a standalone Modify command.
- Added Fusion-style icons for all command buttons.
- Renamed EA Batch Rename to Batch Rename.

## 2026-01-07
- Rolled EA_HoleExport_CSVv1, IGESComponentExport, NewComponentset, and WireframeFromBody scripts into add-in commands.
- Integrated EA_HoleCut_AddIn as a new Hole Cut From Face command.
- Added a dedicated PhilsDesignTools toolbar panel and moved all commands into it.
- Added command icons for the new tools and updated README/CHANGELOG.

## 2026-01-16
- Added Stub Arms To Wall command to create stub-arm sketch lines from RHS columns to wall faces.
- Implemented debug logging and geometry diagnostics for the stub arms workflow.

## 2026-01-21
- Stub Arms To Wall rework: selection now uses a face for the column, sketch is created directly on that face in assembly context, and guide lines are drawn using modelToSketchSpace so they land on the selected face.
- Fixed top/bottom offset inversion by enforcing world Z ordering on the axis endpoints before spacing.
- Simplified face/axis detection to reduce drift; guide lines confirm spacing and offsets are now correct on the selected face.
- Reintroduced wall selection + ray logic; added local/assembly transforms for wall faces and per-pair "no wall hit" debug logging (world + local ray origin/dir and wall normal).
- Added stub arms triangle drawing using the midpoints between guide lines when a wall hit is found (guide lines remain for debugging).
- Marked backup `Addin/PhilsDesignTools/smg_stub_arms.py.bak-Some what working model` as the reference snapshot that produces lines without face-bounds clipping.

Current status
- Guide lines are correct and in the right place, but wall hits are still missing for some linked wall faces.
- Latest debug lines ("Missed pair ... mid_w/dir_w ... mid_l/dir_l ... wall_n_*") should appear in `Addin/PhilsDesignTools/PhilsDesignTools.log` after running the tool.

Suggestions to resume / fix if still missing wall hits
- Confirm Fusion is loading the latest add-in build (restart Fusion after deploy) and check the log for the "Missed pair" debug lines.
- Use the logged world/local ray direction to verify rays are going outward from the selected face; if not, flip the direction or use the selected face normal directly.
- If wall faces are from linked components, test with a native (non-linked) wall face to confirm whether occurrence transforms are still wrong.
- Try intersecting against the wall face plane first, then check point-in-face as a fallback (bypass ray casting issues).
- As a last resort, project the wall face to the sketch and intersect 2D lines to get hit points.

## 2026-01-22
- Stub Arms To Wall finalized: on-face wall hit validation now uses projected boundary polygons (manual point-in-polygon) and removes guide lines.
- Wall boundary sketches are created for validation and removed after the command completes.
- Wall selection supports faces, bodies, and occurrences; column selection supports faces, bodies, and occurrences with auto side-face pick.
- Added stub arm lines component under root to hold all stub arm sketches.
- Added wall clearance input to shift the lower connection point up; if it cannot clear, only the upper line is drawn.

## 2026-01-23
- Stub Arms To Wall now enforces 700-1000 mm spacing between connection points by auto-adjusting point count per column span.
- Added min/max spacing inputs to the Stub Arms UI (defaults 700/1000 mm).
- Added Stub Arms Beta command with faster on-face validation and reduced sketch usage.
- Promoted the optimized Beta logic to the default Stub Arms tool and retired the separate Beta command.
- Stub Arms Export now totals brackets, blocks, bolts/nuts, and screws using the new bracket angle tagging.
- Bracket type classification now compares wall normal to the actual stub arm direction in XY (fallback to line direction).
- Wall hit selection now prefers hits that keep the upper stub arm above (based on column axis projection).
- Bracket tagging now applies to native sketch lines; export uses bracket type even if anchor is missing.
- Fixed Stub Arms export loop so stock/bracket totals write for every line.
- Bracket angle now uses absolute XY/3D comparisons and defaults to swivel when ambiguous.
- Bracket type now uses wall normal at the hit point (fallback to plane normal).
- Added guard to coerce wall normals when Fusion returns lists/tuples.
- Stub Arms now tags column labels on lines; export reads label attributes and defaults missing bracket tags to swivel.
- Stub Arms now prefers component name for sketch/column labels (falls back to occurrence name).
- Bracket classification now uses abs(dot) in XY with 3D fallback; defaults to swivel if angle can't be computed.
