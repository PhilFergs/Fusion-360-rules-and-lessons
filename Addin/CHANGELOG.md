# CHANGELOG

All notable changes to the Phils Design Tools add-in will be tracked here.

## Unreleased
### Added
- DEVLOG.md for ongoing development notes and change tracking.
- README.md with usage and development notes for this branch.
- WORKFLOW.md with the end-to-end workflow, automation plan, and naming rules.
- USER_GUIDE.rtf for training users on the workflow and tools.
- USER_GUIDE.docx for a Word-native version of the user guide.
- VERSION_LOG.md to track uploaded versions.
- tools/deploy_addin.ps1 to back up the active add-in before deployment.
- Split Body (Keep Side) command to split a body and keep the chosen side or all.
- tools/watch_deploy.ps1 to auto-copy add-in changes into the Fusion AddIns folder.
- Split Body Delete command as a standalone tool.
- Renamed EA Batch Rename to Batch Rename.
- Command icons for all tools to match Fusion-style menus.
- EA Hole Export CSV command (from scripts) for hole location exports.
- IGES Component Export command (from scripts) for leaf component exports.
- New Component Set command (from scripts) for batch component creation.
- Wireframe From Body command (from scripts) for centreline sketch creation.
- Hole Cut From Face command (from EA_HoleCut_AddIn).
- Dedicated PhilsDesignTools toolbar panel for all commands.
- Stub Arms To Wall command for creating stub-arm sketch lines from RHS columns to wall surfaces.
- Stub Arms To Wall: wall clearance setting, auto column body selection, and stub-arm sketches grouped under the "stub arm lines" component.
- Stub Arms Beta command (optimized stub arm generation).
### Changed
- Added per-command usage logging across all existing commands.
- Split Body now exposes Extend split tool and handles split failures gracefully.
- Split Body delete now uses a follow-up command and improved implicit split detection.
- Renamed the add-in to Phils Design Tools and updated file paths and IDs.
- Added logging calls across commands and startup/shutdown for debugging.
- Normalized UI strings to ASCII-only text.
- Fixed EA rotate axis selection to use the outer hole face and closest-point axis, with added debug logging for axis/pivot values.
- Removed unused imports and an unused rotate helper to reduce redundancy.
- Documented versioning and deployment steps in WORKFLOW.md.
- Stub Arms To Wall: boundary-only wall hit validation (on-face polygon), supports wall face/body/occurrence selection, removes guide lines and wall sketches, and skips lower lines that cannot clear the wall.
- Stub Arms To Wall: enforce 700-1000 mm spacing between connection points with auto-adjusted point count.
- Stub Arms To Wall: added min/max spacing inputs (defaults 700/1000 mm).
- Stub Arms To Wall: promoted the optimized Beta logic to the default tool; removed separate Beta command.
- Stub Arms Export: adds bracket/block/fastener totals and bracket type counts.
- Stub Arms Export: bracket type now uses the actual stub arm direction vs wall normal in XY (square if within 3 degrees), with fallback to line direction.
- Stub Arms To Wall: prefer wall hits that keep the upper stub arm above, reducing inverted top pairs.
- Stub Arms Export: bracket tags now write to native sketch lines and export reads bracket type even if anchor flag is missing.
- Stub Arms Export: fixed stock/bracket totals not writing due to loop indentation.
- Stub Arms Export: bracket angle now treats opposite directions as parallel and falls back to 3D; defaults to swivel if still ambiguous.
- Stub Arms To Wall: bracket type now uses wall normal at hit point (fallback to plane normal).
- Stub Arms To Wall: guard against non-vector normal returns when classifying brackets.
- Stub Arms To Wall: tag stub arm lines with column labels (occurrence name) for export.
- Stub Arms Export: use column label attribute and default missing bracket tags to swivel.
- Stub Arms To Wall: sketch/column labels now prefer component name over occurrence name.
- Stub Arms To Wall: bracket classification now uses abs(dot) in XY with 3D fallback; defaults to swivel if angle cannot be computed.
