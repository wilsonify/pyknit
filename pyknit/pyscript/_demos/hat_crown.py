"""Hat Crown demo: plan the crown decreases for a hat.

Uses ``pyknit.Hat.Hat.crown_decreases`` for written instructions and derived
a simple top-down SVG crown locally so the demo stays browser-friendly.
"""

DEFAULT_INPUTS = {"repeats": 8, "stitches": 80}

TITLE = "Hat Crown Planner"


def to_html(result):
    """Render crown plan: SVG + the written decrease rounds."""
    rows = "".join(
        f"<tr><td class='mono'>{_esc(line)}</td></tr>" for line in result["rounds"]
    )
    return (
        f"<div class='output-box'>{result['svg']}</div>"
        "<h3>Written instructions</h3>"
        f"<div class='output-box'><table class='instructions'><tbody>{rows}</tbody></table></div>"
    )


def _esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def compute(inputs):
    """Return crown decrease rounds (written) plus a top-down SVG crown."""
    from pyknit.Hat import Hat
    import math

    repeats = int(inputs["repeats"])
    stitches = int(inputs["stitches"])
    if repeats <= 0 or stitches <= 0:
        raise ValueError("repeats and stitches must be positive integers")

    hat = Hat()
    rounds = hat.crown_decreases(repeats, stitches)

    counts = []
    for line in rounds:
        words = str(line).split()
        for word in words:
            if word.startswith("("):
                try:
                    counts.append(int(word.strip("()")))
                except ValueError:
                    pass

    return {
        "repeats": repeats,
        "stitches": stitches,
        "rounds": rounds,
        "svg": _crown_svg(repeats, counts),
    }


def _crown_svg(repeats, counts):
    """Top-down crown SVG: wedge lines + concentric stitch-count rings."""
    import math

    size = 320
    cx = cy = size / 2
    outer = size / 2 - 20

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">'
    ]
    if counts:
        max_count = max(counts)
        for count in counts:
            radius = outer * (count / max_count)
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{radius:.1f}" '
                f'fill="none" stroke="#c9a7e0" stroke-width="1" '
                f'stroke-dasharray="4 3" opacity="0.8"/>'
            )

    for i in range(repeats):
        angle = 2 * math.pi * i / repeats
        x2 = cx + outer * math.cos(angle)
        y2 = cy + outer * math.sin(angle)
        parts.append(
            f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#7b3fa0" stroke-width="2"/>'
        )
        parts.append(
            f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="4" fill="#7b3fa0"/>'
        )
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="#7b3fa0"/>')
    parts.append(
        f'<text x="{cx}" y="{size - 10}" text-anchor="middle" font-size="13" '
        'fill="#5a2a75">top-down crown · '
        + (' · '.join(str(c) for c in counts)) + " sts</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)
DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
