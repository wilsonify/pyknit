"""Sleeve Decreases demo: schedule even decreases down a sleeve.

Uses ``pyknit.sleeve_decreases`` with configurable padding mode and draws a
staircase SVG showing where decrease rows land, plus a row-by-round plan
table and transparent math explanation.
"""

DEFAULT_INPUTS = {
    "number_of_rows": 61,
    "starting_count": 59,
    "ending_count": 43,
    "decrease_per_row": 2,
    "padding_mode": "after",
}

TITLE = "Sleeve Decreases"

PAD_LABELS = {
    "after": "After each decrease (default)",
    "before": "Before each decrease",
    "both": "Split evenly around each decrease",
    "none": "No plain rows between decreases",
}


def to_html(result):
    """Render the staircase chart, summary pills, math, and plan table."""
    pills = [
        ("Starting", f"{result['starting']} sts"),
        ("Ending", f"{result['ending']} sts"),
        ("Decrease rows", f"{result['summary']['number_of_decrease_rows']}"),
        ("Spacing", f"every {result['summary']['spacing']} rows"),
    ]
    if result["summary"]["remainder"] > 0:
        pills.append(("Remainder", f"{result['summary']['remainder']} extra k2tog"))
    pill_html = "".join(
        f"<div class='raglan-pill'><span class='label'>{label}</span>"
        f"<span class='value'>{value}</span></div>"
        for label, value in pills
    )

    math_rows = "".join(f"<li>{_esc(m)}</li>" for m in result["math"])
    assumption_rows = "".join(f"<li>{_esc(a)}</li>" for a in result["assumptions"])

    plan_rows = ""
    for row in result["plan"]:
        kind_class = "mono" if row["kind"] == "Decrease" else ""
        plan_rows += (
            "<tr>"
            f"<td class='mono'>{row['round']}</td>"
            f"<td class='{kind_class}'>{_esc(row['kind'])}</td>"
            f"<td class='mono'>{_esc(row['transition'])}</td>"
            f"<td>{_esc(row['instruction'])}</td>"
            "</tr>"
        )

    warnings = ""
    if result.get("warnings"):
        items = "".join(f"<li>{_esc(w)}</li>" for w in result["warnings"])
        warnings = (
            f"<div class='warning-box'><strong>Worth a second look</strong>"
            f"<ul>{items}</ul></div>"
        )

    est = result.get("_estimator_data", {})
    send_to = ""
    if est.get("stitch_count"):
        send_to = (
            "<div class='button-row'><button class='btn-secondary send-to-estimator' "
            f"data-stitches='{est['stitch_count']}' data-type='{est.get('project_type', 'custom')}'>"
            "Send to Yarn Estimator &rarr;</button></div>"
        )

    return (
        "<style>"
        ".sleeve-pills{display:flex;flex-wrap:wrap;gap:0.5rem;margin:0.6rem 0;}"
        ".sleeve-pill{border:1px solid #ddd8d4;border-radius:6px;padding:0.4rem 0.65rem;background:#fdfcfa;flex:1 1 auto;min-width:90px;text-align:center;}"
        ".sleeve-pill .label{display:block;font-size:0.72rem;color:#6b6572;text-transform:uppercase;letter-spacing:0.04em;}"
        ".sleeve-pill .value{font-size:0.95rem;font-weight:700;color:#2b2333;}"
        ".sleeve-rounds{width:100%;border-collapse:collapse;font-size:0.95rem;}"
        ".sleeve-rounds th,.sleeve-rounds td{border:1px solid #e5e1dc;padding:0.5rem 0.55rem;text-align:left;vertical-align:top;}"
        ".sleeve-rounds th{background:#f3ecf7;color:#5a2a75;font-weight:700;}"
        "</style>"
        f"<div class='output-box'>{result['svg']}</div>"
        f"<div class='sleeve-pills'>{pill_html}</div>"
        f"{send_to}"
        "<section class='plan-section'>"
        "<h4>How this schedule is calculated</h4>"
        f"<ul class='plan-assumptions'>{math_rows}</ul>"
        "</section>"
        f"{warnings}"
        "<section class='plan-section'>"
        "<h4>Assumptions</h4>"
        f"<ul class='plan-assumptions'>{assumption_rows}</ul>"
        "</section>"
        "<h3 class='plan-title'>Row-by-round instructions</h3>"
        "<section class='plan-section'>"
        "<table class='sleeve-rounds'>"
        "<thead><tr><th>Row</th><th>Type</th><th>Stitches</th><th>Instruction</th></tr></thead>"
        f"<tbody>{plan_rows}</tbody></table>"
        "</section>"
    )


