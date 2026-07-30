# Phils Fusion Tools

Phils Fusion Tools is the unified Windows add-in for Phil's Fusion workflows.
Version 2.0 replaces the separately installed Phils BOM and Phils Design Tools
copies with one startup entry, one toolbar panel, shared safety prompts, and
shared diagnostics.

## Toolbar

The **Phils Fusion Tools** panel appears in the Solid workspace and contains:

- **BOM**: Create BOM and BOM Settings.
- **Create**: Create Steel Member, New Component Set, and Wireframe From Body.
- **Modify**: rotation, batch rename, split/delete, position-preserving moves,
  and bulk component replacement.
- **Fabricate**: hole cutting and stub-arm creation/classification.
- **Export**: multi-part CAD, EA holes, stub-arm schedules, and stub-arm DXF.
- **Cleanup**: sorting, name cleanup, structure normalization, descriptions,
  and part numbers.
- **Help**: Diagnostics and About And Migration.

Create Steel Member replaces the six separate EA, SHS, RHS, UB/I Beam, PFC,
and C Channel launchers with one profile-aware dialog. The old command IDs are
retained as hidden compatibility aliases for this release.

## Safety

- Routine commands run without unnecessary confirmation.
- Bulk and destructive commands show an action summary before changing the
  design.
- File exports prompt only when an existing file would be overwritten.
- BOM files are built and validated before an atomic replace.
- Settings and health records are written atomically.
- Operational logs rotate at 2 MiB with three retained backups.

## Installed Location

The production add-in belongs at:

```text
%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsFusionTools
```

Do not place this add-in under `ApplicationPlugins`, `MyScripts\Autorun`, or
inside another `.bundle`.

## Build And Install

From the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\run_quality.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\package_phils_fusion_tools.ps1 -Production
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\install_phils_fusion_tools.ps1
```

The installer is transactional. It verifies the package, the exact production
allowlist, and the independent rollback package before moving legacy copies
into quarantine. After a healthy Fusion startup, use the finalizer described
in `docs/operations/install-and-rollback.md`.

## Local Data

Runtime data is stored under:

```text
%USERPROFILE%\Documents\PhilsFusionTools
```

This folder contains settings, startup health, logs, migration transactions,
and the finalized legacy archive. The verified pre-2.0 rollback package remains
separate under `%USERPROFILE%\Documents\PhilsFusionTools-Rollback`.

## Verification

Run the Python/Ruff/compile gate with `tools\run_quality.ps1` and the Windows
installer contract with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Pester -Script '.\tests\powershell\test_installer_contract.ps1'"
```

The release evidence is in
`docs/verification/release-2.0.0-verification.md`.
