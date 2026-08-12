# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

#!python
"""
pyKnit: a set of tools for knitters to do math, create charts, customise
patterns and more

pyKnit.GaugeSwatch: Tools for measurement and gauge swatching
"""

import math
from typing import Literal, Optional, Set

from pydantic import BaseModel, PositiveFloat, PositiveInt, validate_arguments


class GaugeSwatch(BaseModel):
    """Information from a gauge swatch

    >>> swatch = GaugeSwatch(
    ...     row_count=18, row_measure=3.25, stitch_count=24,
    ...     stitch_measure=4, units="in",
    ... )
    >>> swatch.stitch_gauge()
    6.0
    """

    row_count: PositiveFloat
    row_measure: PositiveFloat
    stitch_count: PositiveFloat
    stitch_measure: PositiveFloat
    units: Literal["cm", "in"]
    # Yarn use per stitch (per design, estimate spec 08). Optional fields used
    # by estimate_yardage() and estimate_weight().
    yardage_per_unit: Optional[PositiveFloat] = None
    weight_per_unit: Optional[PositiveFloat] = None

    def row_gauge(self) -> float:
        """return rows per unit (e.g. cm, inch) number

        >>> swatch = GaugeSwatch(
        ...     row_count=18, row_measure=3.25, stitch_count=24,
        ...     stitch_measure=4, units="in",
        ... )
        >>> swatch.row_gauge()
        5.538461538461538
        """
        return self.row_count / self.row_measure

    def stitch_gauge(self) -> float:
        """return stitches per unit (e.g. cm, inch) number

        >>> swatch = GaugeSwatch(
        ...     row_count=18, row_measure=3.25, stitch_count=24,
        ...     stitch_measure=4, units="in",
        ... )
        >>> swatch.stitch_gauge()
        6.0
        """
        return self.stitch_count / self.stitch_measure

    @validate_arguments
    def measurement_to_stitches(self, measurement: PositiveFloat) -> int:
        """
        Given a measurement, how many stiches would we need?
        Round to closest stitch.

        >>> swatch = GaugeSwatch(
        ...     row_count=18, row_measure=3.25, stitch_count=24,
        ...     stitch_measure=4, units="in",
        ... )
        >>> swatch.measurement_to_stitches(5)
        30
        """
        return round(measurement * self.stitch_gauge())

    @validate_arguments
    def measurement_to_rows(self, measurement: PositiveFloat) -> int:
        """
        Given a measurement, how many rows would we need?
        Round to closest number of rows.

        >>> swatch = GaugeSwatch(
        ...     row_count=18, row_measure=3.25, stitch_count=24,
        ...     stitch_measure=4, units="in",
        ... )
        >>> swatch.measurement_to_rows(11)
        61
        """
        return round(measurement * self.row_gauge())

    @validate_arguments
    def rows_to_measurement(self, rows: PositiveInt) -> float:
        """figure out how long a number of rows will be

        >>> swatch = GaugeSwatch(
        ...     row_count=18, row_measure=3.25, stitch_count=24,
        ...     stitch_measure=4, units="in",
        ... )
        >>> swatch.rows_to_measurement(10)
        1.8055555555555556
        """
        return rows / self.row_gauge()

    @validate_arguments
    def stitches_to_measurement(self, stitches: PositiveInt) -> float:
        """figure out how wide a number of stitches will be

        >>> swatch = GaugeSwatch(
        ...     row_count=18, row_measure=3.25, stitch_count=24,
        ...     stitch_measure=4, units="in",
        ... )
        >>> swatch.stitches_to_measurement(18)
        3.0
        """
        return stitches / self.stitch_gauge()

    @validate_arguments
    def estimate_yardage(self, stitch_count: PositiveInt) -> float:
        """Estimate yarn length needed for stitch_count stitches.

        Scales ``yardage_per_unit`` (yarn length per stitch, e.g. metres per
        stitch) by the number of stitches. Raises ValueError when
        ``yardage_per_unit`` has not been set on this swatch.
        """
        if self.yardage_per_unit is None:
            raise ValueError("yardage_per_unit not set on this swatch")
        return self.yardage_per_unit * stitch_count

    @validate_arguments
    def estimate_weight(self, stitch_count: PositiveInt) -> float:
        """Estimate yarn weight needed for stitch_count stitches.

        Scales ``weight_per_unit`` (yarn weight per stitch, e.g. grams per
        stitch) by the number of stitches. Raises ValueError when
        ``weight_per_unit`` has not been set on this swatch.
        """
        if self.weight_per_unit is None:
            raise ValueError("weight_per_unit not set on this swatch")
        return self.weight_per_unit * stitch_count


# Gauge and stich count related functions


def stitch_count(stitch_array: Set[str], legend: Set[str]) -> int:
    if legend:
        # FIXME: Do calculations per stitch
        return len(stitch_array)

    # otherwise, assume every stitch has width=1

@validate_arguments
def convert_stitch_measure(
    measurement: PositiveFloat, oldGauge: GaugeSwatch, newGauge: GaugeSwatch
) -> float:
    """
    Given a masurement in the original gauge, find out what it would
    be in the new gauge.  e.g. if the sweater was going to be 40 inches
    in pattern gauge, how much would it be in my gauge?

    >>> pattern_gauge = GaugeSwatch(
    ...     row_count=22, row_measure=3.75, stitch_count=18,
    ...     stitch_measure=4, units="in",
    ... )
    >>> my_gauge = GaugeSwatch(
    ...     row_count=18, row_measure=3.25, stitch_count=24,
    ...     stitch_measure=4, units="in",
    ... )
    >>> convert_stitch_measure(40, pattern_gauge, my_gauge)
    30.0
    """
    # Convert my measurement to stitches in original gauge, then
    # use the new gauge to convert the stitch count back to a measurement
    return newGauge.stitches_to_measurement(
        oldGauge.measurement_to_stitches(measurement)
    )

@validate_arguments
def convert_row_measure(
    measurement: PositiveFloat, oldGauge: GaugeSwatch, newGauge: GaugeSwatch
) -> float:
    """
    Given a masurement in the original gauge, find out what it would
    be in the new gauge.  e.g. if the sweater was going to be 40 inches
    in pattern gauge, how much would it be in my gauge?

    >>> pattern_gauge = GaugeSwatch(
    ...     row_count=22, row_measure=3.75, stitch_count=18,
    ...     stitch_measure=4, units="in",
    ... )
    >>> my_gauge = GaugeSwatch(
    ...     row_count=18, row_measure=3.25, stitch_count=24,
    ...     stitch_measure=4, units="in",
    ... )
    >>> convert_row_measure(40, pattern_gauge, my_gauge)
    42.43055555555556
    """
    # Convert my measurement to stitches in original gauge, then
    # use the new gauge to convert the stitch count back to a measurement
    return newGauge.rows_to_measurement(
        oldGauge.measurement_to_rows(measurement)
    )
