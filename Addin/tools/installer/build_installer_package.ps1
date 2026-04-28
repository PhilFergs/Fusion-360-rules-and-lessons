param(
    [string]$OutputDir = (Join-Path $PSScriptRoot "..\dist"),
    [switch]$OpenOutput,
    [switch]$SkipMsi
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[Installer Build] $Message"
}

function Convert-ToMsiVersion {
    param([string]$Version)

    $parts = @()
    foreach ($p in ($Version -split "\.")) {
        if ($p -match '^\d+$') {
            $parts += [int]$p
        }
    }
    while ($parts.Count -lt 3) {
        $parts += 0
    }
    return "$($parts[0]).$($parts[1]).$($parts[2])"
}

function Ensure-LocalWixCli {
    param([string]$CacheRoot)

    $wixExe = Join-Path $CacheRoot "extract\PFiles64\WiX Toolset v7.0\bin\wix.exe"
    $utilExt = Join-Path $CacheRoot "extract\CFiles64\WixToolset\extensions\WixToolset.Util.wixext\7.0.0\wixext7\WixToolset.Util.wixext.dll"

    if ((Test-Path $wixExe) -and (Test-Path $utilExt)) {
        return @{ WixExe = $wixExe; UtilExt = $utilExt }
    }

    New-Item -ItemType Directory -Force -Path $CacheRoot | Out-Null
    $msiPath = Join-Path $CacheRoot "wix-cli-x64.msi"
    $extractDir = Join-Path $CacheRoot "extract"

    if (-not (Test-Path $msiPath)) {
        Write-Info "Downloading portable WiX CLI"
        Invoke-WebRequest -Uri "https://github.com/wixtoolset/wix/releases/download/v7.0.0/wix-cli-x64.msi" -OutFile $msiPath
    }

    if (Test-Path $extractDir) {
        Remove-Item -Recurse -Force $extractDir
    }
    New-Item -ItemType Directory -Force -Path $extractDir | Out-Null

    Write-Info "Extracting WiX CLI locally"
    $msiResolved = (Resolve-Path $msiPath).Path
    $extractResolved = (Resolve-Path $extractDir).Path
    Start-Process msiexec.exe -ArgumentList "/a `"$msiResolved`" /qn TARGETDIR=`"$extractResolved`\`"" -Wait -NoNewWindow

    if (-not (Test-Path $wixExe)) {
        throw "Local WiX extraction failed. Missing: $wixExe"
    }
    if (-not (Test-Path $utilExt)) {
        throw "Local WiX extraction failed. Missing: $utilExt"
    }

    return @{ WixExe = $wixExe; UtilExt = $utilExt }
}

