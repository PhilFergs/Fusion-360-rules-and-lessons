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

## 2026-01-27
- Hole Cut From Face: switched to sketch + extrude cut on a plane normal to the hole axis (replacing temporary tool body + Combine) to avoid tool body reference loss.
- Hole Cut From Face: added linked/read-only target component guard with a clear user message.
- Hole Cut From Face: improved cutting plane creation by using `Plane.create` with a fallback to three-point plane creation.
- Hole Cut From Face: set construction plane/sketch creation occurrence when cutting in an occurrence context and added explicit linked occurrence detection.
- Hole Cut From Face: added DEBUG_HOLECUT logging for selection context, transforms, axis/center in world and target space, plane creation attempts, and sketch/extrude steps.
- Hole Cut From Face: switched occurrence transforms to `transform2` (Fusion-recommended) and expanded matrix debug output via `Matrix3D.asArray()`.
- Hole Cut From Face: temporarily activates the target occurrence before creating the construction plane/sketch and restores the previous active occurrence afterward.
- Hole Cut From Face: expanded plane creation debug to log the actual exception traceback from `ConstructionPlanes.add`.
- Added AGENTS.md guidance to proactively add logging for new issues/commands and allow incremental debug logging between attempts.
- Hole Cut From Face: removed `setByPlane` (not supported in parametric) and now creates planes using `ConstructionPlanes.createInput(occurrence)` plus `setByThreePoints`.
- Hole Cut From Face: avoid construction planes entirely by finding a planar face aligned with the hole axis, projecting the center onto that face, and sketching the cut there.
- Hole Cut From Face: find the actual axis intersection on the target body using `findBRepUsingRay` (forward/backward) and use that hit point/face for the sketch; planar-scan fallback retained.
- Hole Cut From Face: avoid selecting the face boundary profile by creating sketches without projected edges when possible and selecting the smallest profile near the circle center.
- Hole Cut From Face: always restore the root component as the active edit target at the end of the command.
- Hole Cut From Face: support multi-hole selection by allowing multiple cylindrical faces and cutting each valid one with per-hole logging and a skipped summary message.
- Hole Cut From Face: fixed multi-hole logging crash (UnboundLocalError) by removing early references to per-hole variables before the loop.
- Hole Cut From Face: support multi-target selection by associating each hole to the closest intersected selected body along the hole axis (per-target transforms + ray hits).
- Hole Cut From Face: multi-target association now falls back to planar-face distance when ray hits fail, avoiding "no associated target hit" skips.
- Hole Cut From Face: expanded debug logging to include per-hole indices, entity/context details, chosen target face hit data, extrude feature health, and participant body volume deltas.
- Hole Cut From Face: fixed extrude "No target body" failures by setting participant bodies via `ObjectCollection` and using occurrence-context bodies when needed.
- Hole Cut From Face: fixed `participantBodies` TypeError by passing a plain list (with occurrence-context body when available) instead of an `ObjectCollection`.
- Hole Cut From Face: added pre-extrude context logging (active component/occurrence, sketch/profile context, and native vs occurrence participant bodies) to diagnose persistent "No target body" failures.
- Hole Cut From Face: log target component body counts/names and skip `participantBodies` when only one body is present to avoid "No target body" compute failures.
- Hole Cut From Face: expanded target bounds logs with component/occurrence names and added extrude-time reactivation + context logging to diagnose cross-component extrude creation.
- Hole Cut From Face: added extrude collection/parent component identity logging (including `extrudes.parentComponent` and object ids) to diagnose features appearing in the wrong component.
- Hole Cut From Face: when the target is an occurrence, create the sketch + extrude in the root component using occurrence-context faces/bodies to avoid features landing in the wrong component.
- Hole Cut From Face: reverted root-mode extrudes (still failed) and now reset to root then activate the target occurrence before each cut, always setting participant bodies explicitly in the target component context.
- Hole Cut From Face: for occurrence targets, create occurrence-context faces/bodies and transform the cut center into occurrence context before sketch/extrude to keep all inputs in the same context.
- Hole Cut From Face: rolled back `smg_holecut.py` to the pre-multi-target snapshot (`.bak-20260127-115807`) after multi-target changes resulted in sketches but no cuts.
- Hole Cut From Face: fixed a rollback regression where selection logging referenced `hole_body_ctx` before it existed (now logs hole count and first hole body/occurrence safely).
- Added AGENTS.md workflow rules for edit-in-InDevelopment, deploy-to-active, repo sync at session start, linked component handling, and DEVLOG update requirement.
- Stub Arms To Wall: fixed a crash in missed-pair debug logging when the wall face normal is unavailable (now logs `None` safely).
- Stub Arms To Wall: added wall face diagnostics (surface type + plane availability for asm/native faces) to explain "0 made, N missed" cases.
- Stub Arms To Wall: added a non-planar wall fallback that samples a closest point + surface normal (used for ray hits, bracket type, and missed-pair diagnostics).
- Stub Arms To Wall: replaced the normal-sampling ray fallback with a planar sketch fallback for non-planar walls (approx construction plane + projected edges + sketch-plane ray intersection).
- Stub Arms To Wall: added parameter-midpoint normal sampling and explicit diagnostics around non-planar wall sketch creation to expose silent fallback failures on NURBS walls.
- Stub Arms To Wall: switched non-planar wall handling to a best-fit plane (sampled face points + covariance/PCA) and use that plane for wall sketches, ray hits, bracket normals, and diagnostics; removed the now-unused face point/normal fallback.
- Stub Arms To Wall: best-fit plane sampling now falls back to boundary edge sampling and bbox-seeded closest-point queries when parameter extents fail (fixes `pts=0` on some NURBS faces).
- Stub Arms To Wall: best-fit sampling now tries native-face evaluation and maps sampled points into root space via `occ.transform2` when assembly-context NURBS evaluators return no usable points.
- Stub Arms To Wall: added a root-component `findBRepUsingRay` fallback for non-planar walls and filter hits back to the selected wall face/body, while keeping the planar path unchanged.
- Stub Arms To Wall: rolled back all non-planar fallbacks and restored planar-only wall handling to keep the known-working planar path stable.
- Stub Arms To Wall: added a configurable "Wall inset" (default 60 mm) that offsets the wall hit point back toward the column along the wall normal.
- Stub Arms To Wall: updated UI defaults (points=5, min/max spacing=800/1200, bottom/top=200/150) and now persists the last-used numeric settings via root-component attributes.
- Stub Arms To Wall: disabled default debug logging and sketch fallback to reduce runtime overhead on planar walls.
- Stub Arms To Wall: re-enabled sketch fallback after it caused missed wall hits in real models.
- Stub Arms To Wall: made sketch-profile containment the primary wall-hit validator, with on-face ray checks as the fallback (test change).
- Stub Arms To Wall: disabled the ray-based on-face fallback behind a flag (`USE_RAY_FALLBACK = False`) so wall hits rely only on sketch containment during testing.
- BOM Creator: rebuilt `InDevelopment/BOMCreator.bundle/Contents/_BOM_Creator.py` from disassembly/partial decompiles to replace the incompatible `.pyc` after Fusion's Python update.
- BOM Creator: restored settings normalization, column controls, BOM generation for all methods, and CSV/XLSX/XML/JSON export, and mirrored the bundle to `ApplicationPlugins` with a timestamped backup.
- BOM Creator: fixed custom item number preview stepping so it no longer skips values.
- BOM Creator: made the reconstructed add-in unambiguous by assigning a new manifest id/version and disabling the legacy `_BOM_Creator.pyc`/`__pycache__` via renames in both `InDevelopment` and `ApplicationPlugins`.
- BOM Creator: created a fully separate add-in bundle `InDevelopment/BOMCreatorRebuilt.bundle` (new manifest/product codes and `COMMAND_ID = BOMCreatorRebuilt`) and deployed it alongside the legacy bundle at `ApplicationPlugins/BOMCreatorRebuilt.bundle`.
- BOM Creator: added early boot logging in `BOMCreatorRebuilt.bundle/Contents/BOMCreator.py` that writes to `Documents/BOMCreatorRebuilt/BOMCreatorRebuilt_boot.log` to capture load failures before Fusion shows the generic API error.
- BOM Creator: renamed all remaining `*.pyc` files (in both `InDevelopment` and the active bundle) to remove the `.pyc` extension, in case Fusion is pre-scanning bytecode and blocking load before `BOMCreator.py` executes.
- BOM Creator: renamed the rebuilt add-in to **PhilsBom** by changing `COMMAND_ID/COMMAND_NAME`, renaming `BOMCreatorRebuilt.bundle` to `PhilsBom.bundle`, and renaming the core files to `PhilsBom.manifest`, `PhilsBom.py`, and `_PhilsBom.py`.
- BOM Creator: updated the manifest/package metadata (new ids/codes, namespace, version 6.2.0), renamed the command logo to `PhilsBomLogo.png`, and mirrored to `ApplicationPlugins/PhilsBom.bundle` while keeping the prior active bundle as a disabled backup.
- PhilsBom: bumped the add-in version to **1.01** in `_PhilsBom.py`, `PhilsBom.manifest`, and `PackageContents.xml`.
- PhilsBom: added a **Units** group to the settings UI with length, area, volume, mass, and center-of-mass unit dropdowns (per-export control).
- PhilsBom: normalized and persisted unit selections (`_lengthUnit/_areaUnit/_volumeUnit/_massUnit/_comUnit`) and reset them cleanly via the Reset button.
- PhilsBom: replaced manual unit scaling with `unitsManager.convert`-based conversions (internal length/area/volume units -> selected units) and updated CSV headers to show the selected units.
- PhilsBom: expanded settings logging to include the active unit selections and mirrored the updated `PhilsBom.bundle` to `ApplicationPlugins` with a timestamped backup.
- PhilsBom: numeric columns (quantity/volume/area/mass/length/width/height) now export as unquoted values when safe so Excel treats them as numbers, while still quoting when the delimiter would break the CSV.
- PhilsBom: XLSX export now infers numeric columns from headers and writes numeric `<v>` cells instead of `inlineStr`, reducing "number stored as text" warnings in Excel.
- PhilsBom: added a mass total row at the bottom when the Mass column is present, summing `mass * quantity` in the selected mass units.
- PhilsBom: added export toggles for **Include Parent Components** (default off) and **Include Linked Components** (default on), including defaults/normalization, persistence, and Reset handling.
- PhilsBom: applied occurrence filtering in `CreateBOM` and `CreateIndentedBOM`; when parent components are excluded, their children are still traversed and included.
- PhilsBom: removed legacy Autodesk App Store references by disabling update checks, clearing `OnlineDocumentation`, and replacing the help page with local instructions.
- PhilsBom: generated new `ProductCode`/`UpgradeCode` GUIDs and moved legacy docs/resources and in-bundle `*.bak-*` files to `InDevelopment/_archive` to keep the bundle clean.
- PhilsBom: mirrored the cleaned bundle to `ApplicationPlugins/PhilsBom.bundle` with a timestamped disabled-backup.
- PhilsBom: created a clean distribution zip at `InDevelopment/dist/PhilsBom.bundle-1.01.zip` containing the `PhilsBom.bundle` root and excluding `__pycache__`/disabled bytecode.
- PhilsBom: added a one-page installer guide at `InDevelopment/dist/PhilsBom_INSTALL.txt` and moved scratch zips/lists to `InDevelopment/_archive/dist-scratch-*`.
- PhilsBom: guard missing resource folders by falling back to default command icons (prevents add-in load failure if Resources/Icon is missing).
- PhilsBom: refreshed the distribution zip and installer guide after the resource-folder guard change.
- PhilsBom: updated installer guide to v1.02 and built `InDevelopment/dist/PhilsBom.bundle-1.02.zip` for distribution; archived stray dist folder to `InDevelopment/_archive/dist-scratch-*`.
- PhilsBom: clarified install guide to verify the unzipped contents and copy only the `PhilsBom.bundle` folder into `ApplicationPlugins`.
- PhilsBom: corrected install guide wording ("Look" spelling) while keeping version text at v1.02.
- Docs: clarified that this repo hosts two add-ins (PhilsDesignTools + PhilsBom) and documented their source/active paths, install steps, and distribution locations.
- Docs: renamed the PhilsBom distribution folder from `dist` to `PhilsBom`, and updated references to the new paths.
- PhilsBom: placed an unpacked `PhilsBom.bundle` copy inside `InDevelopment/PhilsBom` alongside the zip and install guide.

## 2026-01-28
- PhilsBom: removed the duplicate unpacked bundle from `InDevelopment/PhilsBom` so only the source bundle remains in the repo root.
- PhilsBom: main branch now ships only the versioned zip + install notes (no unpacked bundle).
- Docs: updated README/WORKTREE to match the single-bundle layout and main distribution-only structure.
