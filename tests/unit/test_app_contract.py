from philsfusion.services.settings import SETTINGS_SCHEMA_VERSION


def test_application_settings_schema_symbol_is_exported():
    assert SETTINGS_SCHEMA_VERSION == 2
