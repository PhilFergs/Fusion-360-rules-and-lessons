[CmdletBinding()]
param(
    [string]$PackagePath,
    [string]$HashPath,
    [string]$AllowlistPath,
    [string]$AppDataRoot = $env:APPDATA,
    [string]$DocumentsRoot,
    [string]$RollbackPointer,
    [AllowNull()][string[]]$ObservedProcessNames = $null
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# PSScriptRoot is reliable only after script parameter binding in Windows PowerShell 5.1.
if (-not $PackagePath) {
    $PackagePath = Join-Path $PSScriptRoot "..\build\PhilsFusionTools-2.0.0.zip"
}
if (-not $HashPath) {
    $HashPath = "$PackagePath.sha256"
}
if (-not $AllowlistPath) {
    $AllowlistPath = Join-Path $PSScriptRoot "..\release\package-allowlist.txt"
}
if (-not $DocumentsRoot) {
    $DocumentsRoot = Join-Path $env:USERPROFILE "Documents"
}
if (-not $RollbackPointer) {
    $RollbackPointer = Join-Path $DocumentsRoot (
        "PhilsFusionTools-Rollback\LATEST-VERIFIED.txt"
    )
}

Import-Module (Join-Path $PSScriptRoot "PhilsFusionTools.Transaction.psm1") -Force

if ($PSBoundParameters.ContainsKey("ObservedProcessNames") -and
    $env:PFT_INSTALLER_TEST_MODE -ne "1") {
    throw "ObservedProcessNames is available only to the isolated installer tests."
}
Assert-FusionClosed -ObservedProcessNames $ObservedProcessNames

$package = (Resolve-Path -LiteralPath $PackagePath).Path
$hashFile = (Resolve-Path -LiteralPath $HashPath).Path
$allowlistFile = (Resolve-Path -LiteralPath $AllowlistPath).Path
$pointerFile = (Resolve-Path -LiteralPath $RollbackPointer).Path

$expectedPackageHash = (Get-Content -LiteralPath $hashFile -Raw).Trim().Split()[0].ToLowerInvariant()
$actualPackageHash = (Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash.ToLowerInvariant()
if ($expectedPackageHash -notmatch "^[0-9a-f]{64}$" -or $actualPackageHash -ne $expectedPackageHash) {
    throw "Package SHA-256 verification failed."
}

$pointer = Read-KeyValueFile -Path $pointerFile
if (-not $pointer.ContainsKey("RollbackRoot") -or -not $pointer.ContainsKey("ManifestSHA256")) {
    throw "Rollback pointer is incomplete."
}
$rollbackRoot = (Resolve-Path -LiteralPath $pointer.RollbackRoot).Path
$rollbackManifest = Join-Path $rollbackRoot "rollback-manifest.json"
$actualManifestHash = (Get-FileHash -LiteralPath $rollbackManifest -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualManifestHash -ne $pointer.ManifestSHA256.ToLowerInvariant()) {
    throw "Verified rollback manifest SHA-256 does not match."
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($package)
try {
    $archiveNames = @(
        $archive.Entries |
            Where-Object { $_.Name } |
            ForEach-Object { $_.FullName.Replace("\", "/") }
    )
}
finally {
    $archive.Dispose()
}
$allowed = @(
    Get-Content -LiteralPath $allowlistFile |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ -and -not $_.StartsWith("#") }
)
if (@($archiveNames | Where-Object { $_ -notin $allowed }).Count -gt 0 -or
    @($allowed | Where-Object { $_ -notin $archiveNames }).Count -gt 0) {
    throw "Package content does not match the production allow-list."
}

$addInsRoot = Assert-PathWithin -Path (
    Join-Path $AppDataRoot "Autodesk\Autodesk Fusion 360\API\AddIns"
) -AllowedRoot $AppDataRoot
$dataRoot = Assert-PathWithin -Path (
    Join-Path $DocumentsRoot "PhilsFusionTools"
) -AllowedRoot $DocumentsRoot
$transactionRoot = Join-Path $dataRoot "MigrationTransactions"
$transactionId = "$(Get-Date -Format 'yyyyMMdd-HHmmss')-$([Guid]::NewGuid().ToString('N').Substring(0, 8))"
$transactionPath = Join-Path $transactionRoot $transactionId
$quarantineRoot = Join-Path $transactionPath "quarantine"
$stageRoot = Join-Path $AppDataRoot (
    "PFTStage\$([Guid]::NewGuid().ToString('N').Substring(0, 8))"
)
$stageRoot = Assert-PathWithin -Path $stageRoot -AllowedRoot $AppDataRoot
$finalInstall = Join-Path $addInsRoot "PhilsFusionTools"
$statePath = Join-Path $transactionPath "state.json"
New-Item -ItemType Directory -Force -Path $transactionPath, $quarantineRoot, $addInsRoot | Out-Null

$state = [ordered]@{
    schema_version = 1
    transaction_id = $transactionId
    status = "staging"
    created_at_utc = Get-UtcTimestamp
    app_data_root = [IO.Path]::GetFullPath($AppDataRoot)
    documents_root = [IO.Path]::GetFullPath($DocumentsRoot)
    addins_root = $addInsRoot
    install_path = $finalInstall
    package_path = $package
    package_sha256 = $actualPackageHash
    package_tree_hash = ""
    version = "2.0.0"
    rollback_root = $rollbackRoot
    rollback_manifest_sha256 = $actualManifestHash
    staging_path = $stageRoot
    mappings = @()
}
Write-JsonAtomic -Path $statePath -Value $state

try {
    $index = 0
    foreach ($mapping in Get-LegacyMappings -AppDataRoot $AppDataRoot) {
        $index += 1
        $original = Assert-PathWithin -Path $mapping.original_path -AllowedRoot $AppDataRoot
        if (-not (Test-Path -LiteralPath $original)) {
            continue
        }
        $quarantine = Join-Path $quarantineRoot (
            "{0:D2}-{1}" -f $index, $mapping.label
        )
        Move-Item -LiteralPath $original -Destination $quarantine
        $state.mappings += [ordered]@{
            label = $mapping.label
            kind = $mapping.kind
            original_path = $original
            quarantine_path = $quarantine
        }
        Write-JsonAtomic -Path $statePath -Value $state
    }

    if (Test-Path -LiteralPath $finalInstall) {
        $priorQuarantine = Join-Path $quarantineRoot "99-prior-philsfusiontools"
        Move-Item -LiteralPath $finalInstall -Destination $priorQuarantine
        $state.mappings += [ordered]@{
            label = "prior-philsfusiontools"
            kind = "prior_unified"
            original_path = $finalInstall
            quarantine_path = $priorQuarantine
        }
        Write-JsonAtomic -Path $statePath -Value $state
    }

    if (Test-Path -LiteralPath $stageRoot) {
        throw "Installer staging path already exists: $stageRoot"
    }
    [IO.Compression.ZipFile]::ExtractToDirectory($package, $stageRoot)
    $stagedAddin = Join-Path $stageRoot "PhilsFusionTools"
    $manifest = Join-Path $stagedAddin "PhilsFusionTools.manifest"
    $buildInfoPath = Join-Path $stagedAddin "build-info.json"
    if (-not (Test-Path -LiteralPath $manifest -PathType Leaf) -or
        -not (Test-Path -LiteralPath $buildInfoPath -PathType Leaf)) {
        throw "Staged package is missing its manifest or build identity."
    }

    $buildInfo = Read-JsonFile -Path $buildInfoPath
    if ($buildInfo.version -ne "2.0.0" -or $buildInfo.artifact -ne "production") {
        throw "Staged package is not Phils Fusion Tools 2.0.0 production."
    }
    $actualTreeHash = Get-RuntimeTreeHash -Root $stagedAddin
    if ($actualTreeHash -ne $buildInfo.package_tree_hash) {
        throw "Staged package runtime tree hash does not match build-info.json."
    }

    $validator = Join-Path $PSScriptRoot "validate_runtime.py"
    $python = (Get-Command python -ErrorAction Stop).Source
    & $python $validator $stagedAddin | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Staged Python and resource validation failed."
    }

    Move-Item -LiteralPath $stagedAddin -Destination $finalInstall
    Remove-Item -LiteralPath $stageRoot -Force
    $state.package_tree_hash = $actualTreeHash
    $state.status = "awaiting_health"
    $state.activated_at_utc = Get-UtcTimestamp
    $state.staging_path = $null
    Write-JsonAtomic -Path $statePath -Value $state
}
catch {
    $state.status = "install_failed"
    $state.failure = $_.Exception.Message
    if (Test-Path -LiteralPath $finalInstall) {
        $installedHash = Get-RuntimeTreeHash -Root $finalInstall
        if ($state.package_tree_hash -and $installedHash -eq $state.package_tree_hash) {
            Move-Item -LiteralPath $finalInstall -Destination (
                Join-Path $transactionPath "failed-unified"
            )
        }
    }
    Restore-TransactionMappings -State $state -TransactionPath $transactionPath
    Write-JsonAtomic -Path $statePath -Value $state
    throw
}

[pscustomobject]@{
    Status = $state.status
    Transaction = $transactionPath
    InstallPath = $finalInstall
    PackageSha256 = $actualPackageHash
    PackageTreeHash = $state.package_tree_hash
    QuarantinedPaths = @($state.mappings).Count
}
