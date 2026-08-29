"""Yarn Estimator demo: estimate yarn use and knitting time.

Uses project type, dimensions, gauge, and yarn ball info to produce
realistic, transparent estimates with ranges and plausibility checks.
Falls back to per-stitch inputs in advanced mode.
"""

import math

DEFAULT_INPUTS = {
    "project_type": "hat",
    "project_width": 20,
    "project_height": 9,
    "stitch_gauge": 5,
    "row_gauge": 7,
    "units": "in",
    "yarn_per_ball_yards": 230,
    "yarn_per_ball_grams": 50,
    "yarn_weight_category": "",
    "knitting_pace": "medium",
    "advanced_mode": "false",
    "project_stitches": 12000,
    "yards_per_stitch": 0.02,
    "grams_per_stitch": 0.15,
    "seconds_per_stitch": 3,
    "stitch_count": 24,
    "stitch_measure": 4,
    "row_count": 18,
    "row_measure": 3.25,
}

TITLE = "Yarn & Time Estimator"

PROJECT_TYPES = {
    "hat": {
        "label": "Hat / Beanie",
        "default_width": 20,
        "default_height": 9,
        "shape": "rectangle",
    },
    "scarf": {
        "label": "Scarf / Cowl",
        "default_width": 6,
        "default_height": 60,
        "shape": "rectangle",
    },
    "shawl_triangle": {
        "label": "Triangular Shawl",
        "default_width": 30,
        "default_height": 30,
        "shape": "triangle",
    },
    "shawl_rectangle": {
        "label": "Rectangle Shawl / Wrap",
        "default_width": 30,
        "default_height": 60,
        "shape": "rectangle",
    },
    "shawl_crescent": {
        "label": "Crescent Shawl",
        "default_width": 30,
        "default_height": 15,
        "shape": "triangle",
    },
    "sweater": {
        "label": "Sweater (body only)",
        "default_width": 36,
        "default_height": 28,
        "shape": "rectangle",
    },
    "blanket": {
        "label": "Baby Blanket",
        "default_width": 30,
        "default_height": 40,
        "shape": "rectangle",
    },
    "custom": {
        "label": "Custom dimensions",
        "default_width": 20,
        "default_height": 20,
        "shape": "rectangle",
    },
}

PACE_PRESETS = {
    "slow": {"label": "Beginner / slow", "seconds_per_stitch": 4.0},
    "medium": {"label": "Intermediate / average", "seconds_per_stitch": 2.5},
    "fast": {"label": "Advanced / fast", "seconds_per_stitch": 1.5},
}

YARN_CATEGORY_YARDS_PER_100G = {
    "lace": 600,
    "fingering": 400,
    "sport": 300,
    "dk": 250,
    "worsted": 200,
    "bulky": 130,
    "super bulky": 80,
}

RANGE_FACTOR = 0.15


