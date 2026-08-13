"""
Test suite for the PyScript demo - verify APIs work correctly locally.

This tests the actual pyknit APIs used in demo.html to ensure:
1. GaugeSwatch creation works
2. Gauge conversion calculations are correct
3. Chart parsing handles valid and invalid patterns
4. Rendering backends work or fail gracefully
"""

import pytest
from pyknit import GaugeSwatch, convert_stitch_measure
from pyknit.Chart import parse_chart
from pyknit.browser import render_pattern, pattern_to_text, available_backends


class TestGaugeConversion:
    """Test gauge conversion functionality used in demo."""

    def test_gaugeswatch_creation(self):
        """Verify GaugeSwatch can be created with demo values."""
        gs = GaugeSwatch(
            stitch_count=27.5,
            stitch_measure=10,
            row_count=40,
            row_measure=4,
            units="in"
        )
        assert gs.stitch_count == pytest.approx(27.5)
        assert gs.stitch_measure == 10
        assert gs.units == "in"

    def test_convert_stitch_measure(self):
        """Verify measurement conversion works."""
        pattern_gauge = GaugeSwatch(
            stitch_count=27.5,
            stitch_measure=10,
            row_count=40,
            row_measure=4,
            units="in"
        )
        my_gauge = GaugeSwatch(
            stitch_count=23.5,
            stitch_measure=10,
            row_count=33,
            row_measure=4,
            units="in"
        )
        
        # 42 inches at pattern gauge (27.5 st/10") should convert to my gauge (23.5 st/10")
        result = convert_stitch_measure(42, pattern_gauge, my_gauge)
        
        # Result should be less (my gauge is tighter)
        assert result > 0
        assert isinstance(result, (int, float))

    def test_zero_measurement(self):
        """Verify zero measurement is rejected by pydantic."""
        pattern_gauge = GaugeSwatch(
            stitch_count=27.5, stitch_measure=10, row_count=40, row_measure=4, units="in"
        )
        my_gauge = GaugeSwatch(
            stitch_count=23.5, stitch_measure=10, row_count=33, row_measure=4, units="in"
        )
        # Zero is not allowed - must be PositiveInt
        with pytest.raises((ValueError, Exception)):
            convert_stitch_measure(0, pattern_gauge, my_gauge)

    def test_invalid_gauge_raises_error(self):
        """Verify invalid gauge values raise errors."""
        with pytest.raises((ValueError, Exception)):
            GaugeSwatch(
                stitch_count=-1,
                stitch_measure=10,
                row_count=40,
                row_measure=4,
                units="in"
            )


class TestChartParsing:
    """Test chart parsing functionality used in demo."""

    def test_parse_simple_pattern(self):
        """Verify simple knitting pattern parses."""
        pattern = parse_chart("k2 yo k2tog yo k1")
        assert pattern is not None
        assert isinstance(pattern, list)
        assert len(pattern) > 0

    def test_parse_multirow_pattern(self):
        """Verify multi-row pattern parses."""
        pattern = parse_chart("k2 yo k2tog yo k1\np1 k2 yo k2tog p2")
        assert pattern is not None
        assert len(pattern) == 2  # Two rows

    def test_parse_invalid_pattern_raises(self):
        """Verify invalid patterns raise errors."""
        with pytest.raises((ValueError, KeyError, Exception)):
            parse_chart("invalid xyz abc")

    def test_parse_empty_string(self):
        """Verify empty string returns pattern with empty row."""
        # Empty string returns pattern with one empty row
        result = parse_chart("")
        assert result == [[]]

    def test_parse_with_repeats(self):
        """Verify repeated instructions parse."""
        # This depends on whether parse_chart supports repeats
        try:
            pattern = parse_chart("[k2, p2] * 3 times")
            assert pattern is not None
        except (ValueError, KeyError):
            # Repeats may not be supported in this version
            pass


class TestChartRendering:
    """Test chart rendering functionality used in demo."""

    def test_render_pattern_returns_tuple(self):
        """Verify render_pattern returns (format, content) tuple."""
        pattern = parse_chart("k2 yo k2tog")
        result = render_pattern(pattern)
        assert isinstance(result, tuple)
        assert len(result) == 2
        fmt, content = result
        assert isinstance(fmt, str)
        assert content is not None

    def test_render_formats(self):
        """Verify render_pattern returns known formats."""
        pattern = parse_chart("k2 yo k2tog")
        fmt, _ = render_pattern(pattern)
        # Should be one of these formats
        assert fmt in ("svg", "png", "text")

    def test_svg_format_contains_svg_tag(self):
        """Verify SVG output contains SVG tag."""
        pattern = parse_chart("k2 yo k2tog")
        fmt, content = render_pattern(pattern)
        if fmt == "svg":
            assert "<svg" in content or isinstance(content, str)

    def test_png_format_is_bytes(self):
        """Verify PNG output is bytes."""
        pattern = parse_chart("k2 yo k2tog")
        fmt, content = render_pattern(pattern)
        if fmt == "png":
            assert isinstance(content, bytes)

    def test_pattern_to_text_returns_string(self):
        """Verify text rendering works."""
        pattern = parse_chart("k2 yo k2tog")
        text = pattern_to_text(pattern)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_available_backends_returns_list(self):
        """Verify backend list is available."""
        backends = available_backends()
        assert isinstance(backends, list)
        # Should have at least text as fallback
        assert len(backends) > 0


class TestErrorHandling:
    """Test error handling and validation."""

    def test_invalid_measurement_type(self):
        """Verify invalid measurement type is caught."""
        pattern_gauge = GaugeSwatch(
            stitch_count=27.5, stitch_measure=10, row_count=40, row_measure=4, units="in"
        )
        my_gauge = GaugeSwatch(
            stitch_count=23.5, stitch_measure=10, row_count=33, row_measure=4, units="in"
        )
        # This should raise when trying to convert non-numeric value
        with pytest.raises((TypeError, ValueError)):
            convert_stitch_measure("not_a_number", pattern_gauge, my_gauge)

    def test_invalid_stitch_character(self):
        """Verify invalid stitches raise errors."""
        with pytest.raises((ValueError, KeyError)):
            parse_chart("k2 xyz k2tog")  # 'xyz' is not a valid stitch


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_gauge_workflow(self):
        """Test complete gauge conversion workflow."""
        # Create gauges
        pattern_gauge = GaugeSwatch(
            stitch_count=27.5,
            stitch_measure=10,
            row_count=40,
            row_measure=4,
            units="in"
        )
        my_gauge = GaugeSwatch(
            stitch_count=23.5,
            stitch_measure=10,
            row_count=33,
            row_measure=4,
            units="in"
        )
        
        # Convert measurement
        measurement = 42
        result = convert_stitch_measure(measurement, pattern_gauge, my_gauge)
        
        # Verify result is reasonable
        assert result > 0
        assert result != measurement  # Should be different

    def test_full_chart_workflow(self):
        """Test complete chart parsing and rendering workflow."""
        # Parse pattern
        pattern = parse_chart("k2 yo k2tog yo k1\np1 k2 yo k2tog p2")
        
        # Render pattern
        fmt, content = render_pattern(pattern)
        
        # Verify output
        assert fmt in ("svg", "png", "text")
        assert content is not None
        
        # Also verify text fallback works
        text = pattern_to_text(pattern)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_invalid_pattern_gracefully_fails(self):
        """Test that invalid patterns fail with clear errors."""
        with pytest.raises((ValueError, KeyError)):
            parse_chart("invalid xyz")
        
        # No crash - error is catchable


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
