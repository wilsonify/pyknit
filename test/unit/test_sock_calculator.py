#!/usr/bin/env python3
"""Consistency tests for pyknit.Sock and the Sock Calculator demo plan.

The Sock plan is the contract of the calculator: cast-on -> leg decreases ->
heel flap -> heel turn -> gusset -> foot -> toe.  Every count on the way
must be a whole number, and every step must land exactly on the count the
next step expects.  These tests check that arithmetic across a range of
realistic (and some awkward) measurements, plus the validation failures and
the generated instructions.
"""

import importlib.util
import pathlib
import re

import pytest

from pyknit.Sock import NEGATIVE_EASE, Sock

DEMOS_DIR = pathlib.Path(__file__).parent.parent.parent / "pyknit" / "pyscript" / "_demos"


def load_sock_demo():
    spec = importlib.util.spec_from_file_location("demo_sock_calculator", DEMOS_DIR / "sock_calculator.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Realistic sizes (mirrors the demo's size quick-pick) at two gauges.
SIZES = [
    (dict(), "default"),
    (dict(rows_per_inch=7, stitches_per_inch=5.5), "bulky"),
    (dict(rows_per_inch=9, stitches_per_inch=6), "fingering-loose"),
    (dict(rows_per_inch=12, stitches_per_inch=8), "fingering-tight"),
    (
        dict(
            circumference_at_top=7.5,
            circumference_of_ankle=6.5,
            length_from_sock_top_to_heel_bottom=4.5,
            length_from_heel_to_toe=6.5,
        ),
        "child",
    ),
    (
        dict(
            circumference_at_top=9.5,
            circumference_of_ankle=8,
            length_from_sock_top_to_heel_bottom=6,
            length_from_heel_to_toe=8.5,
        ),
        "womens-S",
    ),
    (
        dict(
            circumference_at_top=10.25,
            circumference_of_ankle=8.5,
            length_from_sock_top_to_heel_bottom=6.5,
            length_from_heel_to_toe=9.25,
        ),
        "womens-M",
    ),
    (
        dict(
            circumference_at_top=11,
            circumference_of_ankle=9,
            length_from_sock_top_to_heel_bottom=7,
            length_from_heel_to_toe=10,
        ),
        "womens-L",
    ),
    (
        dict(
            circumference_at_top=11.5,
            circumference_of_ankle=9.5,
            length_from_sock_top_to_heel_bottom=7.25,
            length_from_heel_to_toe=10.5,
        ),
        "mens-S",
    ),
    (
        dict(
            circumference_at_top=12.5,
            circumference_of_ankle=10.25,
            length_from_sock_top_to_heel_bottom=7.75,
            length_from_heel_to_toe=11,
        ),
        "mens-M",
    ),
    (
        dict(
            circumference_at_top=13.5,
            circumference_of_ankle=11,
            length_from_sock_top_to_heel_bottom=8.25,
            length_from_heel_to_toe=11.75,
        ),
        "mens-L",
    ),
    # awkward but buildable: steep taper, very short leg, fine gauge
    (
        dict(
            circumference_at_top=11,
            circumference_of_ankle=8,
            rows_per_inch=9,
            stitches_per_inch=8,
            length_from_sock_top_to_heel_bottom=5.5,
        ),
        "steep-taper",
    ),
    (
        dict(
            rows_per_inch=14,
            stitches_per_inch=10,
            circumference_at_top=8,
            circumference_of_ankle=7.5,
            length_from_sock_top_to_heel_bottom=4,
            length_from_heel_to_toe=7,
        ),
        "fine-small",
    ),
]


@pytest.mark.parametrize("kwargs,_name", SIZES)
def test_whole_numbers_and_consistency(kwargs, _name):
    """Every construction step stays whole and lands exactly on the next."""
    sock = Sock()
    sock.init(**kwargs)

    cast = sock.cast_on_stitches
    ankle = sock.ankle_stitches
    assert cast % 2 == 0 and ankle % 2 == 0
    assert cast > 0 and ankle > 0

    # ---- leg: decreases sum exactly to the taper ----
    plan = sock.leg_decrease_plan()
    assert len(plan) == sock.number_of_decrease_rows
    total_removed = sum(removed for _, _, removed in plan)
    assert cast - total_removed == ankle
    before = cast
    seen = set()
    for round_no, sts_before, removed in plan:
        assert removed in (2, 4)
        assert sts_before == before
        assert round_no not in seen
        seen.add(round_no)
        before -= removed
    rounds = [r for r, _, _ in plan]
    assert rounds == sorted(rounds)

    # backwards-compatible schedule equals the plan's (round, before)
    assert sock.leg_decrease_schedule() == [(r, b) for r, b, _ in plan]

    # ---- heel: last stitch count exactly consumes the needle ----
    flap = sock.number_of_heel_flap_stitches
    turn_rows, remaining = sock.heel_turn_rows()
    assert remaining == flap - (1 + len(turn_rows))
    assert 1 <= remaining <= flap
    assert len(turn_rows) >= 1
    side_seq = [r["side"] for r in turn_rows]
    assert side_seq == ["RS", "WS"] * (len(turn_rows) // 2) + (["RS"] if len(turn_rows) % 2 else [])

    # ---- gusset: pick-ups decreased back to exactly the ankle ----
    first, rest = sock.gusset_decrease_rounds()
    assert first in (0, 1)
    assert sock.gusset_stitches_after_pickup() - (first + 2 * rest) == ankle
    assert sock.gusset_stitches_after_pickup() >= ankle

    # ---- toe: finish count small, positive and even-4-able ----
    toe = sock._toe_row_schedule()
    assert 4 <= toe["finish_stitches"] <= 8
    assert toe["finish_stitches"] % 2 == 0
    assert toe["phase1_end_stitches"] == (toe["finish_stitches"] + 4 * toe["phase2_decrease_rounds"])
    assert toe["total_rows"] == toe["phase1_span_rows"] + toe["phase2_decrease_rounds"]

    # ---- the pieces add up to the sections the knitter actually knits ----
    plan_dict = sock.get_plan()
    sections = plan_dict["sections"]
    assert len(sections) == 8
    assert plan_dict["measurements"]["cast_on_stitches"][1] == cast
    assert plan_dict["measurements"]["ankle_stitches"][1] == ankle


# ---------------------------------------------------------------------------
# Rounding helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,down,up",
    [
        (68.4, 68, 70),
        (33.5, 32, 34),
        (72.0, 72, 72),
        (0.4, 0, 2),
        (7.9, 6, 8),
    ],
)
def test_round_to_even_helpers(value, down, up):
    sock = Sock()
    assert sock.round_down_even(value) == down
    assert sock.round_up_even(value) == up


def test_round_helpers_return_whole_even_numbers():
    sock = Sock()
    for value in (1.2, 20.7, 99.5, 101.1):
        assert sock.round_down_even(value) % 2 == 0
        assert sock.round_up_even(value) % 2 == 0


# ---------------------------------------------------------------------------
# Negative ease
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ease,expected_percent",
    [
        (NEGATIVE_EASE, 20),
        (1.0, 0),
        (0.9, 10),
        (0.6, 40),
    ],
)
def test_negative_ease_configurable(ease, expected_percent):
    sock = Sock()
    sock.init(negative_ease=ease)
    assert sock.negative_ease == ease
    assert round((1 - sock.negative_ease) * 100) == expected_percent
    # ease applies to both cast-on and ankle counts
    assert sock.cast_on_stitches == sock.round_down_even(sock.stitches_per_inch * sock.circumference_at_top * ease)
    assert sock.ankle_stitches == sock.round_down_even(sock.stitches_per_inch * sock.circumference_of_ankle * ease)


