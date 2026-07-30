$ErrorActionPreference = "Stop"

$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$installer = Join-Path $repoRoot "tools\install_phils_fusion_tools.ps1"
$finalizer = Join-Path $repoRoot "tools\finalize_phils_fusion_tools_migration.ps1"
$package = Join-Path $repoRoot "build\PhilsFusionTools-2.0.0.zip"
$sidecar = "$package.sha256"
$allowlist = Join-Path $repoRoot "release\package-allowlist.txt"
$contractRoot = Join-Path $env:SystemDrive (
    "pft-installer-tests\$([Guid]::NewGuid().ToString('N'))"
)
$originalTestMode = $env:PFT_INSTALLER_TEST_MODE
$env:PFT_INSTALLER_TEST_MODE = "1"
New-Item -ItemType Directory -Force -Path $contractRoot | Out-Null

function New-TestEnvironment {
    param([string]$Name)

    $root = Join-Path $contractRoot $Name
    $appData = Join-Path $root "AppData"
    $documents = Join-Path $root "Documents"
    $rollbackRoot = Join-Path $documents "Rollback\verified"
    New-Item -ItemType Directory -Force -Path $appData, $documents, $rollbackRoot | Out-Null

    $manifest = Join-Path $rollbackRoot "rollback-manifest.json"
    [IO.File]::WriteAllText($manifest, "{}")
    $manifestHash = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant()
    $pointer = Join-Path $documents "Rollback\LATEST-VERIFIED.txt"
    [IO.File]::WriteAllLines(
        $pointer,
        @(
            "RollbackRoot=$rollbackRoot",
            "ManifestSHA256=$manifestHash",
            "VerifiedAt=2026-07-30T00:00:00Z"
        )
    )

    $legacyPaths = @(
        (Join-Path $appData "Autodesk\ApplicationPlugins\PhilsBom.bundle"),
        (Join-Path $appData "Autodesk\Autodesk Fusion 360\API\AddIns\PhilsBom.bundle"),
        (Join-Path $appData "Autodesk\Autodesk Fusion 360\MyScripts\Autorun\PhilsBom.bundle"),
        (Join-Path $appData "Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools"),
        (Join-Path $appData "Autodesk\Autodesk Fusion 360\API\AddIns\_PhilsDesignTools_Backups"),
        (Join-Path $appData "Autodesk\FusionInstallerBackups")
    )
    foreach ($path in $legacyPaths) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
        [IO.File]::WriteAllText((Join-Path $path "sentinel.txt"), $path)
    }

    return @{
        Root = $root
        AppData = $appData
        Documents = $documents
        Pointer = $pointer
        LegacyPaths = $legacyPaths
        AddIns = Join-Path $appData "Autodesk\Autodesk Fusion 360\API\AddIns"
    }
}

function Install-TestPackage {
    param(
        [hashtable]$Environment,
        [string[]]$ObservedProcessNames = @()
    )

    & $installer `
        -PackagePath $package `
        -HashPath $sidecar `
        -AllowlistPath $allowlist `
        -AppDataRoot $Environment.AppData `
        -DocumentsRoot $Environment.Documents `
        -RollbackPointer $Environment.Pointer `
        -ObservedProcessNames $ObservedProcessNames
}

function Get-Transaction {
    param([hashtable]$Environment)

    $root = Join-Path $Environment.Documents "PhilsFusionTools\MigrationTransactions"
    return Get-ChildItem -LiteralPath $root -Directory |
        Sort-Object Name -Descending |
        Select-Object -First 1
}

Describe "Phils Fusion Tools transactional installer" {
    AfterAll {
        $env:PFT_INSTALLER_TEST_MODE = $originalTestMode
        if (Test-Path -LiteralPath $contractRoot) {
            Remove-Item -LiteralPath $contractRoot -Recurse -Force
        }
    }

    It "refuses install while Fusion is running" {
        $environment = New-TestEnvironment "fusion-running"

        { Install-TestPackage $environment @("Fusion") } | Should Throw

        Test-Path -LiteralPath (Join-Path $environment.AddIns "PhilsFusionTools") |
            Should Be $false
    }

    It "rejects a package with the wrong SHA-256" {
        $environment = New-TestEnvironment "bad-hash"
        $badHash = Join-Path $environment.Root "bad.sha256"
        [IO.File]::WriteAllText($badHash, ("0" * 64) + "  package.zip`n")

        {
            & $installer `
                -PackagePath $package `
                -HashPath $badHash `
                -AllowlistPath $allowlist `
                -AppDataRoot $environment.AppData `
                -DocumentsRoot $environment.Documents `
                -RollbackPointer $environment.Pointer `
                -ObservedProcessNames @()
        } | Should Throw

        foreach ($path in $environment.LegacyPaths) {
            Test-Path -LiteralPath $path | Should Be $true
        }
    }

    It "quarantines every configured legacy path and leaves one manifest" {
        $environment = New-TestEnvironment "quarantine"

        Install-TestPackage $environment | Out-Null

        foreach ($path in $environment.LegacyPaths) {
            Test-Path -LiteralPath $path | Should Be $false
        }
        $manifests = @(Get-ChildItem -LiteralPath $environment.AddIns -Recurse -Filter "*.manifest")
        $manifests.Count | Should Be 1
        (Get-Transaction $environment).Name | Should Not BeNullOrEmpty
    }

    It "restores all legacy paths when health verification fails" {
        $environment = New-TestEnvironment "failed-health"
        Install-TestPackage $environment | Out-Null
        $transaction = Get-Transaction $environment
        $healthPath = Join-Path $environment.Documents "PhilsFusionTools\health.json"
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $healthPath) | Out-Null
        @{
            status = "healthy"
            version = "2.0.0"
            package_fingerprint = ("0" * 64)
            groups = 7
            public_commands = 25
            startup_errors = @()
        } | ConvertTo-Json | Set-Content -LiteralPath $healthPath

        {
            & $finalizer `
                -TransactionPath $transaction.FullName `
                -DocumentsRoot $environment.Documents `
                -ObservedProcessNames @()
        } | Should Throw

        foreach ($path in $environment.LegacyPaths) {
            Test-Path -LiteralPath (Join-Path $path "sentinel.txt") | Should Be $true
        }
        Test-Path -LiteralPath (Join-Path $environment.AddIns "PhilsFusionTools") |
            Should Be $false
    }

    It "finalizes only when health matches the installed runtime" {
        $environment = New-TestEnvironment "healthy"
        Install-TestPackage $environment | Out-Null
        $transaction = Get-Transaction $environment
        $statePath = Join-Path $transaction.FullName "state.json"
        $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        $healthPath = Join-Path $environment.Documents "PhilsFusionTools\health.json"
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $healthPath) | Out-Null
        @{
            status = "healthy"
            version = "2.0.0"
            package_fingerprint = $state.package_tree_hash
            groups = 7
            public_commands = 25
            startup_errors = @()
        } | ConvertTo-Json | Set-Content -LiteralPath $healthPath

        & $finalizer `
            -TransactionPath $transaction.FullName `
            -DocumentsRoot $environment.Documents `
            -ObservedProcessNames @() | Out-Null

        $completed = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        $completed.status | Should Be "complete"
        Test-Path -LiteralPath $completed.legacy_archive | Should Be $true
        Test-Path -LiteralPath "$($completed.receipt_path).sha256" | Should Be $true
    }
}
