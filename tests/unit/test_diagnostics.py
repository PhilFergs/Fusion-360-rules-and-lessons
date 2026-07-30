from philsfusion.services.diagnostics import build_diagnostics, format_diagnostics


def test_diagnostics_contains_only_approved_operational_fields():
    diagnostics = build_diagnostics(
        version="2.0.0",
        source_commit="abc1234",
        package_fingerprint="sha256:012345",
        install_path=r"C:\Fusion\AddIns\PhilsFusionTools",
        settings_schema=2,
        startup_health="healthy",
        migration_status="foundation",
        log_path=r"C:\Logs\PhilsFusionTools.log",
    )

    assert diagnostics == {
        "version": "2.0.0",
        "source_commit": "abc1234",
        "package_fingerprint": "sha256:012345",
        "install_path": r"C:\Fusion\AddIns\PhilsFusionTools",
        "settings_schema": 2,
        "startup_health": "healthy",
        "migration_status": "foundation",
        "log_path": r"C:\Logs\PhilsFusionTools.log",
    }
    assert not {"document", "geometry", "selection", "exported_data"} & diagnostics.keys()


def test_diagnostics_text_uses_stable_labels_and_order():
    diagnostics = build_diagnostics(
        version="2.0.0",
        source_commit="abc1234",
        package_fingerprint="sha256:012345",
        install_path=r"C:\Fusion\AddIns\PhilsFusionTools",
        settings_schema=2,
        startup_health="healthy",
        migration_status="foundation",
        log_path=r"C:\Logs\PhilsFusionTools.log",
    )

    assert format_diagnostics(diagnostics).splitlines() == [
        "Version: 2.0.0",
        "Source commit: abc1234",
        "Package fingerprint: sha256:012345",
        r"Install path: C:\Fusion\AddIns\PhilsFusionTools",
        "Settings schema: 2",
        "Startup health: healthy",
        "Migration status: foundation",
        r"Log path: C:\Logs\PhilsFusionTools.log",
    ]

