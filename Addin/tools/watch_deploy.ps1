param(
    [string]$Source = (Join-Path $PSScriptRoot "..\\PhilsDesignTools"),
    [string]$Target = (Join-Path $env:APPDATA "Autodesk\\Autodesk Fusion 360\\API\\AddIns\\PhilsDesignTools"),
    [string]$BackupRoot = (Join-Path $env:APPDATA "Autodesk\\Autodesk Fusion 360\\API\\AddIns\\_PhilsDesignTools_Backups"),
    [int]$DebounceMs = 500
)

$deployScript = Join-Path $PSScriptRoot "deploy_addin.ps1"
if (-not (Test-Path $deployScript)) {
    throw "Deploy script not found: $deployScript"
}

$sourcePath = (Resolve-Path $Source).Path
if (-not (Test-Path $sourcePath)) {
    throw "Source folder not found: $sourcePath"
}

function Invoke-Deploy {
    & $deployScript -Source $sourcePath -Target $Target -BackupRoot $BackupRoot -NoBackup
}

Invoke-Deploy
Write-Output "Watching $sourcePath for changes. Press Ctrl+C to stop."

$script:pending = $false
$script:lastEvent = Get-Date

$handler = {
    $script:pending = $true
    $script:lastEvent = Get-Date
}

$watcher = New-Object System.IO.FileSystemWatcher $sourcePath, "*"
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

Register-ObjectEvent -InputObject $watcher -EventName Changed -Action $handler | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Created -Action $handler | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Deleted -Action $handler | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Renamed -Action $handler | Out-Null

while ($true) {
    if ($script:pending) {
        $elapsed = (New-TimeSpan -Start $script:lastEvent -End (Get-Date)).TotalMilliseconds
        if ($elapsed -ge $DebounceMs) {
            $script:pending = $false
            try {
                Invoke-Deploy
            } catch {
                Write-Warning $_
            }
        }
    }
    Start-Sleep -Milliseconds 200
}
