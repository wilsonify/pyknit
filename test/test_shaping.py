# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

#!python
import logging
import re

import pytest

import pyknit


def count_decrease_rows(instructions: str) -> int:
    """Total number of decrease rows scheduled, expanding ``* N times``."""
    total = 0
    for segment in re.findall(
        r"\[[^\]]*decrease row[^\]]*\] \* \d+ times", instructions
    ):
        total += int(re.search(r"\* (\d+) times", segment).group(1))
    bare = re.sub(r"\[[^\]]*\]", "", instructions)
    total += len(re.findall(r"\bdecrease row\b", bare))
    return total


@pytest.mark.parametrize(
    ("rows", "starting_count", "ending_count", "decrease_per_row", "expected"),
    [
        (
            61,
            59,
            43,
            2,
            "[decrease row, do 7 rows in pattern] * 5 times, "
            "[decrease row, do 6 rows in pattern] * 3 times",
        ),
    ],
)
def test_sleeve_decreases_documented_fixture(
    rows, starting_count, ending_count, decrease_per_row, expected
):
    assert (
        pyknit.sleeve_decreases(
            rows,
            starting_count=starting_count,
            ending_count=ending_count,
            decrease_per_row=decrease_per_row,
        )
        == expected
    )


def test_sleeve_decreases_padding_modes():
    outputs = {
        mode: pyknit.sleeve_decreases(
            10,
            starting_count=20,
            ending_count=12,
            decrease_per_row=2,
            padding_mode=mode,
        )
        for mode in ("before", "after", "both", "none")
    }
    assert len(set(outputs.values())) == 4
    for instructions in outputs.values():
        # each mode schedules the same four decrease rows (8 stitches removed)
        assert count_decrease_rows(instructions) == 4
    assert outputs["after"] == (
        "[decrease row, do 2 rows in pattern] * 2 times, "
        "[decrease row, do 1 rows in pattern] * 2 times"
    )
    assert outputs["before"] == (
        "[do 1 rows in pattern, decrease row] * 2 times, "
        "[do 2 rows in pattern, decrease row] * 2 times"
    )
    assert outputs["both"] == (
        "[do 1 rows in pattern, decrease row, do 1 rows in pattern] * 2 times, "
        "[decrease row, do 1 rows in pattern] * 2 times"
    )
    assert outputs["none"] == (
        "decrease row, decrease row, decrease row, decrease row"
    )


def test_sleeve_decreases_remainder_schedules_extra_decreases(caplog):
    with caplog.at_level(logging.WARNING):
        instructions = pyknit.sleeve_decreases(
            10, starting_count=20, ending_count=11, decrease_per_row=2
        )
    messages = [record.message for record in caplog.records]
    assert not any("add decreases at the end" in message for message in messages)
    assert not any(
        "desired decrease doesn't work exactly" in message for message in messages
    )
    extra = re.search(r"extra decrease: work (\d+) k2tog", instructions)
    assert extra is not None
    assert count_decrease_rows(instructions) * 2 + int(extra.group(1)) == 20 - 11
    assert "the final count is 11 stitches" in instructions


def test_sleeve_decreases_invalid_padding_mode():
    with pytest.raises(ValueError):
        pyknit.sleeve_decreases(
            10,
            starting_count=20,
            ending_count=12,
            decrease_per_row=2,
            padding_mode="sideways",
        )


def test_calculate_spacing_after_before_ordering():
    assert pyknit._calculate_spacing(53, 8, "after") == [(7, 5), (6, 3)]
    assert pyknit._calculate_spacing(53, 8, "before") == [(6, 3), (7, 5)]


def test_calculate_spacing_divisible_and_remainder():
    assert pyknit._calculate_spacing(20, 5) == [(4, 5)]
    assert pyknit._calculate_spacing(21, 5) == [(5, 1), (4, 4)]


def test_calculate_spacing_invalid_count():
    with pytest.raises(ValueError):
        pyknit._calculate_spacing(10, 0)


@pytest.mark.parametrize(
    ("starting_count", "decrease_number", "expected_ks"),
    [
        (11, 3, [1, 2]),
        (19, 5, [1, 2]),
        (21, 5, [2, 3]),
    ],
)
def test_decrease_evenly_uses_shared_spacing(
    starting_count, decrease_number, expected_ks
):
    plan = sorted(pyknit._calculate_spacing(starting_count, decrease_number))
    assert [size - 2 for size, _ in plan] == expected_ks
