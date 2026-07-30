DIAGNOSTIC_FIELDS = (
    ("version", "Version"),
    ("source_commit", "Source commit"),
    ("package_fingerprint", "Package fingerprint"),
    ("install_path", "Install path"),
    ("settings_schema", "Settings schema"),
    ("startup_health", "Startup health"),
    ("migration_status", "Migration status"),
    ("log_path", "Log path"),
)


def build_diagnostics(
    *,
    version: str,
    source_commit: str,
    package_fingerprint: str,
    install_path: str,
    settings_schema: int,
    startup_health: str,
    migration_status: str,
    log_path: str,
) -> dict[str, str | int]:
    return {
        "version": version,
        "source_commit": source_commit,
        "package_fingerprint": package_fingerprint,
        "install_path": install_path,
        "settings_schema": settings_schema,
        "startup_health": startup_health,
        "migration_status": migration_status,
        "log_path": log_path,
    }


def format_diagnostics(diagnostics: dict[str, str | int]) -> str:
    return "\n".join(
        f"{label}: {diagnostics[key]}"
        for key, label in DIAGNOSTIC_FIELDS
    )
