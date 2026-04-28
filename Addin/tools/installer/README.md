# Fusion 360 Add-ins Installer Package

This installer package deploys both add-ins for the current Windows user:

- `PhilsDesignTools` -> `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools`
- `PhilsBom.bundle` -> `%APPDATA%\Autodesk\ApplicationPlugins\PhilsBom.bundle`

## What it does
- Checks whether Fusion 360 is installed.
- Installs both add-ins from packaged payload zips.
- Overwrites existing versions automatically.
- Creates timestamped backups by default.

## Build distributable installers
From this folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer_package.ps1
```

Outputs are written to:

- `Addin/tools/dist/fusion360-addins-installer-pdt-<version>-bom-<version>.zip`
- `Addin/tools/dist/fusion360-addins-installer-pdt-<version>-bom-<version>.msi`

Notes:
- The build now creates a user-scope MSI wrapper that runs the packaged installer script automatically after files are staged.
- WiX CLI is downloaded/extracted locally into `%LOCALAPPDATA%\FusionInstallerTools\wix-cli-7` if it is not already present.
- To skip MSI generation:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer_package.ps1 -SkipMsi
```

## Use the package on any PC
1. Preferred: run the `.msi` package.
2. Fallback: unzip the `.zip` package and run `Install_Fusion_Addins.cmd`.
3. Restart Fusion 360.

## Reduce Defender/SmartScreen warnings
- Sign the MSI with your code-signing certificate (EV cert strongly recommended).
- Keep the same publisher identity and installer naming pattern each release.
- Publish from GitHub Releases or your own HTTPS domain.
- If Defender flags a release, submit it as a false positive to Microsoft.

## Advanced options
Run PowerShell script directly:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_fusion_addins.ps1 -PackageRoot .
```

Optional switches:

- `-NoBackup` skip backup copy of existing add-ins.
- `-DryRun` validate detection and paths without changing files.
