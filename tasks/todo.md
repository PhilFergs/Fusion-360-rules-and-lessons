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

