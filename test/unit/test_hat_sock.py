#!/usr/bin/env python3
from pyknit.Hat import Hat
from pyknit.Sock import Sock

BIND_OFF = "Cut yarn leaving 4 inch tail, thread through remaining stitches " "and pull closed"


def _stitch_counts(instructions):
    counts = []
    for line in instructions:
        if "stitches)" in line:
            counts.append(int(line.split("(")[1].split(" ")[0]))
    return counts


def test_hat_crown_even_division_format_unchanged():
    assert Hat().crown_decreases(8, 24) == [
        "[k1, k2tog] repeat 8 times (16 stitches)",
        "Knit 1 round",
        "k2tog 8 times (8 stitches)",
        "Knit 1 round",
        BIND_OFF,
    ]


def test_hat_crown_remainder_distributes_extra_decreases():
    instructions = Hat().crown_decreases(8, 26)
    assert instructions[0] == ("[k1, k2tog] repeat 8 times, k2tog 2 times (16 stitches)")
    assert instructions[2] == "k2tog 8 times (8 stitches)"
    assert instructions[-1] == BIND_OFF
    counts = _stitch_counts(instructions)
    assert counts == [16, 8]
    assert 26 - counts[0] == 10  # repeats + leftover (8 + 2) removed in round 1
    assert counts[0] - counts[1] == 8  # repeats removed in later rounds


def test_hat_crown_remainder_deterministic():
    result = Hat().crown_decreases(8, 26)
    assert result == Hat().crown_decreases(8, 26)


def test_hat_crown_invalid_params_still_returns_string():
    assert Hat().crown_decreases(0, 10) == "Invalid starting parameters"
    assert Hat().crown_decreases(8, 0) == "Invalid starting parameters"


def test_hat_crown_stops_and_binds_off():
    instructions = Hat().crown_decreases(8, 16)
    assert instructions[-1] == BIND_OFF


def test_sock_init_completes_and_fields_populated():
    sock = Sock()
    sock.init()
    assert sock.cast_on_stitches > 0
    assert sock.ankle_stitches > 0
    assert sock.number_of_decrease_rows > 0
    assert sock.length_of_heel_flap > 0
    assert sock.length_from_sock_top_to_heel_flap > 0
    assert sock.number_of_heel_flap_stitches > 0
    assert sock.length_of_toe_decrease > 0
    assert sock.length_from_heel_to_beginning_of_toe_decrease > 0


def test_sock_number_of_decrease_rows_formula():
    sock = Sock()
    sock.init()
    assert sock.number_of_decrease_rows >= 0
    # Each leg decrease round removes exactly 2 stitches, and with both the
    # cast-on and ankle counts rounded even, the leg must land exactly on the
    # ankle count.
    if sock.cast_on_stitches > sock.ankle_stitches:
        assert sock.cast_on_stitches - sock.ankle_stitches == (sock.number_of_decrease_rows * 2)
    else:
        assert sock.number_of_decrease_rows == 0


def test_sock_heel_to_toe_decrease_geometry():
    sock = Sock()
    sock.init()
    expected = round(sock.length_from_heel_to_toe - sock.length_of_toe_decrease, 2)
    assert sock.length_from_heel_to_beginning_of_toe_decrease == expected


def test_sock_heel_flap_is_square():
    sock = Sock()
    sock.init()
    # A well-fitting flap has as many rows as stitches in it.
    assert sock.length_of_heel_flap == round(sock.number_of_heel_flap_stitches / sock.rows_per_inch, 2)


def test_sock_lengths_add_up():
    sock = Sock()
    sock.init()
    leg = sock.length_from_sock_top_to_heel_flap + sock.length_of_heel_flap
    assert round(leg, 2) == round(sock.length_from_sock_top_to_heel_bottom, 2)
    foot = sock.length_from_heel_to_beginning_of_toe_decrease + sock.length_of_toe_decrease
    assert round(foot, 2) == round(sock.length_from_heel_to_toe, 2)


