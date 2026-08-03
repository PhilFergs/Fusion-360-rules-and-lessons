from philsfusion.services.component_properties import (
    document_metadata_state,
    set_string_property_verified,
    simplified_part_number,
    wait_for_component_metadata,
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


class TransientPropertyTarget:
    def __init__(self, failures_before_persisting):
        self._description = ""
        self.failures_before_persisting = failures_before_persisting
        self.write_attempts = 0

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self.write_attempts += 1
        if self.write_attempts > self.failures_before_persisting:
            self._description = value


class Document:
    def __init__(self, *, saved, modified):
        self.isSaved = saved
        self.isModified = modified


class MetadataComponent:
    def __init__(self, name, model_ids):
        self.name = name
        self._model_ids = iter(model_ids)
        self._last_model_id = ""

    @property
    def mfgdmModelId(self):
        try:
            self._last_model_id = next(self._model_ids)
        except StopIteration:
            pass
        return self._last_model_id


class FakeTime:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


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


def test_verified_property_write_retries_a_transient_cloud_failure():
    target = TransientPropertyTarget(failures_before_persisting=2)
    timer = FakeTime()

    result = set_string_property_verified(
        target,
        "description",
        "EA 50 x 50 x 3",
        attempts=3,
        retry_seconds=1,
        sleep=timer.sleep,
    )

    assert result.persisted is True
    assert result.observed == "EA 50 x 50 x 3"
    assert target.write_attempts == 3
    assert timer.now == 2


def test_document_metadata_requires_a_saved_unmodified_version():
    assert document_metadata_state(Document(saved=False, modified=True)) == "never-saved"
    assert document_metadata_state(Document(saved=True, modified=True)) == "changes-not-saved"
    assert document_metadata_state(Document(saved=True, modified=False)) == "ready"


def test_document_metadata_is_not_assumed_ready_when_state_is_unavailable():
    assert document_metadata_state(object()) == "unknown"


def test_simplified_part_number_keeps_an_already_simple_part_name():
    assert simplified_part_number("PFC1") == "PFC1"


def test_simplified_part_number_removes_a_recognized_profile_suffix():
    assert simplified_part_number("PFC1 - PFC 150 x 75 x 6 x 9.5") == "PFC1"
    assert simplified_part_number("RB12 100x50x3 RHS") == "RB12"


def test_metadata_wait_allows_delayed_cloud_ids_to_become_ready():
    timer = FakeTime()
    pfc = MetadataComponent("PFC1", ["", "", "pfc-model-id"])
    rhs = MetadataComponent("RHS1", ["rhs-model-id"])

    pending = wait_for_component_metadata(
        [pfc, rhs],
        timeout_seconds=5,
        poll_seconds=1,
        monotonic=timer.monotonic,
        sleep=timer.sleep,
    )

    assert pending == ()
    assert timer.now == 2


def test_metadata_wait_returns_every_component_still_pending_at_timeout():
    timer = FakeTime()
    ub = MetadataComponent("UB1", [""])
    pfc = MetadataComponent("PFC1", [""])

    pending = wait_for_component_metadata(
        [ub, pfc],
        timeout_seconds=2,
        poll_seconds=1,
        monotonic=timer.monotonic,
        sleep=timer.sleep,
    )

    assert tuple(component.name for component in pending) == ("UB1", "PFC1")
