from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AboutDetails:
    version: str
    source_commit: str
    package_fingerprint: str
    public_commands: int
    compatibility_aliases: int
    settings_migration: str
    legacy_quarantine: str
    log_folder: str
    rollback_pointer: str


def format_about(details: AboutDetails) -> str:
    return "\n".join(
        (
            f"Phils Fusion Tools {details.version}",
            "",
            "Unified BOM, design, fabrication, export, and cleanup tools.",
            "",
            f"Source commit: {details.source_commit}",
            f"Package fingerprint: {details.package_fingerprint}",
            f"Public commands: {details.public_commands}",
            f"Compatibility aliases: {details.compatibility_aliases}",
            f"Settings migration: {details.settings_migration}",
            f"Legacy quarantine: {details.legacy_quarantine}",
            f"Log folder: {details.log_folder}",
            f"Rollback pointer: {details.rollback_pointer}",
        )
    )
