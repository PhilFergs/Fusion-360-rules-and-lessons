# Phils Design Tools (development)

This branch is scoped to the `Addin/` folder only.

## What it does
- Generates EA, SHS, and RHS steel members from sketch lines.
- Provides a rotate tool for generated steel members.
- Batch renames EA/steel members by selection order with length-based naming.

## Install (Fusion 360)
- Add `Addin/PhilsDesignTools` as a local add-in in Fusion 360.
- Ensure the add-in is enabled; it registers commands in the Solid workspace.

## Commands
- Create panel: EA From Lines, SHS From Lines, RHS From Lines, Rotate Steel Member
- Modify panel: EA Batch Rename

## Development notes
- Update `Addin/CHANGELOG.md` (user-facing) and `Addin/DEVLOG.md` (working notes) with each change set.
- Keep cache/log files out of git; see `Addin/.gitignore`.

