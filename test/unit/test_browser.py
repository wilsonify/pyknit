# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

# !python

import pytest

from pyknit.browser import available_backends, pattern_to_text, render_pattern
from pyknit.Chart import Stitch, parse_chart


@pytest.fixture
def small_pattern():
    return parse_chart("k1 p2 k1\np2 k1 p2")


def test_available_backends_has_expected_and_is_deterministic():
    backends = available_backends()
    assert isinstance(backends, list)
    assert "pillow" in backends
    assert backends == available_backends()


def test_render_pattern_returns_svg_when_svg_available(small_pattern):
    fmt, content = render_pattern(small_pattern)
    assert fmt == "svg"
    assert isinstance(content, str)
    assert content.startswith("<?xml") or content.startswith("<svg")


def test_render_pattern_svg_branch_when_render_chart_svg_exists(small_pattern, monkeypatch):
    """Verify SVG backend is tried when render_chart_svg exists."""
    import pyknit.Chart as chart_module

    monkeypatch.setattr(
        chart_module,
        "render_chart_svg",
        lambda pattern, **kwargs: "<svg/>",
        raising=False,
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


def test_render_pattern_dangling_image_does_not_crash():
    """A pattern whose symbol file is missing must not crash render_pattern."""
    pattern = [
        [Stitch(instruction="cable", symbol="does-not-exist.png", width=2)],
        [Stitch(instruction="cable", symbol="does-not-exist.png", width=2)],
    ]
    fmt, content = render_pattern(pattern)
    assert fmt in ("svg", "text")
    assert isinstance(content, str)
