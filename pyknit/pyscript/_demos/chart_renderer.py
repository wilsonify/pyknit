"""Chart Renderer demo: parse a knitting pattern and render it as a chart.

Pure functions used by ``chart-renderer/demo.html``.  This module touches
nothing but pyknit, so the exact demo logic can be imported and tested from
the test suite.  Rendering to SVG is provided by ``shared.py`` at runtime.

Convention shared by every ``_demos`` module:

* ``DEFAULT_INPUTS`` maps each ``<input>/<textarea>/<select>`` id to its
  default value, used by the tests to drive the demo through a fake DOM.
* ``compute(inputs)`` returns a plain dict.
"""

DEFAULT_INPUTS = {
    "pattern": (
        "k2 yo k2tog yo k1\n"
        "p1 k2 yo k2tog p2\n"
        "k2tog yo k3 yo\n"
        "p3 k2tog yo p1"
    ),
    "legend": "default",
    "lr": "lr",
    "tb": "tb",
}

TITLE = "Chart Renderer"


def _parse(pattern_text, legend):
    from pyknit.Chart import parse_row

    rows = []
    for line in pattern_text.strip().split("\n"):
        row = []
        for section in line.split():
            row.extend(parse_row(section, legend))
        rows.append(row)
    return rows


def compute(inputs):
    """Parse the pattern with the selected legend and direction settings."""
    from pyknit.Chart import stitch_legend, stitch_legend_japanese
    from pyknit.GaugeSwatch import (
        chart_width,
        stitch_operations,
        stitches_consumed,
        stitches_produced,
    )

    legend_name = inputs.get("legend", "default")
    legend = stitch_legend_japanese if legend_name == "japanese" else stitch_legend

    pattern_text = inputs.get("pattern", "")
    if not pattern_text.strip():
        raise ValueError("Pattern is empty - enter some knitting instructions")

    pattern = _parse(pattern_text, legend)
    if not any(pattern):
        raise ValueError("Pattern produced no stitches - check the instructions")

    return {
        "legend": legend_name,
        "lr": inputs.get("lr", "lr"),
        "tb": inputs.get("tb", "tb"),
        "pattern": pattern,
        "text": _pattern_to_text(pattern),
        "report": [
            ("rows", len(pattern)),
            ("stitches", sum(stitch_operations(row) for row in pattern)),
            ("consumed", sum(stitches_consumed(row) for row in pattern)),
            ("produced", sum(stitches_produced(row) for row in pattern)),
            ("chart width", max(chart_width(r) for r in pattern)),
        ],
    }


def _pattern_to_text(pattern):
    lines = []
    for row in pattern:
        codes = []
        for stitch in row:
            symbol = getattr(stitch, "symbol", "?")
            codes.append(symbol if len(symbol) == 1 else "X")
        lines.append("".join(codes))
    return "\n".join(lines)


def to_html(result):
    """Render the chart as inline SVG plus a small stats row."""
    svg = _chart_svg(result["pattern"])
    pills = []
    for label, count in result["report"]:
        pills.append(f"<span class='stat-pill'>{label}: <em>{count}</em></span>")
    return (
        "<div class='stat-row'>" + "".join(pills) + "</div>"
        f"<div class='output-box'>{svg}</div>"
    )


def _chart_svg(pattern):
    """Minimal self-contained SVG chart, no Pillow required."""
    cell = 24
    rows = len(pattern)
    cols = max((len(row) for row in pattern), default=0)
    width = max(280, cols * cell + 20)
    height = max(80, rows * cell + 26)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    ]
    for y, row in enumerate(pattern):
        for x, st in enumerate(row):
            symbol = getattr(st, "symbol", "?").strip() or "·"
            parts.append(
                f'<rect x="{10 + x * cell}" y="{10 + y * cell}" '
                f'width="{cell - 1}" height="{cell - 1}" rx="3" fill="#f3ecf7" '
                'stroke="#7b3fa0" stroke-width="1"/>'
            )
            parts.append(
                f'<text x="{10 + x * cell + cell / 2}" '
                f'y="{10 + y * cell + cell / 2 + 4}" font-size="13" '
                f'fill="#5a2a75" text-anchor="middle">{_esc(symbol)}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def _esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
