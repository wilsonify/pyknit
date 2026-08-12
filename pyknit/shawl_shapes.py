# Copyright (C) 2026 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

"""Written-instruction generators for common shawl shapes.

The generators take a :class:`pyknit.GaugeSwatch` so stitch and row budgets
are derived from measurements via ``measurement_to_stitches`` and
``measurement_to_rows``.  All generators are pure and deterministic: the same
arguments always produce the identical instruction list.

Shape schemes
-------------

square
    Cast on as many stitches as the width requires and knit flat for the same
    measurement of rows, with no shaping.  A plain square shawl needs no
    increases or decreases; ``length`` is ignored.

rectangle
    Cast on width-derived stitches, knit length-derived rows, flat and without
    shaping.

triangle
    Cast on 3 stitches at the point and work one increase row per row,
    distributing the increases evenly with ``increase_evenly``, until the
    stitch count reaches the width-derived target or the length-derived row
    budget runs out, whichever comes first.

crescent
    Cast on half the width-derived stitch count and increase 1 stitch at each
    end of the row (``kfb``) every 4th row, so the shawl widens at both edges.
"""

from typing import List

from . import increase_evenly
from .GaugeSwatch import GaugeSwatch

SUPPORTED_SHAPES = ("square", "rectangle", "triangle", "crescent")

TRIANGLE_START_STITCHES = 3
TRIANGLE_INCREASE_PER_ROW = 2
CRESCENT_INCREASE_INTERVAL = 4


def generate_shawl(
    shape: str, width: float, length: float, gauge: GaugeSwatch
) -> List[str]:
    """Return a deterministic list of written instructions for a shawl shape.

    Args:
        shape: One of "square", "rectangle", "triangle", "crescent".
        width: Desired width of the shawl in ``gauge.units``.
        length: Desired length of the shawl in ``gauge.units``.
        gauge: Gauge swatch used to convert measurements into stitches and rows.

    Returns:
        A list of written instruction strings.

    Raises:
        ValueError: If ``shape`` is not one of the supported shapes.
    """
    if shape == "square":
        return _square_shape(width, gauge)
    if shape == "rectangle":
        return _rectangle_shape(width, length, gauge)
    if shape == "triangle":
        return _triangle_shape(width, length, gauge)
    if shape == "crescent":
        return _crescent_shape(width, length, gauge)
    raise ValueError(
        f"Unknown shawl shape {shape!r}; expected one of {SUPPORTED_SHAPES}."
    )


def _square_shape(width: float, gauge: GaugeSwatch) -> List[str]:
    """Knit a plain square flat: cast on the width-derived stitch count and
    knit the same measurement of rows with no shaping."""
    stitches = gauge.measurement_to_stitches(width)
    rows = gauge.measurement_to_rows(width)
    return [
        f"Cast on {stitches} stitches for a square shawl.",
        f"Work {rows} rows flat in stockinette stitch (no shaping; a square "
        "needs no increases or decreases).",
        f"Bind off all {stitches} stitches.",
    ]


def _rectangle_shape(width: float, length: float, gauge: GaugeSwatch) -> List[str]:
    """Knit a plain rectangle flat: cast on the width-derived stitch count and
    knit the length-derived row count with no shaping."""
    stitches = gauge.measurement_to_stitches(width)
    rows = gauge.measurement_to_rows(length)
    return [
        f"Cast on {stitches} stitches for a rectangle shawl.",
        f"Work {rows} rows flat in stockinette stitch (no shaping).",
        f"Bind off all {stitches} stitches.",
    ]


def _triangle_shape(width: float, length: float, gauge: GaugeSwatch) -> List[str]:
    """Knit a triangle from the point up.

    Cast on ``TRIANGLE_START_STITCHES`` stitches at the point, then work one
    increase row per row with ``increase_evenly`` (asking for
    ``TRIANGLE_INCREASE_PER_ROW`` increases) until the stitch count reaches
    the width-derived target or the length-derived row budget runs out,
    whichever comes first.  Each increase row adds a positive number of
    stitches distributed evenly across the row, so the stitch budget grows
    every row.
    """
    target_stitches = gauge.measurement_to_stitches(width)
    max_rows = gauge.measurement_to_rows(length)
    current_stitches = TRIANGLE_START_STITCHES
    instructions = [
        f"Cast on {TRIANGLE_START_STITCHES} stitches at the point of the triangle."
    ]
    row = 1
    while current_stitches < target_stitches and row <= max_rows:
        spacing = increase_evenly(current_stitches, TRIANGLE_INCREASE_PER_ROW)
        instructions.append(f"Row {row}: {spacing}")
        current_stitches += spacing.count("m1")
        row += 1
    instructions.append(f"Bind off all {current_stitches} stitches.")
    return instructions


def _crescent_shape(width: float, length: float, gauge: GaugeSwatch) -> List[str]:
    """Knit a crescent shawl.

    Cast on half the width-derived stitch count, then work
    ``measurement_to_rows(length)`` rows.  Every
    ``CRESCENT_INCREASE_INTERVAL`` rows, work a row that increases 1 stitch at
    each end (knit front and back, ``kfb``), so the shawl widens at both edges
    as it grows.
    """
    start_stitches = max(2, gauge.measurement_to_stitches(width) // 2)
    rows = gauge.measurement_to_rows(length)
    num_increase_rows = rows // CRESCENT_INCREASE_INTERVAL
    instructions = [
        f"Cast on {start_stitches} stitches (half the desired width).",
        f"Work {rows} rows total, increasing 1 stitch at each end of the row "
        f"every {CRESCENT_INCREASE_INTERVAL}th row.",
    ]
    for increase_number in range(1, num_increase_rows + 1):
        row_number = increase_number * CRESCENT_INCREASE_INTERVAL
        instructions.append(
            f"Row {row_number}: kfb, k across, kfb (1 stitch increased at each end)."
        )
    instructions.append("Knit all remaining rows plain.")
    final_stitches = start_stitches + 2 * num_increase_rows
    instructions.append(f"Bind off all {final_stitches} stitches.")
    return instructions
