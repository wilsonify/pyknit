"""Knit Simulator demo: visualize knitting step by step.

A browser-based knitting simulator that accepts simple instructions and
animates the process of building fabric stitch by stitch.  Supports cast-on,
knit, purl, and basic repeats with play/pause/step/reset controls.
"""

import html
import json
import math

DEFAULT_INPUTS = {
    "instructions": "co 20\n* k2 p2 across\n* k2 p2 across\n* k2 p2 across\nk all",
    "speed": "normal",
}

TITLE = "Knit Simulator"

SPEED_PRESETS = {
    "slow": {"label": "Slow motion", "ms_per_step": 800},
    "normal": {"label": "Normal", "ms_per_step": 400},
    "fast": {"label": "Fast", "ms_per_step": 150},
}

VALID_OPS = {"co", "knit", "k", "purl", "p", "yo", "k2tog", "ssk", "bo"}


def compute(inputs):
    raw = inputs.get("instructions", "")
    speed_key = inputs.get("speed", "normal")

    if speed_key not in SPEED_PRESETS:
        raise ValueError(f"Unknown speed: {speed_key}")

    steps = _parse_instructions(raw)
    if not steps:
        raise ValueError("No valid instructions found. Use: co, k, p, k2tog, ssk, yo, bo")

    stitch_state = []
    fabric_rows = []
    current_row = []
    step_log = []
    needle_left = []
    needle_right = list(stitch_state)
    row_index = 0
    stitch_index = 0

    for step in steps:
        op = step["op"]
        count = step.get("count", 1)
        repeat = step.get("repeat", False)

        if op == "co":
            n = count
            stitch_state = list(range(1, n + 1))
            needle_right = list(stitch_state)
            needle_left = []
            current_row = list(stitch_state)
            step_log.append({
                "op": "cast on",
                "detail": f"{n} stitches",
                "stitches": list(stitch_state),
                "row": None,
                "highlight": list(range(n)),
            })

        elif op in ("knit", "k"):
            if repeat:
                worked = _work_across(stitch_state, "knit", count)
            else:
                worked = _work_row(stitch_state, "knit")
            fabric_rows.append(current_row[:])
            current_row = worked[:]
            stitch_state = worked[:]
            row_index += 1
            step_log.append({
                "op": f"knit row {row_index}",
                "detail": f"{len(worked)} stitches knit",
                "stitches": list(worked),
                "row": row_index,
                "highlight": list(range(len(worked))),
            })

        elif op in ("purl", "p"):
            if repeat:
                worked = _work_across(stitch_state, "purl", count)
            else:
                worked = _work_row(stitch_state, "purl")
            fabric_rows.append(current_row[:])
            current_row = worked[:]
            stitch_state = worked[:]
            row_index += 1
            step_log.append({
                "op": f"purl row {row_index}",
                "detail": f"{len(worked)} stitches purled",
                "stitches": list(worked),
                "row": row_index,
                "highlight": list(range(len(worked))),
            })

        elif op == "yo":
            stitch_state.append(0)
            current_row = list(stitch_state)
            step_log.append({
                "op": "yarn over",
                "detail": f"{len(stitch_state)} stitches (yo added)",
                "stitches": list(stitch_state),
                "row": row_index,
                "highlight": [len(stitch_state) - 1],
            })

        elif op == "k2tog":
            if len(stitch_state) >= 2:
                stitch_state = stitch_state[:-2] + [stitch_state[-1]]
                current_row = list(stitch_state)
                step_log.append({
                    "op": "k2tog",
                    "detail": f"{len(stitch_state)} stitches remaining",
                    "stitches": list(stitch_state),
                    "row": row_index,
                    "highlight": [len(stitch_state) - 1],
                })

        elif op == "ssk":
            if len(stitch_state) >= 2:
                stitch_state = stitch_state[2:] + [stitch_state[0]]
                current_row = list(stitch_state)
                step_log.append({
                    "op": "ssk",
                    "detail": f"{len(stitch_state)} stitches remaining",
                    "stitches": list(stitch_state),
                    "row": row_index,
                    "highlight": [0],
                })

        elif op == "bo":
            if stitch_state:
                n_bo = min(count, len(stitch_state))
                stitch_state = stitch_state[n_bo:]
                current_row = list(stitch_state)
                step_log.append({
                    "op": f"bind off {n_bo}",
                    "detail": f"{len(stitch_state)} stitches remaining",
                    "stitches": list(stitch_state),
                    "row": row_index,
                    "highlight": [],
                })

    if not step_log:
        raise ValueError("No steps produced. Check your instructions.")

    fabric_svg = _render_fabric(fabric_rows, current_row)
    svg = _render_step_view(step_log[0]["stitches"], step_log[0]["highlight"], 0, len(step_log))

    return {
        "steps": step_log,
        "total_steps": len(step_log),
        "fabric_rows": [row for row in fabric_rows] + ([current_row] if current_row else []),
        "final_stitches": list(stitch_state),
        "fabric_svg": fabric_svg,
        "svg": svg,
        "speed_ms": SPEED_PRESETS[speed_key]["ms_per_step"],
        "speed_label": SPEED_PRESETS[speed_key]["label"],
        "warnings": _validate_instructions(raw),
    }


