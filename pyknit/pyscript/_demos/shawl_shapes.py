"""Shawl Shapes demo: generate written instructions for four shawl shapes.

Uses ``pyknit.shawl_shapes.generate_shawl`` for the instructions and draws
a simple silhouette of the chosen shape.
"""

DEFAULT_INPUTS = {
    "shape": "crescent",
    "width": 24,
    "length": 30,
    "stitch_count": 16,
    "stitch_measure": 4,
    "row_count": 20,
    "row_measure": 4,
}

TITLE = "Shawl Shapes"


def to_html(result):
    """Render the shape silhouette plus the instruction list."""
    steps = "".join(
        f"<tr><td class='mono'>{_esc(step)}</td></tr>"
        for step in result["instructions"]
    )
    return (
        f"<div class='output-box'>{result['svg']}</div>"
        "<h3>Instructions</h3>"
        f"<div class='output-box'><table class='instructions'><tbody>{steps}</tbody></table></div>"
    )


def _esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def compute(inputs):
    """Return instructions + an SVG silhouette for the requested shape."""
    from pyknit import shawl_shapes
    from pyknit.GaugeSwatch import GaugeSwatch

    shape = inputs.get("shape", "crescent")
    if shape not in shawl_shapes.SUPPORTED_SHAPES:
        raise ValueError(
            "shape must be one of " + ", ".join(shawl_shapes.SUPPORTED_SHAPES)
        )

    width = float(inputs["width"])
    length = float(inputs["length"])
    mm = _measure(inputs)
    gauge = GaugeSwatch(
        stitch_count=mm["stitch_count"],
        stitch_measure=mm["stitch_measure"],
        row_count=mm["row_count"],
        row_measure=mm["row_measure"],
        units="in",
    )
    if width <= 0 or length <= 0:
        raise ValueError("width and length must be positive")

    instructions = shawl_shapes.generate_shawl(shape, width, length, gauge)
    return {
        "shape": shape,
        "width": width,
        "length": length,
        "instructions": instructions,
        "svg": _shape_svg(shape),
    }


def _measure(inputs):
    for key in ("stitch_count", "stitch_measure", "row_count", "row_measure"):
        if float(inputs[key]) <= 0:
            raise ValueError("gauge values must be positive")
    return {key: float(inputs[key]) for key in inputs if key.startswith(("stitch_", "row_"))}


def _shape_svg(shape):
    """Simple SVG silhouette per shape type."""
    size = 320
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">']
    stroke = 'fill="#e8dcf2" stroke="#7b3fa0" stroke-width="2"'
    if shape == "square":
        parts.append(f'<rect x="40" y="40" width="240" height="240" {stroke}/>')
    elif shape == "rectangle":
        parts.append(f'<rect x="40" y="120" width="240" height="120" {stroke}/>')
    elif shape == "triangle":
        parts.append(
            f'<polygon points="160,30 60,290 260,290" {stroke}/>'
        )
    elif shape == "crescent":
        parts.append(
            f'<path d="M 40 250 C 40 100 160 60 280 180 '
            f'C 200 230 90 250 40 250 Z" {stroke}/>'
        )
    parts.append(
        f'<text x="160" y="{size - 12}" text-anchor="middle" font-size="13" '
        f'fill="#5a2a75">{shape}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)
DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