def to_html(result):
    "Render the estimator output with stat pills, math breakdown, and warnings." ""
    parts = []

    parts.append(f"<div class='output-box'>{result['svg']}</div>")

    pills = (
        f"<span class='stat-pill'>{result['yards_low']}&ndash;{result['yards_high']} yd</span>"
        f"<span class='stat-pill'>{result['grams_low']}&ndash;{result['grams_high']} g</span>"
        f"<span class='stat-pill'><em>{result['balls_yard']}</em> balls (by length)"
        + (
            f" / <em>{result['balls_weight']}</em> balls (by weight)"
            if result["balls_yard"] != result["balls_weight"]
            else ""
        )
        + "</span>"
        f"<span class='stat-pill'>~ <em>{result['time_text']}</em></span>"
        f"<span class='stat-pill'>{result['project_stitches']:,} stitches</span>"
    )
    parts.append(f"<div class='stat-row'>{pills}</div>")

    if result.get("warnings"):
        items = "".join(f"<li>{_esc(w)}</li>" for w in result["warnings"])
        parts.append("<div class='warning-box'><strong>Worth a second look</strong>" f"<ul>{items}</ul></div>")

    parts.append("<div class='output-box'>")
    parts.append("<h3>How this was calculated</h3>")
    parts.append("<table class='instructions'><tbody>")
    for row in result.get("math_rows", []):
        parts.append(f"<tr><th>{_esc(row[0])}</th><td class='mono'>{_esc(row[1])}</td></tr>")
    parts.append("</tbody></table></div>")

    if result.get("balls_detail"):
        parts.append("<div class='output-box'>")
        parts.append("<h3>Ball count breakdown</h3>")
        parts.append("<table class='instructions'><tbody>")
        for label, value in result["balls_detail"]:
            parts.append(f"<tr><th>{_esc(label)}</th><td class='mono'>{_esc(value)}</td></tr>")
        parts.append("</tbody></table></div>")

    if result.get("assumptions"):
        assumption_items = "".join(f"<li>{_esc(a)}</li>" for a in result["assumptions"])
        parts.append(
            "<div class='output-box'>"
            "<h3>Assumptions</h3>"
            f"<ul style='padding-left:1.3rem'>{assumption_items}</ul></div>"
        )

    confidence = result.get("confidence", "medium")
    parts.append(
        f"<p class='field-hint'>Confidence: <strong>{confidence}</strong> &mdash; "
        + {
            "high": "All inputs provided directly; estimate is most reliable.",
            "medium": "Some defaults from project type were used; adjust dimensions for your project.",
            "low": "Per-stitch estimates are rough; a gauge swatch gives better results.",
        }.get(confidence, "")
        + "</p>"
    )

    return "\n".join(parts)


def compute(inputs):
    "Return a full estimate report for a project." ""
    advanced = str(inputs.get("advanced_mode", "false")).lower() == "true"

    if advanced:
        return _compute_advanced(inputs)
    return _compute_friendly(inputs)


