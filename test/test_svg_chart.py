# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

#!python
import xml.etree.ElementTree as ET

import pyknit.Chart as Chart


def _pattern_3_rows():
    """A known 3-row pattern: rows of widths 2, 2 and 3 at 50px cells."""
    return Chart.parse_chart("k p\nk kfb\np p k")


def test_svg_is_valid_xml():
    svg = Chart.render_chart_svg(_pattern_3_rows())
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")


def test_svg_dimensions_match_plot_chart():
    pattern = _pattern_3_rows()
    chart_image = Chart.plot_chart(pattern)
    root = ET.fromstring(Chart.render_chart_svg(pattern))
    assert root.attrib["width"] == str(chart_image.width)
    assert root.attrib["height"] == str(chart_image.height)


def test_svg_renders_char_and_color_symbols():
    pattern = [
        [
            Chart.Stitch("knit", symbol="V", width=1),
            Chart.Stitch("red", symbol="#ff0000", width=1),
        ]
    ]
    root = ET.fromstring(Chart.render_chart_svg(pattern))
    rects = [e for e in root.iter() if e.tag.endswith("rect")]
    texts = [e for e in root.iter() if e.tag.endswith("text")]
    assert any(r.attrib["fill"] == "white" for r in rects)
    assert any(r.attrib["fill"] == "#ff0000" for r in rects)
    assert any(t.text == "V" for t in texts)


def test_svg_multi_width_cable_spans_cells():
    pattern = [[Chart.Stitch("C2-1L", symbol="#00ff00", width=3)]]
    root = ET.fromstring(Chart.render_chart_svg(pattern))
    cable_rects = [
        e
        for e in root.iter()
        if e.tag.endswith("rect") and e.attrib["fill"] == "#00ff00"
    ]
    assert len(cable_rects) == 1
    assert cable_rects[0].attrib["width"] == str(3 * Chart.cell_width)


def test_svg_direction_rl_reverses_row():
    pattern = [
        [
            Chart.Stitch("knit", symbol="A", width=1),
            Chart.Stitch("purl", symbol="B", width=1),
        ],
        [
            Chart.Stitch("knit", symbol="C", width=1),
            Chart.Stitch("purl", symbol="D", width=1),
        ],
    ]
    lr_root = ET.fromstring(Chart.render_chart_svg(pattern, lr_direction="lr"))
    rl_root = ET.fromstring(Chart.render_chart_svg(pattern, lr_direction="rl"))

    def first_data_symbol(root):
        for e in root.iter():
            if e.tag.endswith("text") and e.text in "ABCD":
                return e.text, float(e.attrib["x"])

    assert first_data_symbol(lr_root) == ("A", 75.0)
    assert first_data_symbol(rl_root) == ("B", 25.0)


def test_svg_missing_image_falls_back_to_label():
    pattern = [[Chart.Stitch("missing", symbol="/no/such/missing.png", width=1)]]
    root = ET.fromstring(Chart.render_chart_svg(pattern))
    labels = [t.text for t in root.iter() if t.tag.endswith("text")]
    assert "missing.png" in labels


def test_svg_embeds_existing_image_as_data_uri():
    pattern = [[Chart.stitch_legend["C2-1L"]]]
    root = ET.fromstring(Chart.render_chart_svg(pattern))
    images = [e for e in root.iter() if e.tag.endswith("image")]
    assert len(images) == 1
    assert images[0].attrib["href"].startswith("data:image/png;base64,")
    assert images[0].attrib["width"] == str(Chart.cell_width * 3)


def test_svg_numbering_cells_present():
    root = ET.fromstring(Chart.render_chart_svg(_pattern_3_rows()))
    texts = [t.text for t in root.iter() if t.tag.endswith("text")]
    for number in ("1", "2", "3"):
        assert number in texts


def test_svg_renders_without_pil(monkeypatch):
    class NoPilImage:
        def __init__(self, *args, **kwargs):
            raise AssertionError("render_chart_svg must not build a PIL Image")

    monkeypatch.setattr(Chart, "Image", NoPilImage, raising=False)
    monkeypatch.setattr(Chart, "ImageDraw", NoPilImage, raising=False)
    monkeypatch.setattr(Chart, "ImageFont", NoPilImage, raising=False)
    root = ET.fromstring(Chart.render_chart_svg(_pattern_3_rows()))
    assert root.tag.endswith("svg")