@pytest.mark.parametrize("bad", [0, -0.1, 1.3, 5])
def test_negative_ease_invalid_raises(bad):
    sock = Sock()
    with pytest.raises(ValueError):
        sock.init(negative_ease=bad)


def test_no_ease_means_counts_equal_measured_stitches():
    sock = Sock()
    sock.init(negative_ease=1.0)
    assert sock.cast_on_stitches == sock.round_down_even(sock.stitches_per_inch * sock.circumference_at_top)


# ---------------------------------------------------------------------------
# Validation: impossible plans raise, never silently contradict
# ---------------------------------------------------------------------------


def test_validation_raises_for_zero_gauge():
    sock = Sock()
    with pytest.raises(ValueError, match="Gauge"):
        sock.init(stitches_per_inch=0, rows_per_inch=11)


def test_validation_raises_for_negative_measurement():
    sock = Sock()
    with pytest.raises(ValueError):
        sock.init(circumference_of_ankle=-2)


def test_validation_raises_when_leg_cannot_fit_decreases():
    sock = Sock()
    with pytest.raises(ValueError, match="[Ll]eg"):
        sock.init(
            circumference_at_top=10,
            circumference_of_ankle=8,
            length_from_sock_top_to_heel_bottom=2.5,
            rows_per_inch=11,
            stitches_per_inch=9,
        )


