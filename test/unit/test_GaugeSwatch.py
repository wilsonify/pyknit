# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

# !python

import pytest

from pyknit.Chart import parse_row, stitch_legend
from pyknit.GaugeSwatch import (
    GaugeSwatch,
    chart_width,
    stitch_count,
    stitch_operations,
    stitches_consumed,
    stitches_produced,
)


def test_init():
    gs = GaugeSwatch(row_count=18, row_measure=3.25, stitch_count=24, stitch_measure=4, units="in")
    assert isinstance(gs, GaugeSwatch)
    assert gs.row_count == 18
    assert gs.row_measure == pytest.approx(3.25)
    assert gs.stitch_count == 24
    assert gs.stitch_measure == 4
    assert gs.units == "in"


@pytest.fixture
def example_gauge_swatches():
    gs_good_1 = GaugeSwatch(row_count=22, row_measure=3.75, stitch_count=18, stitch_measure=4, units="in")
    gs_good_2 = GaugeSwatch(row_count=18, row_measure=3.25, stitch_count=24, stitch_measure=4, units="in")
    return [gs_good_1, gs_good_2]


def test_row_gauge(example_gauge_swatches):
    expected = [22 / 3.75, 18 / 3.25]
    computed = [gs.row_gauge() for gs in example_gauge_swatches]
    assert computed == expected


def test_stitch_gauge(example_gauge_swatches):
    expected = [18 / 4, 24 / 4]
    computed = [gs.stitch_gauge() for gs in example_gauge_swatches]
    assert computed == expected


@pytest.fixture
def swatch():
    return GaugeSwatch(row_count=18, row_measure=3.25, stitch_count=24, stitch_measure=4, units="in")


class TestGaugeSwatch:

    def test_row_gauge(self, swatch):
        assert swatch.row_gauge() == pytest.approx(18 / 3.25)

    def test_stitch_gauge(self, swatch):
        assert swatch.stitch_gauge() == 24 / 4

    def test_measurement_to_stitches(self, swatch):
        assert swatch.measurement_to_stitches(5) == 30

    def test_measurement_to_rows(self, swatch):
        assert swatch.measurement_to_rows(11) == 61

    def test_rows_to_measurement(self, swatch):
        assert swatch.rows_to_measurement(10) == pytest.approx(10 / (18 / 3.25))

    def test_stitches_to_measurement(self, swatch):
        assert swatch.stitches_to_measurement(18) == 3


# Tests for stitch counting functions