def _esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def compute(inputs):
    """Return the decrease schedule with plan table, math, and SVG."""
    from pyknit import sleeve_decreases

    rows = int(inputs["number_of_rows"])
    starting = int(inputs["starting_count"])
    ending = int(inputs["ending_count"])
    per_row = int(inputs["decrease_per_row"])
    mode = inputs.get("padding_mode", "after")

    _validate(rows, starting, ending, per_row, mode)

    total_decrease = starting - ending
    num_dec_rows = total_decrease // per_row
    remainder = total_decrease % per_row
    spacing_rows = (rows - num_dec_rows) / max(num_dec_rows, 1)

    result_str = sleeve_decreases(
        rows,
        starting_count=starting,
        ending_count=ending,
        decrease_per_row=per_row,
        padding_mode=mode,
    )
    schedule = _parse_schedule(result_str)
    plan = _build_plan(schedule, starting, ending, per_row, mode)
    math = _build_math(rows, starting, ending, per_row, num_dec_rows, spacing_rows, remainder, mode)
    assumptions = _build_assumptions(per_row, mode)
    warnings = _build_warnings(spacing_rows, num_dec_rows, rows)

    return {
        "rows": rows,
        "starting": starting,
        "ending": ending,
        "mode": mode,
        "result": result_str,
        "schedule": schedule,
        "svg": _staircase_svg(schedule, rows, starting, ending),
        "plan": plan,
        "math": math,
        "assumptions": assumptions,
        "warnings": warnings,
        "summary": {
            "total_decrease": total_decrease,
            "number_of_decrease_rows": num_dec_rows,
            "spacing": f"{spacing_rows:.1f}",
            "remainder": remainder,
        },
        "_estimator_data": {
            "stitch_count": max(1, round((starting + ending) / 2 * rows)),
            "project_type": "sweater",
            "source": "sleeve_decreases",
        },
    }


def _validate(rows, starting, ending, per_row, mode):
    if rows <= 0:
        raise ValueError("total rows must be positive")
    if starting <= 0:
        raise ValueError("starting stitch count must be positive")
    if ending <= 0:
        raise ValueError("ending stitch count must be positive")
    if per_row <= 0:
        raise ValueError("stitches to remove per decrease row must be positive")
    if starting <= ending:
        raise ValueError(
            f"starting count ({starting}) must be greater than ending count ({ending}) "
            "for decreases to be needed"
        )
    total_decrease = starting - ending
    if per_row > total_decrease:
        raise ValueError(
            f"stitches to remove per decrease row ({per_row}) exceeds "
            f"total decrease needed ({total_decrease})"
        )
    num_dec_rows = total_decrease // per_row
    if num_dec_rows > rows:
        raise ValueError(
            f"not enough rows ({rows}) for {num_dec_rows} decrease rows; "
            "increase the total rows or the stitches removed per row"
        )
    if mode not in ("before", "after", "both", "none"):
        raise ValueError(
            f"spacing must be one of 'After each decrease', 'Before each decrease', "
            f"'Split evenly', or 'None'; got '{mode}'"
        )


