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

