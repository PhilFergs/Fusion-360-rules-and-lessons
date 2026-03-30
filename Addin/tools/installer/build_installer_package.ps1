param(
    [string]$OutputDir = (Join-Path $PSScriptRoot "..\dist"),
    [switch]$OpenOutput
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[Installer Build] $Message"
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$addinRoot = Join-Path $repoRoot "Addin"
$philsDesignToolsSource = Join-Path $addinRoot "PhilsDesignTools"
$philsBomSource = Join-Path $repoRoot "PhilsBom.bundle"

$installerScript = Join-Path $PSScriptRoot "install_fusion_addins.ps1"
$installerReadme = Join-Path $PSScriptRoot "README.md"

if (-not (Test-Path $philsDesignToolsSource)) {
    throw "Missing source folder: $philsDesignToolsSource"
}
if (-not (Test-Path $philsBomSource)) {
    throw "Missing source folder: $philsBomSource"
}
if (-not (Test-Path $installerScript)) {
    throw "Missing installer script: $installerScript"
}

$manifest = Get-Content (Join-Path $philsDesignToolsSource "PhilsDesignTools.manifest") -Raw | ConvertFrom-Json
$pdtVersion = [string]$manifest.version

$philsBomManifestRaw = Get-Content (Join-Path $philsBomSource "Contents\PhilsBom.manifest") -Raw
$bomMatch = [regex]::Match($philsBomManifestRaw, '"version"\s*:\s*"([^"]+)"')
if (-not $bomMatch.Success) {
    throw "Unable to parse PhilsBom version from manifest."
}
$bomVersion = $bomMatch.Groups[1].Value

$buildRoot = Join-Path $PSScriptRoot "_build"
$stageRoot = Join-Path $buildRoot "fusion360-addins-installer"
$payloadRoot = Join-Path $stageRoot "payload"

if (Test-Path $stageRoot) {
    Remove-Item -Recurse -Force $stageRoot
}
New-Item -ItemType Directory -Force -Path $payloadRoot | Out-Null

Write-Info "Creating payload archives"
$philsDesignToolsZip = Join-Path $payloadRoot "PhilsDesignTools.zip"
$philsBomZip = Join-Path $payloadRoot "PhilsBom.bundle.zip"

Compress-Archive -Path $philsDesignToolsSource -DestinationPath $philsDesignToolsZip -Force
Compress-Archive -Path $philsBomSource -DestinationPath $philsBomZip -Force

Write-Info "Staging installer files"
Copy-Item -Force $installerScript (Join-Path $stageRoot "install_fusion_addins.ps1")
if (Test-Path $installerReadme) {
    Copy-Item -Force $installerReadme (Join-Path $stageRoot "README.txt")
}

$launcherPath = Join-Path $stageRoot "Install_Fusion_Addins.cmd"
$launcher = "@echo off`r`nsetlocal`r`nset ""PKGROOT=%~dp0.""`r`npowershell -NoProfile -ExecutionPolicy Bypass -File ""%~dp0install_fusion_addins.ps1"" -PackageRoot ""%PKGROOT%"" %*`r`nset EXITCODE=%ERRORLEVEL%`r`nif /I not ""%1""==""--quiet"" pause`r`nexit /b %EXITCODE%`r`n"
Set-Content -Path $launcherPath -Value $launcher -Encoding ASCII

$resolvedOutputDir = [System.IO.Path]::GetFullPath($OutputDir)
New-Item -ItemType Directory -Force -Path $resolvedOutputDir | Out-Null

$packageName = "fusion360-addins-installer-pdt-$pdtVersion-bom-$bomVersion.zip"
$packagePath = Join-Path $resolvedOutputDir $packageName
if (Test-Path $packagePath) {
    Remove-Item -Force $packagePath
}

Write-Info "Creating package $packagePath"
Compress-Archive -Path (Join-Path $stageRoot "*") -DestinationPath $packagePath -Force

Write-Info "Package complete"
Write-Output "OUTPUT:$packagePath"

if ($OpenOutput) {
    Start-Process explorer.exe $resolvedOutputDir
}
