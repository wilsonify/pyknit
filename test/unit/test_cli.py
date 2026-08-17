# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

import sys

import pytest

from pyknit import VERSION, GaugeSwatch
from pyknit.__main__ import (
    _convert_measurement_units,
    convert_row_gauge,
    convert_stitch_gauge,
    main,
)

CENTIMETERS_PER_INCH = 2.54


def test_version_string():
    assert VERSION == "pyKnit 0.1.1"


def test_convert_measurement_units_in_to_cm():
    assert _convert_measurement_units(1.0, "in", "cm") == pytest.approx(
        CENTIMETERS_PER_INCH
    )


def test_convert_measurement_units_cm_to_in():
    assert _convert_measurement_units(
        CENTIMETERS_PER_INCH, "cm", "in"
    ) == pytest.approx(1.0)


def test_convert_measurement_units_same_unit():
    assert _convert_measurement_units(12.0, "in", "in") == pytest.approx(12.0)


def test_convert_measurement_units_unknown_unit():
    with pytest.raises(ValueError):
        _convert_measurement_units(1.0, "in", "yd")


def test_convert_row_gauge_same_units():
    original_gauge = GaugeSwatch(
        row_count=8, stitch_count=1, row_measure=1, stitch_measure=1, units="in"
    )
    new_gauge = GaugeSwatch(
        row_count=9, stitch_count=1, row_measure=1, stitch_measure=1, units="in"
    )
    # 18 in at 8 rows/in = 144 rows; at 9 rows/in that is 16 in
    assert convert_row_gauge(original_gauge, new_gauge, 18.0, "in") == pytest.approx(
        16.0
    )


def test_convert_stitch_gauge_same_units():
    original_gauge = GaugeSwatch(
        stitch_count=8, row_count=1, row_measure=1, stitch_measure=1, units="in"
    )
    new_gauge = GaugeSwatch(
        stitch_count=7.5, row_count=1, row_measure=1, stitch_measure=1, units="in"
    )
    # 18 in at 8 st/in = 144 stitches; at 7.5 st/in that is 19.2 in
    assert convert_stitch_gauge(
        original_gauge, new_gauge, 18.0, "in"
    ) == pytest.approx(19.2)


def test_convert_row_gauge_mixed_units_matching_density():
    # 4 rows/in is the same cloth density as 4 rows per 2.54 cm
    original_gauge = GaugeSwatch(
        row_count=4, stitch_count=1, row_measure=1, stitch_measure=1, units="in"
    )
    new_gauge = GaugeSwatch(
        row_count=4, stitch_count=1, row_measure=2.54, stitch_measure=1, units="cm"
    )
    assert convert_row_gauge(
        original_gauge, new_gauge, 10.0, "in"
    ) == pytest.approx(10.0)


def test_convert_row_gauge_mixed_units_different_density():
    # 10 cm at the original 2 rows/cm = 20 rows; at 4 rows/in that is 5 in,
    # reported back in the original unit: 5 * 2.54 = 12.7 cm
    original_gauge = GaugeSwatch(
        row_count=2, stitch_count=1, row_measure=1, stitch_measure=1, units="cm"
    )
    new_gauge = GaugeSwatch(
        row_count=4, stitch_count=1, row_measure=1, stitch_measure=1, units="in"
    )
    assert convert_row_gauge(
        original_gauge, new_gauge, 10.0, "cm"
    ) == pytest.approx(20 / 4 * CENTIMETERS_PER_INCH)


def test_convert_stitch_gauge_mixed_units_matching_density():
    # 5 st/in is the same fabric density as 5 stitches per 10 cm description
    # below (5 stitches over 3.937 inches).  Re-express as cm for the new gauge.
    original_gauge = GaugeSwatch(
        stitch_count=5, row_count=1, row_measure=1, stitch_measure=1, units="in"
    )
    new_gauge = GaugeSwatch(
        stitch_count=5,
        row_count=1,
        row_measure=1,
        stitch_measure=2.54,
        units="cm",
    )
    assert convert_stitch_gauge(
        original_gauge, new_gauge, 20.0, "in"
    ) == pytest.approx(20.0)


def test_main_prints_version(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pyknit",
            "--convert",
            "row",
            "-ogr",
            "7",
            "-ngr",
            "6",
            "-ogm",
            "1",
            "--original-measurement",
            "12",
        ],
    )
    main()
    captured = capsys.readouterr().out
    assert "pyKnit 0.1.1" in captured