def test_validation_raises_when_flap_longer_than_leg():
    sock = Sock()
    sock.init(
        circumference_at_top=9,
        circumference_of_ankle=9,
        length_from_sock_top_to_heel_bottom=1.0,
        rows_per_inch=11,
        stitches_per_inch=9,
    )
    with pytest.raises(ValueError, match="[Hh]eel flap"):
        sock.get_plan()


def test_validation_raises_for_too_few_ankle_stitches():
    sock = Sock()
    sock.init(
        circumference_at_top=4,
        circumference_of_ankle=3.5,
        stitches_per_inch=2.5,
        rows_per_inch=3,
    )
    with pytest.raises(ValueError):
        sock.get_plan()


def test_buildable_unusual_gauge_warns_but_constructs():
    sock = Sock()
    sock.init(stitches_per_inch=3.5, rows_per_inch=4.5)
    assert any("gauge" in w for w in sock.warnings())
    plan = sock.get_plan()
    assert len(plan["sections"]) == 8


# ---------------------------------------------------------------------------
# Generated instructions: every number has a next action
# ---------------------------------------------------------------------------


def test_instructions_number_consistency():
    sock = Sock()
    sock.init()
    plan = sock.get_plan()
    joined = "\n".join((s.get("intro") or "") + "\n" + "\n".join(s.get("steps") or []) for s in plan["sections"])

    # numbers in the instructions agree with the computed plan
    assert f"Cast on {sock.cast_on_stitches} stitches" in joined
    assert f"exactly {sock.ankle_stitches} stitches" in joined
    assert f"{sock.instep_stitches} instep stitches" in joined
    assert str(sock.gusset_pickup_per_side()) in joined
    toe = sock._toe_row_schedule()
    assert f"{toe['finish_stitches']} stitches" in joined


def test_toe_instructions_split_by_markers():
    sock = Sock()
    sock.init()
    plan = sock.get_plan()
    toe = next(s for s in plan["sections"] if s["heading"].startswith("7."))
    joined = " ".join(toe["steps"])
    instep = sock.instep_stitches
    sole = sock.ankle_stitches - instep
    assert f"{instep} instep stitches" in joined
    assert f"{sole} sole stitches" in joined
    # both side markers are named
    assert "start-of-round marker" in joined
    assert "instep marker" in joined


def test_gusset_instructions_number_consistent():
    sock = Sock()
    sock.init()
    plan = sock.get_plan()
    gusset = next(s for s in plan["sections"] if s["heading"].startswith("5."))
    joined = " ".join(gusset["steps"])
    first, rest = sock.gusset_decrease_rounds()
    assert f"{sock.gusset_pickup_per_side()} stitches" in joined
    assert f"{sock.gusset_stitches_after_pickup()} stitches" in joined
    if first + rest or sock.gusset_stitches_after_pickup() - sock.ankle_stitches > 0:
        assert f"exactly {sock.ankle_stitches} stitches" in joined


