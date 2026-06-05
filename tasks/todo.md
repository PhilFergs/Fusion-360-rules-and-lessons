# Installer Refresh For 1.0.13

Date: 2026-06-05

## Plan
- [x] Confirm current PhilsDesignTools manifest version and installer build workflow
- [x] Bump PhilsDesignTools version metadata for a fresh release package
- [x] Add release notes for Hole Cut, profile-name toggles, generated descriptions, and Fusion API hardening
- [x] Build fresh installer and standalone package artifacts
- [x] Run syntax/package verification
- [x] Commit and push the updated source plus artifacts on `feature/in-development`

## Verification Notes
- `gh` is not installed on this machine, so GitHub CLI auth/PR checks are unavailable; release will use normal `git` commit/push.
- Syntax sweep passed:
  - `py -3 -m py_compile` over all tracked `Addin/PhilsDesignTools/*.py`
- Build outputs confirmed:
  - `Addin/tools/dist/fusion360-addins-installer-pdt-1.0.13-bom-1.03.zip`
  - `Addin/tools/dist/fusion360-addins-installer-pdt-1.0.13-bom-1.03.msi`
  - `Addin/tools/dist/PhilsDesignTools-1.0.13.zip`

# Generated Member Descriptions

Date: 2026-06-05

## Plan
- [x] Inspect Set Component Descriptions output format for EA/SHS/RHS
- [x] Back up generator core and task notes before edits
- [x] Set generated EA/SHS/RHS component descriptions at creation
- [x] Run syntax checks
- [x] Mirror updated core file into the active Fusion add-in folder

## Verification Notes
- Target description format matches Set Component Descriptions: `EA 50 x 50 x 3`, `SHS 100 x 100 x 3`, `RHS 100 x 50 x 3`.
- Repo syntax check passed:
  - `py -3 -m py_compile Addin\PhilsDesignTools\smg_core.py Addin\PhilsDesignTools\smg_ea.py Addin\PhilsDesignTools\smg_shs.py Addin\PhilsDesignTools\smg_rhs.py`
- Active installed syntax check passed:
  - `py -3 -m py_compile` on active `smg_core.py`
- Repo and active installed `smg_core.py` match by SHA-256:
  - `42CB36E89B2F223E12066899BBA43BD05CB41F552FCAD3AFA3B8E6FEB43A6D33`

# From Lines Profile Name Toggle

Date: 2026-06-05

## Plan
- [x] Inspect EA/SHS/RHS command inputs and generated name builders
- [x] Back up generator files and task notes before edits
- [x] Add default-off profile-in-name toggles to EA/SHS/RHS From Lines
- [x] Update core name generation to omit profile suffix by default
- [x] Run syntax checks
- [x] Mirror updated command files into the active Fusion add-in folder

## Verification Notes
- Target behavior: default names `EA186`, `SHS186`, `RHS186`; checkbox restores names like `EA186-50x50x3`.
- Repo syntax check passed:
  - `py -3 -m py_compile Addin\PhilsDesignTools\smg_core.py Addin\PhilsDesignTools\smg_ea.py Addin\PhilsDesignTools\smg_shs.py Addin\PhilsDesignTools\smg_rhs.py`
- Active installed syntax check passed on the same four files.
- Repo and active installed copies match by SHA-256:
  - `smg_core.py`: `87484487146CD42849B022878ED1F64DF2B40169B375B864E71B35C002EF6737`
  - `smg_ea.py`: `364605C54725F8360572EFDDCB4C831C96FA21B614FC8C8BDB2DAC7FF92F8CD0`
  - `smg_shs.py`: `45B8DEFC49C0A00C40C35777466D278D435584ABB652A18A69455EB9EBE60FDF`
  - `smg_rhs.py`: `8E110C7CB1C93D037BB68F699C05F1153501617CB17CD21B7A85552949619E13`

# Hole Cut From Face Root Sketch Fallback

Date: 2026-06-05