def _compute_friendly(inputs):
    "Estimate from project type, dimensions, and gauge." ""
    from pyknit.estimate import estimate_knitting_time, format_knitting_time

    project_type = inputs.get("project_type", "hat")
    if project_type not in PROJECT_TYPES:
        raise ValueError("project_type must be one of " + ", ".join(PROJECT_TYPES.keys()))
    pt = PROJECT_TYPES[project_type]

    width = _pos_float(inputs, "project_width", "project width")
    height = _pos_float(inputs, "project_height", "project height")
    stitch_gauge = _pos_float(inputs, "stitch_gauge", "stitch gauge")
    row_gauge = _pos_float(inputs, "row_gauge", "row gauge")
    ball_yards = _pos_float(inputs, "yarn_per_ball_yards", "yards per ball")
    ball_grams = _pos_float(inputs, "yarn_per_ball_grams", "grams per ball")
    pace_key = inputs.get("knitting_pace", "medium")

    if pace_key not in PACE_PRESETS:
        raise ValueError("knitting_pace must be one of " + ", ".join(PACE_PRESETS.keys()))
    seconds_per_stitch = PACE_PRESETS[pace_key]["seconds_per_stitch"]

    warnings = _plausibility_checks(
        stitch_gauge,
        row_gauge,
        width,
        height,
        ball_yards,
        ball_grams,
        seconds_per_stitch,
        project_type,
    )

    shape = pt["shape"]
    stitches_across = round(width * stitch_gauge)
    rows_tall = round(height * row_gauge)
    project_stitches = stitches_across * rows_tall
    if shape == "triangle":
        project_stitches = project_stitches // 2

    yards = _estimate_yarn_yards(project_stitches, stitch_gauge, row_gauge)
    grams = _estimate_yarn_grams(yards, ball_yards, ball_grams)

    time_delta = estimate_knitting_time(project_stitches, seconds_per_stitch)
    time_text = format_knitting_time(time_delta)

    yards_low, yards_high = _range(yards)
    grams_low, grams_high = _range(grams)

    balls_yard = max(1, math.ceil(yards / ball_yards))
    balls_weight = max(1, math.ceil(grams / ball_grams))

    assumptions = [
        f"Project type: {pt['label']} ({shape}), {width} x {height} inches.",
        f"Gauge: {stitch_gauge} sts/in x {row_gauge} rows/in.",
        f"Stitch workload: {stitches_across} across x {rows_tall} tall"
        + (" / 2 (triangle) = " if shape == "triangle" else " = ")
        + f"{project_stitches:,} stitches.",
        f"Yarn pace: {pace_key} ({seconds_per_stitch} sec/stitch).",
        "Yarn estimate is based on typical yardage per stitch for this gauge. "
        "Weigh your swatch for a more precise number.",
        f"Ranges are +/- {int(RANGE_FACTOR * 100)}% of the central estimate.",
    ]

    math_rows = [
        ("Stitches across", f"{width} in x {stitch_gauge} sts/in = {stitches_across}"),
        ("Rows tall", f"{height} in x {row_gauge} rows/in = {rows_tall}"),
        (
            "Total stitches",
            f"{stitches_across} x {rows_tall}" + (" / 2" if shape == "triangle" else "") + f" = {project_stitches:,}",
        ),
        (
            "Yards needed",
            f"~{yards:.0f} yd (range: {yards_low:.0f}&ndash;{yards_high:.0f})",
        ),
        (
            "Grams needed",
            f"~{grams:.0f} g (range: {grams_low:.0f}&ndash;{grams_high:.0f})",
        ),
        (
            "Knitting time",
            f"{project_stitches:,} stitches x {seconds_per_stitch} sec = {time_text}",
        ),
    ]

    balls_detail = [
        (
            "By length",
            f"ceil({yards:.0f} yd / {ball_yards} yd/ball) = {balls_yard} ball{'s' if balls_yard != 1 else ''}",
        ),
        (
            "By weight",
            f"ceil({grams:.0f} g / {ball_grams} g/ball) = {balls_weight} ball{'s' if balls_weight != 1 else ''}",
        ),
    ]
    if balls_yard != balls_weight:
        balls_detail.append(
            (
                "Why the difference?",
                "Yarn balls vary: some are sold by weight, some by length. Buy the higher number to be safe.",
            )
        )

    return {
        "project_stitches": project_stitches,
        "yards": round(yards, 1),
        "grams": round(grams, 1),
        "yards_low": round(yards_low, 0),
        "yards_high": round(yards_high, 0),
        "grams_low": round(grams_low, 0),
        "grams_high": round(grams_high, 0),
        "time_text": time_text,
        "hours": round(time_delta.total_seconds() / 3600, 1),
        "balls_yard": balls_yard,
        "balls_weight": balls_weight,
        "meters": round(yards * 0.9144, 1),
        "stitches_across": stitches_across,
        "rows_tall": rows_tall,
        "project_type": project_type,
        "shape": shape,
        "confidence": "high" if project_type != "custom" else "medium",
        "warnings": warnings,
        "math_rows": math_rows,
        "balls_detail": balls_detail,
        "assumptions": assumptions,
        "svg": _estimator_svg(yards, grams, project_stitches),
    }


