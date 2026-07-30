[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$addinRoot = Join-Path $root "Addin\PhilsFusionTools"
$pycacheRoot = Join-Path $root "build\pycache"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Development environment is missing. Run: py -3.10 -m venv .venv"
}

$env:PYTHONPYCACHEPREFIX = $pycacheRoot

& $python -m pytest -v
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$ruffTargets = @((Join-Path $root "tests"))
if (Test-Path -LiteralPath $addinRoot -PathType Container) {
    $ruffTargets += $addinRoot
}
& $python -m ruff check @ruffTargets
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if (Test-Path -LiteralPath $addinRoot -PathType Container) {
    & $python -m compileall -q $addinRoot
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

git -C $root diff --check
exit $LASTEXITCODE