class TestStitchCountingFunctions:
    """Test explicit stitch counting APIs that distinguish different concepts."""

    def test_stitch_operations_simple_row(self):
        """Count stitch operations/symbols in a simple row."""
        row = parse_row("k k k p", stitch_legend)
        assert stitch_operations(row) == 4
        # Verify it matches row length
        assert stitch_operations(row) == len(row)

    def test_stitch_operations_with_decreases(self):
        """Count operations including decreases (k2tog is one operation)."""
        row = parse_row("k2tog k2tog", stitch_legend)
        assert stitch_operations(row) == 2
        # But they consume and produce differently
        assert stitches_consumed(row) == 4
        assert stitches_produced(row) == 2

    def test_stitch_operations_with_increases(self):
        """Count operations including increases (kfb is one operation)."""
        row = parse_row("kfb kfb", stitch_legend)
        assert stitch_operations(row) == 2
        # Each kfb consumes 1 but produces 2
        assert stitches_consumed(row) == 2
        assert stitches_produced(row) == 4

    def test_stitch_operations_with_yarn_over(self):
        """Count operations with yarn-overs."""
        row = parse_row("yo yo k", stitch_legend)
        assert stitch_operations(row) == 3

    def test_stitches_consumed_basic(self):
        """Basic knit and purl rows consume 1 stitch each."""
        row = parse_row("k k k p", stitch_legend)
        assert stitches_consumed(row) == 4

    def test_stitches_consumed_decrease(self):
        """k2tog and ssk decrease consume 2 stitches."""
        k2tog_row = parse_row("k2tog k", stitch_legend)
        assert stitches_consumed(k2tog_row) == 3  # 2 + 1
        
        ssk_row = parse_row("ssk k", stitch_legend)
        assert stitches_consumed(ssk_row) == 3  # 2 + 1

    def test_stitches_consumed_yarn_over(self):
        """Yarn-overs consume 0 stitches."""
        row = parse_row("yo yo k", stitch_legend)
        assert stitches_consumed(row) == 1  # Only 'k' consumes

    def test_stitches_consumed_mixed(self):
        """Mixed row with increases, decreases, and yo."""
        row = parse_row("k2tog kfb yo k", stitch_legend)
        # k2tog consumes 2, kfb consumes 1, yo consumes 0, k consumes 1
        assert stitches_consumed(row) == 4

    def test_stitches_produced_basic(self):
        """Basic knit and purl rows produce 1 stitch each."""
        row = parse_row("k k k p", stitch_legend)
        assert stitches_produced(row) == 4

    def test_stitches_produced_increase(self):
        """kfb increases produce 2 stitches."""
        row = parse_row("kfb k", stitch_legend)
        assert stitches_produced(row) == 3  # 2 + 1

    def test_stitches_produced_decrease(self):
        """Decreases produce 1 stitch."""
        k2tog_row = parse_row("k2tog k", stitch_legend)
        assert stitches_produced(k2tog_row) == 2  # 1 + 1
        
        ssk_row = parse_row("ssk k", stitch_legend)
        assert stitches_produced(ssk_row) == 2  # 1 + 1

    def test_stitches_produced_yarn_over(self):
        """Yarn-overs produce 1 stitch."""
        row = parse_row("yo yo k", stitch_legend)
        assert stitches_produced(row) == 3  # 1 + 1 + 1

    def test_stitches_produced_mixed(self):
        """Mixed row with increases, decreases, and yo."""
        row = parse_row("k2tog kfb yo k", stitch_legend)
        # k2tog produces 1, kfb produces 2, yo produces 1, k produces 1
        assert stitches_produced(row) == 5

    def test_chart_width_simple(self):
        """Chart width for simple stitches."""
        row = parse_row("k k k p", stitch_legend)
        assert chart_width(row) == 4

    def test_chart_width_cable(self):
        """Cables have width > 1."""
        # C1-1L has width=2
        row = parse_row("C1-1L", stitch_legend)
        assert chart_width(row) == 2
        
        # C2-2L has width=4
        row = parse_row("C2-2L", stitch_legend)
        assert chart_width(row) == 4

    def test_chart_width_mixed(self):
        """Mixed row with different widths."""
        # C1-1L (width=2) + two k (width=1 each)
        row = parse_row("C1-1L k k", stitch_legend)
        assert chart_width(row) == 4

    def test_stitch_count_backward_compatibility(self):
        """stitch_count() works with PatternRow for backward compatibility."""
        row = parse_row("k k k p", stitch_legend)
        # Should return same as stitch_operations
        assert stitch_count(row) == stitch_operations(row)
        assert stitch_count(row) == 4

    def test_stitch_count_preserves_order_and_duplicates(self):
        """Verify that repeated stitches are counted correctly."""
        # The key fix: Set[str] loses duplicates, but PatternRow preserves them
        row = parse_row("k k k k", stitch_legend)
        # All four stitches should be counted
        assert stitch_operations(row) == 4
        assert stitch_count(row) == 4

    def test_row_consumed_produced_balance(self):
        """Verify consumed/produced accounting for a balanced row."""
        # A row that consumes 10 and produces 10 stitches
        row = parse_row("k k k k k k k k k k", stitch_legend)
        assert stitches_consumed(row) == 10
        assert stitches_produced(row) == 10

    def test_row_with_increase_decrease_imbalance(self):
        """Verify consumed/produced for rows with increases/decreases."""
        # Row that increases: 10 consumed, 11 produced
        row = parse_row("k k k k k k k k k kfb", stitch_legend)
        assert stitches_consumed(row) == 10
        assert stitches_produced(row) == 11
        
        # Row that decreases: 11 consumed, 10 produced
        # We need to have 11 consumed, so use 10 k + 1 k2tog (which consumes 2)
        row = parse_row("k k k k k k k k k k2tog", stitch_legend)
        assert stitches_consumed(row) == 11  # 9x1 + 2 = 11
        assert stitches_produced(row) == 10  # 9x1 + 1 = 10

    def test_complex_pattern(self):
        """Test a complex pattern with multiple operations."""
        row = parse_row("k2tog kfb ssk yo p", stitch_legend)
        # Operations: 5
        assert stitch_operations(row) == 5
        # Consumed: 2 + 1 + 2 + 0 + 1 = 6
        assert stitches_consumed(row) == 6
        # Produced: 1 + 2 + 1 + 1 + 1 = 6
        assert stitches_produced(row) == 6
        # Width: 1 + 1 + 1 + 1 + 1 = 5
        assert chart_width(row) == 5
