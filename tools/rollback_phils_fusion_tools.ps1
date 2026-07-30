[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$TransactionPath,
    [AllowNull()][string[]]$ObservedProcessNames = $null
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Import-Module (Join-Path $PSScriptRoot "PhilsFusionTools.Transaction.psm1") -Force

if ($PSBoundParameters.ContainsKey("ObservedProcessNames") -and
    $env:PFT_INSTALLER_TEST_MODE -ne "1") {
    throw "ObservedProcessNames is available only to the isolated installer tests."
}
Assert-FusionClosed -ObservedProcessNames $ObservedProcessNames

$transaction = (Resolve-Path -LiteralPath $TransactionPath).Path
$statePath = Join-Path $transaction "state.json"
$state = Read-JsonFile -Path $statePath
$expectedTransactionRoot = Join-Path $state.documents_root (
    "PhilsFusionTools\MigrationTransactions"
)
Assert-PathWithin -Path $transaction -AllowedRoot $expectedTransactionRoot | Out-Null
if ($state.status -eq "complete") {
    throw "Completed migrations must use the verified pre-2.0 rollback package."
}

$installPath = Assert-PathWithin -Path $state.install_path -AllowedRoot $state.addins_root
if (Test-Path -LiteralPath $installPath) {
    $installedHash = Get-RuntimeTreeHash -Root $installPath
    if ($installedHash -ne $state.package_tree_hash) {
        throw "Installed unified runtime hash differs; refusing automatic removal."
    }
    $rolledBackUnified = Join-Path $transaction "rolled-back-unified"
    if (Test-Path -LiteralPath $rolledBackUnified) {
        throw "Rollback preservation path already exists: $rolledBackUnified"
    }
    Move-Item -LiteralPath $installPath -Destination $rolledBackUnified
}

Restore-TransactionMappings -State $state -TransactionPath $transaction
$state.status = "rolled_back"
$state | Add-Member -NotePropertyName "rolled_back_at_utc" -NotePropertyValue (
    Get-UtcTimestamp
) -Force
Write-JsonAtomic -Path $statePath -Value $state

[pscustomobject]@{
    Status = $state.status
    Transaction = $transaction
    RestoredPaths = @($state.mappings).Count
}
