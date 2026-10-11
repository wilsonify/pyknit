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
            "Cut yarn leaving 4 inch tail, thread through remaining " "stitches and pull closed",
        ]

    @pytest.mark.parametrize(("repeats", "stitches"), [(0, 10), (4, 0), (-1, 10), (4, -2)])
    def test_invalid_params(self, repeats, stitches):
        with pytest.raises(ValueError, match="Invalid starting parameters"):
            Hat().crown_decreases(repeats, stitches)

    def test_remainder_schedules_extra_decreases(self):
        instructions = Hat().crown_decreases(4, 10)
        assert isinstance(instructions, list)
        assert "(4 stitches)" in instructions[0]
        assert instructions[-1].startswith("Cut yarn")
