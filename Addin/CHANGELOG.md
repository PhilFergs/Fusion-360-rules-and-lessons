# CHANGELOG

All notable changes to the Phils Design Tools add-in will be tracked here.

## Unreleased
### Added
- DEVLOG.md for ongoing development notes and change tracking.
- README.md with usage and development notes for this branch.
- WORKFLOW.md with the end-to-end workflow, automation plan, and naming rules.
- USER_GUIDE.rtf for training users on the workflow and tools.
- USER_GUIDE.docx for a Word-native version of the user guide.
- VERSION_LOG.md to track uploaded versions.
- tools/deploy_addin.ps1 to back up the active add-in before deployment.
### Changed
- Renamed the add-in to Phils Design Tools and updated file paths and IDs.
- Added logging calls across commands and startup/shutdown for debugging.
- Normalized UI strings to ASCII-only text.
- Fixed EA rotate axis selection to use the outer hole face and closest-point axis, with added debug logging for axis/pivot values.
- Removed unused imports and an unused rotate helper to reduce redundancy.
- Documented versioning and deployment steps in WORKFLOW.md.