def _build_plan(schedule, starting, ending, per_row, mode):
    plan = []
    current = starting
    total_decrease = starting - ending

    for i, row_number in enumerate(schedule):
        before = current
        decreased = min((i + 1) * per_row, total_decrease)
        after = starting - decreased
        if mode == "after":
            instruction = f"k2tog at each side of underarm marker ({per_row} sts removed)"
        elif mode == "before":
            instruction = f"k2tog at each side of underarm marker ({per_row} sts removed)"
        elif mode == "both":
            instruction = f"k2tog at each side of underarm marker ({per_row} sts removed)"
        else:
            instruction = f"k2tog at each side of underarm marker ({per_row} sts removed)"

        plan.append({
            "round": row_number + 1,
            "kind": "Decrease",
            "before": before,
            "after": after,
            "transition": f"{before} -> {after}",
            "instruction": instruction,
        })
        current = after

    if not schedule:
        plan.append({
            "round": 1,
            "kind": "Decrease",
            "before": starting,
            "after": ending,
            "transition": f"{starting} -> {ending}",
            "instruction": f"k2tog at each side of underarm marker ({per_row} sts removed)",
        })

    return plan


def _build_math(rows, starting, ending, per_row, num_dec_rows, spacing_rows, remainder, mode):
    total_decrease = starting - ending
    math = [
        f"Total decrease needed: {starting} - {ending} = {total_decrease} stitches",
        f"Decrease rows: {total_decrease} / {per_row} = {num_dec_rows} decrease rows",
        f"Plain rows available: {rows} - {num_dec_rows} = {rows - num_dec_rows} plain rows",
        f"Spacing: {rows - num_dec_rows} plain rows / {num_dec_rows} groups = "
        f"~{spacing_rows:.1f} rows between decrease rows",
    ]
    if remainder > 0:
        math.append(
            f"Remainder: {total_decrease} % {per_row} = {remainder} leftover stitch(s) "
            f"-- work {remainder} extra k2tog at the end of the last row"
        )
    mode_desc = {
        "after": "plain rows follow each decrease row",
        "before": "plain rows precede each decrease row",
        "both": "plain rows are split evenly around each decrease row",
        "none": "no plain rows between decrease rows",
    }
    math.append(f"Padding mode: {mode_desc[mode]}")
    return math


def _build_assumptions(per_row, mode):
    assumptions = [
        f"Each decrease row removes exactly {per_row} stitch(es) (k2tog at each "
        "decrease point along the row).",
        "Decrease points are placed at the underarm seam for a symmetrical taper.",
        "The sleeve is knit flat or in the round from the upper arm toward the cuff.",
    ]
    return assumptions


def _build_warnings(spacing_rows, num_dec_rows, rows):
    warnings = []
    if spacing_rows < 2 and num_dec_rows > 1:
        warnings.append(
            f"Decrease rows are only ~{spacing_rows:.1f} rows apart, which creates "
            "a steep taper. Consider using more rows, fewer decreases, or a "
            "smaller difference between starting and ending stitch counts."
        )
    if rows < num_dec_rows * 2:
        warnings.append(
            "There are very few plain rows between decrease rows. The sleeve "
            "may taper abruptly. Consider increasing the total rows available."
        )
    return warnings


DECREASE_ROW = "decrease row"


def _parse_schedule(text):
    """Return the 0-indexed row numbers on which decrease rows occur.

    Handles every padding mode emitted by ``sleeve_decreases``:
    ``[decrease row, do N rows in pattern] * M times`` (after),
    ``[do N rows in pattern, decrease row] * M times`` (before),
    ``[do A rows in pattern, decrease row, do B rows in pattern] * M times``
    (both), and bare ``decrease row`` items (none).
    """
    import re

    schedule = []
    position = 0
    tokens = re.split(r",\s*(?![^\[]*\])", str(text))
    for token in tokens:
        position, added = _parse_item(token, position)
        schedule.extend(added)
    return schedule


