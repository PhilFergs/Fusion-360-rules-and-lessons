# Phils Fusion Tools 2.0 Design

## Status

Approved for implementation planning on 2026-07-30.

## Product

The unified product is **Phils Fusion Tools 2.0.0**, a Windows-certified Autodesk Fusion add-in that replaces the separate PhilsDesignTools and PhilsBom installations.

The product provides one installation, one manifest, one lifecycle, one toolbar panel, one settings system, and one release identity. Existing geometry and fabrication behaviour is preserved where it is reliable, while unsafe operations and duplicated infrastructure are replaced behind tested interfaces.

## Goals

- Combine PhilsDesignTools and PhilsBom into one add-in.
- Preserve the useful behaviour and local-only profile work already present.
- Correct every critical and high-severity defect identified in the 2026-07-30 audit.
- Prevent silent partial operations, unconfirmed destructive changes, and false success messages.
- Provide a grouped, consistent Fusion user interface with balanced safety prompts.
- Make BOM and file exports deterministic, valid, collision-safe, and verifiable.
- Establish automated tests, clean packaging, reproducible releases, and exact installed-version provenance.
- Preserve a complete, hash-verified rollback path before production files are replaced.

## Non-Goals

- macOS certification for version 2.0.0.
- A from-scratch rewrite of all proven Fusion geometry logic.
- Cloud telemetry or collection of design contents.
- Removal of rollback archives during the 2.0.0 release process.
- A permanent compatibility layer for every legacy command ID.

## Supported Environment

- Operating system: Windows.
- Host: Autodesk Fusion using its CPython add-in engine.
- Install location:
  `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsFusionTools`
- Package identity: `PhilsFusionTools`.
- Initial unified version: `2.0.0`.

The code should remain portable where that does not complicate or weaken Windows behaviour, but version 2.0.0 makes no macOS certification claim.

## Architecture

### Single Add-In

Phils Fusion Tools uses one manifest and one entry point. BOM becomes a native module of the unified add-in rather than a second add-in, bundle, process, or lifecycle.

The add-in is divided into focused units:

- `app`: startup, shutdown, shared context, command registry, toolbar registration, and compatibility aliases.
- `services`: settings, structured logging, validation, safety prompts, file transactions, diagnostics, and version information.
- `core`: Fusion-independent BOM, naming, profile, transform, export, and operation-planning logic.
- `commands/create`: EA, SHS, RHS, I Beam, PFC, and C Channel workflows.
- `commands/modify`: rotate, split, move, wireframe, hole cut, and component replacement workflows.
- `commands/fabricate`: stub arms, stub pairs, brackets, hole outputs, naming, and description workflows.
- `commands/export`: BOM, multi-part CAD, CSV, and DXF workflows.
- `commands/cleanup`: structure normalisation, length-name removal, metadata changes, and other high-impact maintenance workflows.
- `resources`: icons and local help assets.

Fusion API calls remain at adapter and command boundaries. Testable calculations, validation, grouping, escaping, naming, path planning, and change-plan construction live in pure Python modules.

### Command Registry

A central registry is the source of truth for:

- Command ID.
- Display name and tooltip.
- Toolbar group and order.
- Resource directory.
- Handler factory.
- Risk classification.
- Whether preflight and confirmation are required.
- Legacy compatibility aliases.

Startup registers commands from the registry. Shutdown removes controls, definitions, event handlers, and retained references through the same registry. Repeated stop/start cycles must not accumulate handlers.

### Shared Services

The add-in uses common services instead of command-specific copies:

- Versioned settings with schema validation and atomic writes.
- Structured local logs with bounded retention.
- Consistent user-facing errors and completion reports.
- Selection and dimension validation.
- Preflight plan rendering and balanced safety confirmation.
- Collision-safe, atomic file output.
- Version, commit, package fingerprint, install-path, and diagnostics reporting.

## User Interface

The Fusion toolbar panel is named **Phils Fusion Tools** and uses the approved Grouped Workflows layout.

### Toolbar Groups

- **BOM:** prominent one-click access to the primary BOM workflow.
- **Create:** EA, SHS, RHS, I Beam, PFC, and C Channel.
- **Modify:** rotate, split, move, wireframe, hole cut, and component replacement.
- **Fabricate:** stub arms, bracket tools, hole tools, naming, and descriptions.
- **Export:** multi-part CAD, BOM, CSV, and DXF.
- **Cleanup:** normalise structure, remove length names, bulk metadata changes, and other high-impact tools.
- **Help:** version, installation health, diagnostics, logs, settings reset, migration status, and rollback information.

