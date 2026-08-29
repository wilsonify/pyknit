# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

"""
pyKnit: a set of tools for knitters to do math, create charts, customise
patterns and more

pyKnit.GaugeSwatch: Tools for measurement and gauge swatching
"""

from typing import TYPE_CHECKING, Literal, Optional

from pydantic import BaseModel, PositiveFloat, PositiveInt, validate_arguments

if TYPE_CHECKING:
    from .Chart import PatternRow


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
        return float(rows) / self.row_gauge()

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
        return float(stitches) / self.stitch_gauge()

    @validate_arguments
    def estimate_yardage(self, stitch_count: PositiveInt) -> float:
        """Estimate yarn length needed for stitch_count stitches.

        Scales ``yardage_per_unit`` (yarn length per stitch, e.g. metres per
        stitch) by the number of stitches. Raises ValueError when
        ``yardage_per_unit`` has not been set on this swatch.
        """
        if self.yardage_per_unit is None:
            raise ValueError("yardage_per_unit not set on this swatch")
        yardage = self.yardage_per_unit
        return yardage * stitch_count

    @validate_arguments
    def estimate_weight(self, stitch_count: PositiveInt) -> float:
        """Estimate yarn weight needed for stitch_count stitches.

        Scales ``weight_per_unit`` (yarn weight per stitch, e.g. grams per
        stitch) by the number of stitches. Raises ValueError when
        ``weight_per_unit`` has not been set on this swatch.
        """
        if self.weight_per_unit is None:
            raise ValueError("weight_per_unit not set on this swatch")
        weight = self.weight_per_unit
        return weight * stitch_count


# Gauge and stich count related functions


def stitch_operations(row: "PatternRow") -> int:
    """Count the number of stitch operations/symbols in a row.

    This counts the number of distinct stitch objects in the row,
    preserving duplicates and order. Useful for counting chart cells
    or display width.

    Args:
        row: List of Stitch objects representing a knitting row

    Returns:
        The number of stitch symbols in the row

    Examples:
        >>> from pyknit.Chart import stitch_legend, parse_row
        >>> row = parse_row("k k k p")
        >>> stitch_operations(row)
        4
        >>> row = parse_row("k2tog yo")
        >>> stitch_operations(row)
        2
    """
    return len(row)


def stitches_consumed(row: "PatternRow") -> int:
    """Count the total number of stitches consumed by a row.

    Stitches consumed = the number of working stitches used up
    by executing the row. For most stitches this is 1, but decreases
    consume multiple stitches (e.g., k2tog consumes 2).
    Yarn-overs and no-stitch operations consume 0.

    Args:
        row: List of Stitch objects representing a knitting row

    Returns:
        Total stitches consumed by all operations in the row

    Examples:
        >>> from pyknit.Chart import stitch_legend, parse_row
        >>> row = parse_row("k k k p")
        >>> stitches_consumed(row)
        4
        >>> row = parse_row("k2tog yo")  # 2tog consumes 2, yo consumes 0
        >>> stitches_consumed(row)
        2
    """
    return sum(stitch.consumes for stitch in row)


def stitches_produced(row: "PatternRow") -> int:
    """Count the total number of stitches produced by a row.

    Stitches produced = the number of working stitches created
    by executing the row. For most stitches this is 1, but increases
    produce multiple stitches (e.g., kfb produces 2).
    Decreases produce fewer stitches (e.g., k2tog produces 1).
    Yarn-overs produce 1, and no-stitch operations produce 0.

    Args:
        row: List of Stitch objects representing a knitting row

    Returns:
        Total stitches produced by all operations in the row

    Examples:
        >>> from pyknit.Chart import stitch_legend, parse_row
        >>> row = parse_row("k k k p")
        >>> stitches_produced(row)
        4
        >>> row = parse_row("kfb k2tog")  # kfb produces 2, k2tog produces 1
        >>> stitches_produced(row)
        3
    """
    return sum(stitch.produces for stitch in row)


def chart_width(row: "PatternRow") -> int:
    """Calculate the display width of a row in chart cells.

    The width is determined by the sum of the width attributes
    of all stitches. Most stitches have width=1, but multi-stitch
    cables may have width > 1 (e.g., a 4-stitch cable has width=4).

    Args:
        row: List of Stitch objects representing a knitting row

    Returns:
        Total display width in chart cells

    Examples:
        >>> from pyknit.Chart import stitch_legend, parse_row
        >>> row = parse_row("k k k p")
        >>> chart_width(row)
        4
        >>> row = parse_row("C2-2L")  # Cable with width=4
        >>> chart_width(row)
        4
    """
    return sum(stitch.width for stitch in row)


def stitch_count(row: "PatternRow") -> int:
    """Deprecated: Count stitch operations in a row.

    This function is kept for backward compatibility but is ambiguous.
    For a knitting row (PatternRow), it returns the number of stitch
    operations, which is equivalent to stitch_operations().

    New code should use:
    - stitch_operations() for number of symbols
    - stitches_consumed() for stitches consumed by execution
    - stitches_produced() for stitches produced by execution
    - chart_width() for display width

    Args:
        row: List of Stitch objects representing a knitting row

    Returns:
        The number of stitch operations/symbols in the row

    Note:
        The original implementation took a Set[str] which was incorrect
        (sets remove duplicates and lose order). This version accepts
        PatternRow (List[Stitch]) instead.
    """
    return stitch_operations(row)


@validate_arguments
def convert_stitch_measure(measurement: PositiveFloat, old_gauge: GaugeSwatch, new_gauge: GaugeSwatch) -> float:
    """
    Given a measurement in the original gauge, find out what it would
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
    return new_gauge.stitches_to_measurement(old_gauge.measurement_to_stitches(measurement))


@validate_arguments
def convert_row_measure(measurement: PositiveFloat, old_gauge: GaugeSwatch, new_gauge: GaugeSwatch) -> float:
    """
    Given a measurement in the original gauge, find out what it would
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
    return new_gauge.rows_to_measurement(old_gauge.measurement_to_rows(measurement))
