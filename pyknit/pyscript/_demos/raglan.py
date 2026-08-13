"""Raglan Sweater demo: marker setup for a top-down raglan.

Uses ``pyknit.raglan_increases`` and draws a simple raglan schematic.
"""

DEFAULT_INPUTS = {
    "neck_stitches": 80,
    "arm_stitches": 30,
    "bust_stitches": 100,
    "neck_to_bust_rows": 8,
    "increase_per_increase_row": 8,
    "armpit_stitches": 4,
}

TITLE = "Raglan Sweater"


def to_html(result):
    """Render the raglan schematic plus the marker setup instructions."""
    return (
        f"<div class='output-box'>{result['svg']}</div>"
        "<h3>Marker setup</h3>"
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
    """Return the raglan marker setup + an SVG schematic."""
    from pyknit import raglan_increases

    neck = int(inputs["neck_stitches"])
    arm = int(inputs["arm_stitches"])
    bust = int(inputs["bust_stitches"])
    rows = int(inputs["neck_to_bust_rows"])
    per_row = int(inputs.get("increase_per_increase_row", 8))
    armpit = int(inputs.get("armpit_stitches", 4))

    if min(neck, arm, bust, rows) <= 0:
        raise ValueError("all stitch counts and rows must be positive")

    result = raglan_increases(
        neck,
        arm_stitches=arm,
        bust_stitches=bust,
        neck_to_bust_rows=rows,
        increase_per_increase_row=per_row,
        armpit_stitches=armpit,
    )
    return {
        "neck": neck,
        "arm": arm,
        "bust": bust,
        "rows": rows,
        "result": result,
        "svg": _raglan_svg(neck, bust),
    }


def _raglan_svg(neck, bust):
    """Simple top-down circle: neck hole with four raglan seams."""
    size = 340
    cx = cy = size / 2
    neck_r = max(18, neck / 8)
    bust_r = max(70, bust / 2.8)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" '
        f'height="{size}" viewBox="0 0 {size} {size}">'
    ]
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{bust_r}" '
        'fill="#e8dcf2" stroke="#7b3fa0" stroke-width="2"/>'
    )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{neck_r}" fill="white" '
        'stroke="#5a2a75" stroke-width="2"/>'
    )

    for angle in (45, 135, 225, 315):
        import math

        rad = math.radians(angle)
        x2 = cx + bust_r * math.cos(rad)
        y2 = cy + bust_r * math.sin(rad)
        parts.append(
            f'<line x1="{cx + neck_r * math.cos(rad):.1f}" '
            f'y1="{cy + neck_r * math.sin(rad):.1f}" x2="{x2:.1f}" '
            f'y2="{y2:.1f}" stroke="#4aa3a2" stroke-width="3"/>'
        )
    parts.append(
        f'<text x="{cx}" y="{cy - bust_r - 12}" font-size="12" fill="#5a2a75" '
        'text-anchor="middle">'
        f"neck {neck} sts</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)
DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
