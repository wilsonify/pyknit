# Copyright (C) 2026 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

"""Regression tests for the evidence-driven correctness review.

Each class maps to a review finding and locks the fixed behavior.
"""

import json
import logging

import pytest

import pyknit
from pyknit import io
from pyknit.browser import render_pattern
from pyknit.Chart import parse_chart, parse_row, plot_chart, render_chart_svg, stitch_legend
from pyknit.garment_model import build_raglan_model
from pyknit.GaugeSwatch import (
    GaugeSwatch,
    convert_row_measure,
    convert_stitch_measure,
)
from pyknit.Hat import Hat
from pyknit.shawl_shapes import generate_shawl


@pytest.fixture
def swatch_in():
    return GaugeSwatch(row_count=18, row_measure=3.25, stitch_count=24, stitch_measure=4, units="in")


@pytest.fixture
def swatch_cm():
    return GaugeSwatch(row_count=18, row_measure=8.0, stitch_count=24, stitch_measure=10.0, units="cm")


class TestGaugeConversionUnits:
    def test_same_unit_preserved(self, swatch_in):
        pattern = GaugeSwatch(row_count=22, row_measure=3.75, stitch_count=18, stitch_measure=4, units="in")
        assert convert_stitch_measure(40, pattern, swatch_in) == pytest.approx(30.0)

    def test_cross_unit_result_in_new_units(self, swatch_in, swatch_cm):
        # 4 inches at 6 sts/in = 24 sts; 24 sts at 2.4 sts/cm = 10 cm.
        assert convert_stitch_measure(4, swatch_in, swatch_cm) == pytest.approx(10.0)
        assert convert_row_measure(3.25, swatch_in, swatch_cm) == pytest.approx(8.0)

    def test_rounding_documented_single_stitch(self):
        # A fractional measurement rounds once to whole stitches.
        pattern = GaugeSwatch(row_count=22, row_measure=3.75, stitch_count=18, stitch_measure=4, units="in")
        mine = GaugeSwatch(row_count=18, row_measure=3.25, stitch_count=24, stitch_measure=4, units="in")
        assert mine.measurement_to_stitches(0.5) == round(0.5 * 6.0)
        assert convert_stitch_measure(0.5, pattern, mine) == pytest.approx(
            mine.stitches_to_measurement(pattern.measurement_to_stitches(0.5))
        )


class TestChartParsing:
    def test_whitespace_variants_equal(self):
        assert parse_row("k4 p4") == parse_row("  k4\tp4  ")
        assert parse_row("k  k") == parse_row("k k")

    def test_empty_row_returns_empty(self):
        assert parse_row("") == []
        assert parse_row("   ") == []

    def test_unknown_code_actionable(self):
        with pytest.raises(ValueError, match="Unknown stitch code 'zzz'"):
            parse_row("k zzz")

    def test_malformed_tokens_rejected(self):
        for bad in ("k-1", "4k", "k2tog!", "C2-2Lx9!"):
            with pytest.raises(ValueError, match="[Mm]alformed|Unknown"):
                parse_row(bad)

    def test_zero_repetition_rejected(self):
        with pytest.raises(ValueError, match="[Rr]epetition"):
            parse_row("k0")

    def test_excessive_repetition_rejected(self):
        with pytest.raises(ValueError, match="[Ll]imit|more than"):
            parse_row("k10001")

    def test_parse_chart_allows_blank_lines(self):
        pattern = parse_chart("k p\n\nk k")
        assert len(pattern) == 3
        assert pattern[1] == []


class TestChartRendering:
    def test_plot_chart_empty_rejected(self):
        with pytest.raises(ValueError, match="at least one row"):
            plot_chart([])

    def test_plot_chart_empty_row_rejected(self):
        with pytest.raises(ValueError, match="at least one stitch"):
            plot_chart([[]])

    def test_render_svg_empty_rejected(self):
        with pytest.raises(ValueError, match="at least one"):
            render_chart_svg([])

    def test_plot_chart_no_system_font_needed(self):
        image = plot_chart(parse_chart("k p\nk k"))
        assert image.width > 0 and image.height > 0

    def test_plot_chart_missing_symbol_falls_back(self):
        from pyknit.Chart import Stitch

        pattern = [[Stitch("missing", symbol="/no/such/missing.png", width=1)]]
        image = plot_chart(pattern)
        assert image.width > 0