function Build-MsiInstaller {
    param(
        [string]$BuildRoot,
        [string]$StageRoot,
        [string]$OutputPath,
        [string]$MsiVersion,
        [string]$DisplayVersion
    )

    $wixCacheRoot = Join-Path $env:LOCALAPPDATA "FusionInstallerTools\wix-cli-7"
    $wix = Ensure-LocalWixCli -CacheRoot $wixCacheRoot
    $wixExe = $wix.WixExe
    $utilExt = $wix.UtilExt

    Write-Info "Accepting WiX EULA (wix7)"
    & $wixExe eula accept wix7 | Out-Null

    $wxsPath = Join-Path $BuildRoot "fusion360-addins-installer.wxs"
    $wxs = @'
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs" xmlns:util="http://wixtoolset.org/schemas/v4/wxs/util">
  <Package Name="Fusion 360 Add-ins Installer"
           Manufacturer="Phil Fergs"
           Version="$(var.ProductVersion)"
           UpgradeCode="48F15118-8541-4FC7-9A23-6F807D1F43D3"
           Scope="perUser">
    <SummaryInformation Description="Fusion 360 Add-ins Installer (PhilsDesignTools + PhilsBom.bundle)" />
    <MajorUpgrade DowngradeErrorMessage="A newer version of Fusion 360 Add-ins Installer is already installed." />
    <MediaTemplate EmbedCab="yes" />

    <Property Id="ARPCOMMENTS" Value="Installs PhilsDesignTools and PhilsBom.bundle for the current user." />
    <Property Id="ARPURLINFOABOUT" Value="https://github.com/PhilFergs/Fusion-360-rules-and-lessons" />
    <Property Id="ARPNOMODIFY" Value="1" />

    <StandardDirectory Id="LocalAppDataFolder">
      <Directory Id="INSTALLFOLDER" Name="Fusion360AddinsInstaller">
        <Directory Id="VERSIONFOLDER" Name="pdt-$(var.DisplayVersion)" />
      </Directory>
    </StandardDirectory>

    <ComponentGroup Id="InstallerPayload" Directory="VERSIONFOLDER">
      <Files Include="$(var.StageRoot)\**" />
    </ComponentGroup>

    <SetProperty Id="RunFusionAddinsInstall"
                 Value="&quot;[System64Folder]WindowsPowerShell\\v1.0\\powershell.exe&quot; -NoProfile -ExecutionPolicy Bypass -File &quot;[VERSIONFOLDER]install_fusion_addins.ps1&quot; -PackageRoot &quot;[VERSIONFOLDER]&quot;"
                 Before="RunFusionAddinsInstall"
                 Sequence="execute" />

    <CustomAction Id="RunFusionAddinsInstall"
                  BinaryRef="Wix4UtilCA_$(sys.BUILDARCHSHORT)"
                  DllEntry="WixQuietExec"
                  Execute="deferred"
                  Return="check"
                  Impersonate="no" />

    <InstallExecuteSequence>
      <Custom Action="RunFusionAddinsInstall" After="InstallFiles" Condition="NOT Installed" />
    </InstallExecuteSequence>

    <Feature Id="MainFeature" Title="Fusion 360 Add-ins" Level="1">
      <ComponentGroupRef Id="InstallerPayload" />
    </Feature>
  </Package>
</Wix>
'@

    Set-Content -Path $wxsPath -Value $wxs -Encoding UTF8

    if (Test-Path $OutputPath) {
        Remove-Item -Force $OutputPath
    }

    $stageResolved = (Resolve-Path $StageRoot).Path
    Write-Info "Building MSI package $OutputPath"

    & $wixExe build $wxsPath -ext $utilExt -d "StageRoot=$stageResolved" -d "ProductVersion=$MsiVersion" -d "DisplayVersion=$DisplayVersion" -o $OutputPath

    if (-not (Test-Path $OutputPath)) {
        throw "MSI build failed. Missing output: $OutputPath"
    }

    $wixPdbPath = [System.IO.Path]::ChangeExtension($OutputPath, ".wixpdb")
    if (Test-Path $wixPdbPath) {
        Remove-Item -Force $wixPdbPath
    }
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
$msiVersion = Convert-ToMsiVersion -Version $pdtVersion

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

$zipPackageName = "fusion360-addins-installer-pdt-$pdtVersion-bom-$bomVersion.zip"
$zipPackagePath = Join-Path $resolvedOutputDir $zipPackageName
if (Test-Path $zipPackagePath) {
    Remove-Item -Force $zipPackagePath
}

Write-Info "Creating ZIP package $zipPackagePath"
Compress-Archive -Path (Join-Path $stageRoot "*") -DestinationPath $zipPackagePath -Force
Write-Output "OUTPUT_ZIP:$zipPackagePath"

if (-not $SkipMsi) {
    $msiPackageName = "fusion360-addins-installer-pdt-$pdtVersion-bom-$bomVersion.msi"
    $msiPackagePath = Join-Path $resolvedOutputDir $msiPackageName
    Build-MsiInstaller -BuildRoot $buildRoot -StageRoot $stageRoot -OutputPath $msiPackagePath -MsiVersion $msiVersion -DisplayVersion $pdtVersion
    Write-Output "OUTPUT_MSI:$msiPackagePath"
}

Write-Info "Package build complete"

if ($OpenOutput) {
    Start-Process explorer.exe $resolvedOutputDir
}