def test_sock_cast_on_wider_than_ankle():
    sock = Sock()
    sock.init()
    assert sock.cast_on_stitches > sock.ankle_stitches


def test_sock_no_decreases_when_leg_narrower_than_ankle():
    sock = Sock()
    sock.init(
        circumference_at_top=8,
        circumference_of_ankle=10,
    )
    assert sock.number_of_decrease_rows == 0
    assert any("smaller than your ankle" in w for w in sock.warnings())


def test_sock_plan_contains_all_sections():
    sock = Sock()
    sock.init()
    plan = sock.get_plan()
    headings = [s["heading"] for s in plan["sections"]]
    assert "1. Cast on and get started" in headings
    assert "2. The leg (cuff to heel)" in headings
    assert "3. Work the heel flap" in headings
    assert "4. Turn the heel" in headings
    assert "5. Shape the gusset" in headings
    assert "6. Knit the foot" in headings
    assert "7. Knit the toe" in headings
    assert "8. Finish and repeat" in headings
    assert "measurements" in plan
    assert "assumptions" in plan
    assert isinstance(plan["warnings"], list)


def test_sock_plan_leg_decreases_end_at_ankle():
    sock = Sock()
    sock.init()
    schedule = sock.leg_decrease_schedule()
    assert len(schedule) == sock.number_of_decrease_rows
    if schedule:
        _, last_before = schedule[-1]
        assert last_before - 2 == sock.ankle_stitches
        rounds = [r for r, _ in schedule]
        assert rounds == sorted(set(rounds))
        assert rounds[0] > 0


def test_sock_plan_heel_turn_remaining():
    sock = Sock()
    sock.init()
    rows, remaining = sock.heel_turn_rows()
    flap = sock.number_of_heel_flap_stitches
    assert remaining == flap - (1 + len(rows))
    assert remaining < flap
    assert all(r["side"] in ("RS", "WS") for r in rows)
    assert rows[0]["count"] == 5  # the canonical first turn row


def test_sock_plan_gusset_returns_to_ankle():
    sock = Sock()
    sock.init()
    first, rest = sock.gusset_decrease_rounds()
    removed = first + 2 * rest
    assert sock.gusset_stitches_after_pickup() - removed == sock.ankle_stitches
    assert first in (0, 1)


def test_sock_plan_toe_reaches_finish():
    sock = Sock()
    sock.init()
    toe = sock._toe_row_schedule()
    assert 0 < toe["finish_stitches"] <= 8
    assert toe["phase1_decrease_rounds"] > 0
    assert toe["phase2_decrease_rounds"] > 0
    assert toe["total_rows"] == (toe["phase1_span_rows"] + toe["phase2_decrease_rounds"])
    assert sock.length_of_toe_decrease > 0


def test_sock_plan_warnings_for_tiny_ankle():
    sock = Sock()
    sock.init(
        circumference_at_top=3.5,
        circumference_of_ankle=3,
        stitches_per_inch=9,
        rows_per_inch=11,
    )
    assert any("very narrow" in w for w in sock.warnings())


def test_sock_plan_unusual_gauge_warns():
    sock = Sock()
    sock.init(stitches_per_inch=3.5, rows_per_inch=4.5)
    assert any("gauge" in w for w in sock.warnings())


def test_sock_plan_leg_uses_decrease_evenly():
    sock = Sock()
    sock.init()
    plan = sock.get_plan()
    leg = next(s for s in plan["sections"] if s["heading"].startswith("2."))
    assert leg["table"] is not None
    for row in leg["table"]["rows"]:
        assert "k2tog" in row[1]
        assert "2 times" in row[1]


def test_sock_plan_zero_gauge_raises():
    sock = Sock()
    try:
        sock.init(stitches_per_inch=0, rows_per_inch=11)
        assert False, "expected an exception for zero gauge"
    except ValueError:
        pass
