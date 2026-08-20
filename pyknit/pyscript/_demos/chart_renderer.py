"""Chart Renderer demo: parse a knitting pattern and render it as a chart.

Pure functions used by ``chart-renderer/demo.html``.  This module touches
nothing but pyknit, so the exact demo logic can be imported and tested from
the test suite.  Rendering to SVG is provided by ``shared.py`` at runtime.

Convention shared by every ``_demos`` module:

* ``DEFAULT_INPUTS`` maps each ``<input>/<textarea>/<select>`` id to its
  default value, used by the tests to drive the demo through a fake DOM.
* ``compute(inputs)`` returns a plain dict.
"""

import base64
import importlib.resources as ir
from pathlib import Path

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
_SYMBOL_URI_CACHE = {}


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
        "_estimator_data": {
            "stitch_count": sum(stitch_operations(row) for row in pattern) * len(pattern),
            "project_type": "scarf",
            "source": "chart_renderer",
        },
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
    """Render the chart as inline SVG (honouring lr/tb direction) plus a
    small stats row.  Uses the shared renderer so direction options work;
    falls back to the minimal local renderer when the full one is missing."""
    svg = _chart_svg(result["pattern"], result.get("lr", "lr"), result.get("tb", "tb"))
    pills = []
    for label, count in result["report"]:
        pills.append(f"<span class='stat-pill'>{label}: <em>{count}</em></span>")
    est = result.get("_estimator_data", {})
    send_to = ""
    if est.get("stitch_count"):
        send_to = (
            "<div class='button-row'><button class='btn-secondary send-to-estimator' "
            f"data-stitches='{est['stitch_count']}' data-type='{est.get('project_type', 'scarf')}'>"
            "Send to Yarn Estimator &rarr;</button></div>"
        )
    return (
        f"{send_to}"
        "<div class='stat-row'>" + "".join(pills) + "</div>"
        f"<div class='output-box'>{svg}</div>"
    )


def _chart_svg(pattern, lr_direction="lr", tb_direction="tb"):
    """Render the chart as inline SVG.

    Prefers the full ``pyknit.Chart.render_chart_svg`` (which honours the
    lr/tb directions and embeds symbol images as data URIs).  Falls back to
    a minimal self-contained SVG when that renderer is unavailable.
    """
    try:
        from pyknit.Chart import render_chart_svg

        return render_chart_svg(pattern, lr_direction, tb_direction)
    except Exception:
        return _minimal_svg(pattern)


def _minimal_svg(pattern):
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
            raw_symbol = str(getattr(st, "symbol", "?"))
            parts.append(
                f'<rect x="{10 + x * cell}" y="{10 + y * cell}" '
                f'width="{cell - 1}" height="{cell - 1}" rx="3" fill="#f3ecf7" '
                'stroke="#7b3fa0" stroke-width="1"/>'
            )
            symbol_href = _symbol_href(raw_symbol)
            if symbol_href is not None:
                parts.append(
                    f'<image x="{10 + x * cell + 2}" y="{10 + y * cell + 2}" '
                    f'width="{cell - 5}" height="{cell - 5}" href="{symbol_href}" />'
                )
            else:
                symbol = _display_symbol(st)
                parts.append(
                    f'<text x="{10 + x * cell + cell / 2}" '
                    f'y="{10 + y * cell + cell / 2 + 4}" font-size="13" '
                    f'fill="#5a2a75" text-anchor="middle">{_esc(symbol)}</text>'
                )
    parts.append("</svg>")
    return "\n".join(parts)


def _display_symbol(stitch):
    symbol = str(getattr(stitch, "symbol", "?")).strip()
    if not symbol:
        return "·"
    if _looks_like_path(symbol):
        # Japanese legend may expose package paths; never render those literally.
        cat = str(getattr(stitch, "category", "") or "")
        if cat == "decrease":
            return "/"
        if cat == "yarn-over":
            return "O"
        if cat == "purl":
            return "."
        return "·"
    return symbol


def _looks_like_path(symbol):
    return symbol.endswith(".png") or "/" in symbol or "\\" in symbol


def _symbol_href(symbol):
    """Convert a symbol image path into a browser-safe image href."""
    if not _looks_like_path(symbol):
        return None
    name = Path(symbol).name
    if not name or not name.endswith(".png"):
        return None
    cached = _SYMBOL_URI_CACHE.get(name)
    if cached is not None:
        return cached

    data = _read_symbol_bytes(symbol, name)
    if data is None:
        # Fall back to vendored static assets in demos/_assets.
        href = "/_assets/japanese-symbols/" + name
        _SYMBOL_URI_CACHE[name] = href
        return href

    uri = "data:image/png;base64," + base64.b64encode(data).decode("ascii")
    _SYMBOL_URI_CACHE[name] = uri
    return uri


def _read_symbol_bytes(symbol, name):
    try:
        p = Path(symbol)
        if p.is_file():
            return p.read_bytes()
    except Exception:
        pass

    try:
        asset = ir.files("pyknit").joinpath("symbols", "japanese", name)
        if asset.is_file():
            return asset.read_bytes()
    except Exception:
        pass
    return None


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