def _parse_instructions(raw):
    steps = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.lower().split()
        if not parts:
            continue

        repeat = False
        if parts[0] == "*":
            repeat = True
            parts = parts[1:]
            if not parts:
                continue

        op = parts[0]
        count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1

        if op in ("co", "cast", "caston"):
            steps.append({"op": "co", "count": count, "repeat": False})
        elif op in ("knit", "k"):
            steps.append({"op": "knit", "count": count, "repeat": repeat})
        elif op in ("purl", "p"):
            steps.append({"op": "purl", "count": count, "repeat": repeat})
        elif op == "yo":
            steps.append({"op": "yo", "count": 1, "repeat": repeat})
        elif op == "k2tog":
            steps.append({"op": "k2tog", "count": 1, "repeat": repeat})
        elif op == "ssk":
            steps.append({"op": "ssk", "count": 1, "repeat": repeat})
        elif op in ("bo", "bindoff", "bind off"):
            steps.append({"op": "bo", "count": count, "repeat": False})
    return steps


def _work_row(stitches, op):
    """Process a row of stitches. Returns new stitch state."""
    result = []
    for s in stitches:
        if op == "knit":
            result.append(s)
        elif op == "purl":
            result.append(s)
    return result


def _work_across(stitches, op, count):
    """Process stitches across with repeat count."""
    result = list(stitches)
    for _ in range(count - 1):
        result = result[:]
    return result


def _render_fabric(rows, current_row):
    if not rows and not current_row:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="40"><text x="10" y="25" font-size="12" fill="#888">No fabric yet — run some instructions</text></svg>'

    all_rows = list(rows)
    if current_row:
        all_rows.append(current_row)

    max_width = max(len(r) for r in all_rows) if all_rows else 10
    cell = 16
    padding = 20
    width = padding * 2 + max_width * cell
    height = padding * 2 + len(all_rows) * cell

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    ]

    for row_idx, row in enumerate(all_rows):
        y = padding + row_idx * cell
        x_offset = padding + (max_width - len(row)) * cell // 2
        for col_idx, stitch in enumerate(row):
            x = x_offset + col_idx * cell
            if stitch == 0:
                color = "#f3ecf7"
                stroke = "#dcc8e8"
            elif row_idx % 2 == 0:
                color = "#7b3fa0"
                stroke = "#5a2a75"
            else:
                color = "#b38fd4"
                stroke = "#7b3fa0"
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell - 1}" height="{cell - 1}" '
                f'fill="{color}" stroke="{stroke}" rx="2"/>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


