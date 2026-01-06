param(
    [string]$Source = (Join-Path $PSScriptRoot "..\\PhilsDesignTools"),
    [string]$Target = (Join-Path $env:APPDATA "Autodesk\\Autodesk Fusion 360\\API\\AddIns\\PhilsDesignTools"),
    [string]$BackupRoot = (Join-Path $env:APPDATA "Autodesk\\Autodesk Fusion 360\\API\\AddIns\\_PhilsDesignTools_Backups"),
    [switch]$NoBackup
)

$sourcePath = (Resolve-Path $Source).Path
if (-not (Test-Path $sourcePath)) {
    throw "Source folder not found: $sourcePath"
}

if ((-not $NoBackup) -and (Test-Path $Target)) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = Join-Path $BackupRoot $timestamp
    New-Item -ItemType Directory -Force -Path $backupPath | Out-Null
    Copy-Item -Recurse -Force $Target $backupPath
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null
Copy-Item -Recurse -Force (Join-Path $sourcePath "*") $Target

Write-Output "Deployed from $sourcePath to $Target"
