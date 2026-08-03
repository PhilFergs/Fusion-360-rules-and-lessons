# Phils Fusion Tools 2.0.0 Verification

Verified on Windows on 2026-07-30.

## Release Identity

- Package: `build\PhilsFusionTools-2.0.0.zip`
- Package SHA-256:
  `9c12f8c37d28685d6c5017c22dbe17419b1ebe9ecfc78802ff3a4a622c8a4e7d`
- Runtime source commit: `ba61c0f913508716f62c07651bd969ee4ec359bc`
- Runtime tree SHA-256:
  `2128386b2a312f86a964f8c16d0e1cb4d30d50a781786b301f48371a380a2980`
- Production archive entries: 161

## Automated Gate

- Pytest: 114 passed.
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

User testing then exposed a Fusion metadata behavior change: Part Number and
Description setters can return without an exception while an unsaved internal
component has not yet been registered with Fusion's cloud metadata service.
The command now:

1. Refuses to run until the design and latest component changes are saved.
2. Explains that the user must save, wait for sync, and rerun.
3. Reads every property back before incrementing a success count.
4. Reports a visible verification failure if Fusion does not persist a value.

The corrected package passed a second transactional upgrade:

- Upgrade transaction:
  `C:\Users\phil9\Documents\PhilsFusionTools\MigrationTransactions\20260730-130630-0a772a1f`
- Preserved prior unified install:
  `C:\Users\phil9\Documents\PhilsFusionTools\LegacyArchive\20260730-130630-0a772a1f`
- Upgrade receipt SHA-256:
  `5654245e1e881414c21d757ccc06f044937c764a44b705e94a17d359d9f6768f`

Further live testing on 2026-08-03 exposed Fusion-generated timestamp part
numbers and a cloud registration race. In the test design, `PFC1` initially
showed `2026-08-03-08-00-44-487`. The repaired command waits until every target
component has cloud metadata, then applies the simplified component name and
verifies read-back. The live result changed `PFC1` to `PFC1`, set three delayed
part numbers, and reported zero part-number failures. A transient `EA1`
Description write then succeeded on retry; the next live run reported one
description set, zero description failures, and all six part numbers matched.

The final Windows upgrade passed startup health and was finalized:

- Upgrade transaction:
  `C:\Users\phil9\Documents\PhilsFusionTools\MigrationTransactions\20260803-084617-d71ceb82`
- Preserved prior unified install:
  `C:\Users\phil9\Documents\PhilsFusionTools\LegacyArchive\20260803-084617-d71ceb82`
- Upgrade receipt SHA-256:
  `7dbfe3c28599c977748c2cbf2dd8fa9b19b21a89fc7255c0e5e96959a97ba2fe`

## Residual Scope

The startup, registration, migration, packaging, rollback, and non-Fusion
domain behavior are verified. The live check did not execute every geometry
command against every possible Fusion model topology. Destructive commands
therefore retain preflight summaries, explicit confirmation, and per-item
failure reporting rather than claiming all possible document states are
exhaustively proven.
