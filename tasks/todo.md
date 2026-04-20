# Bulk Replace Components Command

Date: 2026-03-30

## Plan
- [x] Back up files before edits
- [x] Add new toolbar command module for bulk component replacement
- [x] Register command in add-in startup/shutdown command lists
- [x] Add icon resources for the new command
- [x] Update README/CHANGELOG/DEVLOG notes
- [x] Run syntax checks

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/PhilsDesignTools.py.bak-20260330-111749`
  - `Addin/README.md.bak-20260330-111749`
  - `Addin/CHANGELOG.md.bak-20260330-111749`
  - `Addin/DEVLOG.md.bak-20260330-111749`
  - `tasks/todo.md.bak-20260330-111749`
- New command module:
  - `Addin/PhilsDesignTools/smg_bulk_replace_components.py`
- New toolbar command id:
  - `PhilsDesignTools_BulkReplaceComponents`
- New resources folder:
  - `Addin/PhilsDesignTools/resources/PhilsDesignTools_BulkReplaceComponents`
- Replacement source flow:
  - Uses Fusion cloud picker (`createCloudFileDialog`) + `Occurrence.replace(newFile, replaceAll)` for external designs (same model as the built-in replace workflow).
- Picker compatibility fix:
  - Removed `*.f3d/*.f3z` cloud dialog filter because it hid valid Fusion cloud items in some project folders.

# Remove Length Cleanup Command

Date: 2026-03-30

## Plan
- [x] Back up files before edits
- [x] Add a one-click toolbar command to remove `-####mm-` from existing names
- [x] Register command in add-in startup/shutdown
- [x] Add command icon resources
- [x] Update README/CHANGELOG/DEVLOG notes
- [x] Run syntax checks

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/PhilsDesignTools.py.bak-20260330-104221`
  - `Addin/README.md.bak-20260330-104221`
  - `Addin/CHANGELOG.md.bak-20260330-104221`
  - `Addin/DEVLOG.md.bak-20260330-104221`
  - `tasks/todo.md.bak-20260330-104221`
- New command module:
  - `Addin/PhilsDesignTools/smg_remove_length_names.py`
- New toolbar command id:
  - `PhilsDesignTools_RemoveLengthNames`
- New resources folder:
  - `Addin/PhilsDesignTools/resources/PhilsDesignTools_RemoveLengthNames`

# Component Name Length Removal

Date: 2026-03-30

## Plan
- [x] Inspect where generated names include length
- [x] Back up files before edits
- [x] Remove `-####mm-` segment from EA/SHS/RHS generated component names
- [x] Remove length segment from Batch Rename output names
- [x] Update command tooltip/docs/changelog/devlog
- [x] Run syntax checks

## Verification Notes
- Applicable code paths found:
  - `Addin/PhilsDesignTools/smg_core.py` (EA, SHS, RHS generation name builders)
  - `Addin/PhilsDesignTools/smg_rename.py` (Batch Rename new-name format builder)
- Created backups:
  - `Addin/PhilsDesignTools/smg_core.py.bak-20260330-095342`
  - `Addin/PhilsDesignTools/smg_rename.py.bak-20260330-095342`
  - `Addin/README.md.bak-20260330-095342`
  - `Addin/CHANGELOG.md.bak-20260330-095342`
  - `Addin/DEVLOG.md.bak-20260330-095342`
  - `tasks/todo.md.bak-20260330-095342`
- Naming format after change:
  - Generated: `EA1-50x50x3`, `SHS1-100x100x3`, `RHS1-100x50x5`
  - Batch Rename: `WP10-75x5` (no length segment)

# Multi Part File Export Upgrade

Date: 2026-03-30

## Plan
- [x] Back up files before edits
- [x] Rename IGES command UI text to Multi Part File Export
- [x] Add filetype dropdown to exporter command UI
- [x] Support multiple component export formats from one command
- [x] Keep robust handling for unavailable export APIs (clear user message instead of crash)
- [x] Run syntax checks
- [x] Update README/CHANGELOG/DEVLOG notes

## Verification Notes
- Created backups:
  - Addin/PhilsDesignTools/smg_iges_export.py.bak-20260330-092954
  - Addin/README.md.bak-20260330-092954
  - Addin/CHANGELOG.md.bak-20260330-092954
  - Addin/DEVLOG.md.bak-20260330-092954
  - tasks/todo.md.bak-20260330-092954
- Syntax check passed:
  - py -3 -m py_compile Addin/PhilsDesignTools/smg_iges_export.py
- Export command now exposes a filetype dropdown and resolves supported formats per Fusion build.
- Rhino 3DM selection is guarded with an explicit unsupported-API message when that API is not available.

# Stub Arms Export Selection Bug Fix

Date: 2026-03-24

## Plan
- [x] Inspect current selection + ordering logic in `smg_stub_arms_export.py`
- [x] Create timestamped backups for files to be edited
- [x] Fix mixed-selection bug so only stub-arm lines are exported
- [x] Prevent duplicate lines when native + occurrence contexts are both selected
- [x] Run syntax checks
- [x] Add verification notes

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/smg_stub_arms_export.py.bak-20260324-130652`
  - `Addin/CHANGELOG.md.bak-20260324-130652`
  - `Addin/DEVLOG.md.bak-20260324-130652`
- Syntax check passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_stub_arms_export.py`
- Code-path verification completed:
  - Selection collection now filters to stub-arm lines only.
  - Line dedupe now uses world-geometry keys to collapse native/occurrence duplicates.

## Release To Main
- [x] Back up any files updated for release metadata
- [x] Bump `PhilsDesignTools.manifest` version to `1.0.5`
- [x] Add release note to `Addin/VERSION_LOG.md`
- [x] Commit and push `feature/in-development`
- [x] Build `PhilsDesignTools-1.0.5.zip` release package
- [x] Update zip-only `main` branch with new package + README
- [x] Push `main`

### Release Verification Notes
- Feature branch pushed: `23ef5f4` on `origin/feature/in-development`
- Main branch pushed: `f006eb6` on `origin/main`
- Main package updated: `PhilsDesignTools-1.0.5.zip` (replaced `PhilsDesignTools-1.0.1.zip`)

## Generic Installer Package
- [x] Create generic installer scripts under `Addin/tools/installer`
- [x] Implement Fusion 360 installed-check and overwrite install behavior for both add-ins
- [x] Build distributable installer package zip for sharing
- [x] Dry-run verify installer logic against packaged payload

### Installer Verification Notes
- Build command:
  - `powershell -ExecutionPolicy Bypass -File Addin/tools/installer/build_installer_package.ps1`
- Generated package:
  - `Addin/tools/dist/fusion360-addins-installer-pdt-1.0.5-bom-1.03.zip`
- Dry run command:
  - `powershell -ExecutionPolicy Bypass -File Addin/tools/installer/_build/fusion360-addins-installer/install_fusion_addins.ps1 -PackageRoot Addin/tools/installer/_build/fusion360-addins-installer -DryRun`
- CMD launcher dry run:
  - `cmd /c "Addin\tools\installer\_build\fusion360-addins-installer\Install_Fusion_Addins.cmd --quiet -DryRun"`
- Hotfix:
  - Fixed `Illegal characters in path` from quoted trailing-backslash PackageRoot on some PCs.

# PhilsBom Duplicate Grouping Fix

Date: 2026-03-31

## Plan
- [x] Back up files before edits
- [x] Fix grouping keys so identical parts merge reliably
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `PhilsBom.bundle/Contents/_PhilsBom.py.bak-20260331-103830`
  - `tasks/todo.md.bak-20260331-103830`
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsBom.bundle\Contents\_PhilsBom.py.bak-20260331-103929`
- Grouping logic updated:
  - `Grouped By Component` now merges by component identity globally (no parent-path split).
  - `Grouped By Part Name` now compares cleaned names (`CleanFusionCompNameInserts`) so Fusion insert suffixes do not fragment quantities.
- Syntax check passed:
  - `py -3 -m py_compile PhilsBom.bundle/Contents/_PhilsBom.py`

# Remove Length From Body Names

Date: 2026-03-31

## Plan
- [x] Back up files before edits
- [x] Extend Remove Length From Names to also rename body names
- [x] Run syntax checks
- [x] Mirror updated command file to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/smg_remove_length_names.py.bak-20260331-132804`
  - `tasks/todo.md.bak-20260331-132804`
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_remove_length_names.py.bak-20260331-132846`
- Command behavior updated:
  - `Remove Length From Names` now strips `-####mm-` from body names in addition to components and occurrences.
  - Command summary and command log now include a `Bodies renamed` count.
- Syntax check passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_remove_length_names.py`

# Remove Length Targets UI

Date: 2026-03-31

## Plan
- [x] Back up files before edits
- [x] Add checkboxes for Components, Bodies, and Sketches
- [x] Apply rename pass only to selected target types
- [x] Run syntax checks
- [x] Mirror updated command file to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/smg_remove_length_names.py.bak-20260331-135045`
  - `tasks/todo.md.bak-20260331-135045`
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_remove_length_names.py.bak-20260331-135212`
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_remove_length_names.py.bak-20260331-135309`
- Command UI now includes three checkboxes:
  - `Components`
  - `Bodies`
  - `Sketches`
- Runtime behavior:
  - Renaming runs only for checked target types.
  - If none are checked, command shows a validation message and exits.
  - Summary and command log include only selected target counts.
- Syntax check passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_remove_length_names.py`

# PhilsBom Profile Split Option

Date: 2026-04-01

## Plan
- [x] Back up files before edits
- [x] Add BOM settings checkbox to split profile size from part name into Material
- [x] Apply split during export row generation (Part Name/Part Number + Material columns)
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `PhilsBom.bundle/Contents/_PhilsBom.py.bak-20260401-074740`
  - `tasks/todo.md.bak-20260401-074740`
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsBom.bundle\Contents\_PhilsBom.py.bak-20260401-075045`
- New setting:
  - `_splitProfileToMaterial` (default `False`)
  - UI label: `Split profile size into Material column`
- Export behavior when enabled:
  - `Part Name` / `Part Number` use the base token before the final profile suffix (for example `C13` from `C13-100x50x3`).
  - `Material` uses the parsed profile token when present (for example `100x50x3`).
  - Non-matching names keep current behavior unchanged.
- Syntax check passed:
  - `py -3 -m py_compile PhilsBom.bundle/Contents/_PhilsBom.py`

# EA Hole Export Summary Mode

Date: 2026-04-01

## Plan
- [x] Back up files before edits
- [x] Add export mode option (Detailed holes / Summary by member)
- [x] Add CSV/XLSX output choice
- [x] Implement summary rows: name, profile/material token, total length, standard-2-hole flag
- [x] Run syntax checks
- [x] Mirror updated command to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/smg_ea_hole_export.py.bak-20260401-082651`
  - `tasks/todo.md.bak-20260401-082651`
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_ea_hole_export.py.bak-20260401-082950`
- New UI options in EA Hole Export:
  - `Export Mode`: `Detailed (one row per hole)` or `Summary (one row per member)`
  - `File Type`: `XLSX (.xlsx)` or `CSV (.csv)` (default is XLSX)
- Summary mode output columns:
  - `PartName`
  - `Material/Profile`
  - `TotalLength_mm`
  - `Standard2Hole` (`Yes` / `No`)
- Name/profile split behavior:
  - Parses names like `C13-100x50x3` into `PartName=C13`, `Material/Profile=100x50x3`.
  - Falls back to body material when a profile token is not present in the name.
- Syntax check passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_ea_hole_export.py`

# PhilsBom Natural Sort

Date: 2026-04-01

## Plan
- [x] Add natural-sort helper for BOM row names (B1, B2, ... B10)
- [x] Apply natural sort to non-indented BOM methods before export
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in locations

## Verification Notes
- Added sort helpers:
  - `_natural_sort_key(text)` for mixed text/number ordering
  - `_bom_row_sort_key(item)` for stable row ordering
- Applied export ordering:
  - All non-indented BOM methods now sort naturally by name (then part number/material/path).
  - Indented BOM remains level-ordered as before.
- Syntax check passed:
  - `py -3 -m py_compile PhilsBom.bundle/Contents/_PhilsBom.py`
  - `py -3 -m py_compile` on active installed copies (API/AddIns, ApplicationPlugins, Autorun)
- Active copy backups:
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsBom.bundle\Contents\_PhilsBom.py.bak-20260401-083908`
  - `C:\Users\phil9\AppData\Roaming\Autodesk\ApplicationPlugins\PhilsBom.bundle\Contents\_PhilsBom.py.bak-20260401-083908`
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\MyScripts\Autorun\PhilsBom.bundle\Contents\_PhilsBom.py.bak-20260401-083908`

# Stub Arm Pair Angled Command

Date: 2026-04-01

## Plan
- [x] Back up files before edits
- [x] Add new single-pair stub arm command with world-ground-referenced top angle
- [x] Add optional top/bottom reference entity selectors (point/vertex/edge/line)
- [x] Register command in add-in startup/shutdown + toolbar
- [x] Add command icon resources
- [x] Run syntax checks
- [x] Mirror updated files to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/PhilsDesignTools.py.bak-20260401-140825`
  - `tasks/todo.md.bak-20260401-140825`
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\PhilsDesignTools.py.bak-20260401-141203`
- New command module:
  - `Addin/PhilsDesignTools/smg_stub_arm_pair.py`
- New toolbar command id:
  - `PhilsDesignTools_StubArmPair`
- New resources folder:
  - `Addin/PhilsDesignTools/resources/PhilsDesignTools_StubArmPair`
- Command capabilities:
  - Single-pair generation from one selected column and wall selection.
  - Top-line angle value referenced to world ground (XY plane).
  - Optional top reference selector accepting point/vertex/edge/line anchors.
  - Bottom line column attachment is now driven by a single distance from the top line attachment (no separate bottom anchor/offset mode).
  - Existing wall inset / clearance handling and bracket tagging reused from stub-arm core logic.
- Syntax checks passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_stub_arm_pair.py`
  - `py -3 -m py_compile Addin/PhilsDesignTools/PhilsDesignTools.py`

# Normalize Component Structure Command

Date: 2026-04-17

## Plan
- [x] Back up files before edits
- [x] Add a new command to normalize mixed/multi-body component structure
- [x] Treat linked child occurrences as child components for conversion checks
- [x] Add a body naming pass to match single direct body names to parent component names
- [x] Register the command in PhilsDesignTools panel startup/shutdown lists
- [x] Add command icon resources
- [x] Run syntax checks
- [x] Mirror updated files to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/PhilsDesignTools.py.bak-20260417-111441`
  - `tasks/todo.md.bak-20260417-111441`
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\PhilsDesignTools.py.bak-20260417-111733`
- New command module:
  - `Addin/PhilsDesignTools/smg_normalize_component_structure.py`
- New toolbar command id:
  - `PhilsDesignTools_NormalizeComponentStructure`
- New resources folder:
  - `Addin/PhilsDesignTools/resources/PhilsDesignTools_NormalizeComponentStructure`
- Command behavior:
  - Scans all components in the active design.
  - Flags a component for conversion when it has direct bodies and either direct child occurrences (including linked occurrences) or multiple direct bodies.
  - Converts each flagged direct body using `BRepBody.createComponent()` so bodies become child components.
  - Runs a second pass to rename every single direct body to match its parent component name.
  - Skips referenced component definitions for direct edits and reports conversion/rename errors in the summary.
- Syntax checks passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_normalize_component_structure.py`
  - `py -3 -m py_compile Addin/PhilsDesignTools/PhilsDesignTools.py`
  - `py -3 -m py_compile` on mirrored active files.

# Stub Arms DXF Export Command

Date: 2026-04-17

## Plan
- [x] Back up files before edits
- [x] Confirm current stub-arm sketch/export behavior and DXF gap
- [x] Add a new command to export selected stub arm lines to DXF geometry
- [x] Register the command in PhilsDesignTools panel startup/shutdown lists
- [x] Add command icon resources
- [x] Update README/CHANGELOG/DEVLOG notes
- [x] Run syntax checks
- [x] Mirror updated files to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/PhilsDesignTools.py.bak-20260417-144215`
  - `Addin/README.md.bak-20260417-144216`
  - `Addin/CHANGELOG.md.bak-20260417-144216`
  - `Addin/DEVLOG.md.bak-20260417-144216`
  - `tasks/todo.md.bak-20260417-144216`
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\PhilsDesignTools.py.bak-20260417-144455`
- DXF export gap confirmed:
  - Stub arm geometry already exists as sketch lines, but the add-in only had quantity/data export and no direct DXF line export command.
  - Fusion can save a sketch as DXF manually, but that is per-sketch and does not provide a one-click export for selected stub arm lines across the model.
- New command module:
  - `Addin/PhilsDesignTools/smg_stub_arms_export_dxf.py`
- New toolbar command id:
  - `PhilsDesignTools_StubArms_Export_DXF`
- New resources folder:
  - `Addin/PhilsDesignTools/resources/PhilsDesignTools_StubArms_Export_DXF`
- Command behavior:
  - Reuses the existing stub-arm selection/filter logic so only real stub arm lines are exported.
  - Accepts selected stub arm lines, sketches, occurrences, or components.
  - Writes a DXF containing `LINE` entities in model/world coordinates with mm units.
  - Groups exported lines onto generated DXF layers using stub arm metadata when available.
- Syntax checks passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_stub_arms_export_dxf.py`
  - `py -3 -m py_compile Addin/PhilsDesignTools/PhilsDesignTools.py`
  - `py -3 -m py_compile` on mirrored active files.
- Rhino compatibility hardening:
  - Updated DXF writer to emit a Rhino-friendlier ASCII R12 (`AC1009`) DXF instead of a minimal `AC1015` file structure.

# Normalize Component Naming Follow-up

Date: 2026-04-20

## Plan
- [x] Back up files before edits
- [x] Confirm why converted normalize child components can end up named `Body1`/`Body2`
- [x] Update normalize naming so converted components avoid generic body names
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/smg_normalize_component_structure.py.bak-20260420-092318`
  - `tasks/todo.md.bak-20260420-092318`
- Naming fix:
  - Generic direct body names (`Body`, `Body1`, `Body2`, etc.) no longer become the new child component names during conversion.
  - Converted child components now use a parent-based fallback name such as `<Parent> Body` or `<Parent> Body 2`.
- Syntax checks passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_normalize_component_structure.py`
  - `py -3 -m py_compile` on the mirrored active add-in file.

# Set Component Descriptions Command

Date: 2026-04-20

## Plan
- [x] Back up files before edits
- [x] Inspect current naming patterns and decide the first-pass description format rules
- [x] Add a new command to write component descriptions from recognised profile names
- [x] Register the command in PhilsDesignTools panel startup/shutdown lists
- [x] Add command icon resources
- [x] Update README/CHANGELOG/DEVLOG notes
- [x] Run syntax checks
- [x] Mirror updated files to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/PhilsDesignTools.py.bak-20260420-101231`
  - `Addin/README.md.bak-20260420-101231`
  - `Addin/CHANGELOG.md.bak-20260420-101231`
  - `Addin/DEVLOG.md.bak-20260420-101231`
  - `tasks/todo.md.bak-20260420-101231`
- Mirrored active add-in backups:
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\PhilsDesignTools.py.bak-20260420-101735`
- New command module:
  - `Addin/PhilsDesignTools/smg_set_component_descriptions.py`
- New toolbar command id:
  - `PhilsDesignTools_SetComponentDescriptions`
- New resources folder:
  - `Addin/PhilsDesignTools/resources/PhilsDesignTools_SetComponentDescriptions`
- First-pass supported families:
  - `SHS`, `RHS`, `CHS`, `EA`, `FLAT BAR`, `PLATE`
- Description output rules:
  - Hollow sections -> `AS/NZS 1163 C350L0`
  - Merchant bar / angles / flat bar -> `AS/NZS 3679.1 Grade 300`
  - Plate -> `AS/NZS 3678 Grade 250`
- Parser spot checks passed:
  - `SHS1-100x100x3` -> `SHS 100 x 100 x 3 AS/NZS 1163 C350L0`
  - `RHS1-100x50x3` -> `RHS 100 x 50 x 3 AS/NZS 1163 C350L0`
  - `EA1-50x50x3` -> `EA 50 x 50 x 3 AS/NZS 3679.1 Grade 300`
  - `BRB1 - 100x3 SHS` -> `SHS 100 x 100 x 3 AS/NZS 1163 C350L0`
  - `BR1 - 50x3 EA` -> `EA 50 x 50 x 3 AS/NZS 3679.1 Grade 300`
  - `FB1-65x10` -> `FLAT BAR 65 x 10 AS/NZS 3679.1 Grade 300`
  - `PL-10` -> `PLATE 10 AS/NZS 3678 Grade 250`
- Syntax checks passed:
  - `py_compile` on repo files:
    - `Addin/PhilsDesignTools/smg_set_component_descriptions.py`
    - `Addin/PhilsDesignTools/PhilsDesignTools.py`
  - `py_compile` on mirrored active add-in files:
    - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py`
    - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\PhilsDesignTools.py`
- Mirror verification:
  - Repo and active installed copies of `smg_set_component_descriptions.py` match by SHA-256.
  - Repo and active installed copies of `PhilsDesignTools.py` match by SHA-256.

# Set Component Descriptions Leaf-Only Filter

Date: 2026-04-20

## Plan
- [x] Back up files before edits
- [x] Restrict description writes to leaf fabrication components only
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/smg_set_component_descriptions.py.bak-20260420-102637`
  - `tasks/todo.md.bak-20260420-102637`
- Leaf-only rule:
  - The command now only attempts to write descriptions when a component has exactly one direct body and zero child occurrences.
  - Assembly components, empty components, and multi-body container components are skipped before profile parsing.
- Command summary update:
  - Added `Non-leaf skipped` count so skipped assembly components are visible in the result dialog.
- Spot check passed:
  - `(1 body, 0 children)` -> included
  - `(1 body, 2 children)` -> skipped
  - `(2 bodies, 0 children)` -> skipped
  - `(0 bodies, 0 children)` -> skipped
- Syntax check passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_set_component_descriptions.py`
- Mirror verification:
  - Active add-in backup created: `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py.bak-20260420-102835`
  - Repo and active installed copies of `smg_set_component_descriptions.py` match by SHA-256.
  - `py_compile` passed on the mirrored active add-in file.

# Set Component Descriptions Geometry Fallback

Date: 2026-04-20

## Plan
- [x] Back up files before edits
- [x] Add body-geometry fallback when profile family cannot be resolved from names
- [x] Update command notes/docs for the new fallback behavior
- [x] Run syntax checks
- [x] Mirror updated files to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/smg_set_component_descriptions.py.bak-20260420-105428`
  - `tasks/todo.md.bak-20260420-105428`
- Geometry fallback behavior:
  - The command still prefers recognised profile names first.
  - If no supported family token is present, it now inspects the actual single-body leaf component geometry.
  - Hollow rectangular sections are inferred from side-face plane offsets and end-face loops.
  - Equal angles are inferred from stepped side-face plane offsets.
  - Solid rectangular sections fall back to flat-bar vs plate heuristics.
- Pure helper spot checks passed:
  - Hollow levels `[-50,-47,47,50] / [-50,-47,47,50]` -> `SHS 100 x 100 x 3 AS/NZS 1163 C350L0`
  - Hollow levels `[-50,-47,47,50] / [-25,-22,22,25]` -> `RHS 100 x 50 x 3 AS/NZS 1163 C350L0`
  - Angle levels `[0,3,100] / [0,3,100]` -> `EA 100 x 100 x 3 AS/NZS 3679.1 Grade 300`
  - Solid rectangle `100 x 3`, long length -> `FLAT BAR 100 x 3 AS/NZS 3679.1 Grade 300`
  - Solid rectangle `100 x 10`, short length -> `PLATE 10 AS/NZS 3678 Grade 250`
- Syntax check passed:
  - `py_compile` on repo file:
    - `Addin/PhilsDesignTools/smg_set_component_descriptions.py`
  - `py_compile` on mirrored active add-in file:
    - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py`
- Mirror verification:
  - Active add-in backup created: `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py.bak-20260420-105644`
  - Repo and active installed copies of `smg_set_component_descriptions.py` match by SHA-256.

# Set Component Descriptions Material Name Sync

Date: 2026-04-20

## Plan
- [x] Update the command to assign simplified material names from recognised profile families
- [x] Update docs/notes for the material-name behavior
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- Material mapping added:
  - `SHS ...` -> `Steel - SHS`
  - `RHS ...` -> `Steel - RHS`
  - `CHS ...` -> `Steel - CHS`
  - `EA ...` -> `Steel - EA`
  - `FLAT BAR ...` -> `Steel - Flat Bar`
  - `PLATE ...` -> `Steel - Plate`
- Material assignment behavior:
  - Reuses an existing design material with the target name when present.
  - Otherwise copies the current/body steel material into the design with the simplified name and assigns it to the leaf body.
- Helper spot checks passed:
  - `SHS 100 x 100 x 3 AS/NZS 1163 C350L0` -> `Steel - SHS`
  - `RHS 100 x 50 x 3 AS/NZS 1163 C350L0` -> `Steel - RHS`
  - `CHS 48.3 x 3.2 AS/NZS 1163 C350L0` -> `Steel - CHS`
  - `EA 100 x 100 x 3 AS/NZS 3679.1 Grade 300` -> `Steel - EA`
  - `FLAT BAR 65 x 10 AS/NZS 3679.1 Grade 300` -> `Steel - Flat Bar`
  - `PLATE 10 AS/NZS 3678 Grade 250` -> `Steel - Plate`
- Syntax checks passed:
  - `py_compile` on repo file:
    - `Addin/PhilsDesignTools/smg_set_component_descriptions.py`
  - `py_compile` on mirrored active add-in file:
    - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py`
- Mirror verification:
  - Active add-in backup created: `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py.bak-20260420-113852`
  - Repo and active installed copies of `smg_set_component_descriptions.py` match by SHA-256.

# Set Component Descriptions Plate Geometry Only

Date: 2026-04-20

## Plan
- [x] Back up files before edits
- [x] Remove remaining plate naming shortcuts from description inference
- [x] Update notes/docs for geometry-only plate resolution
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/smg_set_component_descriptions.py.bak-20260420-114929`
  - `tasks/todo.md.bak-20260420-114929`
- Plate inference changes:
  - Removed `PLATE` / `PL` text parsing from `_description_from_text`.
  - Removed the `PLATE` name hint shortcut from solid-rectangle geometry inference.
  - Plate descriptions now come from the actual body profile only.
- Spot checks passed:
  - `PL-10` -> `None` from name parsing
  - `10 Plate` -> `None` from name parsing
  - Solid rectangle `100 x 10`, short length -> `PLATE 10 AS/NZS 3678 Grade 250`
- Syntax checks passed:
  - `py_compile` on repo file:
    - `Addin/PhilsDesignTools/smg_set_component_descriptions.py`
  - `py_compile` on mirrored active add-in file:
    - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py`
- Mirror verification:
  - Active add-in backup created: `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py.bak-20260420-115034`
  - Repo and active installed copies of `smg_set_component_descriptions.py` match by SHA-256.

# Set Component Descriptions Geometry Only

Date: 2026-04-20

## Plan
- [x] Back up files before edits
- [x] Remove the remaining name-driven profile inference for all supported families
- [x] Update notes/docs for geometry-only recognition
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/smg_set_component_descriptions.py.bak-20260420-125703`
  - `tasks/todo.md.bak-20260420-125703`
- Geometry-only recognition changes:
  - `Set Component Descriptions` now builds descriptions from the actual body shape for all supported profile families.
  - Component/body names are no longer used to infer `SHS`, `RHS`, `CHS`, `EA`, `FLAT BAR`, or `PLATE`.
  - Flat bar vs plate now depends only on the solid-body geometry heuristic.
- Spot checks passed:
  - `SHS1-100x100x3` -> `None` from name parsing
  - `RHS1-100x50x3` -> `None` from name parsing
  - `EA1-50x50x3` -> `None` from name parsing
  - `FB1-65x10` -> `None` from name parsing
  - `PL-10` -> `None` from name parsing
  - Solid rectangle `100 x 3`, long length -> `FLAT BAR 100 x 3 AS/NZS 3679.1 Grade 300`
  - Solid rectangle `100 x 10`, short length -> `PLATE 10 AS/NZS 3678 Grade 250`
- Syntax checks passed:
  - `py_compile` on repo file:
    - `Addin/PhilsDesignTools/smg_set_component_descriptions.py`
  - `py_compile` on mirrored active add-in file:
    - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py`
- Mirror verification:
  - Active add-in backup created: `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py.bak-20260420-125850`
  - Repo and active installed copies of `smg_set_component_descriptions.py` match by SHA-256.

# Set Component Descriptions Hollow Sizing Robustness

Date: 2026-04-20

## Plan
- [x] Back up files before edits
- [x] Replace brittle hollow-section sizing with a more robust geometry measurement path
- [x] Update notes/docs for the new sizing approach
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- Created backups:
  - `Addin/PhilsDesignTools/smg_set_component_descriptions.py.bak-20260420-125703`
  - `tasks/todo.md.bak-20260420-125703`
- Sizing fix:
  - Replaced SHS/RHS sizing based on side-face plane origins with end-face loop measurement.
  - Outer and inner loop bounds are now used to derive hollow-section outer size and wall thickness.
  - This avoids false thin-wall reads caused by arbitrary planar face origins.
- Helper spot checks passed:
  - Hollow levels `[0,8,92,100] / [0,8,92,100]` -> `SHS 100 x 100 x 8 AS/NZS 1163 C350L0`
  - Hollow levels `[0,8,92,100] / [0,8,42,50]` -> `RHS 100 x 50 x 8 AS/NZS 1163 C350L0`
  - Angle levels `[0,8,100] / [0,8,100]` -> `EA 100 x 100 x 8 AS/NZS 3679.1 Grade 300`
  - Solid rectangle `100 x 8`, long length -> `FLAT BAR 100 x 8 AS/NZS 3679.1 Grade 300`
  - Solid rectangle `100 x 8`, short length -> `PLATE 8 AS/NZS 3678 Grade 250`
- Syntax checks passed:
  - `py_compile` on repo file:
    - `Addin/PhilsDesignTools/smg_set_component_descriptions.py`
  - `py_compile` on mirrored active add-in file:
    - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py`
- Mirror verification:
  - Active add-in backup created: `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py.bak-20260420-130843`
  - Repo and active installed copies of `smg_set_component_descriptions.py` match by SHA-256.

# Set Component Descriptions CHS False Positive Fix

Date: 2026-04-20

## Plan
- [x] Fix CHS false positives caused by SHS/RHS cylindrical corner faces
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- Root cause:
  - Geometry-only recognition still checked for CHS before trying the end-face prismatic profile.
  - SHS/RHS corner fillet cylinders could therefore be misclassified as `CHS`.
- Fix applied:
  - `Set Component Descriptions` now tries end-face prismatic profile recognition first.
  - CHS fallback only runs when no usable prismatic end-face profile is found.
- Syntax checks passed:
  - `py_compile` on repo file:
    - `Addin/PhilsDesignTools/smg_set_component_descriptions.py`
  - `py_compile` on mirrored active add-in file:
    - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py`
- Mirror verification:
  - Active add-in backup created: `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py.bak-20260420-131752`
  - Repo and active installed copies of `smg_set_component_descriptions.py` match by SHA-256.

# Set Component Descriptions Flat Bar vs Plate Heuristic

Date: 2026-04-20

## Plan
- [x] Adjust solid-part stock classification so irregular small parts prefer plate over flat bar
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- Heuristic change:
  - Flat bar is now only assigned when the largest broad planar stock face has a simple rectangular outer loop.
  - Irregular cut tabs/brackets are treated as plate stock instead of flat bar.
- Syntax checks passed:
  - `py_compile` on repo file:
    - `Addin/PhilsDesignTools/smg_set_component_descriptions.py`
  - `py_compile` on mirrored active add-in file:
    - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py`
- Mirror verification:
  - Active add-in backup created: `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py.bak-20260420-135531`
  - Repo and active installed copies of `smg_set_component_descriptions.py` match by SHA-256.
