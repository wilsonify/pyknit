# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

#!python
"""Tests for stitch metadata and symbol path resolution."""

import os
import pathlib
import re
import warnings

import pyknit
from pyknit import Chart


COLOR_SYMBOL = re.compile(r"^#[0-9a-fA-F]{6}$")


def test_stitch_metadata_defaults():
    """Unspecified metadata falls back to documented defaults."""
    stitch = Chart.Stitch("knit", symbol=" ", width=1)
    assert stitch.instruction == "knit"
    assert stitch.symbol == " "
    assert stitch.width == 1
    assert stitch.category == ""
    assert stitch.direction == "neutral"
    assert stitch.consumes == 1
    assert stitch.produces == 1


def test_stitch_equality():
    """Two Stitches built the same way compare equal."""
    assert Chart.Stitch("knit", symbol=" ", width=1) == Chart.Stitch(
        "knit", symbol=" ", width=1
    )
    increase = Chart.Stitch(
        "knit front and back",
        symbol="V",
        width=1,
        category="increase",
        consumes=1,
        produces=2,
    )
    assert increase == Chart.Stitch(
        "knit front and back",
        symbol="V",
        width=1,
        category="increase",
        consumes=1,
        produces=2,
    )
    assert Chart.Stitch("knit", symbol=" ", width=1) != increase


def test_default_legend_symbols_exist():
    """Every default-legend image path resolves to a file on disk."""
    for code, stitch in Chart.stitch_legend.items():
        if stitch.symbol.endswith(".png"):
            assert os.path.exists(stitch.symbol), f"{code}: missing {stitch.symbol}"


def test_japanese_legend_symbols_exist():
    """Every Japanese symbol is a colour, a character, or a real image file."""
    for code, stitch in Chart.stitch_legend_japanese.items():
        symbol = stitch.symbol
        if COLOR_SYMBOL.match(symbol):
            continue
        if symbol.endswith(".png"):
            assert os.path.exists(symbol), f"{code}: missing {symbol}"
        elif os.sep in symbol or pathlib.Path(symbol).suffix:
            # looks like a (bare) file reference: it must resolve
            assert os.path.exists(symbol), f"{code}: dangling symbol {symbol}"


def test_chart_module_compiles_without_syntax_warnings():
    """Regression check for the old symbol_dir + "\\japanese" escape warning."""
    module_path = pathlib.Path(pyknit.Chart.__file__)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        compile(module_path.read_text(), str(module_path), "exec")


def test_increase_metadata():
    kfb = Chart.stitch_legend["kfb"]
    assert kfb.category == "increase"
    assert kfb.produces > kfb.consumes
    assert (kfb.consumes, kfb.produces) == (1, 2)
    yo = Chart.stitch_legend["yo"]
    assert yo.category == "yarn-over"
    assert yo.consumes == 0
    assert yo.produces == 1


def test_decrease_metadata():
    k2tog = Chart.stitch_legend["k2tog"]
    assert k2tog.category == "decrease"
    assert k2tog.consumes > k2tog.produces
    assert (k2tog.consumes, k2tog.produces) == (2, 1)
    ssk = Chart.stitch_legend["ssk"]
    assert ssk.category == "decrease"
    assert ssk.consumes > ssk.produces


def test_cable_metadata():
    cable = Chart.stitch_legend["C2-2L"]
    assert cable.category == "cable"
    assert cable.direction == "left"
    assert cable.consumes == cable.produces == cable.width == 4


def test_k2tog_parse_carries_decrease_category():
    parsed = Chart.parse_row("k2tog", Chart.stitch_legend)
    assert len(parsed) == 1
    assert parsed[0].instruction == "knit two together"
    assert parsed[0].category == "decrease"