class TestPackaging:
    def test_console_entry_point_resolves(self):
        import importlib

        mod_name, func_name = "pyknit.__main__:main".split(":")
        mod = importlib.import_module(mod_name)
        assert callable(getattr(mod, func_name))


class TestHatContract:
    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid starting parameters"):
            Hat().crown_decreases(0, 10)

    def test_valid_still_returns_list(self):
        instructions = Hat().crown_decreases(8, 24)
        assert isinstance(instructions, list)
        assert instructions[-1].startswith("Cut yarn")


class TestDecreaseValidation:
    def test_decrease_above_starting_count_names_problem(self):
        with pytest.raises(ValueError, match="bigger than the starting count"):
            pyknit.decrease_evenly(10, 11, in_the_round=True)

    def test_decrease_above_half_names_problem(self):
        with pytest.raises(ValueError, match="less than half"):
            pyknit.decrease_evenly(10, 6, in_the_round=True)

    def test_increase_above_start_has_message(self):
        with pytest.raises(ValueError, match="bigger than the starting count"):
            pyknit.increase_evenly(5, 6)

    def test_odd_times_format_uses_star(self):
        # 21 sts / 5 decreases -> mixed plan with odd groups on both sides.
        result = pyknit.decrease_evenly_round(21, 5)
        assert "] *" in result and "times" in result


class TestSockScheduling:
    def test_spread_positions_rejects_overcrowding(self):
        from pyknit.Sock import Sock

        sock = Sock()
        with pytest.raises(ValueError, match="Cannot spread"):
            sock._spread_positions(2, 5)

    def test_leg_plan_lands_exactly(self):
        from pyknit.Sock import Sock

        sock = Sock()
        sock.init()
        plan = sock.leg_decrease_plan()
        assert sum(removed for _, _, removed in plan) == sock.cast_on_stitches - sock.ankle_stitches
        rounds = [r for r, _, _ in plan]
        assert len(set(rounds)) == len(rounds)


class TestSerialization:
    def test_empty_csv_returns_empty(self):
        assert io.csv_to_pattern("", stitch_legend) == []
        assert io.csv_to_pattern("  \n ", stitch_legend) == []

    def test_blank_lines_skipped(self):
        pattern = parse_chart("k p\nk k")
        csv_string = "k,p\n\nk,k\n"
        assert io.csv_to_pattern(csv_string, stitch_legend) == pattern

    def test_unknown_code_names_position(self):
        with pytest.raises(KeyError, match="row 1, column 2"):
            io.csv_to_pattern("k,zzz\n", stitch_legend)

    def test_json_rejects_malformed_rows(self):
        with pytest.raises(ValueError, match="rows.*list"):
            io.json_to_pattern(json.dumps({"schema_version": 1, "legend": "default", "rows": "k"}))
        with pytest.raises(ValueError, match="must be a list"):
            io.json_to_pattern(json.dumps({"schema_version": 1, "legend": "default", "rows": ["k"]}))

    def test_json_unknown_code_keyerror(self):
        payload = json.dumps({"schema_version": 1, "legend": "default", "rows": [["k", "zzz"]]})
        with pytest.raises(KeyError):
            io.json_to_pattern(payload, stitch_legend)

    def test_round_trip(self):
        pattern = parse_chart("k p k\nkfb yo k2tog", stitch_legend)
        assert io.csv_to_pattern(io.pattern_to_csv(pattern, stitch_legend), stitch_legend) == pattern
        assert io.json_to_pattern(io.pattern_to_json(pattern, stitch_legend), stitch_legend) == pattern