## Plan
- [x] Inspect active Fusion log after origin-plane proxy fallback
- [x] Back up Hole Cut From Face and task notes before edits
- [x] Add root-component sketch/extrude fallback using the selected occurrence-context body
- [x] Run syntax checks
- [x] Mirror updated command into the active Fusion add-in folder

## Verification Notes
- Active log showed even the origin-plane proxy route failed with `InternalValidationError : targetComp`, so the fallback now avoids target-component sketch creation entirely.
- Repo syntax check passed:
  - `py -3 -m py_compile Addin\PhilsDesignTools\smg_holecut.py`
- Active installed syntax check passed:
  - `py -3 -m py_compile` on active `smg_holecut.py`
- Repo and active installed copies match by SHA-256:
  - `8C450F99D223F44D832484CF7E11D57FDD87A5A8DADE8C3EF92FBE1FE3BD6F32`

# Hole Cut From Face Origin Plane Proxy Fallback

Date: 2026-06-05

## Plan
- [x] Inspect active Fusion log for the continued nested sketch path failure
- [x] Back up Hole Cut From Face and task notes before edits
- [x] Try occurrence-context proxies for built-in origin-plane sketch fallback
- [x] Run syntax checks
- [x] Mirror updated command into the active Fusion add-in folder

## Verification Notes
- Active log showed native face, face proxy, and native origin-plane sketch creation all failed in the nested target path with `targetComp` / `failed to get path to component`.
- Repo syntax check passed:
  - `py -3 -m py_compile Addin\PhilsDesignTools\smg_holecut.py`
- Active installed syntax check passed:
  - `py -3 -m py_compile` on active `smg_holecut.py`
- Repo and active installed copies match by SHA-256:
  - `6CC168EBFC2239A9F9CB1FF3B02CB06F1EB332002659C4C33FD7A01438716328`

# Hole Cut From Face Fusion Object Truthiness Fix

Date: 2026-06-05

## Plan
- [x] Inspect active Fusion log for the continued skipped hole case
- [x] Back up Hole Cut From Face and task notes before edits
- [x] Replace sketch fallback truthiness checks with explicit `is not None`
- [x] Run syntax checks
- [x] Mirror updated command into the active Fusion add-in folder

## Verification Notes
- Active log showed the standard origin-plane fallback was selected, then the command continued to construction-plane fallback without any standard-plane sketch failure log. This indicates a valid Fusion API object or sketch may have evaluated false in Python.
- Repo syntax check passed:
  - `py -3 -m py_compile Addin\PhilsDesignTools\smg_holecut.py`
- Active installed syntax check passed:
  - `py -3 -m py_compile` on active `smg_holecut.py`
- Repo and active installed copies match by SHA-256:
  - `350AC429169F6579B28F598753065F0C2DF6817B01F6F6693ADBEF63501F55AE`

# Hole Cut From Face Origin Plane Fallback

Date: 2026-06-05

## Plan
- [x] Inspect active Fusion log for the skipped hole case
- [x] Back up Hole Cut From Face and task notes before edits
- [x] Add a built-in origin-plane sketch fallback for axis-aligned nested cuts
- [x] Run syntax checks
- [x] Mirror updated command into the active Fusion add-in folder

## Verification Notes
- Active log showed nested target face sketch creation fell through to construction-plane creation, then `ConstructionPlanes.add` failed with Fusion internal validation errors.
- Repo syntax check passed:
  - `py -3 -m py_compile Addin\PhilsDesignTools\smg_holecut.py`
- Active installed syntax check passed:
  - `py -3 -m py_compile` on active `smg_holecut.py`
- Repo and active installed copies match by SHA-256:
  - `6084F80A629E4FBAE16EDF5887AE969A1FE8D168F6FCBFECA003A19F9A20357B`

# Fusion Update Fragility Audit

Date: 2026-06-05

