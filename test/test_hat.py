# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

"""Unit tests for pyKnit.Hat crown decreases (openspec spec 07)."""

import pytest

from pyknit.Hat import Hat


class TestCrownDecreases:
    def test_even_division_sequence(self):
        instructions = Hat().crown_decreases(repeats=8, stitches=24)
        assert instructions == [
            "[k1, k2tog] repeat 8 times (16 stitches)",
            "Knit 1 round",
            "k2tog 8 times (8 stitches)",
            "Knit 1 round",
            "Cut yarn leaving 4 inch tail, thread through remaining "
            "stitches and pull closed",
        ]

    @pytest.mark.parametrize(
        ("repeats", "stitches", "expected"),
        [
            (0, 10, "Invalid starting parameters"),
            (4, 0, "Invalid starting parameters"),
            (4, 10, "Error: stitch count does not divide evenly"),
        ],
    )
    def test_invalid_params(self, repeats, stitches, expected):
        assert Hat().crown_decreases(repeats, stitches) == expected
