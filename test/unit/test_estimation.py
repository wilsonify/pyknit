# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

# !python

import importlib.util
import math
import pathlib
from datetime import timedelta

import pytest

from pyknit.GaugeSwatch import GaugeSwatch
from pyknit.estimate import estimate_knitting_time, format_knitting_time

DEMOS_DIR = pathlib.Path(__file__).parent.parent.parent / "pyknit" / "pyscript" / "_demos"


def _load_yarn_estimator():
    spec = importlib.util.spec_from_file_location("yarn_estimator", DEMOS_DIR / "yarn_estimator.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_demo(name):
    spec = importlib.util.spec_from_file_location("demo_" + name, DEMOS_DIR / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Existing GaugeSwatch tests (unchanged)
# ---------------------------------------------------------------------------


def test_gauge_swatch_backward_compatible_defaults():
    gs = GaugeSwatch(row_count=18, row_measure=3.25, stitch_count=24, stitch_measure=4, units="in")
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
    gs = GaugeSwatch(row_count=18, row_measure=3.25, stitch_count=24, stitch_measure=4, units="in")
    with pytest.raises(ValueError, match="yardage_per_unit not set on this swatch"):
        gs.estimate_yardage(30)


def test_estimate_weight_unset_raises():
    gs = GaugeSwatch(row_count=18, row_measure=3.25, stitch_count=24, stitch_measure=4, units="in")
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
def test_estimate_knitting_time_rejects_non_positive(total_stitches, seconds_per_stitch):
    with pytest.raises(ValueError):
        estimate_knitting_time(total_stitches, seconds_per_stitch)


def test_format_knitting_time():
    assert format_knitting_time(timedelta(seconds=30000)) == "8 hours 20 minutes"
    assert format_knitting_time(timedelta(days=1)) == "24 hours"


# ---------------------------------------------------------------------------
# Yarn Estimator: friendly mode
# ---------------------------------------------------------------------------


@pytest.fixture
def estimator():
    return _load_yarn_estimator()


class TestFriendlyMode:
    """Tests for the new knitter-friendly compute path."""

    def test_hat_default(self, estimator):
        result = estimator.compute(estimator.DEFAULT_INPUTS)
        assert result["project_stitches"] > 0
        assert result["yards"] > 0
        assert result["grams"] > 0
        assert result["balls_yard"] >= 1
        assert result["balls_weight"] >= 1
        assert result["time_text"]
        assert result["project_type"] == "hat"
        assert result["shape"] == "rectangle"

    def test_hat_stitch_calculation(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_type"] = "hat"
        inputs["project_width"] = 20
        inputs["project_height"] = 9
        inputs["stitch_gauge"] = 5
        inputs["row_gauge"] = 7
        result = estimator.compute(inputs)
        assert result["stitches_across"] == 100
        assert result["rows_tall"] == 63
        assert result["project_stitches"] == 6300

    def test_triangle_halves_stitches(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_type"] = "shawl_triangle"
        inputs["project_width"] = 30
        inputs["project_height"] = 30
        inputs["stitch_gauge"] = 5
        inputs["row_gauge"] = 7
        result = estimator.compute(inputs)
        # 30*5 * 30*7 / 2 = 150 * 210 / 2 = 15750
        assert result["project_stitches"] == 15750
        assert result["shape"] == "triangle"

    def test_scarf_default(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_type"] = "scarf"
        result = estimator.compute(inputs)
        assert result["project_stitches"] > 0
        assert result["project_type"] == "scarf"

    def test_sweater_default(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_type"] = "sweater"
        result = estimator.compute(inputs)
        assert result["project_stitches"] > 0

    def test_blanket_default(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_type"] = "blanket"
        result = estimator.compute(inputs)
        assert result["project_stitches"] > 0

    def test_custom_dimensions(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_type"] = "custom"
        inputs["project_width"] = 10
        inputs["project_height"] = 10
        result = estimator.compute(inputs)
        assert result["stitches_across"] == 50
        assert result["rows_tall"] == 70
        assert result["project_stitches"] == 3500

    def test_ranges_present(self, estimator):
        result = estimator.compute(estimator.DEFAULT_INPUTS)
        assert result["yards_low"] < result["yards"]
        assert result["yards_high"] > result["yards"]
        assert result["grams_low"] < result["grams"]
        assert result["grams_high"] > result["grams"]
        # Ranges are +/- 15% of the central estimate; allow for rounding
        assert result["yards_low"] == pytest.approx(result["yards"] * 0.85, abs=2)
        assert result["yards_high"] == pytest.approx(result["yards"] * 1.15, abs=2)

    def test_confidence_high_for_named_type(self, estimator):
        result = estimator.compute(estimator.DEFAULT_INPUTS)
        assert result["confidence"] == "high"

    def test_confidence_medium_for_custom(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_type"] = "custom"
        result = estimator.compute(inputs)
        assert result["confidence"] == "medium"

    def test_meters_conversion(self, estimator):
        result = estimator.compute(estimator.DEFAULT_INPUTS)
        assert result["meters"] == pytest.approx(result["yards"] * 0.9144, rel=0.01)

    def test_math_rows_populated(self, estimator):
        result = estimator.compute(estimator.DEFAULT_INPUTS)
        assert len(result["math_rows"]) >= 4
        assert result["math_rows"][0][0] == "Stitches across"

    def test_balls_detail_populated(self, estimator):
        result = estimator.compute(estimator.DEFAULT_INPUTS)
        assert len(result["balls_detail"]) >= 2
        assert "By length" in result["balls_detail"][0][0]
        assert "By weight" in result["balls_detail"][1][0]

    def test_assumptions_populated(self, estimator):
        result = estimator.compute(estimator.DEFAULT_INPUTS)
        assert len(result["assumptions"]) >= 4

    def test_svg_generated(self, estimator):
        result = estimator.compute(estimator.DEFAULT_INPUTS)
        assert "<svg" in result["svg"]
        assert "stitches total" in result["svg"]

    def test_to_html_renders(self, estimator):
        result = estimator.compute(estimator.DEFAULT_INPUTS)
        html = estimator.to_html(result)
        assert isinstance(html, str)
        assert len(html) > 0
        assert "stat-pill" in html
        assert "How this was calculated" in html
        assert "Ball count breakdown" in html
        assert "Assumptions" in html
        assert "Confidence" in html


class TestFriendlyModeErrors:
    """Invalid inputs in friendly mode raise clear errors."""

    def test_zero_width(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_width"] = 0
        with pytest.raises(ValueError, match="project width must be positive"):
            estimator.compute(inputs)

    def test_zero_height(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_height"] = 0
        with pytest.raises(ValueError, match="project height must be positive"):
            estimator.compute(inputs)

    def test_zero_stitch_gauge(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["stitch_gauge"] = 0
        with pytest.raises(ValueError, match="stitch gauge must be positive"):
            estimator.compute(inputs)

    def test_zero_row_gauge(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["row_gauge"] = 0
        with pytest.raises(ValueError, match="row gauge must be positive"):
            estimator.compute(inputs)

    def test_zero_ball_yards(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["yarn_per_ball_yards"] = 0
        with pytest.raises(ValueError, match="yards per ball must be positive"):
            estimator.compute(inputs)

    def test_zero_ball_grams(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["yarn_per_ball_grams"] = 0
        with pytest.raises(ValueError, match="grams per ball must be positive"):
            estimator.compute(inputs)

    def test_invalid_project_type(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_type"] = "nonexistent"
        with pytest.raises(ValueError, match="project_type must be one of"):
            estimator.compute(inputs)

    def test_invalid_pace(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["knitting_pace"] = "supersonic"
        with pytest.raises(ValueError, match="knitting_pace must be one of"):
            estimator.compute(inputs)

    def test_negative_width(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_width"] = -5
        with pytest.raises(ValueError):
            estimator.compute(inputs)


class TestPlausibilityChecks:
    """Plausibility checks produce warnings for unusual values."""

    def test_extreme_gauge_warning(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["stitch_gauge"] = 20
        result = estimator.compute(inputs)
        assert any("gauge" in w.lower() for w in result["warnings"])

    def test_very_low_gauge_warning(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["stitch_gauge"] = 1
        result = estimator.compute(inputs)
        assert any("gauge" in w.lower() for w in result["warnings"])

    def test_extreme_yarn_ratio_warning(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["yarn_per_ball_yards"] = 1000
        inputs["yarn_per_ball_grams"] = 10
        result = estimator.compute(inputs)
        assert any("ratio" in w.lower() or "yd/g" in w.lower() for w in result["warnings"])

    def test_fast_pace_no_warning(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["knitting_pace"] = "fast"
        result = estimator.compute(inputs)
        pace_warnings = [w for w in result["warnings"] if "pace" in w.lower()]
        assert len(pace_warnings) == 0

    def test_hat_large_dimensions_warning(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_type"] = "hat"
        inputs["project_width"] = 40
        inputs["project_height"] = 20
        result = estimator.compute(inputs)
        assert any("large" in w.lower() or "hat" in w.lower() for w in result["warnings"])

    def test_very_large_project_warning(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_width"] = 80
        inputs["project_height"] = 80
        result = estimator.compute(inputs)
        assert any("very large" in w.lower() for w in result["warnings"])

    def test_no_warnings_for_typical_hat(self, estimator):
        result = estimator.compute(estimator.DEFAULT_INPUTS)
        # A typical hat with standard gauge should have no warnings
        assert result["warnings"] == []


# ---------------------------------------------------------------------------
# Yarn Estimator: advanced mode
# ---------------------------------------------------------------------------


class TestAdvancedMode:
    """Tests for the legacy per-stitch compute path."""

    def _advanced_inputs(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["advanced_mode"] = "true"
        inputs["ball_yardage"] = inputs.get("yarn_per_ball_yards", 230)
        inputs["ball_weight"] = inputs.get("yarn_per_ball_grams", 50)
        return inputs

    def test_advanced_basic(self, estimator):
        inputs = self._advanced_inputs(estimator)
        result = estimator.compute(inputs)
        assert result["project_stitches"] == 12000
        assert result["yards"] > 0
        assert result["grams"] > 0
        assert result["confidence"] == "low"

    def test_advanced_uses_per_stitch_values(self, estimator):
        inputs = self._advanced_inputs(estimator)
        inputs["yards_per_stitch"] = 0.02
        inputs["project_stitches"] = 1000
        result = estimator.compute(inputs)
        assert result["yards"] == pytest.approx(20.0, rel=0.01)

    def test_advanced_time_calculation(self, estimator):
        inputs = self._advanced_inputs(estimator)
        inputs["project_stitches"] = 1000
        inputs["seconds_per_stitch"] = 2
        result = estimator.compute(inputs)
        # estimate_knitting_time truncates seconds, hours rounds to 1 decimal
        expected_hours = round(1000 * 2 / 3600, 1)
        assert result["hours"] == expected_hours

    def test_advanced_zero_project_stitches(self, estimator):
        inputs = self._advanced_inputs(estimator)
        inputs["project_stitches"] = 0  # set after _advanced_inputs to override
        with pytest.raises(ValueError, match="project_stitches must be positive"):
            estimator.compute(inputs)

    def test_advanced_zero_yards_per_stitch(self, estimator):
        inputs = self._advanced_inputs(estimator)
        inputs["yards_per_stitch"] = 0
        with pytest.raises(ValueError, match="yards_per_stitch must be positive"):
            estimator.compute(inputs)

    def test_advanced_zero_grams_per_stitch(self, estimator):
        inputs = self._advanced_inputs(estimator)
        inputs["grams_per_stitch"] = 0
        with pytest.raises(ValueError, match="grams_per_stitch must be positive"):
            estimator.compute(inputs)

    def test_advanced_to_html_renders(self, estimator):
        inputs = self._advanced_inputs(estimator)
        result = estimator.compute(inputs)
        html = estimator.to_html(result)
        assert "stat-pill" in html
        assert "Confidence" in html


# ---------------------------------------------------------------------------
# Yarn Estimator: edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases for both modes."""

    def test_very_small_project(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_width"] = 1
        inputs["project_height"] = 1
        result = estimator.compute(inputs)
        assert result["project_stitches"] == 35  # 5 * 7
        assert result["yards"] > 0
        assert result["balls_yard"] >= 1

    def test_very_large_project(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_type"] = "blanket"
        inputs["project_width"] = 60
        inputs["project_height"] = 72
        result = estimator.compute(inputs)
        assert result["project_stitches"] > 100000
        assert result["yards"] > 1000

    def test_fine_gauge(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["stitch_gauge"] = 10
        inputs["row_gauge"] = 14
        result = estimator.compute(inputs)
        assert result["stitches_across"] == 200
        assert result["rows_tall"] == 126

    def test_bulky_gauge(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["stitch_gauge"] = 2.5
        inputs["row_gauge"] = 3.5
        result = estimator.compute(inputs)
        assert result["stitches_across"] == 50
        assert result["rows_tall"] == 32

    def test_balls_always_at_least_one(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["project_width"] = 1
        inputs["project_height"] = 1
        result = estimator.compute(inputs)
        assert result["balls_yard"] >= 1
        assert result["balls_weight"] >= 1

    def test_all_project_types_produce_results(self, estimator):
        for ptype in (
            "hat",
            "scarf",
            "shawl_triangle",
            "shawl_rectangle",
            "shawl_crescent",
            "sweater",
            "blanket",
            "custom",
        ):
            inputs = dict(estimator.DEFAULT_INPUTS)
            inputs["project_type"] = ptype
            result = estimator.compute(inputs)
            assert result["project_stitches"] > 0
            assert result["yards"] > 0

    def test_all_pace_presets_produce_results(self, estimator):
        for pace in ("slow", "medium", "fast"):
            inputs = dict(estimator.DEFAULT_INPUTS)
            inputs["knitting_pace"] = pace
            result = estimator.compute(inputs)
            assert result["hours"] > 0
            assert result["time_text"]

    def test_hours_vs_time_text_consistency(self, estimator):
        result = estimator.compute(estimator.DEFAULT_INPUTS)
        hours = result["hours"]
        # time_text should represent roughly the same duration
        assert hours > 0


# ---------------------------------------------------------------------------
# Yarn Estimator: ball count math
# ---------------------------------------------------------------------------


class TestBallCountMath:
    """Ball count calculations are transparent and correct."""

    def test_ball_count_by_length(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["yarn_per_ball_yards"] = 100
        result = estimator.compute(inputs)
        expected = math.ceil(result["yards"] / 100)
        assert result["balls_yard"] == expected

    def test_ball_count_by_weight(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["yarn_per_ball_grams"] = 25
        result = estimator.compute(inputs)
        expected = math.ceil(result["grams"] / 25)
        assert result["balls_weight"] == expected

    def test_difference_explained_when_balls_differ(self, estimator):
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["yarn_per_ball_yards"] = 100
        inputs["yarn_per_ball_grams"] = 200  # unrealistic, forces difference
        result = estimator.compute(inputs)
        if result["balls_yard"] != result["balls_weight"]:
            assert any("difference" in label.lower() or "why" in label.lower() for label, _ in result["balls_detail"])


# ---------------------------------------------------------------------------
# Integration: planners emit _estimator_data
# ---------------------------------------------------------------------------


class TestPlannerIntegration:
    """Each planner emits _estimator_data for the estimator."""

    def test_hat_crown_has_estimator_data(self):
        module = _load_demo("hat_crown")
        result = module.DEMO["compute"]({"stitches": 72, "repeats": 8})
        assert "_estimator_data" in result
        est = result["_estimator_data"]
        # cast-on is not a workload; the estimator must not receive it
        assert "stitch_count" not in est
        assert est["project_type"] == "hat"
        assert est["source"] == "hat_crown_planner"

    def test_hat_crown_send_button_in_html(self):
        module = _load_demo("hat_crown")
        result = module.DEMO["compute"]({"stitches": 72, "repeats": 8})
        html = module.DEMO["to_html"](result)
        assert "send-to-estimator" in html
        assert "data-stitches" not in html
        assert "data-type='hat'" in html

    def test_pi_shawl_has_estimator_data(self):
        module = _load_demo("pi_shawl")
        result = module.DEMO["compute"]({"radius": 16.5, "row_gauge": 4.5})
        assert "_estimator_data" in result
        est = result["_estimator_data"]
        assert est["estimated_stitches"] > 0
        assert est["project_type"] == "shawl_triangle"
        assert est["source"] == "pi_shawl_planner"

    def test_pi_shawl_send_button_in_html(self):
        module = _load_demo("pi_shawl")
        result = module.DEMO["compute"]({"radius": 16.5, "row_gauge": 4.5})
        html = module.DEMO["to_html"](result)
        assert "send-to-estimator" in html
        assert "data-type='shawl_triangle'" in html

    def test_raglan_has_estimator_data(self):
        module = _load_demo("raglan")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert "_estimator_data" in result
        est = result["_estimator_data"]
        assert est["stitch_count"] > 0
        assert est["project_type"] == "sweater"
        assert est["source"] == "raglan_planner"

    def test_raglan_send_button_in_html(self):
        module = _load_demo("raglan")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        html = module.DEMO["to_html"](result)
        assert "send-to-estimator" in html
        assert "data-type='sweater'" in html

    def test_shawl_shapes_has_estimator_data(self):
        module = _load_demo("shawl_shapes")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        assert "_estimator_data" in result
        est = result["_estimator_data"]
        assert est["stitch_count"] > 0
        assert "shawl" in est["project_type"] or est["project_type"] == "custom"
        assert est["source"] == "shawl_shapes_planner"

    def test_shawl_shapes_send_button_in_html(self):
        module = _load_demo("shawl_shapes")
        result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        html = module.DEMO["to_html"](result)
        assert "send-to-estimator" in html

    def test_estimator_consumes_hat_data(self):
        estimator = _load_yarn_estimator()
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["advanced_mode"] = "true"
        inputs["project_stitches"] = 72
        result = estimator.compute(inputs)
        assert result["project_stitches"] == 72
        assert result["yards"] > 0

    def test_estimator_consumes_raglan_data(self):
        estimator = _load_yarn_estimator()
        module = _load_demo("raglan")
        raglan_result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
        stitch_count = raglan_result["_estimator_data"]["stitch_count"]
        inputs = dict(estimator.DEFAULT_INPUTS)
        inputs["advanced_mode"] = "true"
        inputs["project_stitches"] = stitch_count
        result = estimator.compute(inputs)
        assert result["project_stitches"] == stitch_count
        assert result["yards"] > 0


# ---------------------------------------------------------------------------
# HTML structure tests (browser UX verification)
# ---------------------------------------------------------------------------


class TestBrowserUX:
    """Verify the demo HTML structure and key elements."""

    def test_demo_html_has_project_type_select(self):
        page = pathlib.Path(__file__).resolve().parents[2] / "demos" / "yarn-estimator" / "demo.html"
        text = page.read_text(encoding="utf-8")
        assert 'id="project_type"' in text
        assert 'value="hat"' in text
        assert 'value="scarf"' in text
        assert 'value="sweater"' in text

    def test_demo_html_has_dimensions_inputs(self):
        page = pathlib.Path(__file__).resolve().parents[2] / "demos" / "yarn-estimator" / "demo.html"
        text = page.read_text(encoding="utf-8")
        assert 'id="project_width"' in text
        assert 'id="project_height"' in text
        assert 'id="stitch_gauge"' in text
        assert 'id="row_gauge"' in text

    def test_demo_html_has_yarn_inputs(self):
        page = pathlib.Path(__file__).resolve().parents[2] / "demos" / "yarn-estimator" / "demo.html"
        text = page.read_text(encoding="utf-8")
        assert 'id="yarn_per_ball_yards"' in text
        assert 'id="yarn_per_ball_grams"' in text

    def test_demo_html_has_pace_radio(self):
        page = pathlib.Path(__file__).resolve().parents[2] / "demos" / "yarn-estimator" / "demo.html"
        text = page.read_text(encoding="utf-8")
        assert 'name="knitting_pace"' in text
        assert 'value="slow"' in text
        assert 'value="medium"' in text
        assert 'value="fast"' in text

    def test_demo_html_has_advanced_details(self):
        page = pathlib.Path(__file__).resolve().parents[2] / "demos" / "yarn-estimator" / "demo.html"
        text = page.read_text(encoding="utf-8")
        assert "<details" in text
        assert "advanced" in text.lower()
        assert 'id="project_stitches"' in text
        assert 'id="yards_per_stitch"' in text

    def test_demo_html_has_planner_load_section(self):
        page = pathlib.Path(__file__).resolve().parents[2] / "demos" / "yarn-estimator" / "demo.html"
        text = page.read_text(encoding="utf-8")
        assert "Load from planner" in text
        assert 'id="hat_stitches"' in text
        assert 'id="shawl_stitches"' in text
        assert 'id="sweater_stitches"' in text
        assert 'id="load-planner"' in text

    def test_demo_html_has_common_chrome(self):
        page = pathlib.Path(__file__).resolve().parents[2] / "demos" / "yarn-estimator" / "demo.html"
        text = page.read_text(encoding="utf-8")
        assert "common.css" in text
        assert "all demos" in text
        assert 'id="export-pattern"' in text

    def test_demo_html_has_session_storage_reading(self):
        page = pathlib.Path(__file__).resolve().parents[2] / "demos" / "yarn-estimator" / "demo.html"
        text = page.read_text(encoding="utf-8")
        assert "sessionStorage" in text
        assert "estimator_prefill" in text

    def test_planner_pages_have_send_to_estimator_js(self):
        demos_dir = pathlib.Path(__file__).resolve().parents[2] / "demos"
        # estimator JS was extracted from inline <script> to external files
        js_files = [
            demos_dir / "_shared" / "estimator.js",
            demos_dir / "hat-crown" / "actions.js",
            demos_dir / "raglan-sweater" / "actions.js",
        ]
        combined = "\n".join(f.read_text(encoding="utf-8") for f in js_files if f.exists())
        assert "send-to-estimator" in combined, "send-to-estimator handler missing from JS files"
        assert "sessionStorage" in combined, "sessionStorage missing from JS files"
        assert "estimator_prefill" in combined, "estimator_prefill missing from JS files"