def _render_step_view(stitches, highlight, step_idx, total_steps):
    if not stitches:
        stitches = [0]

    cell = 24
    padding = 30
    width = padding * 2 + len(stitches) * cell
    height = padding * 2 + 80

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    ]

    y_top = padding
    y_bottom = padding + cell + 4

    parts.append(f'<text x="{padding}" y="{y_top - 8}" font-size="11" fill="#888">Left needle</text>')
    parts.append(f'<text x="{padding}" y="{y_bottom + cell + 14}" font-size="11" fill="#888">Right needle</text>')

    for i, stitch in enumerate(stitches):
        x = padding + i * cell
        is_highlight = i in highlight
        if is_highlight:
            fill = "#e74c3c"
            stroke = "#c0392b"
        elif stitch == 0:
            fill = "#f3ecf7"
            stroke = "#dcc8e8"
        else:
            fill = "#7b3fa0"
            stroke = "#5a2a75"

        parts.append(
            f'<rect x="{x}" y="{y_top}" width="{cell - 2}" height="{cell - 2}" '
            f'fill="{fill}" stroke="{stroke}" rx="3" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{x + cell // 2 - 1}" y="{y_top + cell // 2 + 4}" '
            f'font-size="10" fill="white" text-anchor="middle" font-weight="600">'
            f'{stitch}</text>'
        )

    needle_y = y_top + cell + 2
    parts.append(
        f'<line x1="{padding - 5}" y1="{needle_y}" '
        f'x2="{padding + len(stitches) * cell}" y2="{needle_y}" '
        f'stroke="#b38fd4" stroke-width="3" stroke-linecap="round"/>'
    )

    info_y = y_bottom + cell + 28
    parts.append(
        f'<text x="{width // 2}" y="{info_y}" font-size="12" fill="#5a2a75" '
        f'text-anchor="middle" font-weight="600">'
        f'Step {step_idx + 1} of {total_steps}</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


def _validate_instructions(raw):
    warnings = []
    lines = [l.strip() for l in raw.strip().split("\n") if l.strip() and not l.strip().startswith("#")]
    if not lines:
        warnings.append("No instructions provided.")
        return warnings

    first = lines[0].lower().split()
    if not first or first[0] not in ("co", "cast", "caston"):
        warnings.append("Instructions should start with a cast-on (co 20).")

    has_knit = any(l.strip().lower().split()[0] in ("knit", "k", "*") for l in lines if l.strip())
    has_purl = any(l.strip().lower().split()[0] in ("purl", "p") for l in lines if l.strip())
    if not has_knit and not has_purl:
        warnings.append("No knit or purl rows found. Add some k or p instructions.")

    return warnings


def to_html(result):
    parts = []

    parts.append(
        f"<div class='stat-row'>"
        f"<span class='stat-pill'>Steps: <em>{result['total_steps']}</em></span>"
        f"<span class='stat-pill'>Final stitches: <em>{len(result['final_stitches'])}</em></span>"
        f"<span class='stat-pill'>Speed: <em>{_esc(result['speed_label'])}</em></span>"
        f"</div>"
    )

    if result.get("warnings"):
        items = "".join(f"<li>{_esc(w)}</li>" for w in result["warnings"])
        parts.append(
            "<div class='warning-box'><strong>Heads up</strong>"
            f"<ul>{items}</ul></div>"
        )

    parts.append("<div class='output-box'>")
    parts.append("<h3>Current stitch view</h3>")
    parts.append(result["svg"])
    parts.append("</div>")

    parts.append("<div class='output-box'>")
    parts.append("<h3>Fabric so far</h3>")
    parts.append(result["fabric_svg"])
    parts.append("</div>")

    parts.append("<div class='output-box'>")
    parts.append("<h3>Step-by-step log</h3>")
    parts.append("<table class='instructions'><thead><tr><th>#</th><th>Operation</th><th>Detail</th></tr></thead><tbody>")
    for i, step in enumerate(result["steps"]):
        parts.append(
            f"<tr><td class='mono'>{i + 1}</td><td>{_esc(step['op'])}</td>"
            f"<td>{_esc(step['detail'])}</td></tr>"
        )
    parts.append("</tbody></table></div>")

    parts.append(
        "<p class='field-hint'>This is an instructional visualization. "
        "For physical yarn and needle animation, see a video tutorial.</p>"
    )

    return "\n".join(parts)


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


def store_result_for_player(result):
    """Store simulation steps in a JS global so the JavaScript player can
    read them without depending on the Python ``shared`` module."""
    try:
        from js import window  # noqa: F401

        steps = result.get("steps", [])
        # JS needs a plain list of plain dicts — pyodide proxies work but
        # converting via JSON is safest for deep nested structures.
        import json

        window.sim_steps = json.loads(json.dumps(steps))
    except Exception:
        pass
