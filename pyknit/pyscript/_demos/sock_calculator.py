"""Sock Calculator demo: a beginner-friendly guided sock plan.

Uses ``pyknit.Sock.Sock`` to compute every measurement and to generate the
step-by-step instructions (cast-on, leg decreases, heel flap, heel turn,
gusset, foot and toe).  This module only renders the plan and draws the
proportional SVG diagram.
"""

import html

from pyknit.Sock import (
    CUFF_RIB_INCHES,
    TOE_FINISH_STITCHES,
    Sock,
)

DEFAULT_INPUTS = {
    "rows_per_inch": 11,
    "stitches_per_inch": 9,
    "circumference_at_top": 10,
    "circumference_of_ankle": 9.5,
    "length_from_sock_top_to_heel_bottom": 7.75,
    "length_from_heel_to_toe": 10.5,
}

TITLE = "Sock Calculator"


def compute(inputs):
    """Return the Sock plan as a plain dict plus the SVG diagram."""
    sock = Sock()
    sock.init(
        rows_per_inch=_pos(inputs, "rows_per_inch"),
        stitches_per_inch=_pos(inputs, "stitches_per_inch"),
        circumference_at_top=_pos(inputs, "circumference_at_top"),
        circumference_of_ankle=_pos(inputs, "circumference_of_ankle"),
        length_from_sock_top_to_heel_bottom=_pos(
            inputs, "length_from_sock_top_to_heel_bottom"
        ),
        length_from_heel_to_toe=_pos(inputs, "length_from_heel_to_toe"),
    )

    data = {
        "rows_per_inch": sock.rows_per_inch,
        "stitches_per_inch": sock.stitches_per_inch,
        "cast_on_stitches": sock.cast_on_stitches,
        "ankle_stitches": sock.ankle_stitches,
        "number_of_decrease_rows": sock.number_of_decrease_rows,
        "number_of_heel_flap_stitches": sock.number_of_heel_flap_stitches,
        "instep_stitches": sock.instep_stitches,
        "length_of_heel_flap": sock.length_of_heel_flap,
        "length_from_sock_top_to_heel_flap": sock.length_from_sock_top_to_heel_flap,
        "length_from_sock_top_to_heel_bottom": (
            sock.length_from_sock_top_to_heel_bottom
        ),
        "length_of_toe_decrease": sock.length_of_toe_decrease,
        "length_from_heel_to_beginning_of_toe_decrease": (
            sock.length_from_heel_to_beginning_of_toe_decrease
        ),
        "length_from_heel_to_toe": sock.length_from_heel_to_toe,
        "rib_rounds": sock.rib_rounds,
        "plain_leg_rounds": sock.plain_leg_rounds,
        "foot_rounds": sock.foot_rounds(),
        "heel_turn_remaining": sock.heel_turn_remaining(),
        "gusset_stitches_after_pickup": sock.gusset_stitches_after_pickup(),
        "leg_decrease_schedule": sock.leg_decrease_schedule(),
        "toe": sock._toe_row_schedule(),
    }
    plan = sock.get_plan()
    data["warnings"] = plan["warnings"]
    data["plan"] = plan
    data["svg"] = _sock_svg(data)
    return data


def _pos(inputs, key):
    value = float(inputs[key])
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


