"""Pi Shawl demo: plan the increase rounds of a pi shawl.

Uses ``pyknit.pi_shawl`` for the geometric doublings and draws concentric
rings to show where the stitch count doubles.
"""

import math

DEFAULT_INPUTS = {"radius": 16.5, "row_gauge": 4.5}

TITLE = "Pi Shawl Planner"


def _progression(values):
    return " → ".join(str(v) for v in values) if values else "none"


def to_html(result):
    """Render the ring diagram plus a summary table."""
    rows = (
        f"<tr><th>Radius</th><td class='mono'>{result['radius']} {result['unit']}</td></tr>"
        f"<tr><th>Round gauge</th><td class='mono'>{result['row_gauge']} rounds/{result['unit']}</td></tr>"
        f"<tr><th>Formula</th><td class='mono'>total rounds = round(radius × round gauge)</td></tr>"
        f"<tr><th>Total rounds</th><td class='mono'>{result['total_rounds']}</td></tr>"
        f"<tr><th>Full-circle increase rounds</th><td class='mono'>{_progression(result['full_pi'])}</td></tr>"
        f"<tr><th>Half-circle total rows</th><td class='mono'>{result['half_pi_rows']}</td></tr>"
        f"<tr><th>Half-circle increase rows</th><td class='mono'>{_progression(result['half_pi'])}</td></tr>"
    )
    return (
        f"<div class='output-box'>{result['svg']}</div>"
        "<div class='button-row'><button class='btn-secondary send-to-estimator' "
        f"data-stitches='{result.get('_estimator_data', {}).get('estimated_stitches', 0)}' "
        "data-type='shawl_triangle'>"
        "Send to Yarn Estimator &rarr;</button></div>"
        "<div class='output-box'>"
        "<h3>How the math works</h3>"
        "<p><strong>Formula:</strong> total rounds = round(radius × round_gauge).</p>"
        "<p><strong>Full-circle:</strong> the shawl grows as a circle, so total rounds are estimated with the same input unit on both sides of the formula.</p>"  # noqa: E501
        "<p><strong>Half-circle:</strong> the flat version is planned with the same total row count, but the increases happen on lower rows of the same geometric progression.</p>"  # noqa: E501
        "<p><strong>Increase logic:</strong> after the first increase on round 2, the number of plain rounds between increases doubles each time: "  # noqa: E501
        f"{_progression(result['full_pi'])}.</p>"
        "<p><strong>Rounding assumption:</strong> the planner rounds the final total to the nearest whole round, so measured radius and row gauge must use the same unit.</p>"  # noqa: E501
        "</div>"
        "<table class='instructions'><tbody>" + rows + "</tbody></table>"
    )


def compute(inputs):
    """Return total rounds + increase rows + an SVG ring diagram."""
    from pyknit import pi_shawl

    radius = float(inputs["radius"])
    row_gauge = float(inputs["row_gauge"])
    if not math.isfinite(radius) or not math.isfinite(row_gauge):
        raise ValueError("radius and round gauge must be finite numbers")
    if radius <= 0 or row_gauge <= 0:
        raise ValueError("radius and round gauge must be positive")

    total_rounds = pi_shawl.total_rounds_for_pi_shawl(radius, row_gauge)
    full_pi = pi_shawl.pi_shawl_increase_rows(radius, row_gauge)
    half_pi_rows = pi_shawl.total_rows_half_pi(radius, row_gauge)
    half_pi = pi_shawl.half_pi_increase_rows(radius, row_gauge)

    return {
        "radius": radius,
        "row_gauge": row_gauge,
        "unit": "cm",
        "total_rounds": total_rounds,
        "full_pi": full_pi,
        "half_pi_rows": half_pi_rows,
        "half_pi": half_pi,
        "svg": _rings_svg(total_rounds, full_pi),
        "_estimator_data": {
            "estimated_stitches": total_rounds * round(radius * 2),
            "project_type": "shawl_triangle",
            "source": "pi_shawl_planner",
        },
    }


def _rings_svg(total_rounds, increase_rows):
    """Concentric circles marking the increase rounds of the shawl."""
    size = 360
    cx = cy = size / 2
    max_radius = size / 2 - 70
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" ' f'height="{size}" viewBox="0 0 {size} {size}">']

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
        parts.append(f'<circle cx="{cx + radius * 0.72:.1f}" cy="{cy - radius * 0.60:.1f}" ' 'r="2" fill="#f3ecf7"/>')

    parts.append(f'<circle cx="{cx}" cy="{cy}" r="10" fill="#c9a7e0"/>')
    parts.append(
        f'<text x="{cx}" y="{size - 30}" text-anchor="middle" font-size="13" '
        f'fill="#5a2a75">full-circle progression: {_progression(increase_rows)}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
