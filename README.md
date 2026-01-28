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
- `PhilsBom` - distribution folder (zip + install notes).

---

## Add-ins in this repo (paths)
### PhilsDesignTools
- Source (edit): `C:\Users\phil9\Documents\02 - Fusion\InDevelopment\Addin\PhilsDesignTools`
- Active (deployed): `C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools`

### PhilsBom (BOM export)
- Distribution (zip + install): `PhilsBom/PhilsBom.bundle-<version>.zip` + `PhilsBom/PhilsBom_INSTALL.txt`
- Active bundle (deployed): `C:\Users\phil9\AppData\Roaming\Autodesk\ApplicationPlugins\PhilsBom.bundle`
- Source bundle is maintained in the InDevelopment worktree:
  `C:\Users\phil9\Documents\02 - Fusion\InDevelopment\PhilsBom.bundle`

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
- Zip: `PhilsBom/PhilsBom.bundle-<version>.zip`
- Install guide: `PhilsBom/PhilsBom_INSTALL.txt`
