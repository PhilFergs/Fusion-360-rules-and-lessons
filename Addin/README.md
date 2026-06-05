# PhilsDesignTools

This folder contains the PhilsDesignTools Fusion 360 add-in.

## What it does
- Generates EA, SHS, and RHS steel members from sketch lines.
- Provides a rotate tool for generated steel members.
- Batch renames EA/steel members by selection order without length in the generated name.
- Exports EA hole locations to CSV and leaf components to multiple CAD file formats.
- Creates component sets, wireframe centrelines, and hole cuts from faces.

## Install (Fusion 360)
- Add `Addin/PhilsDesignTools` as a local add-in in Fusion 360.
- Ensure the add-in is enabled; it registers commands in the Solid workspace.

## Commands
- PhilsDesignTools panel: EA From Lines, SHS From Lines, RHS From Lines, Rotate Steel Member,
  Batch Rename, Split Body (Keep Side), Split Body Delete, EA Hole Export CSV,
  Multi Part File Export, New Component Set, Wireframe From Body, Hole Cut From Face,
  Stub Arms To Wall, Stub Arms Export, Stub Arms Export DXF, Stub Arms Set Bracket,
  Remove Length From Names, Bulk Replace Components, Normalize Component Structure,
  Move Preserve Position, Set Component Descriptions

## Tool instructions
- EA From Lines: Select sketch lines, set flange/thickness/extra/holes/angle, choose whether to add the profile suffix to generated names, then OK. Names default to `EA###`; generated components get descriptions like `EA 50 x 50 x 3`.
- SHS From Lines: Select sketch lines, set size/thickness/extra/angle, choose whether to add the profile suffix to generated names, then OK. Names default to `SHS###`; generated components get descriptions like `SHS 100 x 100 x 3`.
- RHS From Lines: Select sketch lines, set width/depth/thickness/extra/angle, choose whether to add the profile suffix to generated names, then OK. Names default to `RHS###`; generated components get descriptions like `RHS 100 x 50 x 3`.
- Rotate Steel Member: Select member occurrences, choose 90 or -90, then OK.
- Batch Rename: Select member occurrences, set prefix/start index/size suffix, then OK; the command now prefers native occurrence renames so Fusion component-asset validation errors do not block normal browser renaming.
- Remove Length From Names: One-click cleanup to remove only `-####mm-` from existing component and occurrence names, using guarded occurrence/component rename routes for newer Fusion builds.
- Bulk Replace Components: Select multiple external target occurrences, then choose one external replacement design in the Fusion cloud file picker to replace all targets in one action.
- Split Body (Keep Side): Select body and split tool, set Extend if needed, choose keep or delete mode, then OK.
- Split Body Delete: Select a body to delete after a split, then OK.
- EA Hole Export CSV: Select components/occurrences/bodies, choose a CSV path, then OK.
- Multi Part File Export: Select components/occurrences/bodies, choose file type (STEP/STL/IGES/SAT/SMT/F3D and any other supported format available in your Fusion build), choose folder, confirm linked export choice, then OK.
- New Component Set: Enter prefix, number range (for example 1-40), and suffix, then OK.
- Wireframe From Body: Select solid bodies (6 faces), then OK to create centerline sketches and hide bodies.
- Hole Cut From Face: Select a cylindrical hole face and a target body, then OK to cut; nested assembly selections use guarded face/proxy sketch creation with a construction-plane fallback when Fusion cannot resolve the face path.
- Stub Arms To Wall: Optimized stub arms tool. Select RHS column bodies and wall faces/bodies, set connection count and offsets, optionally angle the shared wall point for the top line (default `0 deg`), and optionally cap the included angle between the upper and lower pair lines (default `45 deg`), then OK. Nested wall sketches prefer plane references before direct face sketching.
- Stub Arms Export: Select stub arm lines or sketches, choose export options and filetype, then save.
- Stub Arms Export DXF: Select stub arm lines, sketches, or components, then save a DXF containing only the stub arm line geometry.
- Stub Arms Set Bracket: Select stub arm lines, choose Square/Swivel, then OK to reclassify.
- Normalize Component Structure: One-click cleanup that moves mixed/multi-body direct bodies into child components and renames single direct bodies to match their parent component.
- Move Preserve Position: Select component occurrences and a target parent occurrence to reparent them while preserving their root/model-space position in hybrid/direct-modeling assemblies.
- Set Component Descriptions: Write Fusion component Description values for supported single-body leaf members from the actual body profile. Optional name fallback and simplified material assignment can be enabled when needed.

## Development notes
- Update `Addin/CHANGELOG.md` (user-facing) and `Addin/DEVLOG.md` (working notes) with each change set.
- Keep cache/log files out of git; see `Addin/.gitignore`.
- Every new command must include debug logging (DEBUG flag + detailed failure reasons) alongside the standard command summary log.
- Before modifying `Addin/PhilsDesignTools/smg_stub_arms.py`, create a timestamped backup in the same folder: `smg_stub_arms.py.bak-YYYYMMDD-HHMMSS`, and note the backup name in the chat.

## Installer package (for other PCs)
- Installer source: `Addin/tools/installer`
- Build package:
  - `powershell -ExecutionPolicy Bypass -File Addin/tools/installer/build_installer_package.ps1`
- Output package:
  - `Addin/tools/dist/fusion360-addins-installer-pdt-<version>-bom-<version>.zip`
- User install flow:
  - Unzip package.
  - Run `Install_Fusion_Addins.cmd`.
  - Script checks for Fusion 360, installs both add-ins, and overwrites existing versions (with backups by default).
