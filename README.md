# PhilsDesignTools - Fusion 360 Add-In

This repository now hosts the PhilsDesignTools add-in, which consolidates the EA/SHS/RHS generation tools, rotation, renaming, exports, and related utilities into a single toolset.

---

## Purpose
- Provide a single, stable add-in that replaces the legacy standalone tools.
- Keep a clear workflow with a stable `main` and ongoing development in the `PhilsDesignTools` branch.

---

## What's included
- `Addin/PhilsDesignTools` - add-in source (entry script, modules, resources).
- `Addin/tools` - deploy and watch scripts.
- `Addin/CHANGELOG.md` and `Addin/DEVLOG.md` - release notes and working notes.
- `Addin/WORKFLOW.md` - development and release workflow.
- `archive/main` - archived rules, notes, and legacy zip releases from the former main branch.
- `PhilsBom.bundle` - separate BOM export add-in bundle (PhilsBom).
- `PhilsBom` - distribution folder (zip + install notes).

---

## Add-ins in this repo (paths)
### PhilsDesignTools
- Source (edit): `C:\Users\phil9\Documents\02 - Fusion\InDevelopment\Addin\PhilsDesignTools`
- Active (deployed): `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools`

### PhilsBom (BOM export)
- Source bundle (edit): `C:\Users\phil9\Documents\02 - Fusion\InDevelopment\PhilsBom.bundle`
- Active bundle (deployed): `C:\Users\phil9\AppData\Roaming\Autodesk\ApplicationPlugins\PhilsBom.bundle`

---

## Install (Fusion 360)
### PhilsDesignTools
1. In Fusion 360, go to Scripts and Add-Ins, then Add.
2. Select the folder `Addin/PhilsDesignTools`.
3. Enable the add-in; commands appear in the Solid workspace.

### PhilsBom
1. Unzip the latest PhilsBom bundle from `PhilsBom/`.
2. Copy `PhilsBom.bundle` into:
   `C:\Users\phil9\AppData\Roaming\Autodesk\ApplicationPlugins`
3. Restart Fusion 360.
4. Run via **Tools > Add-ins > Scripts and Add-ins** (Add-Ins tab).

---

## PhilsDesignTools commands (high level)
- EA/SHS/RHS from sketch lines
- Rotate steel members
- Batch rename members
- EA hole export CSV
- IGES component export
- Component sets, wireframe from body, hole cut from face
- Split body tools

## PhilsBom (BOM export)
- BOM export in CSV/XLSX/XML/JSON
- Per-export unit selection
- Include/exclude hidden items, parent components, and linked components
- Optional mass totals row

---

## Versioning and workflow
- Use semantic versioning in `Addin/PhilsDesignTools/PhilsDesignTools.manifest`.
- Update `Addin/CHANGELOG.md` for user-facing changes and `Addin/DEVLOG.md` for working notes.
- Development happens on `PhilsDesignTools`; `main` is the stable release.

---

## PhilsBom distribution
- Zip: `InDevelopment/PhilsBom/PhilsBom.bundle-<version>.zip`
- Install guide: `InDevelopment/PhilsBom/PhilsBom_INSTALL.txt`

---

## Archive (former main)
Legacy rules, notes, and zip releases are preserved under `archive/main/`.
The ruleset remains the reference standard for add-in work:
`archive/main/Fusion360_AddIn_Rules_Latest.md`

---

## Session starter (Fusion 360 add-in work)
Before generating code, load and follow:
`archive/main/Fusion360_AddIn_Rules_Latest.md`
