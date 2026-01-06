# Phils Design Tools (development)

This branch is scoped to the `Addin/` folder only.

## What it does
- Generates EA, SHS, and RHS steel members from sketch lines.
- Provides a rotate tool for generated steel members.
- Batch renames EA/steel members by selection order with length-based naming.
- Exports EA hole locations to CSV and leaf components to IGES.
- Creates component sets, wireframe centrelines, and hole cuts from faces.

## Install (Fusion 360)
- Add `Addin/PhilsDesignTools` as a local add-in in Fusion 360.
- Ensure the add-in is enabled; it registers commands in the Solid workspace.

## Commands
- PhilsDesignTools panel: EA From Lines, SHS From Lines, RHS From Lines, Rotate Steel Member,
  Batch Rename, Split Body (Keep Side), Split Body Delete, EA Hole Export CSV,
  IGES Component Export, New Component Set, Wireframe From Body, Hole Cut From Face

## Tool instructions
- EA From Lines: Select sketch lines, set flange/thickness/extra/holes/angle, then OK.
- SHS From Lines: Select sketch lines, set size/thickness/extra/angle, then OK.
- RHS From Lines: Select sketch lines, set width/depth/thickness/extra/angle, then OK.
- Rotate Steel Member: Select member occurrences, choose 90 or -90, then OK.
- Batch Rename: Select member occurrences, set prefix/start index/size suffix, then OK.
- Split Body (Keep Side): Select body and split tool, set Extend if needed, choose keep or delete mode, then OK.
- Split Body Delete: Select a body to delete after a split, then OK.
- EA Hole Export CSV: Select components/occurrences/bodies, choose a CSV path, then OK.
- IGES Component Export: Select components/occurrences/bodies, choose folder, confirm linked export choice, then OK.
- New Component Set: Enter prefix, number range (for example 1-40), and suffix, then OK.
- Wireframe From Body: Select solid bodies (6 faces), then OK to create centerline sketches and hide bodies.
- Hole Cut From Face: Select a cylindrical hole face and a target body, then OK to cut.

## Development notes
- Update `Addin/CHANGELOG.md` (user-facing) and `Addin/DEVLOG.md` (working notes) with each change set.
- Keep cache/log files out of git; see `Addin/.gitignore`.