def test_heel_turn_table_lists_real_counts():
    sock = Sock()
    sock.init()
    plan = sock.get_plan()
    heel = next(s for s in plan["sections"] if s["heading"].startswith("4."))
    joined = "\n".join(heel["steps"])
    rows, remaining = sock.heel_turn_rows()
    for row in rows:
        assert f"k{row['count']}" in joined or f"p{row['count']}" in joined
    assert f"{remaining} stitches" in joined


def test_leg_table_every_round_consistent():
    sock = Sock()
    sock.init()
    plan = sock.get_plan()
    leg = next(s for s in plan["sections"] if s["heading"].startswith("2."))
    assert leg["table"] is not None
    plan_list = sock.leg_decrease_plan()
    assert len(leg["table"]["rows"]) == len(plan_list)
    for (round_no, before, removed), row in zip(plan_list, leg["table"]["rows"]):
        assert row[0] == str(round_no)
        assert row[2] == str(before - removed)


# ---------------------------------------------------------------------------
# Demo module: negative ease input is wired through
# ---------------------------------------------------------------------------


def test_demo_defaults_and_ease_wiring():
    module = load_sock_demo()
    inputs = dict(module.DEFAULT_INPUTS)
    assert "negative_ease" in inputs
    result = module.DEMO["compute"](inputs)
    assert result["warnings"] == []
    assert result["negative_ease_percent"] == 20
    assert result["cast_on_stitches"] % 2 == 0
    html = module.DEMO["to_html"](result)
    assert "<svg" in html
    assert "20% negative ease" in html


@pytest.mark.parametrize(
    "pct,expected_cast_direction",
    [
        (0, 1.0),
        (10, 0.9),
        (25, 0.75),
    ],
)
def test_demo_ease_percent_maps_to_factor(pct, expected_cast_direction):
    module = load_sock_demo()
    sock = Sock()
    inputs = dict(module.DEFAULT_INPUTS)
    inputs["negative_ease"] = pct
    result = module.DEMO["compute"](inputs)
    spi = float(inputs["stitches_per_inch"])
    circ = float(inputs["circumference_at_top"])
    expected = sock.round_down_even(spi * circ * expected_cast_direction)
    assert result["cast_on_stitches"] == expected


@pytest.mark.parametrize("bad", [-5, 60, 200])
def test_demo_rejects_out_of_range_ease(bad):
    module = load_sock_demo()
    inputs = dict(module.DEFAULT_INPUTS)
    inputs["negative_ease"] = bad
    with pytest.raises(ValueError):
        module.DEMO["compute"](inputs)


def test_svg_has_no_negative_geometry_across_sizes():
    module = load_sock_demo()
    for kwargs, _name in SIZES:
        inputs = dict(module.DEFAULT_INPUTS)
        for key, value in kwargs.items():
            if key != "negative_ease":
                inputs[key] = value
        try:
            result = module.DEMO["compute"](inputs)
        except ValueError:
            # some of the awkward combos legitimately refuse to make a sock
            continue
        numbers = re.findall(r'(?:width|height|x|y)="(-?\d*\.?\d+)"', result["svg"])
        assert not any(float(n) < 0 for n in numbers), kwargs


def test_plan_measurements_match_computed_sock():
    sock = Sock()
    sock.init()
    plan = sock.get_plan()
    ms = plan["measurements"]
    assert ms["cast_on_stitches"][1] == sock.cast_on_stitches
    assert ms["ankle_stitches"][1] == sock.ankle_stitches
    assert ms["number_of_decrease_rows"][1] == sock.number_of_decrease_rows
    assert ms["number_of_heel_flap_stitches"][1] == sock.number_of_heel_flap_stitches


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
