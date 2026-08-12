#!/usr/bin/env python3
import argparse
from logging.config import dictConfig
from typing import List

from pyknit import logging_config_dict


def total_rounds_for_pi_shawl(desired_radius: float, round_gauge: float) -> int:
    """Return the number of rounds necessary to create a pi shawl of the given radius.

    A pi shawl grows ``round_gauge`` rounds per unit of radius, so the total
    number of rounds is the desired radius multiplied by the round gauge,
    rounded to the nearest round.
    """
    return round(desired_radius * round_gauge)


def pi_shawl_increase_rows(desired_radius: float, round_gauge: float) -> List[int]:
    """Return the round numbers on which to double the stitches of a pi shawl.

    A pi shawl doubles its stitch count at geometrically spaced intervals: the
    number of plain rounds between increases doubles each time.  The first
    increase is on round 2, the first round after the cast-on round, then on
    rounds 6, 13, 26 ... until the total number of rounds for the shawl is
    reached.
    """
    num_rounds_for_pi_shawl = total_rounds_for_pi_shawl(desired_radius, round_gauge)
    num_of_rounds_before_increase_step = 3
    increase_rows = [2]  # increase on first round after cast-on
    num_round = 2
    while num_round <= num_rounds_for_pi_shawl:
        num_rounds_since_last_increase_row = num_round - increase_rows[-1]
        if num_rounds_since_last_increase_row == num_of_rounds_before_increase_step + 1:
            increase_rows.append(num_round)
            num_of_rounds_before_increase_step = num_of_rounds_before_increase_step * 2
        num_round += 1
    return increase_rows


def total_rows_half_pi(desired_radius: float, round_gauge: float) -> int:
    """Return the number of rows in a half-pi shawl.

    A half-pi shawl is worked flat (back and forth) rather than in the round.
    Each row advances the radius by the same amount as a round would, so the
    total number of rows for a given radius equals
    :func:`total_rounds_for_pi_shawl` for the same radius and gauge.
    """
    return total_rounds_for_pi_shawl(desired_radius, round_gauge)


def half_pi_increase_rows(desired_radius: float, round_gauge: float) -> List[int]:
    """Return the row numbers on which to double the stitches of a half-pi shawl.

    A half-pi shawl is worked flat, so it grows half the area of a full pi
    shawl per row.  It doubles its stitches at the same geometric intervals as
    a full pi shawl, but each increase lands at roughly half the row number of
    the corresponding full-pi increase, making its increases about half as
    frequent per the same doubling rule.

    Rule: for every full-pi increase row ``r`` (see
    :func:`pi_shawl_increase_rows`), increase on row ``max(2, r // 2)``.  The
    first increase is clamped up to row 2, the first row after cast-on,
    mirroring the full pi shawl's first increase on round 2.  Full-pi increase
    rows are strictly increasing with gaps of at least 4, so the half-pi rows
    are strictly increasing too and each lands at or before the final row of
    the shawl.
    """
    total_rows = total_rows_half_pi(desired_radius, round_gauge)
    increase_rows = []
    for row in pi_shawl_increase_rows(desired_radius, round_gauge):
        half_pi_row = max(2, row // 2)
        if half_pi_row <= total_rows:
            increase_rows.append(half_pi_row)
    return increase_rows


def main():
    parser = argparse.ArgumentParser(description="Pi shawl calculations")
    parser.add_argument("desired_radius", type=float, help="Radius of your pi shawl")
    parser.add_argument("round_gauge", type=float, help="Rows per measurement unit")
    args = parser.parse_args()
    print(pi_shawl_increase_rows(args.desired_radius, args.round_gauge))


if __name__ == "__main__":
    dictConfig(logging_config_dict)
    main()
