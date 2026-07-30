[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$TransactionPath,
    [string]$DocumentsRoot = (Join-Path $env:USERPROFILE "Documents"),
    [AllowNull()][string[]]$ObservedProcessNames = $null
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Import-Module (Join-Path $PSScriptRoot "PhilsFusionTools.Transaction.psm1") -Force

if ($PSBoundParameters.ContainsKey("ObservedProcessNames") -and
    $env:PFT_INSTALLER_TEST_MODE -ne "1") {
    throw "ObservedProcessNames is available only to the isolated installer tests."
}
$transaction = (Resolve-Path -LiteralPath $TransactionPath).Path
$statePath = Join-Path $transaction "state.json"
$state = Read-JsonFile -Path $statePath
$expectedTransactionRoot = Join-Path $state.documents_root (
    "PhilsFusionTools\MigrationTransactions"
)
Assert-PathWithin -Path $transaction -AllowedRoot $expectedTransactionRoot | Out-Null
if ($state.status -ne "awaiting_health") {
    throw "Transaction is not awaiting health: $($state.status)"
}

$healthPath = Join-Path $DocumentsRoot "PhilsFusionTools\health.json"
$healthError = $null
try {
    $health = Read-JsonFile -Path $healthPath
    if ($health.status -ne "healthy") {
        throw "status is not healthy"
    }
    if ($health.version -ne "2.0.0") {
        throw "version is not 2.0.0"
    }
    if ($health.package_fingerprint -ne $state.package_tree_hash) {
        throw "package fingerprint does not match the installed runtime"
    }
    if ([int]$health.groups -ne 7 -or [int]$health.public_commands -ne 25) {
        throw "registered group or command count is incorrect"
    }
    if (@($health.startup_errors).Count -ne 0) {
        throw "startup errors were reported"
    }
}
catch {
    $healthError = $_.Exception.Message
}

if ($healthError) {
    $rollback = Join-Path $PSScriptRoot "rollback_phils_fusion_tools.ps1"
    if ($env:PFT_INSTALLER_TEST_MODE -eq "1") {
        & $rollback `
            -TransactionPath $transaction `
            -ObservedProcessNames $ObservedProcessNames | Out-Null
    }
    else {
        & $rollback -TransactionPath $transaction | Out-Null
    }
    throw "Health verification failed; transaction was rolled back: $healthError"
}

$archiveParent = Assert-PathWithin -Path (
    Join-Path $DocumentsRoot "PhilsFusionTools\LegacyArchive"
) -AllowedRoot $DocumentsRoot
New-Item -ItemType Directory -Force -Path $archiveParent | Out-Null
$archivePath = Join-Path $archiveParent $state.transaction_id
if (Test-Path -LiteralPath $archivePath) {
    throw "Legacy archive already exists: $archivePath"
}
$quarantine = Join-Path $transaction "quarantine"
Move-Item -LiteralPath $quarantine -Destination $archivePath

$receiptPath = Join-Path $transaction "migration-receipt.json"
$receipt = [ordered]@{
    schema_version = 1
    status = "complete"
    completed_at_utc = Get-UtcTimestamp
    transaction_id = $state.transaction_id
    version = $state.version
    package_sha256 = $state.package_sha256
    package_tree_hash = $state.package_tree_hash
    health_path = $healthPath
    legacy_archive = $archivePath
    rollback_root = $state.rollback_root
    rollback_manifest_sha256 = $state.rollback_manifest_sha256
}
Write-JsonAtomic -Path $receiptPath -Value $receipt
$receiptHash = (Get-FileHash -LiteralPath $receiptPath -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText(
    "$receiptPath.sha256",
    "$receiptHash  $([IO.Path]::GetFileName($receiptPath))`n",
    [Text.ASCIIEncoding]::new()
)

$state.status = "complete"
$state | Add-Member -NotePropertyName "completed_at_utc" -NotePropertyValue (
    Get-UtcTimestamp
) -Force
$state | Add-Member -NotePropertyName "legacy_archive" -NotePropertyValue $archivePath -Force
$state | Add-Member -NotePropertyName "receipt_path" -NotePropertyValue $receiptPath -Force
Write-JsonAtomic -Path $statePath -Value $state

[pscustomobject]@{
    Status = $state.status
    Transaction = $transaction
    LegacyArchive = $archivePath
    Receipt = $receiptPath
    ReceiptSha256 = $receiptHash
}
