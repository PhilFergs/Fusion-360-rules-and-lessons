from philsfusion.commands.help import AboutDetails, format_about


def test_about_text_reports_runtime_migration_and_rollback_details():
    details = AboutDetails(
        version="2.0.0",
        source_commit="abc123",
        package_fingerprint="f" * 64,
        public_commands=25,
        compatibility_aliases=28,
        settings_migration="completed",
        legacy_quarantine="awaiting health verification",
        log_folder=r"C:\Users\Phil\Documents\PhilsFusionTools\logs",
        rollback_pointer=r"C:\Users\Phil\Documents\PhilsFusionTools-Rollback\LATEST-VERIFIED.txt",
    )

    text = format_about(details)

    assert text.startswith("Phils Fusion Tools 2.0.0")
    assert "Public commands: 25" in text
    assert "Compatibility aliases: 28" in text
    assert "Settings migration: completed" in text
    assert "Legacy quarantine: awaiting health verification" in text
    assert "Rollback pointer:" in text

