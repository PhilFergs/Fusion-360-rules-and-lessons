# Phils Fusion Tools 2.0.0 Verification

Verified on Windows on 2026-07-30.

## Release Identity

- Package: `build\PhilsFusionTools-2.0.0.zip`
- Package SHA-256:
  `0b5d2eaa739b16f03a81cbaa64cb342ed79b9fed3d28b41bde73fe6fa62b4ef8`
- Runtime source commit: `c71f6e1c49f9a91afa8a73d01eef781300cbfb3d`
- Runtime tree SHA-256:
  `2b36c5d354bdb12987b2564cc68a1deb9065bed7e082daf368ff37699ab123b6`
- Production archive entries: 160

## Automated Gate

- Pytest: 104 passed.
- Ruff: passed.
- Python compile validation: passed.
- Git whitespace validation: passed.
- Pester installer contract: 6 passed, 0 failed.
- Production package exact-allowlist validation: passed.
- Independent pre-2.0 rollback verification: passed.

The installer contract covers Fusion-process refusal, bad package hash refusal,
default artifact resolution, six-path quarantine, failed-health rollback after
Python cache creation, and healthy finalization.

## Live Fusion Check

Fusion launched the installed add-in and wrote:

```text
C:\Users\phil9\Documents\PhilsFusionTools\health.json
```

The read-back reported:

- Status: `healthy`
- Version: `2.0.0`
- Groups: 7
- Public commands: 25
- Compatibility aliases: 29
- Startup errors: 0
- Runtime fingerprint: matched the installed tree

The installed location is:

```text
C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsFusionTools
```

## Migration Evidence

- Completed transaction:
  `C:\Users\phil9\Documents\PhilsFusionTools\MigrationTransactions\20260730-124638-e35707ec`
- Legacy archive:
  `C:\Users\phil9\Documents\PhilsFusionTools\LegacyArchive\20260730-124638-e35707ec`
- Archived legacy locations: 6
- Migration receipt SHA-256:
  `0cb72780f3a8b1d800213ee84b793e6321b0a98aed051d1227923a14731d75ff`
- Active manifests across the three former scan roots: 1
- Verified rollback:
  `C:\Users\phil9\Documents\PhilsFusionTools-Rollback\20260730-111056`

## Live Defects Found And Closed

The first real invocation exposed two gaps that isolated tests had not modeled:

1. Windows PowerShell evaluated installer path defaults before `$PSScriptRoot`
   was available.
2. Fusion startup exposed a missing settings schema export and generated
   `__pycache__` files that correctly caused the original strict rollback hash
   to refuse automatic removal.

Regression tests were added before each repair. The failed transaction was
rolled back with all six legacy paths restored, the repaired package was built,
and a new transaction then passed live startup and finalization.

## Residual Scope

The startup, registration, migration, packaging, rollback, and non-Fusion
domain behavior are verified. The live check did not execute every geometry
command against every possible Fusion model topology. Destructive commands
therefore retain preflight summaries, explicit confirmation, and per-item
failure reporting rather than claiming all possible document states are
exhaustively proven.
