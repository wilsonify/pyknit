"""
Tests for the complete top-down raglan sweater planner
(pyknit/pyscript/_demos/raglan.py).

The planner derives every stitch count and round count from a gauge and a few
measurements, delegating the raglan arithmetic and sleeve shaping to the
existing pyknit functions (``raglan_increases``, ``sleeve_decreases`` and
``GaugeSwatch``).  These tests cover the derived numbers, the validation,
edge cases, the generated instructions and the exported pattern text.
"""

import importlib.util
import pathlib

import pytest

from pyknit.pyscript._assets import shared

DEMOS_DIR = pathlib.Path(__file__).parent.parent.parent / "pyknit" / "pyscript" / "_demos"


def _load_demo():
    spec = importlib.util.spec_from_file_location(
        "demo_raglan", DEMOS_DIR / "raglan.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestRaglanSweaterPlan:
    """The planner turns defaults into a complete, correct knitting plan."""

    def _compute(self, **overrides):
        module = _load_demo()
        inputs = dict(module.DEMO["DEFAULT_INPUTS"])
        inputs.update(overrides)
        return module, module.DEMO["compute"](inputs)

    def _sections(self, result):
        return result["plan"]["sections"]

    def _section(self, result, needle):
        return next(s for s in self._sections(result) if needle in s["heading"])

    def test_default_plan_has_all_ten_sections(self):
        _, result = self._compute()
        headings = [s["heading"] for s in self._sections(result)]
        assert len(headings) == 10
        for expected in (
            "math", "gauge and finished measurements", "cast on",
            "marker setup", "increase schedule", "underarm cast-on",
            "body instructions", "hem", "sleeve instructions", "cuff",
        ):
            assert any(expected in h.lower() for h in headings), expected

    def test_default_derived_counts_match_hand_calc(self):
        _, result = self._compute()
        m = result["meta"]
        assert m["neck"] == 70
        assert m["bust"] == 180
        assert m["arm"] == 60
        assert m["armpit"] == 10
        assert m["wrist"] == 38
        assert m["working"] == 260
        assert m["inc_rounds"] == 23
        assert m["pre"] == 6
        assert m["calc_neck"] == 76
        assert m["front_start"] == 34
        assert m["back_start"] == 34
        assert m["sleeve_start"] == 4
        assert m["front_final"] == 80
        assert m["back_final"] == 80
        assert m["sleeve_final"] == 50

    def test_default_uses_every_other_round(self):
        _, result = self._compute()
        m = result["meta"]
        assert m["freq"] == "every_other_round"
        assert m["raglan_total_rounds"] == 2 * m["inc_rounds"]  # 46
        assert round(m["depth_in"], 2) == round(46 / 6.5, 2)

    def test_every_round_halves_total_rounds(self):
        _, result = self._compute(increase_frequency="every_round")
        m = result["meta"]
        assert m["raglan_total_rounds"] == m["inc_rounds"]
        assert m["depth_in"] == m["inc_rounds"] / 6.5

    def test_transition_table_starts_and_ends_correctly(self):
        _, result = self._compute()
        m = result["meta"]
        rows = self._section(result, "increase schedule")["table"]["rows"]
        assert len(rows) == m["raglan_total_rounds"]
        assert rows[0][2] == m["calc_neck"] + m["inc"]  # round 1 increases
        last = rows[-1]
        assert last[2] == m["working"]
        assert last[3] == m["front_final"]
        assert last[4] == m["back_final"]
        assert last[5] == m["sleeve_final"]

    def test_transition_table_interleaves_plain_rounds(self):
        _, result = self._compute()
        rows = self._section(result, "increase schedule")["table"]["rows"]
        assert rows[0][1] == "increase"
        assert rows[1][1] == "plain"
        assert rows[1][2] == rows[0][2]  # plain rounds add no stitches

    def test_neck_increase_row_emitted_when_needed(self):
        _, result = self._compute()
        text = " ".join(
            " ".join(s.get("steps", [])) for s in self._sections(result)
        ).lower()
        assert "neck increase round" in text

    def test_no_neck_increase_when_evenly_divisible(self):
        # 13.6 in neck x 5 sts/in = 68; (260 - 68) % 8 == 0
        _, result = self._compute(neck_circumference=13.6)
        m = result["meta"]
        assert m["pre"] == 0
        assert "Increase row" not in result["result"]
        text = " ".join(
            " ".join(s.get("steps", [])) for s in self._sections(result)
        ).lower()
        assert "neck increase round" not in text

    def test_marker_setup_matches_pyknit(self):
        _, result = self._compute()
        assert result["meta"]["marker"] == (
            "k17, pm, k4 (arm), pm, k34, pm, k4 (arm), pm k17"
        )

    def test_sleeve_schedule_uses_sleeve_decreases(self):
        _, result = self._compute()
        m = result["meta"]
        assert "decrease row" in m["sleeve_sched"]
        assert m["sleeve_shaping_rounds"] == 100

    def test_body_hem_and_cuff_rounds(self):
        _, result = self._compute()
        m = result["meta"]
        assert m["body_stock_rounds"] == 74
        assert m["hem_rounds"] == 10
        assert m["cuff_rounds"] == 10
        assert m["collar_rounds"] == 6

    def test_export_text_contains_actionable_plan(self):
        _, result = self._compute()
        text = shared.export_pattern_text(result)
        for needle in (
            "GAUGE AND FINISHED MEASUREMENTS",
            "CAST ON AND NECK SETUP",
            "RAGLAN MARKER SETUP",
            "INCREASE SCHEDULE WITH STITCH TRANSITIONS",
            "SLEEVE SEPARATION AND UNDERARM CAST-ON",
            "BODY INSTRUCTIONS",
            "HEM INSTRUCTIONS",
            "SLEEVE INSTRUCTIONS AND SHAPING",
            "CUFF AND FINISHING",
            "k17, pm",
            "decrease row",
        ):
            assert needle in text, needle

    def test_non_standard_increase_rate_stays_consistent(self):
        # 12 increases per round must still produce marker counts that sum
        # to calc_neck and a final count that sums to working.
        _, result = self._compute(increases_per_round=12)
        m = result["meta"]
        assert m["inc"] == 12
        assert m["seg"] == 3
        assert m["front_start"] + m["back_start"] + 2 * m["sleeve_start"] == m["calc_neck"]
        assert m["front_final"] + m["back_final"] + 2 * m["sleeve_final"] == m["working"]

    def test_export_includes_visible_math(self):
        _, result = self._compute()
        text = shared.export_pattern_text(result)
        assert "Neck cast-on: 14 in x 5 = 70" in text
        assert "Bust: (34 + 2 in ease) x 5 = 180 sts" in text
        assert "Upper arm: 12 in x 5 = 60 sts" in text

    def test_to_html_renders_full_plan(self):
        module, result = self._compute()
        page = module.DEMO["to_html"](result)
        assert "plan-section" in page
        assert "plan-table" in page
        assert "plan-steps" in page
        assert "Traceback" not in page

    def test_small_raglan_gives_friendly_error(self):
        with pytest.raises(ValueError, match="too small for the bust"):
            self._compute(
                upper_arm_circumference=6,
                wrist_circumference=5,
            )

    def test_validation_rejects_bad_inputs(self):
        cases = [
            ("stitches_per_inch", 0, "stitch gauge must be positive"),
            ("rows_per_inch", 0, "row gauge must be positive"),
            ("ease", 20, "ease must be between"),
            ("ease", -10, "ease must be between"),
            ("neck_circumference", 40, "neck circumference must be smaller"),
            ("wrist_circumference", 13, "wrist circumference must be smaller"),
            ("increases_per_round", 6, "increases per round must be one of"),
            ("increase_frequency", "weekly", "increase frequency must be"),
        ]
        for key, value, message in cases:
            with pytest.raises(ValueError, match=message):
                self._compute(**{key: value})

    def test_short_body_rejected(self):
        with pytest.raises(ValueError, match="too short for a"):
            self._compute(body_length=0.5)

    def test_short_sleeve_rejected(self):
        with pytest.raises(ValueError, match="too short to include"):
            self._compute(sleeve_length=0.5)

    def test_wrist_rounding_to_arm_rejected(self):
        # upper arm 6 in -> 30 sts; wrist 5.8 in -> 29 -> 30 sts (even)
        # so the rounded wrist equals the upper arm: no taper room.
        with pytest.raises(ValueError, match="no room for"):
            self._compute(
                upper_arm_circumference=6,
                wrist_circumference=5.8,
            )

    def test_infeasible_large_bust_gives_clear_error(self):
        # A large bust with a small neck cannot distribute the increases
        # evenly (the sleeves would start at zero stitches) and must explain
        # what to change rather than emitting nonsense.
        with pytest.raises(ValueError, match="too small for the bust"):
            self._compute(
                stitches_per_inch=4.5,
                rows_per_inch=6,
                neck_circumference=15,
                bust_circumference=48,
                ease=4,
                upper_arm_circumference=16,
                wrist_circumference=9,
            )

    def test_transition_table_capped_but_export_full(self):
        _, result = self._compute(
            stitches_per_inch=5,
            rows_per_inch=6.5,
            neck_circumference=14,
            bust_circumference=40,
            ease=2,
            upper_arm_circumference=15,
            wrist_circumference=9,
            increase_frequency="every_other_round",
        )
        m = result["meta"]
        assert m["display_rounds"] > 60
        sched = self._section(result, "increase schedule")
        assert len(sched["table"]["rows"]) == 60
        assert len(sched["rows"]) == m["display_rounds"]  # export stays full
        assert "complete schedule" in sched["intro"]

    def test_large_size_still_works(self):
        _, result = self._compute(
            stitches_per_inch=4.5,
            rows_per_inch=6,
            neck_circumference=20,
            bust_circumference=44,
            ease=4,
            upper_arm_circumference=14,
            wrist_circumference=8.5,
            body_length=16,
            sleeve_length=19,
            increases_per_round=8,
        )
        m = result["meta"]
        assert m["bust"] > 0
        assert m["sleeve_final"] > 0
        assert m["working"] == m["bust"] + 2 * m["arm"] - 4 * m["armpit"]
        assert m["front_final"] + m["back_final"] + 2 * m["sleeve_final"] == m["working"]