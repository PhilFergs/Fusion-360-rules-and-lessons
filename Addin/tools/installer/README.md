# Fusion 360 Add-ins Installer Package

This installer package deploys both add-ins for the current Windows user:

- `PhilsDesignTools` -> `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools`
- `PhilsBom.bundle` -> `%APPDATA%\Autodesk\ApplicationPlugins\PhilsBom.bundle`

## What it does
- Checks whether Fusion 360 is installed.
- Installs both add-ins from packaged payload zips.
- Overwrites existing versions automatically.
- Creates timestamped backups by default.

## Build a distributable installer package
From this folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer_package.ps1
```

Output is written to:

- `Addin/tools/dist/fusion360-addins-installer-pdt-<version>-bom-<version>.zip`

## Use the package on any PC
1. Unzip the installer package.
2. Right-click `Install_Fusion_Addins.cmd` and run it.
3. Restart Fusion 360.

## Advanced options
Run PowerShell script directly:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_fusion_addins.ps1 -PackageRoot .
```

Optional switches:

- `-NoBackup` skip backup copy of existing add-ins.
- `-DryRun` validate detection and paths without changing files.
