# Copyright (C) 2026 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests for the shawl shape generators."""

import pytest

from pyknit.GaugeSwatch import GaugeSwatch
from pyknit.shawl_shapes import generate_shawl


def make_swatch() -> GaugeSwatch:
    """A gauge swatch with 6 stitches per inch and 18 rows per 3.25 inches."""
    return GaugeSwatch(
        row_count=18,
        row_measure=3.25,
        stitch_count=24,
        stitch_measure=4,
        units="in",
    )


SHAPES = ["square", "rectangle", "triangle", "crescent"]


@pytest.mark.parametrize("shape", SHAPES)
def test_each_shape_is_non_empty_and_deterministic(shape):
    instructions = generate_shawl(shape, width=20, length=30, gauge=make_swatch())
    assert len(instructions) > 0
    assert all(isinstance(line, str) and line for line in instructions)
    assert instructions == generate_shawl(shape, width=20, length=30, gauge=make_swatch())


def test_rectangle_counts_come_from_gauge_swatch():
    gauge = make_swatch()
    assert gauge.measurement_to_stitches(5) == 30
    assert gauge.measurement_to_rows(11) == 61
    text = "\n".join(generate_shawl("rectangle", width=5, length=11, gauge=gauge))
    assert "Cast on 30 stitches" in text
    assert "Work 61 rows" in text
    assert "Bind off all 30 stitches" in text


def test_square_uses_width_measurement_for_stitches_and_rows():
    gauge = make_swatch()
    text = "\n".join(generate_shawl("square", width=10, length=999, gauge=gauge))
    assert f"Cast on {gauge.measurement_to_stitches(10)} stitches" in text
    assert f"Work {gauge.measurement_to_rows(10)} rows" in text


def test_triangle_increase_rows_grow_the_stitch_budget():
    gauge = make_swatch()
    instructions = generate_shawl("triangle", width=20, length=30, gauge=gauge)
    text = "\n".join(instructions)
    assert "Cast on 3 stitches at the point" in text
    increase_lines = [line for line in instructions if "m1" in line]
    assert increase_lines, "triangle should contain at least one increase row"
    for line in increase_lines:
        assert line.count("m1") >= 1
    total_increases = sum(line.count("m1") for line in increase_lines)
    assert f"Bind off all {3 + total_increases} stitches" in text


def test_crescent_increases_at_both_ends():
    gauge = make_swatch()
    text = "\n".join(generate_shawl("crescent", width=20, length=30, gauge=gauge))
    assert "at each end" in text
    assert "kfb, k across, kfb" in text


def test_unknown_shape_raises_value_error():
    with pytest.raises(ValueError):
        generate_shawl("dodecagon", width=20, length=30, gauge=make_swatch())
