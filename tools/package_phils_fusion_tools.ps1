[CmdletBinding()]
param(
    [switch]$Foundation,
    [switch]$Install
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($Install) {
    throw "This foundation packager never installs or changes Fusion scan paths."
}
if (-not $Foundation) {
    throw "Specify -Foundation. Production packaging is not enabled yet."
}

$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$sourceRoot = Join-Path $repoRoot "Addin\PhilsFusionTools"
$buildRoot = Join-Path $repoRoot "build"
$stageRoot = Join-Path $buildRoot "_phils-fusion-tools-foundation"
$stageAddin = Join-Path $stageRoot "PhilsFusionTools"
$allowlistPath = Join-Path $repoRoot "release\package-allowlist.txt"
$packageName = "PhilsFusionTools-2.0.0-foundation.zip"
$packagePath = Join-Path $buildRoot $packageName
$hashPath = "$packagePath.sha256"

function Remove-CheckedTree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LiteralPath,
        [Parameter(Mandatory = $true)]
        [string]$AllowedParent
    )

    $target = [IO.Path]::GetFullPath($LiteralPath)
    $parent = [IO.Path]::GetFullPath($AllowedParent).TrimEnd("\") + "\"
    if (-not $target.StartsWith($parent, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove path outside build root: $target"
    }
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}

function Get-HexHash {
    param([byte[]]$Bytes)

    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Get-RuntimeTreeHash {
    param(
        [string]$Root,
        [string[]]$RelativeFiles
    )

    $records = foreach ($relative in ($RelativeFiles | Sort-Object)) {
        $nativeRelative = $relative.Replace("/", "\")
        $filePath = Join-Path $Root $nativeRelative
        $fileHash = (Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash.ToLowerInvariant()
        "$relative`0$fileHash"
    }
    $canonical = ($records -join "`n") + "`n"
    return Get-HexHash -Bytes ([Text.Encoding]::UTF8.GetBytes($canonical))
}

$dirtyRuntime = @(& git -C $repoRoot status --porcelain -- Addin/PhilsFusionTools)
if ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect Git status."
}
if ($dirtyRuntime.Count -gt 0) {
    throw "Unified runtime source is dirty. Commit or revert it before packaging."
}

$commit = (& git -C $repoRoot log -1 --format=%H -- Addin/PhilsFusionTools).Trim()
if ($LASTEXITCODE -ne 0 -or $commit -notmatch "^[0-9a-f]{40}$") {
    throw "Unable to resolve the unified runtime source commit."
}

$allowedEntries = @(
    Get-Content -LiteralPath $allowlistPath |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ -and -not $_.StartsWith("#") }
)
if ($allowedEntries.Count -eq 0) {
    throw "Package allow-list is empty."
}
if ($allowedEntries.Count -ne ($allowedEntries | Select-Object -Unique).Count) {
    throw "Package allow-list contains duplicate entries."
}

$buildInfoEntry = "PhilsFusionTools/build-info.json"
if ($buildInfoEntry -notin $allowedEntries) {
    throw "Package allow-list must include $buildInfoEntry."
}

Remove-CheckedTree -LiteralPath $stageRoot -AllowedParent $buildRoot
New-Item -ItemType Directory -Path $stageAddin -Force | Out-Null

$runtimeEntries = @($allowedEntries | Where-Object { $_ -ne $buildInfoEntry })
foreach ($entry in $runtimeEntries) {
    if (-not $entry.StartsWith("PhilsFusionTools/", [StringComparison]::Ordinal)) {
        throw "Allow-list entry is outside the package root: $entry"
    }

    $sourceRelative = $entry.Substring("PhilsFusionTools/".Length).Replace("/", "\")
    $sourcePath = Join-Path $sourceRoot $sourceRelative
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        throw "Allow-listed source file does not exist: $entry"
    }

    $destinationPath = Join-Path $stageAddin $sourceRelative
    $destinationDirectory = Split-Path -Parent $destinationPath
    New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
    Copy-Item -LiteralPath $sourcePath -Destination $destinationPath
}

$treeRelativeFiles = @(
    $runtimeEntries |
        ForEach-Object { $_.Substring("PhilsFusionTools/".Length) }
)
$treeHash = Get-RuntimeTreeHash -Root $stageAddin -RelativeFiles $treeRelativeFiles
$buildInfo = [ordered]@{
    version = "2.0.0"
    artifact = "foundation"
    commit = $commit
    built_at_utc = [DateTime]::UtcNow.ToString("o")
    package_tree_hash = $treeHash
    package_tree_hash_scope = "all allow-listed runtime files except build-info.json"
}
$buildInfoJson = $buildInfo | ConvertTo-Json -Depth 4
[IO.File]::WriteAllText(
    (Join-Path $stageAddin "build-info.json"),
    $buildInfoJson + "`n",
    [Text.UTF8Encoding]::new($false)
)

New-Item -ItemType Directory -Path $buildRoot -Force | Out-Null
foreach ($oldArtifact in @($packagePath, $hashPath)) {
    if (Test-Path -LiteralPath $oldArtifact) {
        Remove-Item -LiteralPath $oldArtifact -Force
    }
}

Compress-Archive -LiteralPath $stageAddin -DestinationPath $packagePath -CompressionLevel Optimal

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($packagePath)
try {
    $archiveNames = @($archive.Entries | ForEach-Object { $_.FullName.Replace("\", "/") })
}
finally {
    $archive.Dispose()
}

$unexpected = @($archiveNames | Where-Object { $_ -notin $allowedEntries })
$missing = @($allowedEntries | Where-Object { $_ -notin $archiveNames })
if ($unexpected.Count -gt 0 -or $missing.Count -gt 0) {
    throw "Package content differs from the allow-list."
}

$packageHash = (Get-FileHash -LiteralPath $packagePath -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText(
    $hashPath,
    "$packageHash  $packageName`n",
    [Text.ASCIIEncoding]::new()
)

Remove-CheckedTree -LiteralPath $stageRoot -AllowedParent $buildRoot

[pscustomobject]@{
    Package = $packagePath
    Sha256 = $packageHash
    Files = $archiveNames.Count
    Commit = $commit
    TreeHash = $treeHash
    InstallChanged = $false
} | Format-List
