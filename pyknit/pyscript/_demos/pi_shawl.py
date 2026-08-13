"""Pi Shawl demo: plan the increase rounds of a pi shawl.

Uses ``pyknit.pi_shawl`` for the geometric doublings and draws concentric
rings to show where the stitch count doubles.
"""

DEFAULT_INPUTS = {"radius": 16.5, "row_gauge": 4.5}

TITLE = "Pi Shawl Planner"


def to_html(result):
    """Render the ring diagram plus a summary table."""
    rows = (
        f"<tr><th>Total rounds</th><td class='mono'>{result['total_rounds']}</td></tr>"
        f"<tr><th>Full pi increase rows</th><td class='mono'>"
        f"{', '.join(map(str, result['full_pi']))}</td></tr>"
        f"<tr><th>Half-pi rows</th><td class='mono'>{result['half_pi_rows']}</td></tr>"
        f"<tr><th>Half-pi increase rows</th><td class='mono'>"
        f"{', '.join(map(str, result['half_pi']))}</td></tr>"
    )
    return (
        f"<div class='output-box'>{result['svg']}</div>"
        "<table class='instructions'><tbody>"
        + rows
        + "</tbody></table>"
    )


def compute(inputs):
    """Return total rounds + increase rows + an SVG ring diagram."""
    from pyknit import pi_shawl

    radius = float(inputs["radius"])
    row_gauge = float(inputs["row_gauge"])
    if radius <= 0 or row_gauge <= 0:
        raise ValueError("radius and row gauge must be positive")

    total_rounds = pi_shawl.total_rounds_for_pi_shawl(radius, row_gauge)
    full_pi = pi_shawl.pi_shawl_increase_rows(radius, row_gauge)
    half_pi_rows = pi_shawl.total_rows_half_pi(radius, row_gauge)
    half_pi = pi_shawl.half_pi_increase_rows(radius, row_gauge)

    return {
        "radius": radius,
        "row_gauge": row_gauge,
        "total_rounds": total_rounds,
        "full_pi": full_pi,
        "half_pi_rows": half_pi_rows,
        "half_pi": half_pi,
        "svg": _rings_svg(total_rounds, full_pi),
    }


def _rings_svg(total_rounds, increase_rows):
    """Concentric circles marking the increase rounds of the shawl."""
    size = 360
    cx = cy = size / 2
    max_radius = size / 2 - 70
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" '
        f'height="{size}" viewBox="0 0 {size} {size}">'
    ]

    for r in increase_rows:
        ratio = r / total_rounds
        radius = max(10, max_radius * ratio)
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius:.1f}" '
            f'fill="none" stroke="#7b3fa0" stroke-width="2" '
            f'stroke-dasharray="6 3"/>'
        )
        parts.append(
            f'<text x="{cx + radius * 0.72:.1f}" y="{cy - radius * 0.60:.1f}" '
            f'font-size="10" fill="#5a2a75">round {r}</text>'
        )
        parts.append(
            f'<circle cx="{cx + radius * 0.72:.1f}" cy="{cy - radius * 0.60:.1f}" '
            'r="2" fill="#f3ecf7"/>'
        )

    parts.append(f'<circle cx="{cx}" cy="{cy}" r="10" fill="#c9a7e0"/>')
    parts.append(
        f'<text x="{cx}" y="{size - 30}" text-anchor="middle" font-size="13" '
        f'fill="#5a2a75">pi shawl · increase rows {", ".join(map(str, increase_rows))}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)
DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
