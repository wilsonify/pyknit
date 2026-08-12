#!/usr/bin/env python3
import math

from pyknit.Hat import Hat
from pyknit.Sock import Sock

BIND_OFF = (
    "Cut yarn leaving 4 inch tail, thread through remaining stitches "
    "and pull closed"
)


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
    assert instructions[0] == (
        "[k1, k2tog] repeat 8 times, k2tog 2 times (16 stitches)"
    )
    assert instructions[2] == "k2tog 8 times (8 stitches)"
    assert instructions[-1] == BIND_OFF
    counts = _stitch_counts(instructions)
    assert counts == [16, 8]
    assert 26 - counts[0] == 10  # repeats + leftover (8 + 2) removed in round 1
    assert counts[0] - counts[1] == 8  # repeats removed in later rounds


def test_hat_crown_remainder_deterministic():
    assert Hat().crown_decreases(8, 26) == Hat().crown_decreases(8, 26)


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
    x = (sock.cast_on_stitches - sock.ankle_stitches) / 2
    assert sock.number_of_decrease_rows == math.ceil(x)
    assert sock.number_of_decrease_rows % 2 == 0
    assert sock.number_of_decrease_rows >= x


def test_sock_heel_to_toe_decrease_geometry():
    sock = Sock()
    sock.init()
    expected = round(sock.length_from_heel_to_toe - sock.length_of_toe_decrease, 2)
    assert sock.length_from_heel_to_beginning_of_toe_decrease == expected