## Plan
- [x] Run syntax sweep across all PhilsDesignTools Python modules
- [x] Search for high-risk Fusion API patterns: direct component renames, nested face sketch creation, `addWithoutEdges`, `moveToComponent`, native/proxy context use, and deprecated angle-unit access
- [x] Harden low-risk direct rename paths in member generation and cleanup tools
- [x] Harden remaining stub-arm face sketch path
- [x] Mirror audited command files into active Fusion add-in folder
- [x] Run live syntax/hash verification

## Verification Notes
- Backups created with stamp `20260605-102847`.
- Initial full syntax sweep passed:
  - `py -3 -m py_compile` over all tracked `Addin/PhilsDesignTools/*.py`
- Preventative hardening applied:
  - EA/SHS/RHS generators now name the occurrence first and component definition second.
  - New Component Set now names occurrence/component through a guarded helper and reports naming issues without crashing.
  - Remove Length From Names now renames matching occurrences plus component definitions through guarded native/object routes.
  - Stub Arms To Wall now finds the `Stub arm lines` container by occurrence or component name and names new containers through guarded occurrence/component routes.
  - Stub Arms To Wall wall-centre sketch creation now tries a plane reference before direct face sketch fallback.
- Active add-in backups created with stamp `20260605-103216` for:
  - `smg_rename.py`
  - `smg_holecut.py`
  - `smg_component_set.py`
  - `smg_core.py`
  - `smg_remove_length_names.py`
  - `smg_stub_arms.py`
- Final verification passed:
  - Full repo `py_compile` sweep over all tracked `Addin/PhilsDesignTools/*.py`
  - Live `py_compile` over the six deployed files
  - All six deployed files match repo copies by SHA-256.

# Hole Cut From Face Nested Face Sketch Fix

Date: 2026-06-05

## Plan
- [x] Back up Hole Cut From Face and notes before edits
- [x] Add guarded face/proxy sketch creation
- [x] Add construction-plane sketch fallback for Fusion face path failures
- [x] Run syntax checks
- [x] Mirror updated command into the active Fusion add-in folder

## Verification Notes
- Backups created with stamp `20260605-101742`.
- Initial syntax check passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_holecut.py`
- Final syntax checks passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_holecut.py Addin/PhilsDesignTools/PhilsDesignTools.py`
  - `py -3 -m py_compile` on the active installed `smg_holecut.py`
- Active add-in backup created:
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_holecut.py.bak-20260605-101951`
- Repo and active installed copies of `smg_holecut.py` match by SHA-256.

# Batch Rename Component Asset Rename Fix

Date: 2026-06-05

## Plan
- [x] Back up Batch Rename and task notes before edits
- [x] Replace direct rename fallback with guarded native occurrence/component rename helpers
- [x] Update conflict-overwrite rename routes to use the same guarded helpers
- [x] Run syntax checks
- [x] Mirror updated command into the active Fusion add-in folder

## Verification Notes
- Backups created:
  - `Addin/PhilsDesignTools/smg_rename.py.bak-20260605-101103`
  - `tasks/todo.md.bak-20260605-101103`
  - Documentation backups with stamp `20260605-101300`
- Initial syntax check passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_rename.py`
- Final syntax checks passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_rename.py Addin/PhilsDesignTools/PhilsDesignTools.py`
  - `py -3 -m py_compile` on the active installed `smg_rename.py`
- Active add-in backup created:
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_rename.py.bak-20260605-101357`
- Repo and active installed copies of `smg_rename.py` match by SHA-256.

# Stub Arms Angle Regression Isolation

Date: 2026-05-11

## Plan
- [x] Compare the current generator with the pre-top-angle deployment backup.
- [x] Roll back `smg_stub_arms.py` to the pre-top-angle implementation for a clean live A/B test.
- [x] Run syntax checks and deploy the rollback to the active Fusion add-in folder.

## Verification Notes
- The `20260511_082100` live backup did not contain `Top line angle`; current generator code was reverted to match that pre-change behavior.
- `python -m py_compile Addin\PhilsDesignTools\smg_stub_arms.py` passed after rollback.

