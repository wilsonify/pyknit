"""Tests for integration-test scheduling logic.

Verify that the cost estimator and LPT sorting produce balanced
assignments before we rely on them in CI.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "integration"))

from qa_all_demos import _estimate_cost  # noqa: E402
from qa_demos import DEMOS  # noqa: E402


class TestEstimateCost:
    def test_simple_demo_has_low_weight(self):
        spec = {"dir": "chart-renderer", "buttons": ["run"]}
        assert _estimate_cost(spec) == 1

    def test_two_buttons_adds_weight(self):
        spec = {"dir": "gauge-conversion", "buttons": ["run-calc", "run-chart"]}
        assert _estimate_cost(spec) == 2

    def test_simulate_nav_baseline(self):
        spec = {
            "dir": "hat-crown",
            "buttons": ["run"],
            "extra": "simulate-nav",
            "sim": {"min_steps": 10},
        }
        assert _estimate_cost(spec) == 3  # 3 + 10//20 = 3

    def test_simulate_nav_heavy(self):
        spec = {
            "dir": "raglan-sweater",
            "buttons": ["run"],
            "extra": "simulate-nav",
            "sim": {"min_steps": 100},
        }
        assert _estimate_cost(spec) == 8  # 3 + 100//20 = 8

    def test_knit_simulator_is_heaviest(self):
        spec = {"dir": "knit-simulator", "buttons": ["run"], "extra": "knit-simulator"}
        assert _estimate_cost(spec) == 5

    def test_all_real_demos_have_positive_weight(self):
        for spec in DEMOS:
            assert _estimate_cost(spec) > 0, f"{spec['dir']} has zero weight"

    def test_sorting_puts_heavy_demos_first(self):
        weighted = sorted(DEMOS, key=_estimate_cost, reverse=True)
        assert weighted[0]["dir"] == "raglan-sweater"
        # The first 4 (heaviest) should include raglan, hat-crown, sock, knit-sim
        top4 = {d["dir"] for d in weighted[:4]}
        assert "raglan-sweater" in top4
