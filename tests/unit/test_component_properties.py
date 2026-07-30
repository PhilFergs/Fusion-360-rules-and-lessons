from philsfusion.services.component_properties import (
    document_metadata_state,
    set_string_property_verified,
)


class PropertyTarget:
    def __init__(self, *, persist=True):
        self._description = ""
        self.persist = persist

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if self.persist:
            self._description = value


class Document:
    def __init__(self, *, saved, modified):
        self.isSaved = saved
        self.isModified = modified


def test_verified_property_write_reports_persisted_value():
    target = PropertyTarget()

    result = set_string_property_verified(target, "description", "SHS 100 x 100 x 3")

    assert result.persisted is True
    assert result.observed == "SHS 100 x 100 x 3"
    assert result.error == ""


def test_verified_property_write_rejects_silent_fusion_failure():
    target = PropertyTarget(persist=False)

    result = set_string_property_verified(target, "description", "SHS 100 x 100 x 3")

    assert result.persisted is False
    assert result.observed == ""
    assert "did not persist" in result.error


def test_document_metadata_requires_a_saved_unmodified_version():
    assert document_metadata_state(Document(saved=False, modified=True)) == "never-saved"
    assert document_metadata_state(Document(saved=True, modified=True)) == "changes-not-saved"
    assert document_metadata_state(Document(saved=True, modified=False)) == "ready"


def test_document_metadata_is_not_assumed_ready_when_state_is_unavailable():
    assert document_metadata_state(object()) == "unknown"