# Stub Arms Shared Top Angle

Date: 2026-05-11

## Plan
- [x] Re-add `Top line angle` from the known-good rollback version only.
- [x] Keep the current shared wall endpoint behavior when the angle is `0 deg`.
- [x] Run syntax checks and deploy to the active Fusion add-in folder.

## Verification Notes
- The new setting adjusts the shared wall endpoint for both FlatBar and EA lines, rather than creating a separate lower endpoint.
- `0 deg` returns before changing the hit point, preserving the current generated geometry.
- `python -m py_compile Addin\PhilsDesignTools\smg_stub_arms.py` passed.
- Deployed with `Addin\tools\deploy_addin.ps1`; installed file contains `stub_top_line_angle` and no `stub_min_pair_angle`.
- Follow-up fix: changed the top-angle adjustment from same-face point sliding to a fresh angled ray/wall intersection so non-zero angles visibly change the generated endpoint.
- Follow-up fix 2: if the angled ray misses the trimmed wall face, the endpoint is now directly shifted by `tan(angle) * run` and projected to the wall plane instead of falling back unchanged.
- Follow-up fix 3: Fusion stores angle input values in radians; `Top line angle` now converts `v.value` with `math.degrees`, so an input of `20` parses as `20 deg` instead of `0.35 deg`.

# Stub Arm Pair Angle Parsing

Date: 2026-05-12

## Plan
- [x] Apply the same Fusion angle parsing fix to `Stub Arm Pair To Wall`.
- [x] Run syntax checks and deploy to the active Fusion add-in folder.

## Verification Notes
- The single-pair top angle now converts Fusion's internal radian value with `math.degrees(v.value)`, matching the bulk Stub Arms To Wall fix.
- `python -m py_compile Addin\PhilsDesignTools\smg_stub_arm_pair.py Addin\PhilsDesignTools\smg_stub_arms.py` passed.
- Deployed with `Addin\tools\deploy_addin.ps1`; installed `smg_stub_arm_pair.py` now uses `math.degrees(float(v.value))`.

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

# Set Component Descriptions C Purlin Recognition

Date: 2026-04-20

## Plan
- [x] Add a channel-like geometry path ahead of EA detection for cold-formed `C` sections
- [x] Update add-in notes for the broader profile coverage
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- Root cause:
  - The prior `EA` geometry path accepted any open thin-walled profile with three-or-more level bands on both axes.
  - That allowed channel-like `C100` purlins to fall through as equal angle.
- Fix applied:
  - Added a `C PURLIN` geometry path before EA classification.
  - Tightened EA recognition so profiles with channel-like extra level bands do not get treated as angle.
  - Added simplified material mapping for `C PURLIN` -> `Steel - C Purlin`.
- Syntax checks passed:
  - `py_compile` on repo file:
    - `Addin/PhilsDesignTools/smg_set_component_descriptions.py`
  - `py_compile` on mirrored active add-in file:
    - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py`
- Mirror verification:
  - Active add-in backup created: `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py.bak-20260420-143739`
  - Repo and active installed copies of `smg_set_component_descriptions.py` match by SHA-256.

# Set Component Descriptions UB And PFC Recognition

Date: 2026-04-20

## Plan
- [x] Add explicit geometry recognition for hot-rolled `UB` and `PFC` profiles
- [x] Keep `UB`/`PFC` detection ahead of the broader open-section fallbacks
- [x] Update notes for the new profile coverage
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- New profile coverage:
  - Added `UB depth x width x web x flange AS/NZS 3679.1 Grade 300` recognition from symmetric I-section end profiles.
  - Added `PFC depth x width x web x flange AS/NZS 3679.1 Grade 300` recognition from channel end profiles.
  - Added simplified material mappings `Steel - UB` and `Steel - PFC`.
- Syntax checks passed:
  - `py_compile` on repo file:
    - `Addin/PhilsDesignTools/smg_set_component_descriptions.py`
  - `py_compile` on mirrored active add-in file:
    - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py`
