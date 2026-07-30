# Phils Fusion Tools 2.0 Install And Rollback

## Safety Preconditions

1. Close Autodesk Fusion, Fusion Launcher, and Fusion Service.
2. Keep the verified rollback folder and `LATEST-VERIFIED.txt` unchanged.
3. Build the production package with:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\package_phils_fusion_tools.ps1 -Production
   ```

## Stage Installation

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\install_phils_fusion_tools.ps1
```

The installer verifies the package SHA-256, exact allowlist, rollback manifest,
runtime tree hash, manifest, Python syntax, and resources. It moves the six
legacy locations into a timestamped transaction quarantine and activates only
`PhilsFusionTools` under Fusion's `API\AddIns` folder.

The transaction remains `awaiting_health`; legacy files are not finalized yet.

## Health Check

1. Start Fusion.
2. Confirm the **Phils Fusion Tools** panel contains BOM, Create, Modify,
   Fabricate, Export, Cleanup, and Help groups.
3. Open **Help > Diagnostics** and confirm startup health is healthy.
4. Close Fusion.

Fusion writes:

```text
Documents\PhilsFusionTools\health.json
```

## Finalize

Run the finalizer with the transaction path printed by the installer:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\finalize_phils_fusion_tools_migration.ps1 -TransactionPath "<transaction>"
```

Finalization requires version `2.0.0`, seven groups, 25 public commands, no
startup errors, and an exact runtime fingerprint. It archives quarantined
legacy files under `Documents\PhilsFusionTools\LegacyArchive` and writes a
SHA-256 receipt.

## Transaction Rollback

Before finalization, close Fusion and run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\rollback_phils_fusion_tools.ps1 -TransactionPath "<transaction>"
```

Rollback verifies the installed runtime hash, preserves the unified install
inside the transaction, and restores every quarantined path in reverse order.
It never modifies or deletes the verified pre-2.0 rollback package.

After finalization, use the verified rollback package's own restore script if a
full pre-2.0 restore is required.
