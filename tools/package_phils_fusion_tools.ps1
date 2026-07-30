[CmdletBinding()]
param(
    [switch]$Foundation,
    [switch]$Production,
    [switch]$Install
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($Install) {
    throw "The packager never installs or changes Fusion scan paths."
}
if ($Foundation -eq $Production) {
    throw "Specify exactly one of -Foundation or -Production."
}

$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$sourceRoot = Join-Path $repoRoot "Addin\PhilsFusionTools"
$buildRoot = Join-Path $repoRoot "build"
$artifact = if ($Production) { "production" } else { "foundation" }
$stageRoot = Join-Path $buildRoot "_phils-fusion-tools-$artifact"
$stageAddin = Join-Path $stageRoot "PhilsFusionTools"
$allowlistPath = Join-Path $repoRoot "release\package-allowlist.txt"
$packageName = if ($Production) {
    "PhilsFusionTools-2.0.0.zip"
}
else {
    "PhilsFusionTools-2.0.0-foundation.zip"
}
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

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Python quality environment was not found: $python"
}
$validator = Join-Path $repoRoot "tools\validate_runtime.py"
& $python $validator $stageAddin
if ($LASTEXITCODE -ne 0) {
    throw "Staged runtime validation failed."
}

$treeRelativeFiles = @(
    $runtimeEntries |
        ForEach-Object { $_.Substring("PhilsFusionTools/".Length) }
)
$treeHash = Get-RuntimeTreeHash -Root $stageAddin -RelativeFiles $treeRelativeFiles
$buildInfo = [ordered]@{
    version = "2.0.0"
    artifact = $artifact
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

$zipBuilder = Join-Path $repoRoot "tools\build_runtime_zip.py"
& $python $zipBuilder $stageAddin $packagePath
if ($LASTEXITCODE -ne 0) {
    throw "Production archive creation failed."
}

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
if ($Production) {
    $legacyRoots = @(
        $archiveNames |
            Where-Object {
                $_.StartsWith("PhilsDesignTools/", [StringComparison]::OrdinalIgnoreCase) -or
                $_.StartsWith("PhilsBom.bundle/", [StringComparison]::OrdinalIgnoreCase)
            }
    )
    if ($legacyRoots.Count -gt 0) {
        throw "Production package contains a legacy root."
    }
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