- Mirror verification:
  - Active add-in backup created: `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py.bak-20260420-144130`
  - Repo and active installed copies of `smg_set_component_descriptions.py` match by SHA-256.

# Set Component Descriptions C Purlin Tightening

Date: 2026-04-20

## Plan
- [x] Tighten `C PURLIN` recognition so equal angles do not fall through as purlins
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- Root cause:
  - The `C PURLIN` path still accepted some plain open L-sections when hole/fillet detail increased the detected end-profile edge count.
- Fix applied:
  - `C PURLIN` now requires a real lip signature in the major-axis level bands.
  - Plain open sections without a detected lip fall back to `EA`/other profile checks instead of being labelled as purlins.
- Follow-up tightening:
  - `C PURLIN` now also requires a channel-like level pattern of `depth >= 4 bands` and `width == 3 bands`, plus a clear depth-vs-flange difference.
  - `EA` recognition now tolerates extra section bands introduced by fillets, so equal angles like `40 x 40 x 3` no longer fall through when their inner radii create extra projection levels.
- Syntax checks passed:
  - `py_compile` on repo file:
    - `Addin/PhilsDesignTools/smg_set_component_descriptions.py`
  - `py_compile` on mirrored active add-in file:
    - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py`
- Mirror verification:
  - Active add-in backup created: `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py.bak-20260420-155745`
  - Repo and active installed copies of `smg_set_component_descriptions.py` match by SHA-256.
# Set Component Descriptions - Strip Standards

Date: 2026-04-27

## Plan
- [x] Back up target script before edit
- [x] Remove standards/grade suffix from generated profile descriptions for all profile families
- [x] Run syntax checks
- [x] Mirror updated script to active Fusion add-in folder

## Verification Notes
- Created backup:
  - `Addin/PhilsDesignTools/smg_set_component_descriptions.py.bak-20260427-135231`
  - `tasks/todo.md.bak-20260427-140348`
  - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_set_component_descriptions.py.bak-20260427-140124`
- Updated output format examples:
  - `EA 50 x 50 x 3` (instead of including AS/NZS + Grade text)
  - Same profile-only format now applied to SHS/RHS/CHS/UB/PFC/FLAT BAR/PLATE.
- Syntax checks passed:
  - `py -3 -m py_compile Addin/PhilsDesignTools/smg_set_component_descriptions.py`
  - `py -3 -m py_compile` on mirrored active file.
# Installer Hardening (MSI Wrapper)

Date: 2026-04-28

## Plan
- [x] Add MSI build path to installer packaging workflow
- [x] Keep existing ZIP package path as fallback
- [x] Use local portable WiX extraction (no machine-wide install required)
- [x] Build MSI that runs packaged install script automatically
- [x] Document MSI/signing workflow in installer README
- [x] Build and verify updated artifacts in dist

## Verification Notes
- Backups created:
  - `Addin/tools/installer/build_installer_package.ps1.bak-20260428-220052`
  - `Addin/tools/installer/README.md.bak-20260428-220052`
  - `tasks/todo.md.bak-20260428-220605`
- Updated files:
  - `Addin/tools/installer/build_installer_package.ps1`
  - `Addin/tools/installer/README.md`
- Build output confirmed:
  - `fusion360-addins-installer-pdt-1.0.8-bom-1.03.zip`
  - `fusion360-addins-installer-pdt-1.0.8-bom-1.03.msi`
- WiX CLI handling:
  - Portable WiX 7 CLI is downloaded/extracted automatically into `%LOCALAPPDATA%\FusionInstallerTools\wix-cli-7`.
  - Build auto-accepts WiX `wix7` EULA for CI/scripted usage.

# Stub Arms Max Pair Angle

Date: 2026-04-29

