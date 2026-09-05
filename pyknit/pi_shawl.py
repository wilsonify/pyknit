#!/usr/bin/env python3
import argparse
import math
from logging.config import dictConfig
from typing import List

from pyknit import logging_config_dict


def _validate_radius_and_gauge(desired_radius: float, round_gauge: float) -> None:
    """Validate the pi-shawl inputs used to size the shawl."""
    if not math.isfinite(desired_radius) or not math.isfinite(round_gauge):
        raise ValueError("radius and round gauge must be finite numbers")
    if desired_radius <= 0 or round_gauge <= 0:
        raise ValueError("radius and round gauge must be positive")


def total_rounds_for_pi_shawl(desired_radius: float, round_gauge: float) -> int:
    """Return the number of rounds necessary to create a pi shawl of the given radius.

    The total round count is based on the simple radius formula:
    total_rounds = round(radius × round_gauge).

    The round gauge is treated as the number of rounds needed to grow one unit of
    radius, so the result is rounded to the nearest whole round.
    """
    _validate_radius_and_gauge(desired_radius, round_gauge)
    return round(desired_radius * round_gauge)


def pi_shawl_increase_rows(desired_radius: float, round_gauge: float) -> List[int]:
    """Return the round numbers on which to double the stitches of a pi shawl.

    The increase pattern grows geometrically: after the first increase on round 2,
    the number of plain rounds between increases doubles each time. The classic
    sequence is 2, 6, 13, 26, ... and continues until the final shawl round.
    """
    _validate_radius_and_gauge(desired_radius, round_gauge)
    num_rounds_for_pi_shawl = total_rounds_for_pi_shawl(desired_radius, round_gauge)
    num_of_rounds_before_increase_step = 3
    increase_rows = [2]
    num_round = 2
    while num_round <= num_rounds_for_pi_shawl:
        num_rounds_since_last_increase_row = num_round - increase_rows[-1]
        if num_rounds_since_last_increase_row == num_of_rounds_before_increase_step + 1:
            increase_rows.append(num_round)
            num_of_rounds_before_increase_step *= 2
        num_round += 1
    return increase_rows


def total_rows_half_pi(desired_radius: float, round_gauge: float) -> int:
    """Return the number of rows in a half-pi shawl.

    A half-pi shawl is worked flat instead of in the round. For planning, the
    total row count is treated the same as the full-circle result because each
    row advances the radius by the same amount as a round would in the circular
    version.
    """
    _validate_radius_and_gauge(desired_radius, round_gauge)
    return total_rounds_for_pi_shawl(desired_radius, round_gauge)


def half_pi_increase_rows(desired_radius: float, round_gauge: float) -> List[int]:
    """Return the row numbers for the half-circle version of the shawl.

    The half-circle version is a flat pattern, so the increases happen on the
    corresponding lower rows of the same geometric sequence: each full-circle
    increase row is mapped to roughly half that row number, clamped at 2.
    """
    _validate_radius_and_gauge(desired_radius, round_gauge)
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
