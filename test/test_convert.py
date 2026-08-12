# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

"""Cross-gauge conversion math and GaugeSwatch validation (openspec spec 05)."""

import pydantic
import pytest

from pyknit.GaugeSwatch import (
    GaugeSwatch,
    convert_row_measure,
    convert_stitch_measure,
)


@pytest.fixture
def pattern_gauge():
    return GaugeSwatch(
        stitch_count=27.5,
        stitch_measure=10,
        row_count=40,
        row_measure=4,
        units="in",
    )


@pytest.fixture
def my_gauge():
    return GaugeSwatch(
        stitch_count=23.5,
        stitch_measure=10,
        row_count=33,
        row_measure=4,
        units="in",
    )


@pytest.fixture
def swatch():
    return GaugeSwatch(
        row_count=18,
        row_measure=3.25,
        stitch_count=24,
        stitch_measure=4,
        units="in",
    )


@pytest.mark.parametrize(
    ("measurement", "expected"),
    [
        (42, 49.36170212765957),  # README 42in chest -> ~49in
        (38, 44.25531914893617),  # README 38in -> ~44.25in
        (34, 40.0),  # README 34in -> 40in
    ],
)
def test_convert_stitch_measure_readme_example(
    pattern_gauge, my_gauge, measurement, expected
):
    assert convert_stitch_measure(
        measurement, pattern_gauge, my_gauge
    ) == pytest.approx(expected)


def test_convert_row_measure(pattern_gauge, my_gauge):
    # 40 rows/4in -> 33 rows/4in; 10in in pattern gauge = 12.12in in mine
    assert convert_row_measure(10, pattern_gauge, my_gauge) == pytest.approx(
        12.121212121212121
    )


@pytest.mark.parametrize("measurement", [0, -5])
def test_measurement_to_stitches_invalid(swatch, measurement):
    with pytest.raises(pydantic.ValidationError):
        swatch.measurement_to_stitches(measurement)


@pytest.mark.parametrize(
    "invalid_kwargs",
    [
        {"row_count": 0},
        {"stitch_count": -1},
        {"units": "mm"},
    ],
)
def test_gauge_swatch_invalid_construction_args(invalid_kwargs):
    valid = dict(
        row_count=18,
        row_measure=3.25,
        stitch_count=24,
        stitch_measure=4,
        units="in",
    )
    valid.update(invalid_kwargs)
    with pytest.raises(pydantic.ValidationError):
        GaugeSwatch(**valid)


def test_convert_row_measure_zero_measurement(pattern_gauge, my_gauge):
    with pytest.raises(pydantic.ValidationError):
        convert_row_measure(0, pattern_gauge, my_gauge)