def _compute_advanced(inputs):
    "Estimate from direct stitch count and per-stitch values (legacy mode)." ""
    from pyknit.estimate import estimate_knitting_time, format_knitting_time
    from pyknit.GaugeSwatch import GaugeSwatch

    for field in (
        "stitch_count",
        "stitch_measure",
        "row_count",
        "row_measure",
        "yards_per_stitch",
        "grams_per_stitch",
    ):
        val = inputs.get(field)
        if val is None or float(val) <= 0:
            raise ValueError(f"{field} must be positive")

    ball_yards = _get_ball_yards(inputs)
    ball_grams = _get_ball_grams(inputs)

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
        raise ValueError("project_stitches must be positive")
    if float(inputs["seconds_per_stitch"]) <= 0:
        raise ValueError("seconds_per_stitch must be positive")

    yards = gs.estimate_yardage(project_stitches)
    grams = gs.estimate_weight(project_stitches)
    time_delta = estimate_knitting_time(project_stitches, float(inputs["seconds_per_stitch"]))
    time_text = format_knitting_time(time_delta)

    yards_low, yards_high = _range(yards)
    grams_low, grams_high = _range(grams)

    balls_yard = max(1, math.ceil(yards / ball_yards))
    balls_weight = max(1, math.ceil(grams / ball_grams))

    warnings = _plausibility_checks(
        gs.stitch_gauge(),
        gs.row_gauge(),
        None,
        None,
        ball_yards,
        ball_grams,
        float(inputs["seconds_per_stitch"]),
        "advanced",
    )

    assumptions = [
        "Advanced mode: using per-stitch yardage and weight values.",
        f"Gauge: {gs.stitch_gauge():.1f} sts/in x {gs.row_gauge():.1f} rows/in.",
        f"Yardage per stitch: {float(inputs['yards_per_stitch']):.4f} yd.",
        f"Weight per stitch: {float(inputs['grams_per_stitch']):.4f} g.",
        f"Ranges are +/- {int(RANGE_FACTOR * 100)}% of the central estimate.",
    ]

    math_rows = [
        (
            "Yards",
            f"{float(inputs['yards_per_stitch']):.4f} yd/st x {project_stitches:,} sts = {yards:.1f} yd",
        ),
        (
            "Grams",
            f"{float(inputs['grams_per_stitch']):.4f} g/st x {project_stitches:,} sts = {grams:.1f} g",
        ),
        (
            "Time",
            f"{project_stitches:,} sts x {float(inputs['seconds_per_stitch'])} sec = {time_text}",
        ),
    ]

    balls_detail = [
        (
            "By length",
            f"ceil({yards:.1f} yd / {ball_yards} yd/ball) = {balls_yard} ball{'s' if balls_yard != 1 else ''}",
        ),
        (
            "By weight",
            f"ceil({grams:.1f} g / {ball_grams} g/ball) = {balls_weight} ball{'s' if balls_weight != 1 else ''}",
        ),
    ]

    return {
        "project_stitches": project_stitches,
        "yards": round(yards, 1),
        "grams": round(grams, 1),
        "yards_low": round(yards_low, 0),
        "yards_high": round(yards_high, 0),
        "grams_low": round(grams_low, 0),
        "grams_high": round(grams_high, 0),
        "time_text": time_text,
        "hours": round(time_delta.total_seconds() / 3600, 1),
        "balls_yard": balls_yard,
        "balls_weight": balls_weight,
        "meters": round(yards * 0.9144, 1),
        "stitch_gauge": round(gs.stitch_gauge(), 2),
        "row_gauge": round(gs.row_gauge(), 2),
        "confidence": "low",
        "warnings": warnings,
        "math_rows": math_rows,
        "balls_detail": balls_detail,
        "assumptions": assumptions,
        "svg": _estimator_svg(yards, grams, project_stitches),
    }


def _get_ball_yards(inputs):
    "Get yards per ball from either legacy or friendly field names." ""
    raw = inputs.get("ball_yardage") or inputs.get("yarn_per_ball_yards")
    if raw is None or str(raw).strip() == "":
        raise ValueError("yards per ball is required")
    try:
        val = float(raw)
    except (TypeError, ValueError):
        raise ValueError("yards per ball must be a number")
    if val <= 0:
        raise ValueError("yards per ball must be positive")
    return val


def _get_ball_grams(inputs):
    "Get grams per ball from either legacy or friendly field names." ""
    raw = inputs.get("ball_weight") or inputs.get("yarn_per_ball_grams")
    if raw is None or str(raw).strip() == "":
        raise ValueError("grams per ball is required")
    try:
        val = float(raw)
    except (TypeError, ValueError):
        raise ValueError("grams per ball must be a number")
    if val <= 0:
        raise ValueError("grams per ball must be positive")
    return val


def _pos_float(inputs, key, label):
    "Parse a positive float from inputs, raising ValueError on bad values." ""
    raw = inputs.get(key)
    if raw is None or str(raw).strip() == "":
        raise ValueError(f"{label} is required")
    try:
        val = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number")
    if val <= 0:
        raise ValueError(f"{label} must be positive")
    return val


def _estimate_yarn_yards(project_stitches, stitch_gauge, row_gauge):
    """Estimate yards from stitch count and gauge.

    Uses a empirical approximation: yarn per stitch depends on the yarn
    thickness (reflected in gauge).  Finer gauge = thinner yarn = less
    yardage per stitch.
    """
    sts_per_yard = stitch_gauge * 36 * 0.7
    if sts_per_yard <= 0:
        return project_stitches * 0.02
    return project_stitches / sts_per_yard


