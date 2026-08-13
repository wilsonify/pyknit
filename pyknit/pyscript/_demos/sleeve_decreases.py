"""Sleeve Decreases demo: schedule even decreases down a sleeve.

Uses ``pyknit.sleeve_decreases`` with configurable padding mode and draws a
little staircase SVG showing where decrease rows land.
"""

DEFAULT_INPUTS = {
    "number_of_rows": 61,
    "starting_count": 59,
    "ending_count": 43,
    "decrease_per_row": 2,
    "padding_mode": "after",
}

TITLE = "Sleeve Decreases"


def to_html(result):
    """Render the staircase chart plus the written schedule."""
    return (
        f"<div class='output-box'>{result['svg']}</div>"
        "<h3>Written instructions</h3>"
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
    """Return the decrease schedule string + a staircase SVG."""
    from pyknit import sleeve_decreases

    rows = int(inputs["number_of_rows"])
    starting = int(inputs["starting_count"])
    ending = int(inputs["ending_count"])
    per_row = int(inputs["decrease_per_row"])
    mode = inputs.get("padding_mode", "after")

    if rows <= 0 or starting <= 0 or per_row <= 0:
        raise ValueError("rows, starting count and decrease per row must be positive")

    result = sleeve_decreases(
        rows,
        starting_count=starting,
        ending_count=ending,
        decrease_per_row=per_row,
        padding_mode=mode,
    )
    schedule = _parse_schedule(result)

    return {
        "rows": rows,
        "starting": starting,
        "ending": ending,
        "mode": mode,
        "result": result,
        "schedule": schedule,
        "svg": _staircase_svg(schedule, rows, starting, ending),
    }


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
        token = token.strip()
        match = re.match(r"\[([^\]]*)\]\s*\*\s*(\d+)\s*times", token)
        if match:
            body, times = match.group(1), int(match.group(2))
            pattern = body.split("decrease row")[0]
            pattern = pattern.split("]")[0]
            plain_rows = re.findall(r"do (\d+) rows?", pattern)
            plain = int(plain_rows[0]) if plain_rows else 0
            before_decr = "decrease row" in body.split(",")[0]
            segment = []
            for _ in range(times):
                if before_decr:
                    position += plain
                    segment.append(position)
                    position += 1
                else:
                    segment.append(position)
                    position += 1
                    position += plain
            schedule.extend(segment)
            continue

        if "decrease row" in token:
            count = int(token.split("decrease row")[0].strip() or "1") or 1
            for _ in range(count):
                schedule.append(position)
                position += 1
            continue

        # plain non-decrease group
        plain_rows = re.findall(r"do (\d+) rows?", token)
        if plain_rows:
            position += int(plain_rows[0])
    return schedule


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
        "row →</text>"
    )
    parts.append(
        f'<text x="8" y="{height - 3 * margin}" font-size="11" fill="#5a2a75" '
        'transform="rotate(-90 8 40)">stitches ↓</text>'
    )

    prev_x = margin
    prev_y = height - margin
    for i, row_number in enumerate(schedule):
        x = margin + row_number * x_scale
        # stitch count after i+1 decrease rows
        decreased = min((i + 1) * (per_row or 1), total_decrease)
        y = height - margin - decreased * y_scale
        # horizontal flat span up to this decrease
        parts.append(
            f'<line x1="{prev_x}" y1="{prev_y}" x2="{x}" y2="{prev_y}" '
            'stroke="#c9a7e0" stroke-width="2"/>'
        )
        # vertical drop at the decrease row
        parts.append(
            f'<line x1="{x}" y1="{prev_y}" x2="{x}" y2="{y}" '
            'stroke="#7b3fa0" stroke-width="2"/>'
        )
        parts.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#7b3fa0"/>')
        prev_x, prev_y = x, y

    # remainder line to the final row
    parts.append(
        f'<line x1="{prev_x}" y1="{prev_y}" x2="{width - margin}" y2="{prev_y}" '
        'stroke="#c9a7e0" stroke-width="2"/>'
    )
    parts.append(
        f'<circle cx="{width - margin}" cy="{prev_y}" r="3.5" fill="#4aa3a2"/>'
    )
    parts.append("</svg>")
    return "\n".join(parts)
DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
