# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

# !python

import pytest

from pyknit.browser import available_backends, pattern_to_text, render_pattern
from pyknit.Chart import Stitch, parse_chart


@pytest.fixture
def small_pattern():
    return parse_chart("k1 p2 k1\np2 k1 p2")


def test_available_backends_has_pillow_and_is_deterministic():
    backends = available_backends()
    assert isinstance(backends, list)
    assert "pillow" in backends  # Pillow is a hard dependency of pyKnit
    assert backends == available_backends()


def test_render_pattern_returns_png_bytes(small_pattern):
    fmt, content = render_pattern(small_pattern)
    assert fmt == "png"
    assert isinstance(content, bytes)
    # PNG magic number: \x89PNG\r\n\x1a\n
    assert content.startswith(b"\x89PNG\r\n\x1a\n")


def test_render_pattern_svg_branch_when_render_chart_svg_exists(
    small_pattern, monkeypatch
):
    """Stand-in for pyknit.Chart.render_chart_svg (planned on another branch)."""

    def fake_render_chart_svg(pattern, legend=None, **kwargs):
        return "<svg/>"

    # render_chart_svg does not exist yet, so patch the module attribute
    # directly rather than via a dotted import path.
    import pyknit.Chart as chart_module

    monkeypatch.setattr(
        chart_module, "render_chart_svg", fake_render_chart_svg, raising=False
    )
    fmt, content = render_pattern(small_pattern)
    assert fmt == "svg"
    assert content == "<svg/>"


def test_pattern_to_text_matches_row_lengths(small_pattern):
    text = pattern_to_text(small_pattern)
    lines = text.split("\n")
    assert len(lines) == len(small_pattern)
    for line, row in zip(lines, small_pattern):
        assert len(line) == len(row)


def test_render_pattern_falls_back_to_text_for_dangling_image():
    """A pattern whose symbol file is missing must not crash render_pattern."""
    pattern = [
        [Stitch(instruction="cable", symbol="does-not-exist.png", width=2)],
        [Stitch(instruction="cable", symbol="does-not-exist.png", width=2)],
    ]
    fmt, content = render_pattern(pattern)
    # plot_chart raises on the missing image, so we degrade to a text grid.
    assert fmt == "text"
    assert "X" in content
