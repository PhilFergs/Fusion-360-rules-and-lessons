import itertools

import pytest

from philsfusion.commands.bom.domain import (
    bom_row_sort_key,
    clean_component_name,
    csv_cell,
    item_number_sequence,
    split_name_and_profile,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Bracket:1", "Bracket"),
        ("Bracket (3)", "Bracket"),
        ("  Bracket (12):4  ", "Bracket"),
        ("Bracket", "Bracket"),
    ],
)
def test_component_names_remove_only_fusion_instance_suffixes(raw, expected):
    assert clean_component_name(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("EA1-50x50x3", ("EA1", "50x50x3")),
        ("RHS-100x50x3.2", ("RHS", "100x50x3.2")),
        ("Bracket (3)", ("Bracket", "")),
        ("", ("", "")),
    ],
)
def test_profile_suffix_is_split_from_clean_component_name(raw, expected):
    assert split_name_and_profile(raw) == expected


def test_csv_cells_escape_delimiters_quotes_and_newlines():
    assert csv_cell('A,"B"\nC', ",") == '"A,""B""\nC"'
    assert csv_cell("A,B", ";") == "A,B"
    assert csv_cell(" 12 ", ",", numeric=True) == "12"


def test_bom_rows_sort_naturally_and_stably():
    rows = [
        {"name": "Bracket 10", "partnumber": "B"},
        {"name": "Bracket 2", "partnumber": "C"},
        {"name": "Bracket 2", "partnumber": "A"},
    ]

    assert sorted(rows, key=bom_row_sort_key) == [rows[2], rows[1], rows[0]]


def test_custom_item_number_sequence_matches_legacy_placeholders():
    sequence = item_number_sequence("Part /@2/ - /#3/")

    assert list(itertools.islice(sequence, 3)) == [
        "Part AA - 001",
        "Part AA - 002",
        "Part AA - 003",
    ]

