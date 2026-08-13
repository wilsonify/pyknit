"""Sock Calculator demo: work out a personalised sock.

Uses ``pyknit.Sock.Sock`` to compute every measurement of a sock from a
person's foot measurements and gauge, then renders a labelled SVG sock.
"""

DEFAULT_INPUTS = {
    "rows_per_inch": 11,
    "stitches_per_inch": 9,
    "circumference_at_top": 10,
    "circumference_of_ankle": 9.5,
    "length_from_sock_top_to_heel_bottom": 7.75,
    "length_from_heel_to_toe": 10.5,
}

TITLE = "Sock Calculator"


def to_html(result):
    """Render the sock schematic + a measurement table."""
    svg = result["svg"]
    rows = ""
    for key, label in (
        ("cast_on_stitches", "Cast on"),
        ("ankle_stitches", "Ankle stitches"),
        ("number_of_decrease_rows", "Leg decrease rows"),
        ("length_from_sock_top_to_heel_flap", "Leg length (in)"),
        ("length_of_heel_flap", "Heel flap length (in)"),
        ("number_of_heel_flap_stitches", "Heel flap stitches"),
        ("length_from_heel_to_beginning_of_toe_decrease", "Heel to toe start (in)"),
        ("length_of_toe_decrease", "Toe decrease length (in)"),
    ):
        rows += (
            f"<tr><th>{label}</th>"
            f"<td class='mono'>{float(result[key]):.2f}</td></tr>"
        )
    return (
        f"<div class='output-box'>{svg}</div>"
        "<table class='instructions'><tbody>"
        + rows
        + "</tbody></table>"
    )


def compute(inputs):
    """Return the Sock object's computed fields as a plain dict + SVG."""
    from pyknit.Sock import Sock

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
        "length_of_heel_flap": sock.length_of_heel_flap,
        "length_from_sock_top_to_heel_flap": sock.length_from_sock_top_to_heel_flap,
        "number_of_heel_flap_stitches": sock.number_of_heel_flap_stitches,
        "length_of_toe_decrease": sock.length_of_toe_decrease,
        "length_from_heel_to_toe": sock.length_from_heel_to_toe,
        "length_from_heel_to_beginning_of_toe_decrease": (
            sock.length_from_heel_to_beginning_of_toe_decrease
        ),
    }
    data["svg"] = _sock_svg(data)
    return data


def _pos(inputs, key):
    value = float(inputs[key])
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def _measurement(data, key, default):
    return float(data.get(key, default))


def _sock_svg(data):
    """Rough labelled sock silhouette with the key measurements."""
    import math

    top = 20
    leg = _measurement(data, "length_from_sock_top_to_heel_flap", 5.5)
    heel = _measurement(data, "length_from_sock_top_to_heel_bottom", 7.75)
    ankle_y = top + 120 * (leg / 8)
    heel_y = top + 120 * (heel / 10)
    toe_y = top + 250

    width = 360
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{toe_y - top + 60}" viewBox="0 0 {width} {toe_y - top + 60}">'
    ]
    leg_left = 100
    leg_right = 180
    decreasing_y = top + 120 * (
        (data["length_from_sock_top_to_heel_flap"] + 0.5) / 8
    )

    # leg rectangle
    parts.append(
        f'<rect x="{leg_left}" y="{top}" width="{leg_right - leg_left}" '
        f'height="{min(decreasing_y, heel_y) - top}" '
        'fill="#e8dcf2" stroke="#7b3fa0" stroke-width="2"/>'
    )
    # heel flap
    parts.append(
        f'<rect x="{leg_left}" y="{heel_y}" width="{leg_right - leg_left}" '
        f'height="{top + 45 - heel_y}" fill="#f3ecf7" '
        'stroke="#7b3fa0" stroke-width="2"/>'
    )
    # foot
    foot_left = leg_left + (leg_right - leg_left) / 2 - 15
    parts.append(
        f'<path d="M {foot_left} {heel_y} L {foot_left} {toe_y - 15} '
        f'Q {foot_left - 12} {toe_y} {foot_left - 2} {toe_y} '
        f'L {leg_right + 12} {toe_y} Q {leg_right + 24} {toe_y} '
        f'{leg_right + 24} {toe_y - 15} L {leg_right + 24} {heel_y} Z" '
        'fill="#e8dcf2" stroke="#7b3fa0" stroke-width="2"/>'
    )

    def label(y, text, color="#5a2a75"):
        parts.append(
            f'<text x="{leg_right + 34}" y="{y}" font-size="11" fill="{color}">'
            f"{text}</text>"
        )

    parts.append(
        f'<rect x="{leg_right - 6}" y="{top}" width="2" '
        f'height="{heel_y - top}" fill="#4aa3a2" opacity="0.6"/>'
    )
    label(top + 8, f"top · cast on {data['cast_on_stitches']}")
    label(ankle_y + 6, f"ankle · {data['ankle_stitches']} sts")
    label(
        heel_y + 4,
        f"heel flap {data['length_of_heel_flap']:.2f}",
    )
    label(toe_y - 10, f"toe decrease {data['length_of_toe_decrease']:.2f}")
    parts.append(
        f'<text x="{leg_left}" y="{toe_y + 40}" font-size="11" fill="#5a2a75">'
        f"stitches per inch {data['stitches_per_inch']} · "
        f"rows per inch {data['rows_per_inch']}</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)
DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