class TestTriangleShawl:
    def test_final_count_matches_increase_math(self, swatch_in):
        import math

        instructions = generate_shawl("triangle", 20, 20, swatch_in)
        target = swatch_in.measurement_to_stitches(20)
        max_rows = swatch_in.measurement_to_rows(20)
        # Each row adds exactly TRIANGLE_INCREASE_PER_ROW (2) stitches.
        rows_done = min(max_rows, math.ceil((target - 3) / 2))
        assert instructions[-1] == f"Bind off all {3 + 2 * rows_done} stitches."
        assert instructions[0].startswith("Cast on 3 stitches")

    def test_invalid_dimensions_rejected(self, swatch_in):
        with pytest.raises(ValueError, match="[Pp]ositive"):
            generate_shawl("triangle", 0, 20, swatch_in)
        with pytest.raises(ValueError, match="[Pp]ositive"):
            generate_shawl("rectangle", 20, -1, swatch_in)

    def test_impossible_triangle_rejected(self, swatch_in):
        with pytest.raises(ValueError, match="[Tt]riangle|wider"):
            generate_shawl("triangle", 0.1, 20, swatch_in)


class TestBrowserFallback:
    def test_backend_failure_is_logged_and_falls_through(self, caplog):
        pattern = parse_chart("k p\nk k")

        def boom(_pattern, **_kwargs):
            raise RuntimeError("svg exploded")

        import pyknit.Chart as chart_module

        orig = chart_module.render_chart_svg
        chart_module.render_chart_svg = boom
        try:
            with caplog.at_level(logging.WARNING):
                fmt, content = render_pattern(pattern)
            assert fmt in ("png", "text")
            assert any("svg" in r.message and "exploded" in r.message for r in caplog.records)
        finally:
            chart_module.render_chart_svg = orig


class TestGarmentModel:
    def _meta(self):
        return {
            "neck": 80,
            "calc_neck": 80,
            "arm": 30,
            "bust": 100,
            "armpit": 4,
            "raglan_total_rounds": 8,
            "inc": 64,
            "seg": 8,
            "freq": "every_round",
            "working": 144,
            "body_stock_rounds": 50,
            "hem_rounds": 10,
            "sleeve_final": 34,
            "wrist": 26,
            "cuff_rounds": 8,
            "collar_rounds": 4,
            "pre": 0,
            "sleeve_shaping_rounds": 5,
        }

    def test_missing_keys_useful_error(self):
        with pytest.raises(ValueError, match="missing required keys: neck, arm"):
            build_raglan_model({})

    def test_sleeves_symmetric(self):
        model = build_raglan_model(self._meta())
        left = model.get_stage(model.stages[5].stage_type)
        right = [s for s in model.stages if s.label == "Right Sleeve"][0]
        assert [o.to_dict() for o in left.operations] == [o.to_dict() for o in right.operations]


class TestStitchHelpers:
    def test_box_writes_bordered_file(self, tmp_path):
        from pyknit.Stitches import box

        out = box(str(tmp_path / "sym"), 50, 50, 1)
        assert out.endswith(".png")
        from PIL import Image

        with Image.open(out) as img:
            assert img.size == (50, 50)
            # Border drawn: corner pixel is the black outline, not blank white.
            assert img.getpixel((0, 0)) == (0, 0, 0)

    def test_cable_returns_paths(self, tmp_path):
        from pyknit.Stitches import cable

        paths = cable(str(tmp_path / "c"), 10, 10, 1, 1)
        assert len(paths) == 2
        import os

        assert all(os.path.isfile(p) for p in paths)

    def test_empty_fname_rejected(self):
        from pyknit.Stitches import box, cable

        with pytest.raises(ValueError, match="non-empty"):
            box("", 50, 50, 1)
        with pytest.raises(ValueError, match="non-empty"):
            cable("", 10, 10, 1, 1)


class TestStitchSharingContract:
    def test_parsed_cells_share_legend_instances(self):
        row = parse_row("k p")
        assert row[0] is stitch_legend["k"]
        assert row[1] is stitch_legend["p"]