Routine member creation remains fast and does not gain unnecessary confirmation dialogs.

### Balanced Safety Prompts

Destructive, bulk, overwrite, and structure-changing operations require:

1. A preflight summary of the intended changes.
2. Validation of every selected entity and numeric input.
3. Counts, destinations, collisions, and skipped items.
4. Explicit confirmation before execution.
5. A completion report that separates successes, skips, failures, and recovery actions.

The add-in must not report success unless the requested result is verified.

### Consistency Improvements

- Common terminology across all commands.
- Inline dimension and selection guidance.
- Remembered safe defaults.
- Predictable button labels and dialog ordering.
- Clear tooltips describing scope and side effects.
- Collision-safe suggested filenames.
- Local diagnostics packaging that excludes design geometry and user document contents.
- Actionable startup alerts only; successful health checks remain unobtrusive.

## Operation Safety

High-impact commands use a two-phase model.

### Preflight

Preflight resolves selections, validates dimensions and assembly context, constructs an immutable change plan, identifies file collisions, and presents the exact scope to the user.

Preflight does not change the Fusion design or final output files.

### Execution

Execution consumes the approved plan. It records the original state needed for recovery, verifies each change, and stops safely when an invariant fails.

Required protections include:

- Component moves record the original parent and world transform and restore both on failure.
- Component normalisation retains the original wrapper until every child move and transform is verified.
- Split-body deletion requires a matching split-session identity and refuses unrelated bodies.
- New components or bodies created by a failed workflow are removed where Fusion permits safe cleanup.
- Bulk metadata changes provide before/after counts and do not silently overwrite unsupported components.
- Existing export files are never overwritten without explicit confirmation.

Fusion operations that cannot be made fully transactional must fail conservatively, preserve the original entity where possible, and clearly describe any manual recovery requirement.

## BOM Design

BOM data collection, grouping, column selection, unit conversion, and serialization are separated.

The BOM core must:

- Include root-component bodies when no occurrences exist.
- Recalculate linked-component state per occurrence and remain order-independent.
- Respect final body visibility when hidden items are excluded.
- Use stable entity identities for grouping instead of cleaned display names alone.
- Preserve distinct parts whose names differ by meaningful numeric parentheticals.
- Keep grouping, item numbering, and output ordering deterministic.
- Return structured success or failure results to the command layer.

Serializers must use appropriate libraries or escaping rules for CSV, JSON, XML, and XLSX. Spreadsheet-bound text that begins with formula control characters is neutralised. Double quotes in legitimate values are preserved and correctly escaped.

Temporary output is written beside the target, validated, and atomically promoted only after successful serialization.

## Profile And Geometry Design

The profile tools share a parameterised profile-generation core while retaining focused command adapters and profile definitions.

All profile commands validate:

- Positive dimensions and thickness.
- Physically valid wall/flange/web relationships.
- Supported section selections.
- Extra-length limits.
- Sketch-line validity.
- Assembly context and transform requirements.

SHS/RHS and channel-family duplication is consolidated without changing proven orientation behaviour. Existing local C Channel, I Beam, and PFC work is preserved and brought under source control.

## Compatibility And Migration

Version 2.0.0 provides one-release compatibility aliases for existing Design Tools command IDs. Aliases route to the new handlers and are not duplicated as visible toolbar commands.

Existing BOM settings are imported into the new versioned settings schema on first successful migration. Original settings are retained in the rollback archive and are not deleted.

The migration records:

- Previous install paths and fingerprints.
- Imported settings source and schema.
- Compatibility aliases activated.
- New version, source commit, and package fingerprint.
- Backup and rollback locations.

The compatibility layer is reviewed for removal in the next major release after users have migrated shortcuts and workflows.

## Backup And Rollback

Rollback creation is the first implementation gate before production installation changes.

The rollback set contains:

- Every installed PhilsDesignTools and PhilsBom folder, including misplaced duplicates.
- Relevant settings and logs.
- A complete source snapshot including tracked modifications and untracked files.
- A Git bundle containing all branches and history.
- Binary diffs and a working-tree inventory.
- SHA-256 hashes for every archived file.
- Environment, path, version, and commit metadata.
- A restore script with dry-run and apply modes.

The rollback set is stored under a timestamped `PhilsFusionTools-Rollback` directory outside Fusion scan paths. A verification pass proves archive readability and file hashes before implementation proceeds.

Old installations are moved out of Fusion scan paths only after:

- Backup verification passes.
- The new package passes static and staging checks.
- The installation plan confirms Fusion is closed.

If runtime startup or registration fails, the restore script reinstates the exact archived folders and settings.

## Installer And Packaging

The installer:

- Requires Fusion to be closed before replacement.
- Supports dry-run, install, verify, and rollback actions.
- Refuses to proceed when backup or package hash validation fails.
- Stages files before swapping the installed directory.
- Removes no rollback data.
- Archives old add-ins outside scan paths rather than deleting them.
- Writes an installation manifest with version, commit, package fingerprint, timestamp, and source archive hashes.

Release packages use an explicit allow-list. Backups, bytecode, caches, logs, test data, development notes, build intermediates, and visual-companion files are excluded.

The release output includes:

- `PhilsFusionTools-2.0.0.zip`.
- Windows installer package.
- Rollback package and restore script.
- SHA-256 manifest.
- Release notes and installation guide.

## Testing

### Automated Tests

Pure-Python unit tests cover:

- BOM root bodies, linked traversal, visibility, grouping, item numbering, and deterministic order.
- CSV, JSON, XML, and XLSX escaping and validation.
- Spreadsheet formula neutralisation.
- Profile dimensions, names, and section validation.
- File collision planning and atomic promotion.
- Settings migration and schema validation.
- Command registry uniqueness and lifecycle cleanup.
- Move, normalise, and split preflight and rollback plans.
- Package allow-list and version consistency.
- Installer dry-run and rollback manifests.

Contract tests use controlled Fusion API adapters for command registration, selection handling, lifecycle cleanup, and operation execution boundaries.

### Static Gates

- Python compilation.
- `pytest`.
- Ruff linting.
- Clean release-tree and package-content checks.
- Manifest, release version, commit, and fingerprint consistency.
- No critical or high-severity static-audit findings.

### Fusion Smoke Matrix

Every command is exercised on sacrificial Windows Fusion designs with:

- Valid top-level selections.
- Nested assembly selections where supported.
- Invalid and empty selections.
- Boundary dimensions.
- Cancelled dialogs.
- Partial-operation failure simulation where practical.
- Existing output-file collisions.
- Repeated add-in stop/start cycles.

Release requires every command's normal path and defined failure paths to pass. Fusion-dependent limitations that cannot be automated are documented as manual evidence.

## Release Process

1. Verify and preserve the original state.
2. Implement the shared platform and test infrastructure.
3. Integrate and repair BOM.
4. Migrate Design Tools commands and consolidate duplicated workflows.
5. Add the grouped UI, diagnostics, help, and compatibility aliases.
6. Run automated gates.
7. Run the Fusion smoke matrix on sacrificial designs.
8. Build from a clean commit.
9. Stage and verify installation.
10. Archive legacy scan-path copies.
11. Confirm startup, toolbar registration, command execution, settings migration, and diagnostics.
12. Tag the exact source commit and publish artifacts generated from that commit.

The installed Help and Diagnostics screen displays version `2.0.0`, source commit, package fingerprint, install path, settings schema, and migration state so future audits can compare the running installation with GitHub.

## Delivery Decomposition

Implementation is divided into independently testable plans:

1. Rollback capture, source preservation, clean worktree, and test harness.
2. Unified application shell, command registry, services, settings migration, and grouped toolbar.
3. BOM extraction, correctness fixes, serializers, and BOM UI integration.
4. Design Tools critical safety fixes and command migration.
5. Profile-family consolidation and local profile integration.
6. Export safety, cleanup workflows, diagnostics, and compatibility aliases.
7. Installer, rollback, packaging, release provenance, and documentation.
8. Fusion smoke validation, staged installation, release build, and GitHub reconciliation.

Each plan must produce working, testable software and pass its own review gate before the next plan changes production installation state.

## Acceptance Criteria

- Only one Phils Fusion Tools add-in is present in Fusion scan paths.
- The grouped toolbar registers once and cleans up completely on stop.
- Existing BOM settings migrate without loss.
- Compatibility aliases route old shortcuts without adding duplicate visible controls.
- All automated checks pass.
- Every command passes the Windows Fusion smoke matrix.
- No known critical or high-severity defects remain.
- Release archives contain no backups, caches, logs, or build intermediates.
- The installed version, GitHub tag, source commit, release archive, and fingerprint agree.
- The verified rollback restores the exact pre-2.0 installation and settings.

Absolute absence of future defects cannot be guaranteed. The release standard is no known critical or high-severity defects, complete automated and Fusion smoke evidence, conservative failure handling, and a verified rollback path.