## Plan
- [x] Back up `smg_stub_arms.py` before edits
- [x] Add a user-adjustable max pair angle input to the Stub Arms To Wall command
- [x] Keep the current upper-line hit generation unchanged
- [x] Limit only the lower line by sliding its member-side endpoint along the member axis when needed
- [x] Update add-in notes
- [x] Run syntax checks
- [x] Mirror updated file to active Fusion add-in folder

## Verification Notes
- Backup created:
  - `Addin/PhilsDesignTools/smg_stub_arms.py.bak-20260429-101049`
- New UI/settings:
  - Added `Max pair angle` input to `Stub Arms To Wall`.
  - Default is `45 deg`, and the value is persisted in the command settings.
- Geometry behavior:
  - Upper pair line generation remains unchanged.
  - Lower pair line still applies the existing wall-clearance adjustment first.
  - If the included angle at the shared wall-hit point is greater than the requested maximum, the lower member-side endpoint is moved along the member axis toward the upper point until the angle is within limit.
- Syntax checks passed:
  - `py_compile` on repo file:
    - `Addin/PhilsDesignTools/smg_stub_arms.py`
  - `py_compile` on mirrored active add-in file:
    - `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_stub_arms.py`
- Mirror verification:
  - Active add-in backup created: `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_stub_arms.py.bak-20260429-101248`
  - Repo and active installed copies of `smg_stub_arms.py` match by SHA-256.
- UI hotfix:
  - Replaced `um.defaultAngleUnits` with a fixed `"deg"` unit string because this Fusion build's `UnitsManager` does not expose `defaultAngleUnits`.
  - Verified both repo and active installed copies still compile after the hotfix.
  - Active add-in backup created: `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools\smg_stub_arms.py.bak-20260429-102351`

# Installer Refresh For 1.0.9

Date: 2026-04-29

## Plan
- [x] Bump PhilsDesignTools manifest version for the new stub-arm behavior
- [x] Add a version log entry for the new package build
- [x] Rebuild installer artifacts from the current source
- [x] Refresh the single-addin ZIP to the same version for consistency
- [x] Stage only the intended version/build outputs
- [x] Commit and push the package refresh

## Verification Notes
- Manifest bumped:
  - `Addin/PhilsDesignTools/PhilsDesignTools.manifest` -> `1.0.9`
- Version log updated:
  - `Addin/VERSION_LOG.md`
- Build outputs confirmed:
  - `Addin/tools/dist/fusion360-addins-installer-pdt-1.0.9-bom-1.03.zip`
  - `Addin/tools/dist/fusion360-addins-installer-pdt-1.0.9-bom-1.03.msi`
  - `PhilsDesignTools-1.0.9.zip`

# Installer Refresh For 1.0.10

Date: 2026-05-26

## Plan
- [x] Confirm the live installed stub-arm files match the current working source
- [x] Bump PhilsDesignTools version metadata for a fresh release package
- [x] Add a version log entry for the current live-matching stub-arm behavior
- [x] Build fresh 1.0.10 installer and standalone package artifacts
- [x] Commit and push the updated source plus artifacts on `feature/in-development`
- [ ] Refresh `main` release files and direct download links to 1.0.10

## Verification Notes
- Live install check:
  - Current working copies of `smg_stub_arms.py`, `smg_stub_arm_pair.py`, and `PhilsDesignTools.manifest` match the active Fusion add-in install by SHA-256.
- Syntax checks passed:
  - `py_compile` on:
    - `Addin/PhilsDesignTools/smg_stub_arms.py`
    - `Addin/PhilsDesignTools/smg_stub_arm_pair.py`
    - `Addin/PhilsDesignTools/PhilsDesignTools.py`
- Build outputs confirmed:
  - `Addin/tools/dist/fusion360-addins-installer-pdt-1.0.10-bom-1.03.zip`
  - `Addin/tools/dist/fusion360-addins-installer-pdt-1.0.10-bom-1.03.msi`
  - `PhilsDesignTools-1.0.10.zip`