# ---------------------------------------------------------------------------
# SVG schematic
# ---------------------------------------------------------------------------


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _sock_svg(m):
    """Draw a proportional sock diagram with stitch counts and measurements.

    The sock is drawn as a bent schematic: the leg hangs down on the left,
    the heel sits at the bottom-left, and the foot extends to the right
    ending in a rounded toe.  All section lengths and widths scale with the
    real measurements and stitch counts.
    """
    cast = m["cast_on_stitches"]
    ankle = m["ankle_stitches"]
    flap = m["number_of_heel_flap_stitches"]
    rib_in = _clamp(m["rib_rounds"] / m["rows_per_inch"], 0, 1.2)

    total_in = m["length_from_sock_top_to_heel_bottom"] + m["length_from_heel_to_toe"]
    pp = _clamp(300 / total_in, 6, 30)  # pixels per inch

    bx = 30
    ty = 22
    leg_len = m["length_from_sock_top_to_heel_bottom"]
    ankle_y = ty + m["length_from_sock_top_to_heel_flap"] * pp
    heel_y = ty + leg_len * pp
    rib_y = ty + rib_in * pp

    foot_even = m["length_from_heel_to_beginning_of_toe_decrease"]
    toe_in = m["length_of_toe_decrease"]
    toe_start_x = bx + foot_even * pp
    toe_end_x = toe_start_x + toe_in * pp

    depth_cuff = _clamp(14 + cast * 0.45, 26, 90)
    depth_ankle = _clamp(13 + ankle * 0.43, 24, 84)
    sole_y = heel_y
    toe_rise = depth_ankle * 0.55

    h = heel_y + 44
    w = max(340, toe_end_x + 40, bx + max(depth_cuff, depth_ankle) + 150)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(w)}" '
        f'height="{int(h)}" viewBox="0 0 {int(w)} {int(h)}" '
        'font-family="system-ui, sans-serif">'
    ]

    # instep line from toe tip back to the ankle front
    toe_tip = (toe_end_x, sole_y - toe_rise)
    instep_end = (bx + depth_ankle, ankle_y)
    cuff_front = (bx + depth_cuff, ty)

    # --- body ---
    body = (
        f"M {bx} {ty} "
        f"L {bx} {sole_y} "
        f"L {toe_start_x} {sole_y} "
        f"Q {toe_end_x} {sole_y} {toe_tip[0]:.1f} {toe_tip[1]:.1f} "
        f"L {instep_end[0]:.1f} {instep_end[1]:.1f} "
        f"L {cuff_front[0]:.1f} {cuff_front[1]:.1f} Z"
    )
    parts.append(
        f'<path d="{body}" fill="#eef0fa" stroke="#7b3fa0" stroke-width="2"/>'
    )

    # --- cuff ribbing band ---
    if rib_y > ty + 3:
        parts.append(
            f'<path d="M {bx} {ty} L {bx} {rib_y:.1f} '
            f'L {cuff_front[0]:.1f} {rib_y:.1f} '
            f'L {cuff_front[0]:.1f} {ty} Z" '
            'fill="#d9cceb" stroke="#7b3fa0" stroke-width="2"/>'
        )

    # --- heel flap tab (drawn behind the leg for clarity) ---
    flap_px = max(0, heel_y - ankle_y)
    if flap_px > 4:
        parts.append(
            f'<rect x="{bx - 9}" y="{ankle_y:.1f}" width="9" '
            f'height="{flap_px:.1f}" rx="2" fill="#e6d7f0" '
            'stroke="#7b3fa0" stroke-width="1.5" stroke-dasharray="4 3"/>'
        )

    # --- foot / toe divider ---
    if toe_start_x > bx + 4:
        x = toe_start_x
        top_y = instep_end[1] + (toe_tip[1] - instep_end[1]) * (
            (x - instep_end[0]) / max(1, toe_tip[0] - instep_end[0])
        )
        parts.append(
            f'<line x1="{x:.1f}" y1="{sole_y:.1f}" x2="{x:.1f}" '
            f'y2="{top_y:.1f}" stroke="#7b3fa0" stroke-width="1" '
            'stroke-dasharray="3 3"/>'
        )
        parts.append(
            f'<text x="{x + 4:.1f}" y="{sole_y - 8:.1f}" font-size="11" '
            'fill="#5a2a75">toe starts</text>'
        )

    # --- section labels on the left ---
    parts.append(
        f'<text x="{bx + 4}" y="{ty - 6}" font-size="12" font-weight="600" '
        f'fill="#5a2a75">cast on {cast} sts</text>'
    )
    parts.append(
        f'<text x="{bx + 4}" y="{min(sole_y - 4, max(ty + 14, rib_y + 14)):.1f}" '
        'font-size="11" fill="#5a2a75">cuff · k2, p2 rib</text>'
    )
    if flap_px > 4:
        parts.append(
            f'<text x="{bx - 9}" y="{(ankle_y + heel_y) / 2:.1f}" '
            'font-size="11" fill="#5a2a75" text-anchor="end">'
            f'heel flap · {flap} sts</text>'
        )
    parts.append(
        f'<text x="{bx + 4}" y="{min(sole_y - 4, max(rib_y, ty + 18) + 16):.1f}" '
        'font-size="11" fill="#5a2a75">leg · '
        f'{m["number_of_decrease_rows"]} decrease rounds</text>'
    )
    parts.append(
        f'<text x="{bx + 4}" y="{sole_y + 18:.1f}" font-size="11" '
        f'fill="#5a2a75">foot · {ankle} sts</text>'
    )
    parts.append(
        f'<text x="{toe_end_x - 6:.1f}" y="{sole_y - toe_rise - 6:.1f}" '
        'font-size="11" fill="#5a2a75" text-anchor="end">toe · '
        f'{m["toe"]["finish_stitches"]} sts to finish</text>'
    )

    # --- dimension lines on the right ---
    dim_x = max(bx + depth_cuff, bx + depth_ankle, toe_end_x) + 26

    def dim_vertical(y1, y2, label, at_x):
        mid = (y1 + y2) / 2
        parts.append(
            f'<line x1="{at_x}" y1="{y1:.1f}" x2="{at_x}" y2="{y2:.1f}" '
            'stroke="#4aa3a2" stroke-width="1"/>'
        )
        for yy in (y1, y2):
            parts.append(
                f'<line x1="{at_x - 4}" y1="{yy:.1f}" x2="{at_x + 4}" '
                f'y2="{yy:.1f}" stroke="#4aa3a2" stroke-width="1"/>'
            )
        parts.append(
            f'<text x="{at_x + 7}" y="{mid:.1f}" font-size="11" fill="#16707f">'
            f"{label}</text>"
        )

    def dim_horizontal(x1, x2, label, at_y):
        mid = (x1 + x2) / 2
        parts.append(
            f'<line x1="{x1:.1f}" y1="{at_y}" x2="{x2:.1f}" y2="{at_y}" '
            'stroke="#4aa3a2" stroke-width="1"/>'
        )
        for xx in (x1, x2):
            parts.append(
                f'<line x1="{xx:.1f}" y1="{at_y - 4}" x2="{xx:.1f}" '
                f'y2="{at_y + 4}" stroke="#4aa3a2" stroke-width="1"/>'
            )
        parts.append(
            f'<text x="{mid:.1f}" y="{at_y - 6}" font-size="11" '
            'fill="#16707f" text-anchor="middle">'
            f"{label}</text>"
        )

    dim_vertical(ty, ankle_y, f"leg {m['length_from_sock_top_to_heel_flap']:.2f} in", dim_x)
    if flap_px > 4:
        dim_vertical(ankle_y, heel_y, f"heel flap {m['length_of_heel_flap']:.2f} in", dim_x)
    dim_horizontal(bx, toe_start_x, f"foot {foot_even:.2f} in", sole_y + 30)
    dim_horizontal(toe_start_x, toe_end_x, f"toe {toe_in:.2f} in", sole_y + 44)

    # total length annotation
    parts.append(
        f'<text x="{bx}" y="{heel_y + 64:.1f}" font-size="11" fill="#5a2a75">'
        f'gauge · {m["stitches_per_inch"]:g} sts/in × '
        f'{m["rows_per_inch"]:g} rows/in</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------


def _esc(text):
    return html.escape(str(text), quote=False)


SECTION_END = "</section>"


def _render_steps(steps):
    parts = ["<ol class='plan-steps'>"]
    for step in steps:
        parts.append(f"<li>{_esc(step)}</li>")
    parts.append("</ol>")
    return "\n".join(parts)


def _render_table(table):
    parts = ["<table class='plan-table'><thead><tr>"]
    for col in table["columns"]:
        parts.append(f"<th>{_esc(col)}</th>")
    parts.append("</tr></thead><tbody>")
    for row in table["rows"]:
        parts.append("<tr>")
        for cell in row:
            parts.append(f"<td>{_esc(cell)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "\n".join(parts)


def _render_sections(plan):
    blocks = []
    for section in plan["sections"]:
        parts = ['<section class="plan-section">',
                 f'<h4>{_esc(section["heading"])}</h4>']
        if section.get("intro"):
            parts.append(f'<p class="plan-intro">{_esc(section["intro"])}</p>')
        if section.get("steps"):
            parts.append(_render_steps(section["steps"]))
        table = section.get("table")
        if table:
            parts.append(_render_table(table))
        parts.append(SECTION_END)
        blocks.append("\n".join(parts))
    return "\n".join(blocks)


def to_html(result):
    """Render the SVG diagram plus the full guided plan."""
    plan = result["plan"]

    warnings = ""
    if result["warnings"]:
        items = "".join(
            f"<li>{_esc(w)}</li>" for w in result["warnings"]
        )
        warnings = (
            f"<div class='warning-box'><strong>Before you start</strong>"
            f"<ul>{items}</ul></div>"
        )

    assumptions = "".join(
        f"<li>{_esc(a)}</li>" for a in plan["assumptions"]
    )

    rows = ""
    for key, (label, value, unit) in plan["measurements"].items():
        rows += (
            f"<tr><th>{_esc(label)}</th>"
            f"<td class='mono'>{value}</td><td class='mono unit'>{unit}</td></tr>"
        )

    return "\n".join([
        f"<div class='output-box'>{result['svg']}</div>",
        warnings,
        "<section class='plan-section'>",
        "<h4>How this sock is built</h4>",
        f"<ul class='plan-assumptions'>{assumptions}</ul>",
        SECTION_END,
        "<section class='plan-section'>",
        "<h4>Your numbers at a glance</h4>",
        "<table class='plan-table measure-table'><tbody>",
        rows,
        "</tbody></table>",
        SECTION_END,
        "<h3 class='plan-title'>Knit along</h3>",
        _render_sections(plan),
    ])


DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}