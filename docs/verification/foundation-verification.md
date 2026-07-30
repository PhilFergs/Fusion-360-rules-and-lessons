# Phils Fusion Tools 2.0 Foundation Verification

Verified on 2026-07-30 in the isolated Windows worktree. This artifact is a
development foundation only. It does not install itself and is not a production
release.

## Rollback Evidence

- Rollback root:
  `C:\Users\phil9\Documents\PhilsFusionTools-Rollback\20260730-111056`
- Verified rollback manifest SHA-256:
  `898b56dac144dbc432e46babe364654e66750377e9bee99e4cdce2aa9eae4223`
- `verify-rollback.ps1` result: passed.
- Restore script dry-run result: passed with no writes.
- Restore apply mode was intentionally not run.

## Source Evidence

- Worktree:
  `C:\Users\phil9\OneDrive\Documents\01-vsc\projects\fusion-360-rules-and-lessons-worktrees\phils-fusion-tools-2`
- Branch: `codex/phils-fusion-tools-2.0`
- Foundation package tooling commit:
  `df5ddfe1bba701ed8af0ff384d3f710e93396ef0`
- Unified runtime source commit:
  `ca6b256ad0b250aacc964aac1f5f8e904d0044b9`
- Python: `3.10.11`
- pytest: `8.4.2`
- Ruff: `0.12.12`

## Quality Evidence

- Full test suite: 34 passed.
- Ruff: passed.
- Python compileall for `Addin\PhilsFusionTools`: passed.
- Git diff whitespace check: passed.
- Unified release-tree hygiene check: passed.
- Manifest contract: passed for ID `PhilsFusionTools`, version `2.0.0`,
  startup enabled, Windows support, CPython, and entry point
  `PhilsFusionTools.py`.
- Lifecycle tests: passed for idempotent start/stop, reverse cleanup, retained
  handler cleanup, and rollback after a partial startup failure.

## Package Evidence

- Artifact: `build\PhilsFusionTools-2.0.0-foundation.zip`
- Artifact SHA-256:
  `09e9fd034eb7ef64428ec724246c84edca27059143e6561a8035d3d14b3e80ad`
- Runtime tree SHA-256:
  `146702f0e969b1227d6cec66507bbc06a452bb4171dc26e43dcef60b51b1c259`
- Size: 11,069 bytes.
- File count: 13.
- Allow-list comparison: exact match.
- Forbidden cache, test, log, and backup files: none.
- SHA-256 sidecar comparison: passed.
- Installer action: refused by design.

## Installed-State Check

The foundation packager wrote only below the ignored worktree `build`
directory. It did not write to an Autodesk or Fusion scan path.

A SHA-256 comparison against the verified rollback archive found:

- All 44 files in the ApplicationPlugins BOM bundle matched.
- All 47 files in the API AddIns BOM bundle matched.
- All 46 files in the Autorun BOM bundle matched.
- 214 of 215 files in the active PhilsDesignTools add-in matched.
- The only changed active file was `PhilsDesignTools.log`. It gained normal
  `started` and `stopped` entries at 11:17 and 11:20 after the backup.
- No PhilsDesignTools Python source, manifest, resource, or executable asset
  changed.
- Fusion was not running at the end of this check.

The mutable log difference is runtime evidence, not an installation change.
The verified rollback still contains its original pre-foundation log.
