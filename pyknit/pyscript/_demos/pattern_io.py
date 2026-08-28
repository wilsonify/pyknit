"""Pattern I/O demo: import & export patterns as CSV or JSON.

Uses ``pyknit.io`` for the round-trip, then renders a simple SVG chart of
the re-imported pattern so the demo works with a pure pyknit import.
"""

DEFAULT_INPUTS = {
    "pattern": ("k2 yo k2tog yo k1\n" "p1 k2 yo k2tog p2"),
    "format": "json",
}

TITLE = "Pattern I/O (CSV & JSON)"


def to_html(result):
    """Render the exported format + re-imported chart + instructions."""
    pills = (
        f"<span class='stat-pill'>round-trip rows <em>{result['roundtrip_rows']}</em></span>"
        f"<span class='stat-pill'>round-trip stitches "
        f"<em>{result['roundtrip_stitches']}</em></span>"
    )
    return (
        "<div class='stat-row'>" + pills + "</div>"
        f"<div class='output-box'><pre class='mono'>{_esc(result['exported'])}</pre></div>"
        f"<div class='output-box'>{result['svg']}</div>"
        "<h3>Recovered instructions</h3>"
        f"<div class='output-box'><pre class='mono'>{_esc(result['instructions'])}</pre></div>"
    )


def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def compute(inputs):
    """Parse the pattern, export to the chosen format, and round-trip it."""
    import json as _json

    from pyknit.Chart import parse_chart
    from pyknit.io import (
        csv_to_pattern,
        json_to_pattern,
        pattern_to_csv,
        pattern_to_json,
        pattern_to_instructions,
    )

    text = inputs.get("pattern", "").strip("\n")
    fmt = inputs.get("format", "json")
    if not text.strip():
        raise ValueError("Pattern is empty - enter some knitting instructions")

    pattern = parse_chart(text)
    if not any(pattern):
        raise ValueError("Pattern produced no stitches - check the instructions")

    if fmt == "csv":
        serialized = pattern_to_csv(pattern)
        reparsed = csv_to_pattern(serialized)
        exported = serialized
    elif fmt == "json":
        serialized = pattern_to_json(pattern, metadata={"source": "pattern-io demo"})
        reparsed = json_to_pattern(serialized)
        exported = _json.dumps(_json.loads(serialized), indent=2)
    else:
        raise ValueError("format must be 'csv' or 'json'")

    return {
        "format": fmt,
        "exported": exported,
        "instructions": pattern_to_instructions(reparsed),
        "text": _pattern_to_text(reparsed),
        "roundtrip_rows": len(reparsed),
        "roundtrip_stitches": sum(len(row) for row in reparsed),
        "svg": _chart_svg(reparsed),
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


def _chart_svg(pattern):
    """Minimal self-contained SVG chart, no Pillow required."""
    cell = 22
    rows = len(pattern)
    cols = max((len(row) for row in pattern), default=0)
    width = max(240, cols * cell + 20)
    height = max(60, rows * cell + 26)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" ' f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
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
                f'fill="#5a2a75" text-anchor="middle">{symbol}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
