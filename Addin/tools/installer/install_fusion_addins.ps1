param(
    [string]$PackageRoot = $PSScriptRoot,
    [switch]$NoBackup,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[Fusion Installer] $Message"
}

function Test-FusionInstalled {
    $prodRoot = Join-Path $env:LOCALAPPDATA "Autodesk\webdeploy\production"
    if (Test-Path $prodRoot) {
        $fusionExe = Get-ChildItem -Path $prodRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { Test-Path (Join-Path $_.FullName "Fusion360.exe") } |
            Select-Object -First 1
        if ($fusionExe) {
            return $true
        }
    }

    $uninstallRoots = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )

    foreach ($root in $uninstallRoots) {
        $match = Get-ItemProperty -Path $root -ErrorAction SilentlyContinue |
            Where-Object {
                $_.DisplayName -and $_.DisplayName -like "*Fusion 360*"
            } |
            Select-Object -First 1
        if ($match) {
            return $true
        }
    }

    return $false
}

function Expand-ZipToRoot {
    param(
        [string]$ZipPath,
        [string]$DestinationRoot,
        [string]$ExpectedFolderName,
        [string]$BackupRoot,
        [switch]$NoBackup,
        [switch]$DryRun
    )

    $targetPath = Join-Path $DestinationRoot $ExpectedFolderName

    if (-not (Test-Path $ZipPath)) {
        throw "Missing package file: $ZipPath"
    }

    if (-not $DryRun) {
        New-Item -ItemType Directory -Force -Path $DestinationRoot | Out-Null
    }

    if (Test-Path $targetPath) {
        if (-not $NoBackup) {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $backupPath = Join-Path $BackupRoot "$ExpectedFolderName-$timestamp"
            Write-Info "Backing up existing '$ExpectedFolderName' to '$backupPath'"
            if (-not $DryRun) {
                New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
                Copy-Item -Recurse -Force $targetPath $backupPath
            }
        }

        Write-Info "Removing existing '$targetPath'"
        if (-not $DryRun) {
            Remove-Item -Recurse -Force $targetPath
        }
    }

    Write-Info "Installing '$ExpectedFolderName' from '$ZipPath'"
    if (-not $DryRun) {
        Expand-Archive -Path $ZipPath -DestinationPath $DestinationRoot -Force
    }

    if (-not $DryRun -and -not (Test-Path $targetPath)) {
        throw "Install failed. Expected folder missing after extract: $targetPath"
    }
}

try {
    Write-Info "Starting installer"
    $packageRootRaw = [string]$PackageRoot
    $packageRootClean = $packageRootRaw.Trim().Trim('"')
    if ([string]::IsNullOrWhiteSpace($packageRootClean)) {
        throw "Package root path is empty."
    }
    try {
        $packageRootClean = [System.IO.Path]::GetFullPath($packageRootClean)
    } catch {
        throw "Invalid package root path: '$PackageRoot'"
    }
    if (-not (Test-Path $packageRootClean)) {
        throw "Package root does not exist: $packageRootClean"
    }
    Write-Info "Package root: $packageRootClean"

    if (-not (Test-FusionInstalled)) {
        throw "Fusion 360 was not detected on this PC. Install Fusion 360 first, then run this installer again."
    }

    $payloadRoot = Join-Path $packageRootClean "payload"
    $philsDesignToolsZip = Join-Path $payloadRoot "PhilsDesignTools.zip"
    $philsBomZip = Join-Path $payloadRoot "PhilsBom.bundle.zip"

    $addinsRoot = Join-Path $env:APPDATA "Autodesk\Autodesk Fusion 360\API\AddIns"
    $pluginsRoot = Join-Path $env:APPDATA "Autodesk\ApplicationPlugins"
    $backupRoot = Join-Path $env:APPDATA "Autodesk\FusionInstallerBackups"

    Expand-ZipToRoot -ZipPath $philsDesignToolsZip -DestinationRoot $addinsRoot -ExpectedFolderName "PhilsDesignTools" -BackupRoot $backupRoot -NoBackup:$NoBackup -DryRun:$DryRun
    Expand-ZipToRoot -ZipPath $philsBomZip -DestinationRoot $pluginsRoot -ExpectedFolderName "PhilsBom.bundle" -BackupRoot $backupRoot -NoBackup:$NoBackup -DryRun:$DryRun

    if ($DryRun) {
        Write-Info "Dry run complete. No files were changed."
    } else {
        Write-Info "Install complete. Restart Fusion 360 if it was open."
    }

    exit 0
} catch {
    Write-Error $_
    exit 1
}
