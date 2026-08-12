#!/usr/bin/env python3
# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

from pyknit import pi_shawl


@pytest.mark.parametrize(
    ("desired_radius", "round_gauge", "expected"),
    [
        (5, 5, 25),
        (50, 3, 150),
        (10, 4.5, 45),
    ],
)
def test_total_rounds_for_pi_shawl(desired_radius, round_gauge, expected):
    assert pi_shawl.total_rounds_for_pi_shawl(desired_radius, round_gauge) == expected


def test_pi_shawl_increase_rows():
    assert pi_shawl.pi_shawl_increase_rows(5, 5) == [2, 6, 13]
    assert pi_shawl.pi_shawl_increase_rows(50, 3) == [2, 6, 13, 26, 51, 100]


def test_total_rounds_for_pi_shawl():
    assert pi_shawl.total_rounds_for_pi_shawl(50, 3) == 150


def test_half_pi_increase_rows_start_at_2_are_strictly_increasing_and_in_bounds():
    for radius, gauge in [(5, 5), (50, 3)]:
        increase_rows = pi_shawl.half_pi_increase_rows(radius, gauge)
        total_rows = pi_shawl.total_rows_half_pi(radius, gauge)
        assert increase_rows[0] == 2
        assert increase_rows == sorted(set(increase_rows))
        assert increase_rows[-1] <= total_rows


def test_half_pi_increase_rows_is_deterministic():
    assert pi_shawl.half_pi_increase_rows(5, 5) == pi_shawl.half_pi_increase_rows(
        5, 5
    )
    assert pi_shawl.half_pi_increase_rows(50, 3) == pi_shawl.half_pi_increase_rows(
        50, 3
    )


def test_half_pi_increase_rows_matches_documented_values():
    assert pi_shawl.half_pi_increase_rows(5, 5) == [2, 3, 6]
    assert pi_shawl.half_pi_increase_rows(50, 3) == [2, 3, 6, 13, 25, 50]


def test_total_rows_half_pi_matches_full_pi_rounds():
    assert pi_shawl.total_rows_half_pi(5, 5) == pi_shawl.total_rounds_for_pi_shawl(
        5, 5
    )
    assert pi_shawl.total_rows_half_pi(50, 3) == pi_shawl.total_rounds_for_pi_shawl(
        50, 3
    )
