# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

"""Unit tests for pyKnit chart and pattern parsing functions (openspec spec 02/03)."""

import pytest

from pyknit.Chart import Stitch, instruction_to_plot_order, parse_chart, parse_row


class TestStitch:
    def test_repr_shows_symbol(self):
        assert repr(Stitch("knit", "X", 1)) == "'X'"

    def test_str_shows_instruction(self):
        assert str(Stitch("knit", "X", 1)) == "knit"

    @pytest.mark.parametrize(
        ("left", "right", "expected"),
        [
            (Stitch("knit", " ", 1), Stitch("knit", " ", 1), True),
            (Stitch("knit", " ", 1), Stitch("purl", ".", 1), False),
            (Stitch("knit", " ", 1), Stitch("knit", "X", 1), False),
            (Stitch("knit", " ", 1), "knit", False),
        ],
    )
    def test_equality(self, left, right, expected):
        assert (left == right) is expected


class TestParseRow:
    @pytest.mark.parametrize(
        ("row", "expected_width"),
        [
            ("C1-1L", 2),
            ("C2-1R", 3),
            ("C2-2L", 4),
            ("C2-2R", 4),
        ],
    )
    def test_cable_width(self, row, expected_width):
        stitches = parse_row(row)
        assert sum(stitch.width for stitch in stitches) == expected_width

    def test_cable_before_compound_stitch(self):
        stitches = parse_row("C2-2L k2tog")
        assert [stitch.instruction for stitch in stitches] == [
            "sl 2st onto cn, with cn in front, k2, k2 from cn",
            "knit two together",
        ]


class TestParseChart:
    def test_multiline(self):
        pattern = parse_chart("k1 p1\np1 k1")
        assert len(pattern) == 2
        assert pattern[0] == [Stitch("knit", " ", 1), Stitch("purl", ".", 1)]
        assert pattern[1] == [Stitch("purl", ".", 1), Stitch("knit", " ", 1)]


class TestInstructionToPlotOrder:
    @pytest.fixture
    def pattern(self):
        return parse_chart("k1 p1\np1 k1")

    @pytest.mark.parametrize(
        ("vertical_order", "horizontal_order", "expected_symbols"),
        [
            ("bt", "rl", [[" ", "."], [".", " "]]),
            ("tb", "lr", [[" ", "."], [".", " "]]),
            ("bt", "lr", [[".", " "], [" ", "."]]),
            ("tb", "rl", [[".", " "], [" ", "."]]),
        ],
    )
    def test_reorders(
        self, pattern, vertical_order, horizontal_order, expected_symbols
    ):
        result = instruction_to_plot_order(pattern, vertical_order, horizontal_order)
        assert [[stitch.symbol for stitch in row] for row in result] == expected_symbols

    def test_defaults_are_bt_rl(self, pattern):
        assert instruction_to_plot_order(pattern) == instruction_to_plot_order(
            pattern, "bt", "rl"
        )