def _estimate_yarn_grams(yards, ball_yards, ball_grams):
    "Derive grams from yards using the ball's yard-to-weight ratio." ""
    if ball_yards <= 0:
        return yards * 0.2
    grams_per_yard = ball_grams / ball_yards
    return yards * grams_per_yard


def _range(central):
    "Return (low, high) range around a central value." ""
    delta = central * RANGE_FACTOR
    return max(0, central - delta), central + delta


def _plausibility_checks(
    stitch_gauge,
    row_gauge,
    width,
    height,
    ball_yards,
    ball_grams,
    seconds_per_stitch,
    project_type,
):
    "Run sanity checks and return a list of warning strings." ""
    warnings = []
    _check_gauge(warnings, stitch_gauge, row_gauge)
    _check_yarn_ratio(warnings, ball_yards, ball_grams)
    _check_pace(warnings, seconds_per_stitch)
    _check_dimensions(warnings, width, height, project_type)
    return warnings


def _check_gauge(warnings, stitch_gauge, row_gauge):
    if stitch_gauge < 2 or stitch_gauge > 15:
        warnings.append(
            f"Stitch gauge of {stitch_gauge} sts/in is unusual. Typical range is 2-15 sts/in. Double-check your swatch."
        )
    if row_gauge < 3 or row_gauge > 20:
        warnings.append(f"Row gauge of {row_gauge} rows/in is unusual. Typical range is 3-20 rows/in.")


def _check_yarn_ratio(warnings, ball_yards, ball_grams):
    if ball_yards > 0 and ball_grams > 0:
        ratio = ball_yards / ball_grams
        if ratio < 2 or ratio > 12:
            warnings.append(
                f"Yarn ball ratio is {ratio:.1f} yd/g, which is outside the "
                "typical range (2-12 yd/g). Check your ball label."
            )


def _check_pace(warnings, seconds_per_stitch):
    if seconds_per_stitch < 0.5 or seconds_per_stitch > 10:
        warnings.append(f"Pace of {seconds_per_stitch} sec/stitch is unusual. Typical range is 0.5-10 sec/stitch.")


def _check_dimensions(warnings, width, height, project_type):
    if width is None or height is None:
        return
    if project_type == "hat" and (width > 30 or height > 15):
        warnings.append(
            f"Dimensions {width} x {height} in are large for a hat. "
            "Typical hat is 18-24 in circumference, 7-10 in tall."
        )
    if width > 72 or height > 72:
        warnings.append(f"Dimensions {width} x {height} in are very large. Consider whether this is correct.")


def _estimator_svg(yards, grams, project_stitches):
    "Horizontal bar chart of the estimate." ""
    width = 460
    height = 140
    margin = 40
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" ' f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    ]
    max_val = max(yards, grams)
    scale = (width - margin - 20) / max(max_val, 1)

    parts.append(f'<text x="{margin}" y="16" font-size="11" fill="#5a2a75">yards</text>')
    parts.append(f'<rect x="{margin}" y="24" width="{yards * scale:.1f}" height="16" ' 'fill="#7b3fa0" rx="4"/>')
    parts.append(
        f'<text x="{margin + yards * scale + 6:.1f}" y="36" font-size="11" ' f'fill="#5a2a75">{yards:.0f} yd</text>'
    )
    parts.append(f'<text x="{margin}" y="62" font-size="11" fill="#4aa3a2">grams</text>')
    parts.append(f'<rect x="{margin}" y="70" width="{grams * scale:.1f}" height="16" ' 'fill="#4aa3a2" rx="4"/>')
    parts.append(
        f'<text x="{margin + grams * scale + 6:.1f}" y="82" font-size="11" ' f'fill="#4aa3a2">{grams:.0f} g</text>'
    )
    parts.append(
        f'<text x="{margin}" y="115" font-size="11" fill="#888">' f"{project_stitches:,} stitches total</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
