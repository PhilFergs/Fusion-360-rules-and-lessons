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
- [ ] Commit and push `feature/in-development`
- [ ] Build `PhilsDesignTools-1.0.5.zip` release package
- [ ] Update zip-only `main` branch with new package + README
- [ ] Push `main`
