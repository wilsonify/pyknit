# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

# !python

from datetime import timedelta

import pytest

from pyknit.GaugeSwatch import GaugeSwatch
from pyknit.estimate import estimate_knitting_time, format_knitting_time


def test_gauge_swatch_backward_compatible_defaults():
    gs = GaugeSwatch(
        row_count=18, row_measure=3.25, stitch_count=24, stitch_measure=4, units="in"
    )
    assert gs.row_count == 18
    assert gs.stitch_gauge() == 6
    assert gs.yardage_per_unit is None
    assert gs.weight_per_unit is None


@pytest.fixture
def swatch_with_yarn():
    return GaugeSwatch(
        row_count=18,
        row_measure=3.25,
        stitch_count=24,
        stitch_measure=4,
        units="in",
        yardage_per_unit=0.5,
        weight_per_unit=0.3,
    )


def test_gauge_swatch_with_yarn_fields(swatch_with_yarn):
    assert swatch_with_yarn.yardage_per_unit == pytest.approx(0.5)
    assert swatch_with_yarn.weight_per_unit == pytest.approx(0.3)


def test_estimate_yardage_scales_linearly(swatch_with_yarn):
    assert swatch_with_yarn.estimate_yardage(10) == pytest.approx(5.0)
    assert swatch_with_yarn.estimate_yardage(20) == pytest.approx(10.0)
    assert swatch_with_yarn.estimate_yardage(30) == pytest.approx(15.0)


def test_estimate_weight_scales_linearly(swatch_with_yarn):
    assert swatch_with_yarn.estimate_weight(10) == pytest.approx(3.0)
    assert swatch_with_yarn.estimate_weight(20) == pytest.approx(6.0)
    assert swatch_with_yarn.estimate_weight(30) == pytest.approx(9.0)


def test_estimate_yardage_with_6_st_per_inch_swatch():
    gs = GaugeSwatch(
        row_count=22,
        row_measure=4,
        stitch_count=24,
        stitch_measure=4,
        units="in",
        yardage_per_unit=0.5,
    )
    assert gs.stitch_gauge() == pytest.approx(6)
    assert gs.estimate_yardage(30) == pytest.approx(0.5 * 30)


def test_estimate_yardage_unset_raises():
    gs = GaugeSwatch(
        row_count=18, row_measure=3.25, stitch_count=24, stitch_measure=4, units="in"
    )
    with pytest.raises(ValueError, match="yardage_per_unit not set on this swatch"):
        gs.estimate_yardage(30)


def test_estimate_weight_unset_raises():
    gs = GaugeSwatch(
        row_count=18, row_measure=3.25, stitch_count=24, stitch_measure=4, units="in"
    )
    with pytest.raises(ValueError, match="weight_per_unit not set on this swatch"):
        gs.estimate_weight(30)


def test_estimate_knitting_time():
    assert estimate_knitting_time(6000, 5) == timedelta(0, 30000)


def test_estimate_knitting_time_deterministic():
    first = estimate_knitting_time(6000, 5)
    for _ in range(5):
        assert estimate_knitting_time(6000, 5) == first


@pytest.mark.parametrize(
    "total_stitches, seconds_per_stitch",
    [(0, 5), (-10, 5), (10, 0), (0, 0)],
)
def test_estimate_knitting_time_rejects_non_positive(
    total_stitches, seconds_per_stitch
):
    with pytest.raises(ValueError):
        estimate_knitting_time(total_stitches, seconds_per_stitch)


def test_format_knitting_time():
    assert format_knitting_time(timedelta(seconds=30000)) == "8 hours 20 minutes"
    assert format_knitting_time(timedelta(days=1)) == "24 hours"
