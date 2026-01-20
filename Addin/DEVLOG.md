# DEVLOG

Ongoing development notes for the Phils Design Tools add-in.

## Update checklist
- Add a brief entry to this DEVLOG for each change set.
- Update CHANGELOG.md under Unreleased for user-facing changes.

## 2026-01-02
- Added add-in scoped CHANGELOG.md, DEVLOG.md, and README.md for development tracking.
- Added WORKFLOW.md capturing the workflow map and agreed rules.
- Renamed the add-in to Phils Design Tools and updated IDs/paths.
- Added logger usage across command handlers and startup/shutdown.
- Added USER_GUIDE.rtf for onboarding users to the workflow.
- Added USER_GUIDE.docx for Word-native distribution.
- Fixed EA rotate axis drift by selecting the planar face with hole circles farthest from the body center and deriving the axis from closest points on the two holes; added debug logging to capture axis/pivot values.
- Note to self: always bind face geometry (e.g., `plane`) in loops before using it, and avoid mixing edges from multiple faces when defining rotation axes.
- Added `VERSION_LOG.md` and `tools/deploy_addin.ps1` to log uploads and back up the active add-in before deployment.
- Documented versioning and deployment steps in WORKFLOW.md.

## 2026-01-06
- Added Split Body (Keep Side) command with post-split keep selection (positive, negative, or all).
- Added auto-deploy watcher script and optional no-backup deploy flag for faster iteration.
- Logged usage details for all existing commands via smg_logger.log_command.
- Exposed Extend split tool option and added guardrails for split failures.
- Reworked Split Body delete flow to use a follow-up command and improved implicit split detection.
- Added Split Body Delete as a standalone Modify command.
- Added Fusion-style icons for all command buttons.
- Renamed EA Batch Rename to Batch Rename.

## 2026-01-07
- Rolled EA_HoleExport_CSVv1, IGESComponentExport, NewComponentset, and WireframeFromBody scripts into add-in commands.
- Integrated EA_HoleCut_AddIn as a new Hole Cut From Face command.
- Added a dedicated PhilsDesignTools toolbar panel and moved all commands into it.
- Added command icons for the new tools and updated README/CHANGELOG.

## 2026-01-16
- Added Stub Arms To Wall command to create stub-arm sketch lines from RHS columns to wall faces.
- Implemented debug logging and geometry diagnostics for the stub arms workflow.
