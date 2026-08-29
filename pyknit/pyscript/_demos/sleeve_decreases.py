"""Sleeve Decreases demo: schedule even decreases down a sleeve.

Uses ``pyknit.sleeve_decreases`` with configurable padding mode and draws a
staircase SVG showing where decrease rows land, plus a row-by-round plan
table and transparent math explanation.

The schedule is generated directly from the measured inputs (starting count,
ending count, available rows, stitches removed per decrease row) so the
displayed spacing, row numbers and stitch counts are always consistent with
the same arithmetic.  The generated row-by-row plan contains exactly
``number_of_rows`` rows and distributes the decrease rounds as evenly as
possible.
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
        ("Shaping rows", f"{result['rows']}"),
        ("Decrease rounds", f"{result['summary']['number_of_decrease_rows']}"),
        ("Per round", f"-{result['decrease_per_row']} sts"),
        ("Spacing", f"every {result['summary']['spacing']} rows"),
    ]
    if result["summary"]["remainder"] > 0:
        pills.append(("Remainder", f"{result['summary']['remainder']} extra k2tog"))
    pill_html = "".join(
        f"<div class='raglan-pill'><span class='label'>{label}</span>" f"<span class='value'>{value}</span></div>"
        for label, value in pills
    )

    math_rows = "".join(f"<li>{_esc(m)}</li>" for m in result["math"])
    assumption_rows = "".join(f"<li>{_esc(a)}</li>" for a in result["assumptions"])

    # decrease-row numbers (1-indexed) for the knitter
    dec_numbers = result.get("decrease_row_numbers") or [r + 1 for r in result["schedule"]]
    if dec_numbers:
        dec_list = ", ".join(str(n) for n in dec_numbers)
        dec_summary = f"<p class='plan-intro'><strong>Decrease rows:</strong> { _esc(dec_list) } (rows { _esc(dec_numbers[0]) }&ndash;{ _esc(dec_numbers[-1]) } of {result['rows']})</p>"  # noqa: E501
    else:
        dec_summary = ""

    # Full row-by-row plan: one row per knitted row
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
        warnings = f"<div class='warning-box'><strong>Worth a second look</strong>" f"<ul>{items}</ul></div>"

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
        ".sleeve-pill{border:1px solid #ddd8d4;border-radius:6px;padding:0.4rem 0.65rem;background:#fdfcfa;flex:1 1 auto;min-width:90px;text-align:center;}"  # noqa: E501
        ".sleeve-pill .label{display:block;font-size:0.72rem;color:#6b6572;text-transform:uppercase;letter-spacing:0.04em;}"  # noqa: E501
        ".sleeve-pill .value{font-size:0.95rem;font-weight:700;color:#2b2333;}"
        ".sleeve-rounds{width:100%;border-collapse:collapse;font-size:0.95rem;}"
        ".sleeve-rounds th,.sleeve-rounds td{border:1px solid #e5e1dc;padding:0.5rem 0.55rem;text-align:left;vertical-align:top;}"  # noqa: E501
        ".sleeve-rounds th{background:#f3ecf7;color:#5a2a75;font-weight:700;}"
        "</style>"
        f"<div class='output-box'>{result['svg']}</div>"
        f"<div class='sleeve-pills'>{pill_html}</div>"
        f"{dec_summary}"
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
        f"<p class='plan-intro'>Work from the upper arm (row 1) toward the cuff (row {result['rows']}). Decrease rows remove {result['decrease_per_row']} sts at the underarm seam; plain rows are knit even.</p>"  # noqa: E501
        "<table class='sleeve-rounds'>"
        "<thead><tr><th>Row</th><th>Type</th><th>Stitches</th><th>Instruction</th></tr></thead>"
        f"<tbody>{plan_rows}</tbody></table>"
        "</section>"
    )


def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
    # Generate the schedule directly from the measured inputs so it is
    # mathematically consistent and evenly distributed.  The old
    # ``_parse_schedule`` path is kept only as a fallback for legacy text.
    try:
        schedule = _generate_schedule(rows, num_dec_rows, mode)
    except Exception:
        schedule = _parse_schedule(result_str)

    # Full row-by-row plan: exactly ``rows`` entries, preserving total count
    plan = _build_full_plan(schedule, rows, starting, ending, per_row, remainder)
    # Decrease-only rows (for backwards compatibility) are available as
    # ``plan`` callers that expect length == num_dec_rows can filter.
    math = _build_math(rows, starting, ending, per_row, num_dec_rows, spacing_rows, remainder, mode)
    assumptions = _build_assumptions(per_row, mode)
    warnings = _build_warnings(spacing_rows, num_dec_rows, rows)

    decrease_row_numbers = [r + 1 for r in schedule]

    return {
        "rows": rows,
        "starting": starting,
        "ending": ending,
        "mode": mode,
        "decrease_per_row": per_row,
        "result": result_str,
        "schedule": schedule,
        "decrease_row_numbers": decrease_row_numbers,
        "svg": _staircase_svg(schedule, rows, starting, ending),
        "plan": plan,
        # backwards-compat: callers that expected only decrease rows can
        # derive it; we keep the full plan as ``plan`` so the table shows
        # every row the knitter will actually work.
        "full_plan": plan,
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
            f"starting count ({starting}) must be greater than ending count ({ending}) " "for decreases to be needed"
        )
    total_decrease = starting - ending
    if per_row > total_decrease:
        raise ValueError(
            f"stitches to remove per decrease row ({per_row}) exceeds " f"total decrease needed ({total_decrease})"
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


def _generate_schedule(rows, num_dec_rows, mode):
    """Return 0-indexed decrease row positions, evenly spaced across *rows*.

    The schedule preserves the total row count: the sum of decrease rows and
    the plain rows distributed between them equals *rows*.  Intervals are
    balanced via :func:`pyknit._calculate_spacing` so remainder groups are
    spread one at a time.

    Modes:
    - ``after``: decrease then plain (the historical default).
    - ``before``: plain then decrease.
    - ``both``: plain rows split evenly around each decrease.
    - ``none``: decreases back-to-back at the start (no distribution).
    """
    from pyknit import _calculate_spacing

    if num_dec_rows <= 0:
        return []
    if mode == "none":
        return list(range(num_dec_rows))
    padding = rows - num_dec_rows
    if padding < 0:
        return list(range(num_dec_rows))
    plan = _calculate_spacing(padding, num_dec_rows, "after" if mode != "before" else "before")
    return _layout_schedule(plan, mode)


def _layout_schedule(plan, mode):
    schedule = []
    pos = 0
    for interval, groups in plan:
        for _ in range(groups):
            if mode == "before":
                pos += interval
                schedule.append(pos)
                pos += 1
            elif mode == "both":
                pos += interval // 2
                schedule.append(pos)
                pos += 1
                pos += interval - interval // 2
            else:  # after
                schedule.append(pos)
                pos += 1 + interval
    return schedule


def _make_plan_entry(idx, kind, before, after, instruction):
    """Assemble a single plan row dictionary."""
    return {
        "round": idx + 1,
        "kind": kind,
        "before": before,
        "after": after,
        "transition": f"{before} -> {after}",
        "instruction": instruction,
    }


def _decrease_target_removed(dec_index, num_dec, per_row, remainder, total_decrease):
    """Stitches removed after a given decrease row."""
    target = min(
        (dec_index + 1) * per_row,
        total_decrease - (remainder if dec_index < num_dec - 1 else 0),
    )
    if dec_index == num_dec - 1 and remainder > 0:
        target = total_decrease
    return target


def _decrease_instruction(per_row, remainder, dec_index, num_dec, ending):
    """Build the human-readable instruction for a decrease row."""
    if remainder and dec_index == num_dec - 1:
        return f"k2tog at each side ({per_row} sts) plus {remainder} extra " f"k2tog to reach {ending} sts"
    if remainder == 0 or dec_index < num_dec - 1:
        return f"k2tog at each side of underarm marker ({per_row} sts removed)"
    if remainder:
        return f"k2tog at each side plus {remainder} extra k2tog " f"({per_row + remainder} sts removed)"
    return f"k2tog at each side of underarm marker ({per_row} sts removed)"


def _build_full_plan(schedule, rows, starting, ending, per_row, remainder):
    """Build the full row-by-row plan with exactly *rows* entries."""
    dec_set = set(schedule)
    sorted_dec = sorted(dec_set)
    num_dec = len(schedule)
    plan = []
    current = starting
    total_decrease = starting - ending
    for idx in range(rows):
        before = current
        if idx not in dec_set:
            plan.append(_make_plan_entry(idx, "Plain", before, current, "Knit plain (no shaping)"))
            current = before
            continue
        dec_index = sorted_dec.index(idx)
        target_removed = _decrease_target_removed(dec_index, num_dec, per_row, remainder, total_decrease)
        after = starting - target_removed
        if after < ending:
            after = ending
        instruction = _decrease_instruction(per_row, remainder, dec_index, num_dec, ending)
        plan.append(_make_plan_entry(idx, "Decrease", before, after, instruction))
        current = after
    # sanity: ensure final count matches ending
    if plan and plan[-1]["after"] != ending:
        plan[-1]["after"] = ending
        plan[-1]["transition"] = f"{plan[-1]['before']} -> {ending}"
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
        f"Each decrease row removes exactly {per_row} stitch(es) (k2tog at each " "decrease point along the row).",
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
    """Legacy parser for ``sleeve_decreases`` instruction strings (fallback)."""
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
    """Parse a ``[body] * N times`` bracket group (legacy fallback)."""
    import re

    body, times = match.group(1), int(match.group(2))
    # Find all plain counts in the body; for 'both' mode there are two.
    plain_rows = re.findall(r"do (\d+) rows?", body)
    # For the simple after/before cases there is one count; for both, two.
    if len(plain_rows) == 2:
        # both mode: before and after
        before = int(plain_rows[0])
        after = int(plain_rows[1])
        added = []
        for _ in range(times):
            position += before
            added.append(position)
            position += 1
            position += after
        return position, added
    plain = int(plain_rows[0]) if plain_rows else 0
    # Determine whether the decrease comes first (after) or last (before)
    # by looking at the first comma-separated piece.
    first_piece = body.split(",")[0].strip()
    before_decr = DECREASE_ROW in first_piece
    added = []
    for _ in range(times):
        if before_decr:
            added.append(position)
            position += 1
            position += plain
        else:
            position += plain
            added.append(position)
            position += 1
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
        '<svg xmlns="http://www.w3.org/2000/svg" ' f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    ]
    # axes
    parts.append(
        f'<line x1="{margin}" y1="{height - margin}" ' f'x2="{width - margin}" y2="{height - margin}" stroke="#999"/>'
    )
    parts.append(f'<line x1="{margin}" y1="{margin * 0.4}" x2="{margin}" ' f'y2="{height - margin}" stroke="#999"/>')
    parts.append(f'<text x="{margin}" y="{height - 10}" font-size="11" fill="#5a2a75">' "row -></text>")
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
        parts.append(f'<line x1="{prev_x}" y1="{prev_y}" x2="{x}" y2="{prev_y}" ' 'stroke="#c9a7e0" stroke-width="2"/>')
        parts.append(f'<line x1="{x}" y1="{prev_y}" x2="{x}" y2="{y}" ' 'stroke="#7b3fa0" stroke-width="2"/>')
        parts.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#7b3fa0"/>')
        if i == 0 or i == len(schedule) - 1:
            label = starting - decreased
            parts.append(f'<text x="{x + 5}" y="{y - 5}" font-size="10" fill="#5a2a75">' f"{label} sts</text>")
        prev_x, prev_y = x, y

    parts.append(
        f'<line x1="{prev_x}" y1="{prev_y}" x2="{width - margin}" y2="{prev_y}" ' 'stroke="#c9a7e0" stroke-width="2"/>'
    )
    parts.append(f'<circle cx="{width - margin}" cy="{prev_y}" r="3.5" fill="#4aa3a2"/>')
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
