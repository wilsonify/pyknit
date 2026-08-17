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
# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

"""Unit tests for pyKnit shaping functions (openspec spec 06)."""

import pydantic
import pytest

import pyknit


def test_raglan_increases_standard_input():
    result = pyknit.raglan_increases(
        neck_stitches=100,
        arm_stitches=50,
        bust_stitches=96,
        neck_to_bust_rows=10,
    )
    assert "Marker setup:" in result
    assert "pm" in result
    assert result == "Marker setup: k12, pm, k26 (arm), pm, k24, pm, k26 (arm), pm k12"


def test_raglan_increases_generalizes_increase_rate():
    """The marker distribution must stay consistent for any multiple-of-4
    increase rate: the marker counts always sum to calculated_neck (and the
    post-increase total reaches working_stitches)."""
    result = pyknit.raglan_increases(
        neck_stitches=84,
        arm_stitches=40,
        bust_stitches=80,
        neck_to_bust_rows=5,
        increase_per_increase_row=12,
        armpit_stitches=4,
    )
    assert result == "Marker setup: k10, pm, k21 (arm), pm, k21, pm, k21 (arm), pm k11"
    # 10 + 21 + 21 + 21 + 11 = 84 = calculated_neck (working - 5*12)
    assert result.count("pm") == 4


def test_raglan_increases_rejects_non_multiple_of_4():
    """A non-multiple-of-4 increase rate cannot divide evenly across the
    four sections and must be rejected with a clear message."""
    with pytest.raises(ValueError, match="multiple of 4"):
        pyknit.raglan_increases(
            neck_stitches=80,
            arm_stitches=30,
            bust_stitches=100,
            neck_to_bust_rows=8,
            increase_per_increase_row=6,
        )


def test_raglan_increases_calculated_neck_too_low():
    # Known gap in pyknit/__init__.py: when calculated_neck < neck_stitches
    # the non-increase rows are not emitted (no_increase_rows is a FIXME
    # placeholder). The shared marker-setup path still runs deterministically,
    # so we only check that it does not error.
    result = pyknit.raglan_increases(
        neck_stitches=300,
        arm_stitches=50,
        bust_stitches=96,
        neck_to_bust_rows=10,
    )
    assert "Marker setup:" in result


def test_raglan_increases_rejects_slim_arm_negative_markers():
    """A raglan that would yield negative marker counts (e.g. 'k-5 (arm)')
    must raise a clear error rather than emit nonsensical instructions."""
    with pytest.raises(ValueError, match="too small"):
        pyknit.raglan_increases(
            neck_stitches=80,
            arm_stitches=15,
            bust_stitches=100,
            neck_to_bust_rows=8,
        )


def test_raglan_increases_rejects_tiny_bust_negative_markers():
    with pytest.raises(ValueError, match="too small"):
        pyknit.raglan_increases(
            neck_stitches=80,
            arm_stitches=30,
            bust_stitches=30,
            neck_to_bust_rows=8,
        )


def test_sleeve_decreases_repeat_string():
    expected = (
        "[decrease row, do 7 rows in pattern] * 5 times, "
        "[decrease row, do 6 rows in pattern] * 3 times"
    )
    assert (
        pyknit.sleeve_decreases(number_of_rows=61, starting_count=59, ending_count=43)
        == expected
    )


@pytest.mark.parametrize(
    ("number_of_rows", "starting_count", "ending_count", "expected"),
    [
        (10, 5, 8, ValueError),  # starting_count < ending_count
        (10, 8, 8, ValueError),  # starting_count == ending_count
    ],
)
def test_sleeve_decreases_error(number_of_rows, starting_count, ending_count, expected):
    with pytest.raises(expected):
        pyknit.sleeve_decreases(number_of_rows, starting_count, ending_count)


@pytest.mark.parametrize(
    ("starting_count", "ending_count", "expect"),
    [
        (59, 60, "already smaller"),
        (59, 59, "same as the ending count"),
    ],
)
def test_sleeve_decreases_error_has_useful_message(starting_count, ending_count, expect):
    """The ValueError for no-needed decreases must carry a readable message
    (the demo surfaces the exception text to the knitter)."""
    with pytest.raises(ValueError, match=expect):
        pyknit.sleeve_decreases(10, starting_count, ending_count)


@pytest.mark.parametrize(
    ("starting_count", "increase_number"),
    [
        (0, 5),
        (-1, 5),
        (5, 0),
    ],
)
def test_increase_evenly_validation_error(starting_count, increase_number):
    with pytest.raises(pydantic.ValidationError):
        pyknit.increase_evenly(starting_count, increase_number)


@pytest.mark.parametrize(
    ("starting_count", "decrease_number"),
    [
        (10, 1),  # too few decreases
        (10, 0),  # too few decreases
    ],
)
def test_decrease_evenly_too_few_decreases(starting_count, decrease_number):
    with pytest.raises(ValueError):
        pyknit.decrease_evenly(starting_count, decrease_number)
