"""Even Shaping demo: increase/decrease evenly across a round or a row.

Uses ``pyknit.increase_evenly`` and ``pyknit.decrease_evenly`` and turns the
resulting instruction string into a simple SVG representation of the row.
"""

DEFAULT_INPUTS = {
    "operation": "increase",
    "in_the_round": "true",
    "starting_count": 20,
    "number": 5,
}

TITLE = "Even Shaping"


def to_html(result):
    """Render the row diagram plus the written instruction."""
    return (
        f"<div class='output-box'>{result['svg']}</div>"
        "<h3>Written instruction</h3>"
        f"<div class='output-box'><pre class='mono'>{_esc(result['result'])}</pre></div>"
    )


def _esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def compute(inputs):
    """Return the even-shaping instruction + an SVG row diagram."""
    import pyknit

    op = inputs.get("operation", "increase")
    in_the_round = inputs.get("in_the_round", "true") in ("true", "on", "1")
    starting = int(inputs["starting_count"])
    number = int(inputs["number"])

    if starting <= 0 or number <= 0:
        raise ValueError("starting count and number must be positive")
    if number > starting:
        raise ValueError("number must not exceed the starting count")

    if op == "increase":
        result = pyknit.increase_evenly(starting, number, in_the_round)
        svg = _row_svg(starting, number, increasing=True)
    elif op == "decrease":
        if number >= starting:
            raise ValueError("number must be smaller than the starting count")
        result = pyknit.decrease_evenly(starting, number, in_the_round)
        svg = _row_svg(starting, number, increasing=False)
    else:
        raise ValueError("operation must be 'increase' or 'decrease'")

    return {
        "operation": op,
        "in_the_round": in_the_round,
        "starting": starting,
        "number": number,
        "result": result,
        "svg": svg,
    }


def _row_svg(starting, number, increasing):
    """Small diagram of a round: cells with +/− markers on the changes."""
    width = 560
    cell = 18
    margin = 40
    total = starting
    gap = total / number
    height = 110

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    ]
    x = margin
    marker = "+" if increasing else "-"
    color = "#28a745" if increasing else "#dc3545"
    for i in range(total):
        if number > 1 and i % max(1, int(gap)) == 0 and i > 0:
            parts.append(
                f'<text x="{x - cell / 2}" y="{height - 28}" '
                f'font-size="13" fill="{color}" text-anchor="middle">'
                f"{marker}</text>"
            )
        parts.append(
            f'<rect x="{x}" y="14" width="{cell}" height="{cell}" '
            f'rx="3" fill="#f3ecf7" stroke="#7b3fa0" stroke-width="1"/>'
        )
        x += cell
    parts.append(
        f'<text x="{margin}" y="{height - 4}" font-size="11" fill="#5a2a75">'
        f'{total} stitches · {number} evenly-spaced {"increases" if increasing else "decreases"}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)
DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
