"""Yarn Estimator demo: estimate yarn use and knitting time.

Uses ``pyknit.GaugeSwatch`` (with yardage/weight per unit) and
``pyknit.estimate`` to give a full project estimate.
"""

DEFAULT_INPUTS = {
    "stitch_count": 24,
    "stitch_measure": 4,
    "row_count": 18,
    "row_measure": 3.25,
    "units": "in",
    "project_stitches": 12000,
    "yards_per_stitch": 0.02,
    "grams_per_stitch": 0.15,
    "seconds_per_stitch": 3,
    "ball_yardage": 230,
    "ball_weight": 50,
}

TITLE = "Yarn Estimator"


def to_html(result):
    """Render the estimator bars plus the summary digits."""
    pills = (
        f"<span class='stat-pill'>{result['yards']} yd ≈ "
        f"<em>{result['balls']}</em> balls</span>"
        f"<span class='stat-pill'>{result['grams']} g ≈ "
        f"<em>{result['balls_by_weight']}</em> balls</span>"
        f"<span class='stat-pill'>{result['meters']} m</span>"
        f"<span class='stat-pill'>~ <em>{result['time_text']}</em></span>"
    )
    return (
        f"<div class='output-box'>{result['svg']}</div>"
        "<div class='stat-row'>"
        + pills
        + "</div>"
    )


def compute(inputs):
    """Return a full estimate report for a project."""
    from pyknit.estimate import estimate_knitting_time, format_knitting_time
    from pyknit.GaugeSwatch import GaugeSwatch

    for field in (
        "stitch_count",
        "stitch_measure",
        "row_count",
        "row_measure",
        "yards_per_stitch",
        "grams_per_stitch",
        "ball_yardage",
        "ball_weight",
    ):
        if float(inputs[field]) <= 0:
            raise ValueError(f"{field} must be positive")

    gs = GaugeSwatch(
        stitch_count=float(inputs["stitch_count"]),
        stitch_measure=float(inputs["stitch_measure"]),
        row_count=float(inputs["row_count"]),
        row_measure=float(inputs["row_measure"]),
        units=inputs.get("units", "in"),
        yardage_per_unit=float(inputs["yards_per_stitch"]),
        weight_per_unit=float(inputs["grams_per_stitch"]),
    )
    project_stitches = int(inputs["project_stitches"])
    if project_stitches <= 0:
        raise ValueError("project stitches must be positive")
    if float(inputs["seconds_per_stitch"]) <= 0:
        raise ValueError("seconds per stitch must be positive")

    yards = gs.estimate_yardage(project_stitches)
    grams = gs.estimate_weight(project_stitches)
    time_delta = estimate_knitting_time(
        project_stitches, float(inputs["seconds_per_stitch"])
    )
    time_text = format_knitting_time(time_delta)

    ball_yards = float(inputs["ball_yardage"])
    ball_grams = float(inputs["ball_weight"])
    balls = max(1, -(-yards // ball_yards))
    balls_by_weight = max(1, -(-grams // ball_grams))

    return {
        "stitch_gauge": round(gs.stitch_gauge(), 2),
        "row_gauge": round(gs.row_gauge(), 2),
        "yards": round(yards, 1),
        "grams": round(grams, 1),
        "time_text": time_text,
        "hours": round(time_delta.total_seconds() / 3600, 1),
        "balls": int(balls),
        "balls_by_weight": int(balls_by_weight),
        "meters": round(yards * 0.9144, 1),
        "svg": _estimator_svg(yards, grams, project_stitches),
    }


def _estimator_svg(yards, grams, project_stitches):
    """Simple horizontal bar chart of the estimate."""
    width = 460
    height = 120
    margin = 40
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    ]
    max_val = max(yards, grams)
    scale = (width - margin - 20) / max(max_val, 1)

    parts.append(f'<text x="{margin}" y="16" font-size="11" fill="#5a2a75">yards</text>')
    parts.append(
        f'<rect x="{margin}" y="24" width="{yards * scale:.1f}" height="16" '
        'fill="#7b3fa0" rx="4"/>'
    )
    parts.append(f'<text x="{margin}" y="62" font-size="11" fill="#5a2a75">grams</text>')
    parts.append(
        f'<rect x="{margin}" y="70" width="{grams * scale:.1f}" height="16" '
        'fill="#4aa3a2" rx="4"/>'
    )
    parts.append(
        f'<text x="{margin}" y="108" font-size="11" fill="#888">'
        f"{project_stitches:,} stitches</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)
DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
