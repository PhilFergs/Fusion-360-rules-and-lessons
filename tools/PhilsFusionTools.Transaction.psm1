Set-StrictMode -Version Latest

function Get-UtcTimestamp {
    return [DateTime]::UtcNow.ToString("o")
}

function Get-HexHash {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)

    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Assert-PathWithin {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$AllowedRoot
    )

    $candidate = [IO.Path]::GetFullPath($Path)
    $root = [IO.Path]::GetFullPath($AllowedRoot).TrimEnd("\") + "\"
    if (-not $candidate.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside its allowed root: $candidate"
    }
    return $candidate
}

function Assert-FusionClosed {
    param([AllowNull()][string[]]$ObservedProcessNames = $null)

    $names = if ($null -eq $ObservedProcessNames) {
        @(Get-Process -ErrorAction SilentlyContinue | ForEach-Object { $_.ProcessName })
    }
    else {
        @($ObservedProcessNames)
    }
    $fusionNames = @("Fusion", "Fusion360", "FusionLauncher", "FusionService", "AdskFusion")
    $running = @($names | Where-Object { $_ -in $fusionNames } | Select-Object -Unique)
    if ($running.Count -gt 0) {
        throw "Autodesk Fusion must be closed. Running: $($running -join ', ')"
    }
}

function Read-KeyValueFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    $values = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            $values[$parts[0].Trim()] = $parts[1].Trim()
        }
    }
    return $values
}

function Write-JsonAtomic {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )

    $target = [IO.Path]::GetFullPath($Path)
    $parent = Split-Path -Parent $target
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $temporary = "$target.tmp-$([Guid]::NewGuid().ToString('N'))"
    try {
        $json = $Value | ConvertTo-Json -Depth 12
        [IO.File]::WriteAllText($temporary, $json + "`n", [Text.UTF8Encoding]::new($false))
        Get-Content -LiteralPath $temporary -Raw | ConvertFrom-Json | Out-Null
        Move-Item -LiteralPath $temporary -Destination $target -Force
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Get-RuntimeTreeHash {
    param([Parameter(Mandatory = $true)][string]$Root)

    $resolvedRoot = [IO.Path]::GetFullPath($Root).TrimEnd("\")
    $records = @(
        Get-ChildItem -LiteralPath $resolvedRoot -File -Recurse |
            Where-Object {
                $_.Name -ne "build-info.json" -and
                $_.Extension -ne ".pyc" -and
                $_.FullName -notmatch "[\\/]__pycache__[\\/]"
            } |
            ForEach-Object {
                $relative = $_.FullName.Substring($resolvedRoot.Length + 1).Replace("\", "/")
                $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                [pscustomobject]@{ Relative = $relative; Record = "$relative`0$hash" }
            } |
            Sort-Object Relative |
            ForEach-Object { $_.Record }
    )
    $canonical = ($records -join "`n") + "`n"
    return Get-HexHash -Bytes ([Text.Encoding]::UTF8.GetBytes($canonical))
}

function Get-LegacyMappings {
    param([Parameter(Mandatory = $true)][string]$AppDataRoot)

    return @(
        [ordered]@{
            label = "applicationplugins-philsbom"
            original_path = Join-Path $AppDataRoot "Autodesk\ApplicationPlugins\PhilsBom.bundle"
            kind = "legacy"
        },
        [ordered]@{
            label = "api-addins-philsbom"
            original_path = Join-Path $AppDataRoot "Autodesk\Autodesk Fusion 360\API\AddIns\PhilsBom.bundle"
            kind = "legacy"
        },
        [ordered]@{
            label = "autorun-philsbom"
            original_path = Join-Path $AppDataRoot "Autodesk\Autodesk Fusion 360\MyScripts\Autorun\PhilsBom.bundle"
            kind = "legacy"
        },
        [ordered]@{
            label = "api-addins-philsdesigntools"
            original_path = Join-Path $AppDataRoot "Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools"
            kind = "legacy"
        },
        [ordered]@{
            label = "api-addins-philsdesigntools-backups"
            original_path = Join-Path $AppDataRoot "Autodesk\Autodesk Fusion 360\API\AddIns\_PhilsDesignTools_Backups"
            kind = "legacy"
        },
        [ordered]@{
            label = "fusion-installer-backups"
            original_path = Join-Path $AppDataRoot "Autodesk\FusionInstallerBackups"
            kind = "legacy"
        }
    )
}

function Restore-TransactionMappings {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][string]$TransactionPath
    )

    $conflictRoot = Join-Path $TransactionPath "restore-conflicts"
    $mappings = @($State.mappings)
    [array]::Reverse($mappings)
    foreach ($mapping in $mappings) {
        $original = Assert-PathWithin `
            -Path $mapping.original_path `
            -AllowedRoot $State.app_data_root
        $quarantine = Assert-PathWithin `
            -Path $mapping.quarantine_path `
            -AllowedRoot $TransactionPath
        if (-not (Test-Path -LiteralPath $quarantine)) {
            continue
        }
        if (Test-Path -LiteralPath $original) {
            New-Item -ItemType Directory -Force -Path $conflictRoot | Out-Null
            $conflict = Join-Path $conflictRoot (
                "$($mapping.label)-$([Guid]::NewGuid().ToString('N'))"
            )
            Move-Item -LiteralPath $original -Destination $conflict
        }
        New-Item -ItemType Directory -Force -Path (
            Split-Path -Parent $original
        ) | Out-Null
        Move-Item -LiteralPath $quarantine -Destination $original
    }
}

Export-ModuleMember -Function *