def _parse_item(token, position):
    """Handle a single comma-split instruction token."""
    import re

    token = token.strip()
    match = re.match(r"\[([^\]]*)\]\s*\*\s*(\d+)\s*times", token)
    if match:
        return _parse_repeated(match, position)
    if DECREASE_ROW in token:
        return _parse_decrease(token, position)
    plain_rows = re.findall(r"do (\d+) rows?", token)
    if plain_rows:
        return position + int(plain_rows[0]), []
    return position, []


def _parse_repeated(match, position):
    """Parse a ``[body] * N times`` bracket group."""
    import re

    body, times = match.group(1), int(match.group(2))
    pattern = body.split(DECREASE_ROW)[0].split("]")[0]
    plain_rows = re.findall(r"do (\d+) rows?", pattern)
    plain = int(plain_rows[0]) if plain_rows else 0
    before_decr = DECREASE_ROW in body.split(",")[0]
    added = []
    for _ in range(times):
        if before_decr:
            position += plain
            added.append(position)
            position += 1
        else:
            added.append(position)
            position += 1
            position += plain
    return position, added


def _parse_decrease(token, position):
    """Parse a bare ``decrease row`` item (possibly counted)."""
    count = int(token.split(DECREASE_ROW)[0].strip() or "1") or 1
    return position + count, [position + i for i in range(count)]


def _staircase_svg(schedule, rows, starting, ending):
    """Staircase line chart: stitch count per row with decreases marked."""
    width = 460
    height = 220
    margin = 36
    total_decrease = starting - ending
    per_row = schedule and (total_decrease // len(schedule)) or 0

    y_scale = (height - 2 * margin) / max(total_decrease, 1)
    x_scale = (width - 2 * margin) / max(rows, 1)

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    ]
    # axes
    parts.append(
        f'<line x1="{margin}" y1="{height - margin}" '
        f'x2="{width - margin}" y2="{height - margin}" stroke="#999"/>'
    )
    parts.append(
        f'<line x1="{margin}" y1="{margin * 0.4}" x2="{margin}" '
        f'y2="{height - margin}" stroke="#999"/>'
    )
    parts.append(
        f'<text x="{margin}" y="{height - 10}" font-size="11" fill="#5a2a75">'
        "row -></text>"
    )
    parts.append(
        f'<text x="8" y="{height - 3 * margin}" font-size="11" fill="#5a2a75" '
        'transform="rotate(-90 8 40)">stitches</text>'
    )

    prev_x = margin
    prev_y = height - margin
    for i, row_number in enumerate(schedule):
        x = margin + row_number * x_scale
        decreased = min((i + 1) * (per_row or 1), total_decrease)
        y = height - margin - decreased * y_scale
        parts.append(
            f'<line x1="{prev_x}" y1="{prev_y}" x2="{x}" y2="{prev_y}" '
            'stroke="#c9a7e0" stroke-width="2"/>'
        )
        parts.append(
            f'<line x1="{x}" y1="{prev_y}" x2="{x}" y2="{y}" '
            'stroke="#7b3fa0" stroke-width="2"/>'
        )
        parts.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#7b3fa0"/>')
        if i == 0 or i == len(schedule) - 1:
            label = starting - decreased
            parts.append(
                f'<text x="{x + 5}" y="{y - 5}" font-size="10" fill="#5a2a75">'
                f'{label} sts</text>'
            )
        prev_x, prev_y = x, y

    parts.append(
        f'<line x1="{prev_x}" y1="{prev_y}" x2="{width - margin}" y2="{prev_y}" '
        'stroke="#c9a7e0" stroke-width="2"/>'
    )
    parts.append(
        f'<circle cx="{width - margin}" cy="{prev_y}" r="3.5" fill="#4aa3a2"/>'
    )
    parts.append(
        f'<text x="{width - margin - 5}" y="{prev_y - 8}" font-size="10" '
        f'fill="#4aa3a2" text-anchor="end">{ending} sts</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
