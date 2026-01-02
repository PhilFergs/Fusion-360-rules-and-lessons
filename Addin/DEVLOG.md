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

